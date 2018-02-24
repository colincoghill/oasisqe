# still preliminary, using phusion because it's close to ubuntu

FROM alpine:3.7

CMD ["/bin/sh"]

RUN apk add --no-cache apache2 

RUN apk add --no-cache unzip memcached supervisor
RUN apk add --no-cache apache2-mod-wsgi

# Use apk to install packages that pip would need a dev environment (gcc) to install
RUN apk add --no-cache py2-bcrypt py2-psycopg2 
RUN apk add --no-cache py2-pillow py2-lxml
RUN apk add --no-cache py2-pip py2-cffi py2-openssl

RUN apk add --no-cache postgresql-client 

ADD src/docker/requirements.txt /tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt

RUN mkdir -p /opt/oasisqe/3.9
COPY src /opt/oasisqe/3.9/src/
COPY deploy  /opt/oasisqe/3.9/deploy/
COPY bin  /opt/oasisqe/3.9/bin/
COPY LICENSE.md README.md GNU_AGPL_3.0 /opt/oasisqe/3.9/

RUN mkdir /etc/supervisor.d
COPY src/docker/supervisord.conf /etc/supervisord.conf
COPY src/docker/supervisor-memcached.ini /etc/supervisor.d/memcached.ini
COPY src/docker/supervisor-apache2.ini /etc/supervisor.d/apache2.ini

RUN mkdir -p /run/apache2

# make sure it's a file so volume mount doesn't create a dir
RUN touch /etc/oasisqe.ini  

EXPOSE 22 80

CMD ["/usr/bin/supervisord", "-c", "/etc/supervisord.conf"]
