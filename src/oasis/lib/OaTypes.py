# -*- coding: utf-8 -*-

"""Some useful data types.
"""

import datetime


def epochToDatetime(epoch):
    """Converts a datetime in seconds to a datetime.datetime.
    """

    return datetime.datetime.fromtimestamp(epoch)


def todatetime(mydate):
    """ Convert the given thing to a datetime.datetime.
        This is intended mainly to be used with the mx.DateTime that psycopg sometimes returns,
        but could be extended in the future to take other types.
    """
    if isinstance(mydate, datetime.datetime):
        return mydate    # Already a datetime
    if not mydate:
        return mydate    # maybe it was None
        # this works for mx.DateTime without requiring us to explicitly
    # check for mx.DateTime (which is annoying if it may not even be installed) 
    return datetime.datetime.fromtimestamp(mydate)
