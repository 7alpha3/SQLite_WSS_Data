'''
SQLite_WSS_Data main script file
- connect to WSS server to receive environmental data
- store received data in a SQLite3 database
- manage received data and database
'''

import sys, copy, time, json, traceback
from logger_file import logging, CustomLogger
from flag_manager import FlagManager
from process_lock import ProcessLock
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import datetime as dt
import numpy as np
import jsonschema
import contextlib
import socket
import asyncio
import websockets
import sqlite3

wss_uri = 'wss://websockets.weatherstem.com?target=001D0A71267A'

database_path = '/Users/7alph/Documents/PyFiles/SQLite_WSS_Data/websocket_data.db'

# global reference to database connection used to close connection on program exit
db_connection = None
# global reference to trim_scheduler (BackgroundScheduler instance) used to shutdown trim_scheduler on program exit
trim_scheduler = None

# Function to establish a SQLite3 database connection
def connect_to_database(): 
    global db_connection

    try:
        connection = sqlite3.connect(database_path, timeout=5, isolation_level='IMMEDIATE')
        print_and_log(f'Connected to database: {database_path}')
        
        db_connection = connection
        
        return database_create(connection)

    except sqlite3.Error as err:
        logger.debug(f'Error connecting to the database: {err}')
        return None, None

def database_create(connection):
    # get the cursor for this instance
    cursor = connection.cursor()
    # create table and index if they don't exist yet
    create_table(cursor)
    create_index(cursor)
    # commit any changes to database
    connection.commit()
    return connection, cursor

