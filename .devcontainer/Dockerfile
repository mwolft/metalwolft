FROM mcr.microsoft.com/devcontainers/python:3.11-bookworm

ENV PYTHONUNBUFFERED 1

RUN rm -f /etc/apt/sources.list.d/yarn.list \
    && apt-get update \
    && export DEBIAN_FRONTEND=noninteractive \
    && apt-get -y install --no-install-recommends postgresql-client
