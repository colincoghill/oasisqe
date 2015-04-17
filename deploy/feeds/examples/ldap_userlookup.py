#!/usr/bin/python

# A script to query our LDAP server and fetch user details

# This should be run whenever OASIS encounters a new user account.
# By C.Coghill (July 2013)

import sys
import ldap
import ConfigParser


# The server likes to respond with Windows encoded strings
INPUT_ENCODING = 'iso-8859-1'

# We read our configuration from the following config file:
CONFIG_FILE = "/etc/foe/oasis/ldap_config.ini"
# Expect something like:
# You will need to fill in all your own details here:
#
#  [ldap]
#  server: ldaps://ldap.oasisqe.com
#  binddn: cn=oasis,ou=webapps,ou=oasisqe,o=oasisqe
#  passwd: SECRET
#  gbase: ou=faculty_group,dc=oasisqe,dc=com
#  ubase: ou=users,dc=oasisqe,dc=com
#
#  namefield: displayName
#  emailfield: mail

# binddn is the credentials we connect to the LDAP server with
# gbase is the base query to look for groups
# ubase is the base query to look for user details


def fetch_userdetails(server, binddn, password, base, username):

        conn = ldap.initialize(server)
        conn.bind_s(binddn, password)

        searchstr = "(cn=%s)" % username

        fields = ['displayName', 'mail', 'UOAid']
        search = conn.search_s(base, ldap.SCOPE_SUBTREE, searchstr, fields)

        mail = search[0][1]['mail'][0]
        name = search[0][1]['displayName'][0]
        uoaid = search[0][1]['UOAid'][0]
        return {'username': username,
                'email': mail,
                'name': name,
                'universityid': uoaid}


cp = ConfigParser.ConfigParser()
cp.read(CONFIG_FILE)

server = cp.get('ldap', 'server')
binddn = cp.get('ldap', 'binddn')
password = cp.get('ldap', 'passwd')
base = cp.get('ldap', 'ubase')

# Expect a series of usernames
userlist = sys.argv[1:]

users = []
for username in userlist:
    try:
        user = fetch_userdetails(server, binddn, password, base, username)
        users.append(user)
    except Exception as err:
        print "ERROR"
        print err
        sys.exit()

print "OK"
for user in users:
    print "%(username)s,%(name)s,%(email)s,%(universityid)s" % user
