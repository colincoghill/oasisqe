# testing module

import os

TESTINI = "src/oasis/lib/test.ini"

# In PROGRESS. Still thinking this through.
def setup():

    # Switch us to use a test database
    test_config = """



    """

    f = open(TESTINI,"w")
    f.write(test_config)
    f.close()
    global DB

    from oasis.lib import DB  # Do this *after* writing the test ini file.

    DB.run_sql("SELECT name, value FROM config WHERE name='test_status';")
    # assert ret

def teardown():
    os.remove(TESTINI)
