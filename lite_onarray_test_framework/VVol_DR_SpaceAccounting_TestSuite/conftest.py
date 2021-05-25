import pytest

def pytest_addoption(parser):
    parser.addoption("--setup-env", action="store", default="false", help="my option: true or false")
    parser.addoption("--teardown-env", action="store", default="false", help="my option: true or false")

@pytest.fixture(scope='class')
def if_setup_env(request):
    return request.config.getoption("--setup-env")

@pytest.fixture(scope='class')
def if_teardown_env(request):
    return request.config.getoption("--teardown-env")

