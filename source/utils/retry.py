"""
Retry logic decorator with exponential backoff.

Sprint: 005-system-reliability
Task: T014 - Universal retry logic implementation
"""

import time
import functools
import logging
import threading
from typing import Callable, Any, Type
from enum import Enum

# Get logger from utils
logger = logging.getLogger(__name__)


class TransientError(Exception):
    """Transient error that should be retried."""
    pass


class PermanentError(Exception):
    """Permanent error that should NOT be retried."""
    pass


def retry_with_backoff(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    backoff_multiplier: float = 2.0,
    transient_exceptions: tuple = (TransientError, ConnectionError, TimeoutError),
    permanent_exceptions: tuple = (PermanentError, ValueError, TypeError)
):
    """
    Decorator for retry logic with exponential backoff.
    
    Args:
        max_attempts: Maximum number of retry attempts
        base_delay: Base delay in seconds before first retry
        backoff_multiplier: Multiplier for exponential backoff
        transient_exceptions: Exceptions that trigger retry
        permanent_exceptions: Exceptions that should not be retried
        
    Returns:
        Decorated function with retry logic
        
    Example:
        @retry_with_backoff(max_attempts=3, base_delay=0.5)
        def fetch_data():
            # Function that may fail transiently
            pass
    """
    
    # Thread-local storage for concurrent operation isolation
    _local = threading.local()
    
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            last_exception = None
            
            for attempt in range(1, max_attempts + 1):
                try:
                    result = func(*args, **kwargs)
                    
                    # Log success after retry
                    if attempt > 1:
                        func_name = getattr(func, '__name__', 'unknown_function')
                        logger.info(
                            f"Operation '{func_name}' succeeded on attempt {attempt}/{max_attempts}"
                        )
                    
                    return result
                    
                except permanent_exceptions as e:
                    # Permanent errors should not be retried
                    func_name = getattr(func, '__name__', 'unknown_function')
                    logger.error(
                        f"Permanent error in '{func_name}': {type(e).__name__}: {e}"
                    )
                    raise
                    
                except transient_exceptions as e:
                    last_exception = e
                    
                    # Log retry event with diagnostic context
                    if attempt < max_attempts:
                        delay = base_delay * (backoff_multiplier ** (attempt - 1))
                        func_name = getattr(func, '__name__', 'unknown_function')
                        logger.warning(
                            f"Retry attempt {attempt}/{max_attempts} for '{func_name}' "
                            f"after {type(e).__name__}: {e}. "
                            f"Retrying in {delay:.2f}s..."
                        )
                        time.sleep(delay)
                    else:
                        func_name = getattr(func, '__name__', 'unknown_function')
                        logger.error(
                            f"Retry exhausted for '{func_name}' after {max_attempts} attempts. "
                            f"Last error: {type(e).__name__}: {e}"
                        )
                        raise
                        
                except Exception as e:
                    # Unexpected exceptions - treat as transient by default
                    func_name = getattr(func, '__name__', 'unknown_function')
                    logger.warning(
                        f"Unexpected exception in '{func_name}': {type(e).__name__}: {e}"
                    )
                    last_exception = e
                    
                    if attempt < max_attempts:
                        delay = base_delay * (backoff_multiplier ** (attempt - 1))
                        logger.warning(f"Retrying in {delay:.2f}s...")
                        time.sleep(delay)
                    else:
                        logger.error(f"Retry exhausted after {max_attempts} attempts")
                        raise
            
            # Should not reach here, but handle it gracefully
            if last_exception:
                raise last_exception
                
        return wrapper
    return decorator
