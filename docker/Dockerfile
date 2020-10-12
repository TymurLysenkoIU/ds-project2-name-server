FROM python:3.8.6-alpine3.12

# Make declarations and copy the entrypoint script, because it doesn't change often,
# so the earlear this is done, the faster subsequent builds will be, when source code
# of the application changes
ENV LANG="en_US.utf8"
ENV LANGUAGE="en_US:en"
ENV LC_ALL="en_US.utf8"

RUN apk update && \
    apk add \
      build-base libffi-dev libressl-dev

EXPOSE 80

# Install requirements
COPY ./requirements.txt /requirements.txt
RUN pip3 install -r /requirements.txt

# Declare environment variables for the application
ENV DJANGO_SECRET_KEY="set_your_secret"
ENV MONGO_HOST="mongo:27017"
ENV MONGO_USER="mongo"
ENV MONGO_PASS="admin"
ENV FTP_USER="ftpuser"
ENV FTP_PASS="ftp-pass"
ENV STORAGE_REQUEST_TIMEOUT=1

# Copy the application to the image
COPY ./name_server_proj /name-server/name_server_proj
COPY ./name_server_app /name-server/name_server_app
COPY ./docker/settings.py /name-server/name_server_proj/
# Copy static files
COPY ./manage.py /name-server/
RUN cd /name-server/ && python3 manage.py collectstatic --noinput
# nginx needs to be configured to serve static files, but is not needed for now

WORKDIR /name-server
ENTRYPOINT [\
    "daphne",\
    "-b", "0.0.0.0", "-p", "80",\
    "name_server_proj.asgi:application"\
  ]
