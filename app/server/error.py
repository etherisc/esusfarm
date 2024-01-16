import inspect

from util.logging import get_logger

WARNING = "WARNING"
ERROR = "ERROR"

logger = get_logger()


class NotFoundError(KeyError):
    pass


def raise_with_log(error_class, error_message: str, level: str = WARNING):
    current_frame = inspect.currentframe()
    outer_frame = inspect.getouterframes(current_frame)

    caller_path = outer_frame[1].filename
    path_parts = caller_path.split('/')
    caller_filename = '/'.join(path_parts[-2:]) if len(path_parts) > 1 else  path_parts[-1]
    caller_lineno = outer_frame[1].lineno

    error_name = error_class.__name__
    log_message = f"{error_name} {caller_filename}:{caller_lineno} {error_message}"

    if level == ERROR:
        logger.error(log_message)
    else:
        logger.warning(log_message)

    raise error_class(error_message)
