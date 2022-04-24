import functools
import logging
import pathlib
import inspect

DETAIL = 5
logging.addLevelName(DETAIL, 'DETAIL')

def get_file_logger(name: str|None=None, level: int|None=None):
    """Returns a logger that logs event to a file associated with `name`
    (or the caller if name is none) in __file__\..\logs ."""
    
    if name is None:
        caller_info = inspect.stack()[1]
        caller_pth = pathlib.Path(caller_info.filename).resolve()
        
        log_name, log_file = _log_dest(caller_pth)
    else:
        log_name, log_file = _log_dest(name)
    
    print(log_file)

    logger = logging.getLogger(log_name)
    if level:
        logger.setLevel(level)

    # the logger hasn't been initalized yet
    if not logger.handlers:
        handler = logging.FileHandler(log_file, encoding='UTF-8')
        handler.setLevel(logging.DEBUG)
        handler.setFormatter(logging.Formatter(
            fmt="[%(asctime)s] %(levelname)s: %(message)s",
        ))

        logger.addHandler(handler)

    return logger

def log_call(logger: logging.Logger, level: int, log_errors: bool|int=False):
    """A wrapper to log calls to a function."""

    caller_info = inspect.stack()[1]
    

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
        logger.log(level, 'call to %s', fn.__qualname__)
        return fn(*args, **kwargs)
    
    return wrapper

def _log_call_err(logger:logging.Logger, level, err_lvl, fn):
    # returns a wrapper arousd `fn` that logs all 
    # calls to `fn` and all errors `fn` raises
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        logger.log(level, 'call to %s', fn.__qualname__)
        try:
            return fn(*args, **kwargs)
        except Exception:
            logger.log(
                err_lvl,
                'an exception occured while calling %s',
                fn.__qualname__,
                exc_info=True
            )
            raise

    return wrapper

def _log_dest(to: str|pathlib.Path) -> (pathlib.Path):
    # returns a pathlib.Path to write the logging to
    curr_dir = pathlib.Path(__file__).parent

    if isinstance(to, pathlib.Path):
        try:
            rel_pth = to.relative_to(pathlib.Path(__file__).parent)
        except ValueError as err:
            print('err:', err)
            rel_pth = to
        
        name = rel_pth.name
        if len(split_name := name.split('.')) > 1:
            name = '.'.join(split_name[:-1])
        
        
        if len(rel_pth.parts) >= 2:
            _dir = '.'.join(rel_pth.parts[:-1])
            file_name = _dir + '.' + name + '.log'
        else:
            file_name = name + '.log'

        return file_name[:-4], str((curr_dir / 'logs' / file_name).resolve())

    file_name = to + '.log'
    return to, str((curr_dir / 'logs' / file_name).resolve())
    