import logging
import traceback
import functools
import time

# used to retry api calls from gateway
# in future will replace retry in send to telegram channel

def retry(retry_num, retry_sleep_sec=1):
    """
    retry help decorator.
    :param retry_num: the retry num;
    :param retry_sleep_sec: retry sleep sec;
    :return: decorator
    """

    def decorator(func):
        """decorator"""

        # preserve information about the original function, or the func name will be "wrapper" not "func"
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            """wrapper"""
            for attempt in range(retry_num):
                try:
                    return func(*args, **kwargs)  # should return the raw function's return value
                except Exception as err:  # pylint: disable=broad-except
                    logging.error(err)
                    logging.error(traceback.format_exc())
                    time.sleep(retry_sleep_sec)
                logging.error("Trying attempt %s of %s.", attempt + 1, retry_num)
            logging.error("func %s retry failed", func)
            raise Exception('Exceed max retry num: {} failed'.format(retry_num))

        return wrapper

    return decorator
