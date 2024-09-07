FROM modpipe-base:latest
COPY . .
CMD /flask/start.sh
