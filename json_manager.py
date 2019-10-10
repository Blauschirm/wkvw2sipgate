import os
import json
import uuid
import logging
from main import init_logger

init_logger()
logger = logging.getLogger('JSON-Manager')


class JsonManager(object):
    """
    Manager for json files as a poor mans database.
    Makes updating data easier.
    """

    def __init__(self, filename):
        self.filename = filename
        with open(filename, 'r', encoding='utf-8') as f:
            self.data = json.load(f)

    def save_to_disk(self):
        filename = self.filename

        if not self.data:
            logger.warning(
                "new JSON Data is empty. Skipping saving to disk to not loose data.")
            return

        # create randomly named temporary file to avoid
        # interference with other thread/asynchronous request
        tempfile = os.path.join(os.path.dirname(filename), str(uuid.uuid4()))
        with open(tempfile, 'w', encoding='utf8') as f:
            json.dump(self.data, f, indent=4, ensure_ascii=False)

        # replace old file with temporary file
        os.replace(tempfile, filename)
