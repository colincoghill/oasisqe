FROM alpine:3.7

CMD ["/bin/sh"]

RUN apk add --no-cache unzip supervisor postgresql-client rsyslog ca-certificates

# Use apk to install packages that pip would need a dev environment (gcc) to install
RUN apk add --no-cache py2-bcrypt py2-psycopg2 py2-pillow py2-lxml py2-pip py2-cffi py2-openssl

ADD docker/requirements.txt /tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt

RUN mkdir -p /opt/oasisqe/3.9/src

COPY ./ /opt/oasisqe/3.9/src/
COPY docker/oasisqe.ini /etc/oasisqe.ini

RUN cp -R /opt/oasisqe/3.9/src/scripts /opt/oasisqe/3.9/bin

RUN adduser -S oasisqe
RUN mkdir -p /var/cache/oasisqe/3.9 && \  
    chown -R oasisqe /var/cache/oasisqe

COPY docker/supervisord.conf /etc/supervisord.conf
RUN mkdir /etc/supervisor.d
COPY docker/supervisor.d/ /etc/supervisor.d/

EXPOSE 8000

CMD ["/usr/bin/supervisord","-c","/etc/supervisord.conf"]
