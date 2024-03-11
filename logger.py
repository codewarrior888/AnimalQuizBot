import logging
import time

logger = logging.getLogger('AnimalQuizBot')
logger.setLevel(logging.INFO)

formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

file_handler = logging.FileHandler('logging.log')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)


def log_performance(func):
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        execution_time = time.time() - start_time
        logger.info(f"Function '{func.__name__}' executed in {execution_time:.2f} seconds")
        return result
    return wrapper


def log_error(exception, message=None):
    logger.error(f"An error occurred: {exception}")
    if message:
        logger.error(f"Message: {message}")


def log_errors(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as _ex:
            log_error(_ex, message=args[0] if args else None)
    return wrapper
