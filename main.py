import logging, json, time
from logging import handlers
import os

def setup_logging(log_folder_path: str, log_level: str, external_lib_log_level: str, rotate_logger_configuration: dict):
    """
    Sets up a console and a rotating file handler for logging.

    Parameters:
    ------------
    rotate_logger_configuration: {when: str, interval: int, backupCount: int}


    """


    print(f'Configuring logging with level={log_level}')

    ## Create Logging handlers
    # Define formatting
    timestamp_formatter = logging.Formatter('%(asctime)s - %(levelname)-7s - %(name)-20s - %(message)s')
    formatter = logging.Formatter('%(levelname)-7s - %(name)-20s - %(message)s')
    
    # console logger
    console_handler = logging.StreamHandler()
    console_handler.setLevel(LOG_LEVEL)
    console_handler.setFormatter(formatter)
    
    # file logger
    if not os.path.exists(log_folder_path):
        print(f'Creating log directory {log_folder_path}')
        os.makedirs(log_folder_path)
    
    file_handler = logging.handlers.TimedRotatingFileHandler(f'{log_folder_path}/log.log', **rotate_logger_configuration)#when=rotate_logger_configuration['when'], interval=rotate_logger_configuration['interval'], backupCount=rotate_logger_configuration['backupCount'])
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(timestamp_formatter)

    # configure logging
    logging.basicConfig(
        level=LOG_LEVEL,
        format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
        handlers=[console_handler, file_handler])
        
    # Configure other libraries to only log WARNINGs
    logging.info("Setting logging for external libraries to {external_lib_log_level}")
    logging.getLogger("requests").setLevel(external_lib_log_level)
    logging.getLogger("urllib3").setLevel(external_lib_log_level)

if __name__ == "__main__":

    with open('config.json', 'r') as config_file:
        config = json.load(config_file)

    config_logging = config["logging"]
    
    LOG_LEVEL = config_logging["log_level"] or "DEBUG"
    LOG_PATH = config_logging["log_path"] or "log"
    ROTATE_CONFIG = config_logging["rotate"] or { "when": 'D', "interval": 1, "backupCount": 10 }
    
    setup_logging(log_folder_path=LOG_PATH, log_level=LOG_LEVEL, external_lib_log_level="WARNING", rotate_logger_configuration=ROTATE_CONFIG)
    
    import crawler





        

