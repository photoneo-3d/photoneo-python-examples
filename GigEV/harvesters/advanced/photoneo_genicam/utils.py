import time
from functools import wraps


def measure_time(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        execution_time_ms = (end_time - start_time) * 1000
        print(f"Execution time of {func.__name__}: {execution_time_ms:.2f} milliseconds")
        return result

    return wrapper


def write_raw_array(filename: str, array):
    with open(filename, "wb") as file:
        for element in array:
            file.write(element.tobytes())
