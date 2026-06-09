FROM postgres:16

ENV POSTGRES_DB=server_monitor
ENV POSTGRES_USER=admin
ENV POSTGRES_PASSWORD=admin123

COPY init.sql /docker-entrypoint-initdb.d/ 