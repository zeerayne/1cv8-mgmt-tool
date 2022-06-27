import logging
import os

from conf import settings


def configure_logging(log_level):
    log_format = logging.Formatter('%(asctime)s [%(levelname)-3.3s] %(message)s')
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    # log to console and to file
    for handler in [logging.StreamHandler(), logging.FileHandler(os.path.join(settings.LOG_PATH, settings.LOG_FILENAME))]:
        handler.setFormatter(log_format)
        handler.setLevel(log_level)
        root_logger.addHandler(handler)
    # mitigate spammy debug output from third party modules
    for logger_name in ['aioboto3', 'aiobotocore', 'botocore', 'boto3', 'urllib3']:
        logging.getLogger(logger_name).setLevel(logging.INFO)