def create_table(cursor):
    # Create a table to store received data
    try:
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS websocket_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP, 
                ts INTEGER UNIQUE, 
                temperature FLOAT, 
                humidity FLOAT, 
                dew_point FLOAT, 
                heat_index FLOAT
            )'''
        )
    except sqlite3.Error as err:
        logger.debug(f'Error in create_table(): {err}')

def create_index(cursor):
    # Create index idx_ts on the ts column
    try:
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_ts ON websocket_data (ts)')
    except sqlite3.Error as err:
        logger.debug(f'Error in create_index(): {err}')

def is_database_connected(connection):

    try:
        cursor = connection.cursor()
        cursor.execute('SELECT 1')
        return True
    except sqlite3.Error:
        logger.debug('Database not connected')
        return False

# Function to close the SQLite3 database connection
def close_database_connection():
    global db_connection

    if db_connection is not None:
        try:
            db_connection.close()
            print_and_log('Database connection closed')
        except sqlite3.Error as err:
            logger.debug(f'Error closing the database connection: {err}')

# Function to check for and fill time gaps in data before next data entry into database 
def fill_time_gaps(next_data, cursor):
    # get the timestamp being inserted next 
    next_ts = next_data[0]
    
    last_data = get_latest_data(cursor)
    
    count = get_record_count(cursor)
    
    # if record count is zero then this the database was reset at midnight. Insert a starting record for midnight.
    if count == 0 or last_data is None:
        logger.debug(f'next_ts: {next_ts}, (count == 0 or last_data is None)')

        insert_midnight_record(next_data, cursor)    
        fill_time_gaps(next_data, cursor)
        return

    # Check if there is only one record
    if count == 1 and last_data is not None:
        logger.debug(f'next_ts: {next_ts}, (count == 1 and last_data is not None)')
        insert_midnight_record(last_data, cursor)    

    # if last_data is None then something went wrong. Nothing to do but log the error and return
    if last_data is None:
        logger.debug(f'next_ts: {next_ts}, problem in fill_time_gaps(). An empty database?')
        return

    # Calculate the seconds elapsed since the last recorded entry
    time_gap = next_ts -  last_data[0]

    if 5 < time_gap < 10:
        logger.debug(f'Logging time_gap - Gap: {time_gap}')

    if time_gap > 6:
        # There is a time gap exceeding 6 seconds
        # Calculate the number of missed readings
        quotient = time_gap // 5

        logger.debug(f'time gap exceeding 6 sec - Gap: {time_gap}, quotient: {quotient}')

        if quotient > 1:
            missed_count = quotient - 1
        else:
            return

        insert_missed_readings(last_data, next_data, missed_count, cursor)

def get_latest_data(cursor):
    try:
        # Get the latest timestamp and data in the database
        cursor.execute('SELECT ts, temperature, humidity, dew_point, heat_index FROM websocket_data WHERE ts = (SELECT MAX(ts) FROM websocket_data)')
        return cursor.fetchone()
    except sqlite3.Error as err:
        logger.debug(f'Error get_latest_data(): {err}')
        return None

def get_record_count(cursor):
    try:
        cursor.execute('SELECT COUNT(*) FROM websocket_data')
        return cursor.fetchone()[0]
    except sqlite3.Error as err:
        logger.debug(f'Error get_record_count(): {err}')
        return 0

def insert_midnight_record(record, cursor):

    col_data = copy.deepcopy(list(record))
    col_data[0] = midnight_time()[0]
    insert_db_record(col_data, cursor) 
    logger.debug(f'Midnight Record - data: {col_data}')

def insert_missed_readings(last_data, next_data, missed_count, cursor):

    last_ts, last_temperature, last_humidity, last_dew_point, last_heat_index = last_data
    next_ts, next_temperature, next_humidity, next_dew_point, next_heat_index = next_data

    logger.debug(f'Missing readings - missed: {missed_count}')
    logger.debug(f'Last readings - Last ts: {last_ts}, Last Temp: {last_temperature}, Last Humidity: {last_humidity}...')
    logger.debug(f'Next readings - Next ts: {next_ts}, Next Temp: {next_temperature}, Next Humidity: {next_humidity}...')
    
    # Estimate the missed readings, interpolate between adjacent readings.
    temperature_values = interpolate_values(last_temperature, next_temperature, num_values=missed_count)
    humidity_values = interpolate_values(last_humidity, next_humidity, num_values=missed_count)
    dew_point_values = interpolate_values(last_dew_point, next_dew_point, num_values=missed_count)
    heat_index_values = interpolate_values(last_heat_index, next_heat_index, num_values=missed_count)
    
    # build a list of tuples for all missed records in the time gap
    bulk_data = [
    (
        last_ts + ((i + 1) * 5),
        temperature_values[i],
        humidity_values[i],
        dew_point_values[i],
        heat_index_values[i],
    )
    for i in range(missed_count)
    ]
    
    logger.debug(f'Insert missed records bulk data: {bulk_data}')
    # insert missed records into the table
    insert_bulk_records(bulk_data, cursor)


def interpolate_values(start_value, end_value, num_values=1):

    if num_values <= 0:
        raise ValueError('Number of values to interpolate must be at least 1')

    if num_values == 1:
        interpolated_value = (start_value + end_value) / 2
        return np.round(np.array([interpolated_value]), 1)

    # Calculate the step size for interpolation
    step = (end_value - start_value) / (num_values + 1)
    # Generate the interpolated values as a NumPy array
    return np.round(np.array([start_value + step * (i + 1) for i in range(num_values)]), 1)

def trim_database(trim_flag, cursor):
    
    if trim_flag.is_set():
        return

    midnight_ts, midnight, now = midnight_time()
    logger.debug(f'trim_database() Time: {now}')
    try:
        # SQL DELETE statement to remove rows where timestamp is earlier than trim_limit
        cursor.execute(f'DELETE FROM websocket_data WHERE ts < {midnight_ts}')
        rows_deleted = cursor.rowcount
    except sqlite3.Error as err:
        logger.debug(f'Error in trim_database(): {err}')
        return

    trim_flag.set_flag()

    logger.debug(f'trim_database() rows_deleted: {rows_deleted}')

def trim_operation():

    midnight_ts, midnight, now = midnight_time()
    logger.debug(f'trim_operation() Time: {now}')

    try:
        connection = sqlite3.connect(database_path, timeout=5, isolation_level='IMMEDIATE')
        cursor = connection.cursor()
    except sqlite3.Error as err:
        logger.debug(f'Error connecting to the database: {err}')
        return

    try:
        # SQL DELETE statement to remove rows where timestamp is earlier than trim_limit
        cursor.execute(f'DELETE FROM websocket_data WHERE ts < {midnight_ts}')
        rows_deleted = cursor.rowcount
        connection.commit()
    except sqlite3.Error as err:
        logger.debug(f'Error in trim_operation(): {err}')
        return
    # Close the database connection
    connection.close()

    logger.debug(f'trim_operation() rows_deleted: {rows_deleted}')

def start_trim_scheduler():
    global trim_scheduler

    if trim_scheduler is not None:
        trim_scheduler.shutdown()

    scheduler = BackgroundScheduler()

    midnight_trigger = CronTrigger(hour=0, minute=0)
    midnight_trigger2 = CronTrigger(hour=0, minute=1)

    scheduler.add_job(trim_operation, trigger=midnight_trigger, misfire_grace_time=30)
    scheduler.add_job(trim_operation, trigger=midnight_trigger2, misfire_grace_time=30)
    
    scheduler.start()

    trim_scheduler = scheduler
    return scheduler

def midnight_time():
    now = dt.datetime.now()
    midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)
    return int(midnight.timestamp()), midnight, now

def get_column_data(data):

    ts = int(data['ts'])
    temp = round(data['polledConditions'][0]['temp'], 1)
    hum = round(data['polledConditions'][0]['hum'], 1)
    dew_point = round(data['polledConditions'][0]['dew_point'], 1)
    heat_index = round(data['polledConditions'][0]['heat_index'], 1)
    # return tuple of data columns 
    return ts, temp, hum, dew_point, heat_index

# Function to handle received JSON data and save it to the database
def handle_received_data(data, trim_flag, connection, cursor):

    col_data = get_column_data(data)

    fill_time_gaps(col_data, cursor)    
    insert_db_record(col_data, cursor)
    trim_database(trim_flag, cursor)

    connection.commit()

def insert_db_record(col_data, cursor):
    try:
        cursor.execute('INSERT OR IGNORE INTO websocket_data (ts, temperature, humidity, dew_point, heat_index) VALUES (?, ?, ?, ?, ?)', col_data)
    except sqlite3.Error as err:
        logger.debug(f'Error inserting data into the database: {err}')

def insert_bulk_records(bulk_data, cursor):
    
    if len(bulk_data) <= 0:
        logger.debug('Nothing to do, empty list passed to insert_bulk_records()')
        return
    
    validate_bulk_data(bulk_data)
    
    try:
        cursor.executemany('INSERT OR IGNORE INTO websocket_data (ts, temperature, humidity, dew_point, heat_index) VALUES (?, ?, ?, ?, ?)', bulk_data)
        logger.debug(f'Bulk data insert of {cursor.rowcount} data records')
    except sqlite3.Error as err:
        logger.debug(f'Error inserting bulk data into the database: {err}')
        
def validate_bulk_data(bulk_data):
    
    schema = {
        'type': 'array',
        'items': {
            'minItems': 5,
            'maxItems': 5,
            'items': {'type': 'number'}
        }
    }

    jsonschema.validate(bulk_data, schema)

    for record in bulk_data:
        if not isinstance(record, tuple):
            raise ValueError('Records in bulk_data must be tuples')
    
    for record in bulk_data:
        if any(not isinstance(value, (int, float)) for value in record):
            raise ValueError('All record values in bulk_data must be numeric')

def print_and_log(msg):
    print(msg)
    logger.debug(msg)
    
def shutdown_trim_scheduler():
    global trim_scheduler
    if trim_scheduler is not None:
        trim_scheduler.shutdown()
        logger.debug('trim scheduler is shutdown')
    trim_scheduler = None

# function called to cleanup, quit program and exit to command prompt
def graceful_exit(code=0):
    # Stop asyncio coroutine loops that connect to WSS server and receive server data
    exit_event.set()
    # Shutdown scheduler threads
    shutdown_trim_scheduler()
    # Close connection to SQLite3 database file
    close_database_connection()
    # Release the process lock. This will close the file and delete the file from the system temp folder
    lock.release()
    # Close the logger handler
    logger.close(f'Closing logger, graceful_exit() called with code {code}')
    # Almost done...
    print_and_log('Exiting Program...Please wait')
    time.sleep(1)
    sys.exit(0)

##### asyncio and websockets coroutines and functions below this line to handle connecting, receiving, and handling wss data from server
async def connect_to_server(wss_uri, exit_event):
    print_and_log('Running SQLite_WSS_Data...')

    # Set the connection ping interval in seconds
    ping_interval = 30  # seconds
    # Set the connection ping timeout in seconds
    ping_timeout = 6  # seconds

    while not exit_event.is_set():    
        try:
            async with websockets.connect(wss_uri, ping_interval=ping_interval, ping_timeout=ping_timeout) as websocket:
                print_and_log(f'Connected to server: {wss_uri}')
                await handle_connection(websocket, exit_event)

        except websockets.ConnectionClosed as err:
            print_and_log(f'WebSocket ConnectionClosed. {err} Attempting to reconnect...')
        except websockets.ConnectionClosedError as err:
            print_and_log(f'Error: WebSocket ConnectionClosedError. {err} Attempting to reconnect...')
        except asyncio.TimeoutError as err:
            print_and_log(f'Error: WebSocket TimeoutError. {err} Attempting to reconnect...')
        except websockets.WebSocketException as err:
            logger.debug(f'WebSocketException: {err}')
        except OSError as err:
            if '[WinError 121]' in str(err):
                # Handle the specific error
                logger.debug(f'Semaphore timeout period has expired: {err}')
            else:
                # Handle other OSError cases
                logger.debug(f'An OSError occurred: {err}')
        except socket.gaierror as err: 
            logger.debug(f'Error: socket.getaddrinfo failed: {err}')
        except Exception as err:
            traceback.print_exc()
            logger.debug(f'Exception (connect_to_server): {err}')

        print_and_log('Please wait...Attempting to reconnect to server')    
        await asyncio.sleep(5)  # Wait for a few seconds before reconnecting

    await websocket.close() 
    
    with contextlib.suppress(asyncio.CancelledError):
        await exit_event.wait()
        
async def handle_connection(websocket, exit_event):

    connection, cursor = connect_to_database()
    
    trim_flag = FlagManager()
    
    start_trim_scheduler()

    while not exit_event.is_set():
        try:
            message = await websocket.recv()
            # Handle the received message
            
            # check if exit_event was set while awaiting message
            if exit_event.is_set():
                logger.debug('The exit_event flag was set while awaiting message')
                break
            
            # Parse the received JSON data
            try:
                data = json.loads(message)
            except json.JSONDecodeError as err:
                logger.debug(f'Error decoding JSON: {err.msg}')
                logger.debug(f'Dump of JSON received: {message}')
                print('JSONDecodeError: Check log for details')
                continue

            # Save the data to the SQLite3 database
            handle_received_data(data, trim_flag, connection, cursor)

        except websockets.ConnectionClosed as err:
            # If the connection is closed, close database, exit the inner loop and allow the outer loop to attempt reconnection
            print_and_log(f'websockets.ConnectionClosed in handle_connection: {err}')
            if err.code == 1006:
                logger.debug('Error Code 1006: Connection closed due to a ping timeout')
            else:
                logger.debug(f'Connection closed with error code {err.code}: {err}')
            break
        except websockets.WebSocketException as err:
            logger.debug(f'WebSocketException  in handle_connection code: {err}')
            break
        except OSError as err:
            if '[WinError 121]' in str(err):
                logger.debug(f'Semaphore timeout period has expired: {err}')
            else:
                # Handle other OSError cases
                logger.debug(f'An OSError occurred: {err}')
            break
        except Exception as err:
            traceback.print_exc()
            logger.debug(f'Exception (handle_connection): {err}')
            break

    logger.debug('Shutting down trim_scheduler and closing database connection')
    shutdown_trim_scheduler()
    close_database_connection()

    await websocket.close() 


############################## __main__ ##############################

if __name__ == '__main__':

    logger = CustomLogger(clear_log=False, level=logging.NOTSET )
    logger.debug('##### Starting in SQLite_WSS_Data, entering __main__ #####')
    
    # use a lock file to ensure only one instance of this program is running
    with ProcessLock('SQLite_WSS_Data.lock', logger) as lock:
        # create event flag to signal asyncio coroutine to end when flag is set 
        exit_event = asyncio.Event()

        ##### Connect to wss server wss_uri in asyncio coroutine which serves as the main program loop.
        ##### Receive, handle and process data until exit_event flag is set for a graceful exit.
        try:
            asyncio.run(connect_to_server(wss_uri, exit_event))

        except KeyboardInterrupt:
            logger.debug('User aborted through keyboard (Ctrl + c)')
            graceful_exit(2)
        except asyncio.CancelledError as err:
            logger.debug(f'The asyncio task was cancelled. {err}')
        except Exception as err:
            traceback.print_exc()
            logger.debug(f'Exception in __main__ (try: connect_to_server): {err}')
        finally:
            logger.debug('connect_to_server() asyncio coroutine event loop is exiting')
            # Make attempt to release ProcessLock lock file. There is no effect if it has already been released
            lock.release()








######################### Archived Code #########################
'''
# Function to create a backup of the database file
def backup_database(db_file, backup_folder):
    if not os.path.exists(backup_folder):
        os.makedirs(backup_folder)

    backup_file = os.path.join(backup_folder, f'{os.path.basename(db_file)}.bak')

    try:
        shutil.copy(db_file, backup_file)
        logger.debug(f'Database backed up to: {backup_file}')
    except Exception as err:
        logger.debug(f'Error creating backup: {err}')
