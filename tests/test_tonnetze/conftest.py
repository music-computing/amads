"""
Pytest configuration for the tonnetze test suite.
"""


def pytest_configure(config):
    config.addinivalue_line(
        "markers", "slow: takes roughly two minutes, run with -m slow"
    )
