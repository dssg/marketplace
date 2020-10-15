# DSSG Solve container build file
#

ARG PYVERSION=3.7

FROM python:$PYVERSION

ARG APPVERSION
ARG CHVERSION=2.2.0

# build for production by default, but allow use of alternative Python
# requirement files for alternative runtime targets (such as development)
ARG TARGET=production

# redeclare PYVERSION argument for access in label
ARG PYVERSION

LABEL version="0.4" \
      appversion="$APPVERSION" \
      chversion="$CHVERSION" \
      pyversion="$PYVERSION" \
      target="$TARGET"

ENV APP_VERSION "$APPVERSION"
ENV DEBIAN_FRONTEND noninteractive
ENV PYTHONUNBUFFERED 1

RUN apt-get update && apt-get install -y \
      supervisor \
    && rm -rf /var/lib/apt/lists/*

# install chamber for (non-development) environments, which can populate
# the environ of CMD with environment-specific values, at run-time, via
# entrypoint override, e.g.:
#
#     [ /usr/local/bin/chamber, exec, marketplace/production, -- ]
#
# (chamber does not yet fully support a null backend, nor specification
# of the service by environment variable; so, it is not yet appropriate
# to integrate by default.)
RUN curl -fL \
      -o /usr/local/bin/chamber \
      https://github.com/segmentio/chamber/releases/download/v${CHVERSION}/chamber-v${CHVERSION}-linux-amd64 \
    && chmod +x /usr/local/bin/chamber

RUN groupadd webapp \
    && useradd webapp -g webapp
RUN mkdir -p /var/log/webapp \
    && chown webapp /var/log/webapp \
    && chmod ug+rx /var/log/webapp
RUN mkdir -p /var/run/webapp \
    && chown webapp /var/run/webapp \
    && chmod ug+rx /var/run/webapp

RUN mkdir -p /var/log/supervisor
COPY supervisor.conf /etc/supervisor/conf.d/webapp.conf

RUN mkdir -p /etc/webapp
COPY gunicorn.conf /etc/webapp/
COPY requirement /etc/webapp/requirement

WORKDIR /app
COPY src /app
RUN chown -R webapp /app

RUN pip install --upgrade pip
RUN pip install				\
      --no-cache-dir 			\
      --trusted-host pypi.python.org 	\
      -r /etc/webapp/requirement/$TARGET.txt

CMD supervisord -n -c /etc/supervisor/supervisord.conf

EXPOSE 8000
