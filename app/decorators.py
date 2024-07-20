import time
import logging
from functools import wraps
from typing import Callable, TypeVar, Tuple, Any

logger = logging.getLogger(__name__)

T = TypeVar('T')


def timed_operation(func: Callable[..., T]) -> Callable[..., T]:
    @wraps(func)
    def wrapper(*args, **kwargs) -> Tuple[T, float]:
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        elapsed_time = end_time - start_time
        logger.debug(f"{func.__name__} took {elapsed_time:.4f} seconds")
        return result, elapsed_time
    return wrapper
