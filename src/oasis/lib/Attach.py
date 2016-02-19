# -*- coding: utf-8 -*-

# This code is under the GNU Affero General Public License
# http://www.gnu.org/licenses/agpl-3.0.html

"""Attach.py
 Send a question attachment
"""


def is_restricted(fname):
    """ Is the filename restricted
        - not to be downloaded by non question editors?

        :param fname: a filename, generally of an attachment
        :type fname: string
        :rtype: bool

        :example:
        >>> is_restricted("datfile.dat")
        True
        >>>
    """
    if fname in ('datfile.txt', 'datfile.dat', 'qtemplate.html',
                 'marker.py', 'results.py'):
        return True
    if fname.startswith("_"):
        return True
    if fname.endswith(".oqe"):
        return True
    if fname.endswith(".qe2"):
        return True

    return False
