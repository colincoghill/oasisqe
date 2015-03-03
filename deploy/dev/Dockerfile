FROM     ubuntu:trusty
MAINTAINER  "colin@colincoghill.com"

# Use a local apt cache
RUN /sbin/ip route | awk '/default/ { print "Acquire::http::Proxy \"http://"$3":3142\";" }' > /etc/apt/apt.conf.d/30proxy

RUN      apt-get -y update
RUN      apt-get -y upgrade

# ---------------- #
#   Installation   #
# ---------------- #

# Deps
RUN     apt-get -y install --no-install-recommends apache2 memcached
RUN     apt-get -y install --no-install-recommends python-bcrypt python-decorator python-flask python-imaging python-jinja2
RUN     apt-get -y install python-memcache python-psycopg2 python-openpyxl
RUN     apt-get -y install postgresql-9.3 postgresql-client-9.3 libapache2-mod-wsgi

# System

RUN     adduser --system --quiet oasisqe 

RUN     mkdir -p /opt/oasisqe                    &&\
        cd /opt/oasisqe          

ADD     oasis3.9_latest.tgz  /opt/oasisqe

RUN     mkdir -p /var/cache/oasisqe/v3.9              &&\
        chown -R oasisqe /var/cache/oasisqe           &&\
        mkdir -p /var/log/oasisqe                     &&\
        chown -R oasisqe /var/log/oasisqe

ADD     devconfig.ini /etc/oasisqe.ini

RUN     service postgresql start && sleep 5 &&\
        su postgres -c "createuser oasisdb -d -l "    &&\
        su postgres -c "createdb -O oasisdb oasisdb"    &&\
        su postgres -c "psql -Uoasisdb -h localhost -W oasisdb < /opt/oasisqe/3.9/deploy/emptyschema.sql"


# Apache

RUN    rm /etc/apache2/sites-enabled/000-default.conf &&\
       cp /opt/oasisqe/3.9/deploy/apacheconfig.sample /etc/apache2/sites-available/oasisqe &&\
       a2ensite oasisqe 

# -------- #
#   Run!   #
# -------- #

EXPOSE 80/tcp

CMD     ["/usr/sbin/apache2ctl -D FOREGROUND"]

