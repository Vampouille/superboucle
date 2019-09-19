FROM debian:buster

WORKDIR /usr/src
COPY superboucle_1.2.0-1_all.deb /usr/src
RUN dpkg -i superboucle_1.2.0-1_all.deb || true && \
    apt update && \
    apt --fix-broken install -y && \
    apt clean
