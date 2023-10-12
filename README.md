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
