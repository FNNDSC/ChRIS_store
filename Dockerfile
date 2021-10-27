#
# Docker file for ChRIS store image
#
# Build production image:
#
#   docker build -t <name> .
#
# For example if building a local production image:
#
#   docker build -t local/chris_store .
#
# Build development image:
#
#   docker build --build-arg ENVIRONMENT=local -t <name>:<tag> .
#
# For example if building a local development image:
#
#   docker build --build-arg ENVIRONMENT=local -t local/chris_store:dev .
#
# In the case of a proxy (located at say proxy.tch.harvard.edu:3128), do:
#
#    export PROXY="http://proxy.tch.harvard.edu:3128"
#
# then add to any of the previous build commands:
#
#    --build-arg http_proxy=${PROXY}
#
# For example if building a local development image:
#
# docker build --build-arg http_proxy=${PROXY} --build-arg ENVIRONMENT=local -t local/chris_store:dev .
#

FROM fnndsc/ubuntu-python3:ubuntu20.04-python3.8.5
MAINTAINER fnndsc "dev@babymri.org"

# Pass a UID on build command line (see above) to set internal UID
ARG UID=1001
ARG ENVIRONMENT=production
ENV UID=$UID DEBIAN_FRONTEND=noninteractive VERSION="0.1"

ENV APPROOT="/home/localuser/store_backend" REQPATH="/usr/src/requirements"
COPY ["./requirements", "${REQPATH}"]
COPY ["./docker-entrypoint.sh", "/usr/src"]

RUN apt-get update                                               \
  && apt-get install -y locales                                  \
  && export LANGUAGE=en_US.UTF-8                                 \
  && export LANG=en_US.UTF-8                                     \
  && export LC_ALL=en_US.UTF-8                                   \
  && locale-gen en_US.UTF-8                                      \
  && dpkg-reconfigure locales                                    \
  && apt-get install -y libssl-dev libpq-dev                     \
  && apt-get install -y apache2 apache2-dev                      \
  && pip install --upgrade pip                                   \
  && pip install -r ${REQPATH}/${ENVIRONMENT}.txt                \
  && useradd -l -u $UID -ms /bin/bash localuser

# Start as user localuser
USER localuser

COPY --chown=localuser ["./store_backend", "${APPROOT}"]

WORKDIR $APPROOT
ENTRYPOINT ["/usr/src/docker-entrypoint.sh"]
EXPOSE 8010

# Start ChRIS store production server
CMD ["mod_wsgi-express", "start-server", "config/wsgi.py", "--host", "0.0.0.0", "--port", "8010", "--processes", "2", "--server-root", "/home/localuser/mod_wsgi-0.0.0.0:8010"]
#python manage.py runmodwsgi --working-directory $(pwd) --host 0.0.0.0 --port 8010 --server-name localhost --server-root ~/mod_wsgi-0.0.0.0:8010 --reload-on-changes
#mod_wsgi-express setup-server config/wsgi.py --host 0.0.0.0 --port 8010 --processes 4 --server-name localhost --server-root /home/localuser/mod_wsgi-0.0.0.0:8010
#to start daemon:
#/home/localuser/mod_wsgi-0.0.0.0:8010/apachectl start
#to stop deamon
#/home/localuser/mod_wsgi-0.0.0.0:8010/apachectl stop
