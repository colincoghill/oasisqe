#!/usr/bin/python

# University of Auckland, Faculty of Engineering

# A script query our LDAP server and fetch the membership of a
# netaccount group.

# This will be run by OASIS when it wants to find the members of a group
# By C.Coghill (July 2013)

import sys
import ldap
import re
import ConfigParser

INPUT_ENCODING = 'iso-8859-1'

CONFIG_FILE = "/etc/foe/oasis/ldap_config.ini"


def cn_to_username(cn):

        return re.findall(r'^cn=(.*),ou=ec_users', cn)[0]


def fetch_upids_in_ldap_group(server, binddn, password, base, groupname):

        conn = ldap.initialize(server)
        conn.bind_s(binddn, password)
        search = conn.search_s(base, ldap.SCOPE_SUBTREE, '(cn=' + groupname + ')', ['member'])

        res = []
        for group, members in search:
                if members:
                        for user in members['member']:
                            res.append(cn_to_username(user))
        res.sort()
        return res


cp = ConfigParser.ConfigParser()
cp.read(CONFIG_FILE)

server = cp.get('ldap', 'server')
binddn = cp.get('ldap', 'binddn')
password = cp.get('ldap', 'passwd')
base = cp.get('ldap', 'gbase')

groupname = sys.argv[1]

try:
    upids = fetch_upids_in_ldap_group(server, binddn, password, base, groupname)
except Exception, err:
    print "ERROR"
    print err
    sys.exit()


print "OK"
for upid in upids:
    print upid
