import pytest
import os

def pytest_addoption(parser):
    parser.addoption("--device", action="store", help="Device ID for testing")

def pytest_configure(config):
    os.environ["device"] = config.getoption("device")
