# -*- coding: utf-8 -*-

# This code is under the GNU Affero General Public License
# http://www.gnu.org/licenses/agpl-3.0.html

""" Functions used by the OQE Smark Marker functions
"""

from oasis.lib import OqeFuncUtils


def comp_raw_bool_eqs(eq1str, eq2str):
    """ Will compare two boolean equations to see if they are the same.
        The equations can be written using the characters '&', '+' and '!'
        for 'and', 'or' and 'not' respectively.
    """
    (eqn1, eqn1vars) = OqeFuncUtils.get_vars_bool_eqn(eq1str)
    (eqn2, eqn2vars) = OqeFuncUtils.get_vars_bool_eqn(eq2str)

    if eqn1 == '' or eqn2 == '':
        return -1

    varlist = []
    for i in eqn1vars:
        if not i in varlist:
            varlist.append(i)
    for i in eqn2vars:
        if not i in varlist:
            varlist.append(i)

    return OqeFuncUtils.comp_bool_eqs(eqn1, eqn2, varlist)