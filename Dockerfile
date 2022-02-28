
ARG BASE_CONTAINER=python:3.7-buster
FROM $BASE_CONTAINER

ARG PUID=1001
ARG PGID=1001
ARG USERNAME=lincoln
ARG WORKDIR=/package
ARG VERSION=0.1.0

WORKDIR $WORKDIR

COPY dist/clients-$VERSION-py3-none-any.whl .

RUN pip install --upgrade pip

RUN groupadd --gid $PGID $USERNAME \
    && useradd --uid $PUID --gid $PGID -m $USERNAME \
    && chown -R $PUID:$PGID $WORKDIR

USER $USERNAME

ENV SHELL="/bin/bash"
ENV PATH="/home/${USERNAME}/.local/bin:${PATH}"

RUN pip install --user clients-$VERSION-py3-none-any.whl && \
    rm -f *.whl

ENTRYPOINT ["clients"]

