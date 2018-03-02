# still preliminary, using phusion because it's close to ubuntu

FROM alpine:3.7

CMD ["/bin/sh"]

RUN apk add --no-cache apache2 

RUN apk add --no-cache unzip supervisor
RUN apk add --no-cache apache2-mod-wsgi

# Use apk to install packages that pip would need a dev environment (gcc) to install
RUN apk add --no-cache py2-bcrypt py2-psycopg2 
RUN apk add --no-cache py2-pillow py2-lxml
RUN apk add --no-cache py2-pip py2-cffi py2-openssl

RUN apk add --no-cache postgresql-client 

ADD docker/requirements.txt /tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt

RUN mkdir -p /opt/oasisqe/3.9/src

COPY fonts /opt/oasisqe/3.9/src/fonts/
COPY oasis /opt/oasisqe/3.9/src/oasis
COPY scripts /opt/oasisqe/3.9/src/scripts
COPY static /opt/oasisqe/3.9/src/static
COPY templates /opt/oasisqe/3.9/src/templates
COPY oasis.wsgi /opt/oasisqe/3.9/src/oasis.wsgi

COPY docker/oasisqe.ini /etc/oasisqe.ini
COPY docker/oasisqe-apache2.conf /etc/apache2/conf.d/oasisqe.conf

RUN mkdir /etc/supervisor.d

COPY docker/supervisord.conf /etc/supervisord.conf
COPY docker/supervisor-apache2.ini /etc/supervisor.d/apache2.ini

RUN mkdir -p /run/apache2

EXPOSE 80

CMD ["/usr/bin/supervisord", "-c", "/etc/supervisord.conf"]
