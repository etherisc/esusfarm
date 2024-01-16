# file mostly copied from https://gist.github.com/nkhitrov:
# https://gist.github.com/nkhitrov/a3e31cfcc1b19cba8e1b626276148c49
import logging
import sys

# if you dont like imports of private modules
# you can move it to typing.py module
from loguru import logger
from loguru._defaults import LOGURU_FORMAT

from server.settings import settings


from server.util.mongo import (
    get_client,
    get_collection
)

UVICORN = 'uvicorn'

LOGGING_DEBUG = 'DEBUG'
LOGGING_INFO = 'INFO'
LOGGING_WARNING = 'WARNING'
LOGGING_ERROR = 'ERROR'
LOGGING_CRITICAL = 'CRITICAL'

LOGGING_LEVEL = {
    LOGGING_DEBUG: logging.DEBUG,
    LOGGING_INFO: logging.INFO,
    LOGGING_WARNING: logging.WARNING,
    LOGGING_ERROR: logging.ERROR,
    LOGGING_CRITICAL: logging.CRITICAL
}

LOGGING_LEVEL_DEFAULT = logging.DEBUG
LOGGING_FORMAT_DEFAULT = LOGURU_FORMAT


log_collection = None

# custom sink function to write logs to mongo
def mongodb_sink(message):
    log_record = message.record
    file_name = log_record['file'].name
    line = log_record['line']
    module = log_record['module']
    function = log_record['function']

    log_data = {
        "level": log_record["level"].name,
        # "source": ':'.join([log_record["module"],log_record["name"],log_record["function"],log_record["file"].name,str(log_record["line"])]),
        "source": f"{file_name}:{line} ({module}.{function})",
        "message": log_record["message"],
        "time": log_record["time"]
    }
    log_collection.insert_one(log_data)


class InterceptHandler(logging.Handler):
    """
    Default handler from examples in loguru documentaion.
    See https://loguru.readthedocs.io/en/stable/overview.html#entirely-compatible-with-standard-logging
    """

    def emit(self, record: logging.LogRecord):
        # Get corresponding Loguru level if it exists
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Find caller from where originated the logged message
        frame, depth = logging.currentframe(), 2
        while frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )


def setup_logging() -> None:
    """make uvicorn use loguru logging"""

    global log_collection

    # disable handlers for specific uvicorn loggers
    # to redirect their output to the default uvicorn logger
    # works with uvicorn==0.11.6
    loggers = (
        logging.getLogger(name)
        for name in logging.root.manager.loggerDict
        if name.startswith('{}.'.format(UVICORN))
    )

    for uvicorn_logger in loggers:
        uvicorn_logger.handlers = []

    # change handler for default uvicorn logger
    intercept_handler = InterceptHandler()
    logging.getLogger(UVICORN).handlers = [intercept_handler]

    # update logging level from settings if available
    logging_level = LOGGING_LEVEL_DEFAULT

    if settings.logging_level and len(settings.logging_level) > 0:
        if settings.logging_level in LOGGING_LEVEL:
            logging_level = LOGGING_LEVEL[settings.logging_level]
            logger.info("setting logging level to {} ({})",
                settings.logging_level,
                logging_level)
        else:
            logger.warning("unsupported logging level '{}', using default instead", 
            settings.logging_level,
            logging_level)

    # update logging format from settings if available
    logging_format = LOGGING_FORMAT_DEFAULT

    if settings.logging_format and len(settings.logging_format) > 0:
        logger.info('setting logging format to {}', settings.logging_format)
        logging_format = settings.logging_format


    # set logs output, level and format
    # logger.add(sys.stdout, level=logging_level, format=logging_format)

    log_collection = get_log_collection()
    if log_collection is not None:
        if not settings.logging_mongo_level:
            logger.add(mongodb_sink)
        else:
            logger.add(mongodb_sink, level=settings.logging_mongo_level)


def get_log_collection():
    if log_collection is not None:
        return log_collection
    
    # attempt to get log collection using settings info
    if not settings.logging_mongo_uri:
        return None
    
    if not settings.logging_mongo_db:
        return None
    
    if not settings.logging_mongo_collection:
        return None

    mongo = get_client(settings.logging_mongo_uri)
    collection = get_collection(
        mongo, 
        settings.logging_mongo_db, 
        settings.logging_mongo_collection,
        create=True)
    
    return collection

    # logger.configure(
    #     handlers=[
    #         {
    #             'sink': sys.stdout,
    #             'level': logging_level,
    #             'format': logging_format
    #         },
    #         {
    #             'sink': sys.stdout,
    #             'level': logging_level,
    #             'format': logging_format
    #         }
    #     ]
    # )
