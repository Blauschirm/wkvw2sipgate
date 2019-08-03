import logging, json, time
from logging import handlers

if __name__ == "__main__":

    with open('config.json', 'r') as config_file:
        config_data = json.load(config_file)

    LOG_LEVEL = config_data["logging"]["log_level"] or "DEBUG"
    LOG_PATH = config_data["logging"]["log_path"] or "log"
    print(f"Starting with LOG_LEVEL={LOG_LEVEL}")
    
    # Define formatting
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    # console logger
    ch = logging.StreamHandler()
    ch.setLevel(LOG_LEVEL)
    ch.setFormatter(formatter)
    # file logger
    fh = logging.handlers.TimedRotatingFileHandler(f'{LOG_PATH}/log.log', when='S', interval=1, backupCount=10)
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(formatter)
    # configure logging
    logging.basicConfig(
        level=LOG_LEVEL,
        format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
        handlers=[ch, fh])
        
    logger = logging.getLogger("crawler")
    logger.info(f"Started application! Tadaaaaa")
    logger.info("binfo")
    logging.info('Root said this')

    for i in range(1000):
        time.sleep(0.0.1)
        logger.info(f"Slept {i}s")







        

