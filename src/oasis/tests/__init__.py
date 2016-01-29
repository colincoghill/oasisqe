# -*- coding: utf-8 -*-

"""testing module
"""

import os

TESTINI = "src/oasis/lib/test.ini"


# In PROGRESS. Still thinking this through.
def setup():
    """ Prepare database  and configuration file for testing
    """
    # Switch us to use a test database
    test_config = """



    """

    f = open(TESTINI, "w")
    f.write(test_config)
    f.close()
    global DB

    from oasis.lib import DB  # Do this *after* writing the test ini file.

    assert DB.check_safe(), "Database not safe for tests"


def teardown():
    """
        Remove testing configuration file and otherwise clean up.
    """
    os.remove(TESTINI)
