FROM ghcr.io/modpipe/modpipe-base:latest
COPY . .
CMD /flask/start.sh
