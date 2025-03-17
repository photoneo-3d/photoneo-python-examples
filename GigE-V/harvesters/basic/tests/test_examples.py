import importlib.util
import io
import logging
import os
import sys
from pathlib import Path

import pytest

# Ensure the project's root directory is in PYTHONPATH
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)


script_dir = Path(__file__).parent.resolve()
EXAMPLES_DIR = script_dir.parent.resolve()
OUTPUT_DIR = Path(script_dir / "output")
LOG_HEADER = "HarverserExamples"

os.makedirs(OUTPUT_DIR, exist_ok=True)


def load_module(file_path):
    module_name = os.path.splitext(os.path.basename(file_path))[0]
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def get_main_function(module):
    return getattr(module, "main", None)


example_files = [
    os.path.join(EXAMPLES_DIR, f) for f in os.listdir(EXAMPLES_DIR) if f.endswith(".py")
]


@pytest.mark.parametrize("script_path", example_files)
def test_example(script_path, request):
    module = load_module(script_path)
    main_func = get_main_function(module)

    if main_func is not None:
        # Capture stdout
        original_stdout = sys.stdout
        captured_output = io.StringIO()
        sys.stdout = captured_output

        # Capture logging output to the same buffer
        log_output = io.StringIO()
        log_handler = logging.StreamHandler(log_output)
        log_handler.setLevel(logging.DEBUG)

        logger = logging.getLogger(LOG_HEADER)
        logger.setLevel(logging.DEBUG)
        logger.addHandler(log_handler)
        try:
            # Execute main function
            try:
                result = main_func(os.getenv("device"))
            except TypeError:
                result = main_func()
            assert (
                result is not False
            ), f"`main()` in {script_path} caused an error during execution"
        except Exception as e:
            pytest.fail(f"Script failed with error: {str(e)}")
        finally:
            # Reset log/stdout capture
            sys.stdout = original_stdout
            logger.removeHandler(log_handler)

        log_handler.flush()

        # Write result
        output_file = os.path.join(OUTPUT_DIR, f"{os.path.basename(script_path)}.log")
        with open(output_file, "w", encoding="utf-8") as f:
            f.write("--- Stdout ---\n")
            f.write(captured_output.getvalue())
            f.write("\n--- Logs ---\n")
            f.write(log_output.getvalue())
        assert True
