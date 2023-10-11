import os, sys, errno, time, tempfile

MAX_RETRIES = 5
RETRY_DELAY = 0.5 # seconds

##### ProcessLock (context manager) class to implement a file based process lock with retries and logging.
class ProcessLock:

    def __init__(self, lockfile_name, logger):
        self.lockfile_path = os.path.join(tempfile.gettempdir(), lockfile_name)
        self.logger = logger
        self.lock_file = None

    def __enter__(self):
        self.logger.debug(f'ProcessLock attempting to acquire lock file: {self.lockfile_path}')
        for i in range(MAX_RETRIES):
            attempt = i + 1
            try:
                self.lock_file = open(self.lockfile_path, 'x')
                self.logger.debug(f'ProcessLock lock file acquired: {self.lockfile_path}')
                break
            except OSError as e:
                if e.errno != errno.EEXIST:
                    self.logger.debug(f'Unexpected error in attempt {attempt} of {MAX_RETRIES} to acquire lock file: {e}')
                    raise
                self.logger.debug(f'ProcessLock failed to acquire lock file on attempt: {attempt} of {MAX_RETRIES}')
                if attempt == MAX_RETRIES:
                    print('Unable to acquire lock, process is already running.')
                    print(f'Lock file, {self.lockfile_path}, already exists, exiting.')
                    self.logger.debug(f'Exiting script! Lock file already exists: {self.lockfile_path}')
                    self.logger.close('Closing logger instance from ProcessLock before sys.exit().')
                    sys.exit(1)
                time.sleep(RETRY_DELAY)        
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.release()
        if exc_type is not None:
            if issubclass(exc_type, SystemExit) and exc_value.code == 0:
                self.logger.debug('ProcessLock exited context successfully.')
            else:
                self.logger.debug(f'In ProcessLock __exit__ method an exception of type {exc_type} occurred with value {exc_value}')
        return False  # If True, suppresses any exception that occurred

    def release(self):
        if self.lock_file:
            try:
                self.lock_file.close()
                os.unlink(self.lockfile_path)
                self.lock_file = None
                self.logger.debug(f'ProcessLock lock file released: {self.lockfile_path}')
            except OSError as e:
                print(f'Unexpected error releasing lock file, {self.lockfile_path}: {e}')
