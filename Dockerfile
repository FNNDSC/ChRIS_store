#
# Docker file for ChRIS store production server
#
# Build with
#
#   docker build -t <name> .
#
# For example if building a local version, you could do:
#
#   docker build -t local/chris_store .
#
# In the case of a proxy (located at proxy.tch.harvard.edu:3128), do:
#
#    docker build --build-arg http_proxy=http://proxy.tch.harvard.edu:3128 --build-arg UID=$UID -t local/chris_store .
#
# To run an interactive shell inside this container, do:
#
#   docker run -ti --entrypoint /bin/bash local/chris_store
#

FROM fnndsc/ubuntu-python3:latest
MAINTAINER fnndsc "dev@babymri.org"

# Pass a UID on build command line (see above) to set internal UID
ARG UID=1001
ENV UID=$UID  VERSION="0.1"

ENV APPROOT="/home/localuser/store_backend" REQPATH="/usr/src/requirements"
COPY ["./requirements", "${REQPATH}"]
COPY ["./docker-entrypoint.sh", "/usr/src"]

RUN apt-get update \
  && apt-get install -y libssl-dev libmysqlclient-dev                 \
  && apt-get install -y apache2 apache2-dev                           \
  && pip install -r ${REQPATH}/production.txt                           \
  && useradd -u $UID -ms /bin/bash localuser

# Start as user localuser
USER localuser

COPY --chown=localuser ["./store_backend", "${APPROOT}"]

WORKDIR $APPROOT
ENTRYPOINT ["/usr/src/docker-entrypoint.sh"]
EXPOSE 8010
