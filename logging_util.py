import functools
import logging
import pathlib

DETAIL = 5
logging.addLevelName(DETAIL, 'DETAIL')

def get_file_logger(name: str, level: int|None=None):
    """Returns a logger that logs event to __file__/../logs/`log_file`.log ."""

    logger = logging.getLogger(name)
    if level:
        logger.setLevel(level)

    # the logger hasn't been initalized yet
    if not logger.handlers:
        log_file = str(_log_file(name).resolve())
        handler = logging.FileHandler(log_file, encoding='UTF-8')
        handler.setLevel(logging.DEBUG)
        handler.setFormatter(logging.Formatter(
            fmt="[%(asctime)s] %(levelname)s: %(message)s",
        ))

        logger.addHandler(handler)

    return logger

def log_call(logger: logging.Logger, level: int, log_errors: bool|int=False):
    """A wrapper to log calls to a function."""
    if log_errors:
        err_lvl = log_errors if isinstance(log_errors, int) else logging.ERROR
        return functools.partial(
            _log_call_err, logger, level, err_lvl
        )
    else:
        return functools.partial(
            _log_call_no_err, logger, level
        )

def _log_call_no_err(logger: logging.Logger, level, fn):
    # returns a wrapper around `fn` that logs all calls to `fn`
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        logger.log(level, 'call to %s', fn.__name__)
        return fn(*args, **kwargs)
    
    return wrapper

def _log_call_err(logger:logging.Logger, level, err_lvl, fn):
    # returns a wrapper arousd `fn` that logs all 
    # calls to `fn` and all errors `fn` raises
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        logger.log(level, 'call to %s', fn.__name__)
        try:
            return fn(*args, **kwargs)
        except Exception:
            logger.log(
                err_lvl,
                'an exception occured while calling %s',
                fn.__name__,
                exc_info=True
            )
            raise

    return wrapper

def _log_file(name: str) -> pathlib.Path:
    # returns a pathlib.Path to write the logging of `name` to
    curr_dir = pathlib.Path(__file__).parent
    file_name = name + '.log'

    return curr_dir / 'logs' / file_name
