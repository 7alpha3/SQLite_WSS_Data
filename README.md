# SQLite_WSS_Data

This is a Python script that connects to a WebSocket server (WSS server) to receive environmental data and stores the received data in a SQLite3 database. It also manages the received data and the database. Below is an overview of the script and its functionality.

## Features

- **Connect to WSS Server**: The script connects to a WebSocket server (WSS server) at the specified URI to receive environmental data.

- **SQLite3 Database**: It stores the received data in a SQLite3 database. The database path is configurable.

- **Database Management**: The script creates and maintains the database, ensuring that the necessary table and index are in place.

- **Time Gap Handling**: The script checks for time gaps in the received data and fills them with interpolated values before storing the data in the database.

- **Data Trimming**: The script periodically trims the database by removing records older than a specific timestamp to manage the database size.

## How to Use

1. Ensure you have Python installed on your system.

2. Install the required packages using `pip`:

   ```shell
   pip install websockets apscheduler numpy jsonschema
   ```

3. Modify the following variables in the script to suit your configuration:

   - `wss_uri`: Set the WebSocket server URI you want to connect to.
   - `database_path`: Set the path to the SQLite3 database file where you want to store the data.

4. Run the script:

   ```shell
   python script_name.py
   ```

   Replace `script_name.py` with the name of your Python script.

5. The script will connect to the WebSocket server, receive data, and store it in the SQLite3 database. It will continue running until you stop it manually.

6. To gracefully exit the script, press `Ctrl + C`. The script will perform cleanup and close the database connection.

## Dependencies

This script relies on the following Python packages:

- `websockets`: Used for WebSocket communication.
- `apscheduler`: Provides background scheduling for tasks like data trimming.
- `numpy`: Utilized for numerical operations and data manipulation.
- `jsonschema`: Used for data validation and schema enforcement.

## Notes

- Ensure that you have the necessary permissions to write to the database file path specified in `database_path`.

- The script is designed to run continuously and handle incoming data. You can run it as a background process or daemon.

- Data received from the WebSocket server is expected to be in a specific format. Ensure that the data format matches the schema used in the script.

- Be cautious when modifying the script to handle different data formats or databases, as it may require adjustments to the code.

# Custom Logger

The `CustomLogger` class is a Python utility for logging messages to a timed rotating log file using the `logging` module. It provides an easy way to configure and manage log files for your applications. Below is an explanation of the key features and how to use this class.

## Features

- **Timed Rotating Log Files**: The `CustomLogger` creates log files that rotate at specific intervals (e.g., daily) to ensure that log files do not grow indefinitely.

- **Customizable Logging Levels**: You can log messages with different severity levels, including DEBUG, INFO, WARNING, ERROR, and CRITICAL.

- **Clear Log on Start**: Optionally, you can clear the log file each time your application starts, or you can append new log entries to an existing log file.

## Usage

1. Import the `CustomLogger` class:

   ```python
   from custom_logger import CustomLogger
   ```

2. Create an instance of the `CustomLogger` class:

   ```python
   logger = CustomLogger(name='MyLogger', clear_log=True, level=logging.DEBUG)
   ```

   - `name`: The name of the logger (default is `None`).
   - `clear_log`: Set to `True` to clear the log file when starting the application, or `False` to append new log entries to the existing log file.
   - `level`: The logging level for the logger (default is `logging.NOTSET`).

3. Use the logger to log messages with different severity levels:

   - `logger.debug(message)`: Log a message with DEBUG level.
   - `logger.info(message)`: Log a message with INFO level.
   - `logger.warning(message)`: Log a message with WARNING level.
   - `logger.error(message)`: Log a message with ERROR level.
   - `logger.critical(message)`: Log a message with CRITICAL level.

   Example:

   ```python
   logger.debug("This is a debug message")
   logger.error("An error occurred")
   ```

4. Close the logger when you're done:

   ```python
   logger.close("Closing logger.")
   ```

   This is important for ensuring that all log entries are flushed to the log file and for proper cleanup.

## Log File Configuration

- The log file path is set to `'./debug/debug.txt'` by default. You can modify it by changing the `file_path` attribute in the `CustomLogger` class.

- The log files are rotated daily (`when='midnight'`) by default, and up to 5 backup log files are retained. You can customize these settings by modifying the `TimedRotatingFileHandler` configuration in the class.

- The log entries include a timestamp, logger name, log level, module name, function name, and the log message.

## Example

Here's an example of how to use the `CustomLogger` class:

```python
from custom_logger import CustomLogger
import logging

logger = CustomLogger(name='MyLogger', clear_log=True, level=logging.DEBUG)

logger.debug("This is a debug message")
logger.info("This is an info message")
logger.error("An error occurred")

logger.close("Closing logger.")
```

In this example, a `CustomLogger` instance is created, and messages with different log levels are logged. The log entries are stored in a timed rotating log file with the specified configuration.
