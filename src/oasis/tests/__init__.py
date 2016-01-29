# -*- coding: utf-8 -*-

"""testing module
"""

from oasis.lib import DB
assert DB.check_safe(), "Database not safe for tests"


def setup():
    """ Prepare database  and configuration file for testing
    """
    pass

def teardown():
    """
        Remove testing configuration file and otherwise clean up.
    """
    pass
