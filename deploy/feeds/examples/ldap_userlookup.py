#!/usr/bin/python

# A script to query our LDAP server and fetch user details 

# This should be run whenever OASIS encounters a new user account.
# By C.Coghill (March 2013)

import sys
import ldap
import re
import ConfigParser

INPUT_ENCODING='iso-8859-1'

CONFIG_FILE = "/etc/foe/oasis/ldap_config.ini"


def fetch_userdetails(server, binddn, password, base, upid):

        conn = ldap.initialize(server)
        conn.bind_s(binddn, password)

        searchstr = "(cn=%s)"%upid

        fields = ['displayName', 'mail']
        search = conn.search_s(base,ldap.SCOPE_SUBTREE,searchstr,fields)

        mail = search[0][1]['mail'][0]
        name = search[0][1]['displayName'][0]
        return {'upid': upid, 'email': mail, 'name': name}


cp = ConfigParser.ConfigParser()
cp.read(CONFIG_FILE)

server = cp.get('ldap','server')
binddn = cp.get('ldap', 'binddn')
password = cp.get('ldap', 'passwd')
base = cp.get('ldap','ubase')


upids = sys.argv[1:]

users = []
for upid in upids:
    try:
        user = fetch_userdetails(server, binddn, password, base, upid)
        users.append(user)
    except Exception, err:
        print "ERROR"
        print err
        sys.exit()

print "OK"
for user in users:
    print "%(upid)s,%(name)s,%(email)s" % user
