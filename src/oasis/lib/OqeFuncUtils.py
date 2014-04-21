# -*- coding: utf-8 -*-

# This code is under the GNU Affero General Public License
# http://www.gnu.org/licenses/agpl-3.0.html

# OqeFuncUtils.py

"""Functions used by the OQE question editor
"""


def chrange(start, end):
    """Generates a range of characters from start to end
    """
    return [chr(i) for i in range(ord(start), ord(end) + 1)]


def splitall(string, splitcharlist):
    """Splits the supplied string at all of the characters given in the
       second argument list
    """
    strlist = [string]
    for i in splitcharlist:
        newlist = []
        for j in strlist:
            tmplist = j.split(i)
            for k in tmplist:
                newlist.append(k)
        strlist = []
        for j in newlist:
            strlist.append(j)
    newlist = []
    for i in strlist:
        if i != '':
            newlist.append(i)
    return newlist


VALID_EQ_CHARS = chrange('0', '9') + chrange('a', 'z') + chrange('A', 'Z') + [
    '_']   # Later adds on the operation characters
VALID_BOOLOPS = ['+', '&', '!', '(', ')']


def get_vars_bool_eqn(eqnstr):
    """Gets the variables in a boolean equation and checks for invalid chars.
    """
    valid_ops = VALID_BOOLOPS
    valid_chars = VALID_EQ_CHARS + valid_ops

    eqnstr = eqnstr.replace(' ', '').lower()
    for i in eqnstr:
        if i not in valid_chars:
            return '', []
    eqnvars = splitall(eqnstr, valid_ops)

    eqnstr = eqnstr.replace("+", " or ")
    eqnstr = eqnstr.replace("&", " and ")
    eqnstr = eqnstr.replace("!", "not ")

    return eqnstr, eqnvars


def inc_bool_val_list(boollist):
    """ Given a list of 0 or 1 values, will increment in a boolean fashion
    """
    for i in range(len(boollist) - 1, -1, -1):
        if boollist[i] == 0:
            boollist[i] = 1
            return boollist
        elif boollist[i] == 1:
            boollist[i] = 0
    return boollist


def comp_bool_eqs(eq1str, eq2str, varlist):
    """ Will compare two boolean equations to see if they are the same.
        Assumes that the input strings are valid python expressions (i.e.
        use the operators 'not','and','or'). All variables
        in the equation must be specified in a list in 'varlist'.
    """
    numvars = len(varlist)
    boolvals = []
    for i in range(numvars):
        boolvals.append(0)

    vardict = {}
    anslist1 = []
    anslist2 = []
    for i in range(2 ** numvars):
        for j in range(numvars):
            vardict[varlist[j]] = boolvals[j]
        try:
            anslist1.append(eval(eq1str, vardict))
            anslist2.append(eval(eq2str, vardict))
        except BaseException:  # we use eval() so a lot could go wrong
            return -1
        boolvals = inc_bool_val_list(boolvals)

    for i in range(2 ** numvars):
        if not ((anslist1[i] and anslist2[i])
                or (not anslist1[i]) and (not anslist2[i])):
            return 0
    return 1