from Framework.setup_testsuite import *

# test only
#from component import *

##############################################################################
# Module Variable
##############################################################################

LOG = ExecuteLog('unit_convert_and_assert_tool', LOG_LEVEL, testlog)

##############################################################################
# Assert Function
##############################################################################

def assert_ture(x):
    err_str = "{} is not True!".format(x)
    if x is not True:
        logging_and_assert_with_error(LOG, err_str)

def assert_false(x):
    err_str = "{} is not False!".format(x)
    assert not x, "[Assert Error] " + err_str

def assert_equal(x, y, deviation=0):
    assert (type(x) is int or float) and (type(y) is int or float), "[Assert Error] Input variable must be int or float!"
    assert 0 <= deviation <= 1, "[Assert Error] The deviation must be between 0 and 1!"
    err_str = "{} is not equal to {}!".format(x, y)
    if type(x) is float or type(y) is float:
        x = float(x)
        y = float(y)
    if deviation == 0:
        assert x == y, "[Assert Error] " + err_str
    else:
        z = abs(abs(x) - abs(y))
        #print(z)
        #print(abs(y * deviation))
        assert z <= abs(y * deviation), "[Assert Error] " + err_str

def assert_greater(x, y):
    assert (type(x) is int or float) and (type(y) is int or float), "[Assert Error] Input variable must be int or float!"
    err_str = "{} is not greater than {}!".format(x, y)
    assert x > y, "[Assert Error] " + err_str

def assert_greater_or_equal(x, y):
    assert (type(x) is int or float) and (type(y) is int or float), "[Assert Error] Input variable must be int or float!"
    err_str = "{} is not greater than nor equal to {}!".format(x, y)
    assert x > y or x == y, "[Assert Error] " + err_str

def assert_smaller(x, y):
    assert (type(x) is int or float) and (type(y) is int or float), "[Assert Error] Input variable must be int or float!"
    err_str = "{} is not smaller than {}!".format(x, y)
    assert x < y, "[Assert Error] " + err_str

def assert_smaller_or_equal(x, y):
    assert (type(x) is int or float) and (type(y) is int or float), "[Assert Error] Input variable must be int or float!"
    err_str = "{} is not smaller than nor equal to {}!".format(x, y)
    assert x < y or x == y, "[Assert Error] " + err_str


##############################################################################
# Unit Conversion Function
##############################################################################

def block_to_GB(block_num):
    """
    :param block_num:
    :return: GB
    """
    return float(int(block_num) * 8 / 1024 / 1024)


def slice_to_GB(slice_num):
    """
    :param slice_num:
    :return: GB
    """
    return float(int(slice_num) * 256 / 1024)


def sector_to_GB(sector_num):
    """
    :param sector_num:
    :return: GB
    """
    return float(int(sector_num) / 2 / 1024 / 1024)


def KB_to_GB(KB):
    """
    :param KB:
    :return: GB
    """
    return float(int(KB) / 1024 / 1024)


def B_to_GB(B):
    """
    :param B:
    :return: GB
    """
    return float(int(B) / 1024 / 1024 / 1024)

def GB_to_B(GB):
    """
    :param GB:
    :return: B
    """
    assert type(GB) is int or type(GB) is float, "[Assert Error] Input GB is invalid!"
    return int(GB * 1024 * 1024 * 1024)


def get_size_in_kb_human(size_str):
    """
    :param size_str: 10737418240 (10.0G)
    :return: size_b: 10737418240, size_hu: 10.0G
    """
    assert type(size_str) is str and len(size_str) > 0, "[Assert Error] Input size_str:{} is invalid!".format(size_str)
    m = re.search(r'([0-9]+)(\s+\(([0-9\.KMGTP]+)\))?', size_str)
    assert m, "[Assert Error] Failed to get size info from size_str:{}!".format(size_str)
    size_b = int(m.group(1))
    size_hu = None
    if m.group(2):
        size_hu = m.group(3)
    return size_b, size_hu


def get_percentage(output_str):
    """
    :param output_str: 95%
    :return: 95
    """
    assert type(output_str) is str and len(output_str) > 0, "[Assert Error] Input output_str:{} is invalid!".format(output_str)
    m = re.search(r'(\d+)%', output_str)
    assert m, "[Assert Error] Failed to get percent from output_str:{}!".format(output_str)
    return int(m.group(1))


def get_ratio(output_str):
    """
    :param output_str: 2.9:1
    :return: 2.9
    """
    assert type(output_str) is str and len(output_str) > 0, "[Assert Error] Input output_str:{} is invalid!".format(output_str)
    m = re.search(r'([0-9\.]+):1', output_str)
    assert m, "[Assert Error] Failed to get ratio from output_str:{}!".format(output_str)
    return float(m.group(1))

