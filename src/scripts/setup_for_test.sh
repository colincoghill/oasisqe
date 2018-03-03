#!/bin/bash

# Sets up Ubuntu (Trusty) or Debian (Jessie) to run OASIS with a useful "test" configuration.
#
# Note: this will trash databases, don't give it creds to your production database!

su oasisqe -c "/opt/oasisqe/3.9/bin/oasisdb init"

echo 
echo OASIS setup for testing
echo
echo "********************************************"
su oasisqe -c "/opt/oasisqe/3.9/bin/reset_admin_password oasistest"
echo "********************************************"