'''
'''    
async def graceful_exit(exit_event):
    logger.debug('Entering graceful_exit code')

    with contextlib.suppress(asyncio.CancelledError):
        await exit_event.wait()
        
    logger.debug('Exiting graceful_exit code')
    graceful_exit(1)
'''
'''        
    ##### Start asyncio coroutine to handle exit_event on (Ctrl + c) KeyboardInterrupt
    try:
        asyncio.run(graceful_exit(exit_event))
    except KeyboardInterrupt:
        print('User graceful_exited through keyboard')
        graceful_exit(3)
    except Exception as err:
        traceback.print_exc()
        print(f'Exception in __main__ (try: graceful_exit): {err}')
'''
'''
    try:
        asyncio.run(main(wss_uri, exit_event))
    except KeyboardInterrupt:
        print('User aborted through keyboard')
        graceful_exit(2)
    except socket.gaierror as err: 
        print(f'Error: socket.getaddrinfo failed: {err}')
    except Exception as err:
        traceback.print_exc()
        print(f'Exception in __main__ (try: main): {err}')
    
'''
'''
    # Insert each missing reading into the database
    #col_data = [missing_ts, missing_temperature, missing_humidity, missing_dew_point, missing_heat_index]
    #insert_db_record(col_data, cursor)    
    #logger.debug(f'Insert data - {col_data}')
    #col_data = (missing_ts, missing_temperature, missing_humidity, missing_dew_point, missing_heat_index)
'''
