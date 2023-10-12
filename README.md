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

# ProcessLock

The `ProcessLock` class is a Python utility for implementing a file-based process lock with retries and logging. It is designed to ensure that only one instance of a particular process is running at a time. This can be useful in situations where concurrent execution of the same script or application is undesirable. Below is an explanation of the key features and how to use this class.

## Features

- **File-Based Lock**: The `ProcessLock` uses a file as a lock to prevent multiple instances of a process from running simultaneously.

- **Retries**: If the lock cannot be acquired immediately, the class retries a specified number of times with a configurable delay between each attempt.

- **Logging**: The class logs events and errors to provide information about the lock acquisition process.

## Usage

1. Import the `ProcessLock` class:

   ```python
   from process_lock import ProcessLock
   ```

2. Create an instance of the `ProcessLock` class with a lock file name and a logger object:

   ```python
   logger = logging.getLogger(__name__)  # Replace with your own logger configuration
   process_lock = ProcessLock("my_process.lock", logger)
   ```

   - `lockfile_name`: The name of the lock file. This should be unique to the process you want to lock.

3. Use the `ProcessLock` as a context manager within a `with` block to acquire the lock:

   ```python
   with process_lock:
       # Your code here
   ```

   The lock will be acquired, and the code within the `with` block will execute. If the lock cannot be acquired, the script will log an error and exit gracefully.

4. The lock is automatically released when the `with` block exits, whether due to successful execution or an exception.

## Configuration

- `MAX_RETRIES`: The maximum number of times the lock acquisition is retried. This is set to 5 by default but can be customized to your requirements.

- `RETRY_DELAY`: The delay (in seconds) between each retry attempt. The default is 0.5 seconds.

- The lock file is created in the system's temporary directory (retrieved using `tempfile.gettempdir()`) with the specified lock file name.

- The class logs the lock acquisition process and any unexpected errors that occur during the lock release.

## Example

Here's an example of how to use the `ProcessLock` class:

```python
import os, sys, errno, time, tempfile, logging

MAX_RETRIES = 5
RETRY_DELAY = 0.5  # seconds

logger = logging.getLogger(__name__)

process_lock = ProcessLock("my_process.lock", logger)

with process_lock:
    # Your code that should run exclusively
    print("Lock acquired, running the process...")

# The lock is automatically released when the 'with' block exits.
print("Process completed.")
```

In this example, a `ProcessLock` instance is created with a lock file name, and it is used as a context manager within a `with` block. If the lock cannot be acquired due to another running process, the script will exit gracefully. If the lock is acquired, the code within the `with` block will execute, ensuring exclusive access to the process.

# FlagManager

The `FlagManager` class is a simple Python utility designed to encapsulate a boolean flag value stored in a mutable list. It provides a straightforward and reusable way to manage boolean flags in your code. This class is particularly useful when you need to share a flag's state among different parts of your program or ensure safe thread access to a shared flag.

## Features

- **Encapsulation**: The class encapsulates a boolean flag within a mutable list, allowing you to modify the flag's value using methods.

- **Set and Clear**: You can easily set or clear the flag's value using dedicated methods.

- **Querying State**: Check whether the flag is set or cleared using the `is_set` and `is_cleared` methods.

- **Safe Mutable State**: The mutable list helps ensure safe access to the flag in multi-threaded or shared memory environments.

- **Destructor**: The class defines a destructor method, `__del__`, which is not used but can be extended for specific cleanup tasks if needed.

## Usage

1. Import the `FlagManager` class:

   ```python
   from flag_manager import FlagManager
   ```

2. Create an instance of the `FlagManager` class:

   ```python
   flag = FlagManager()
   ```

3. Use the following methods to manage the flag:

   - `set_flag()`: Set the flag to `True`.
   - `clear_flag()`: Clear the flag (set it to `False`).
   - `is_set()`: Check if the flag is set (returns `True` if set, otherwise `False`).
   - `is_cleared()`: Check if the flag is cleared (returns `True` if cleared, otherwise `False`).

   Example:

   ```python
   flag = FlagManager()
   flag.set_flag()
   if flag.is_set():
       print("Flag is set.")
   flag.clear_flag()
   if flag.is_cleared():
       print("Flag is cleared.")
   ```

4. The flag's value is stored within the `FlagManager` instance, and you can safely use it in your code to control program flow, synchronization, or other logic.

## Example

Here's an example of how to use the `FlagManager` class:

```python
from flag_manager import FlagManager

# Create a flag instance
flag = FlagManager()

# Set the flag
flag.set_flag()
if flag.is_set():
    print("Flag is set.")

# Clear the flag
flag.clear_flag()
if flag.is_cleared():
    print("Flag is cleared.")
```

In this example, a `FlagManager` instance is created, and the flag is set and cleared using the provided methods. You can use this class to manage flags in a clean and organized way within your code.
