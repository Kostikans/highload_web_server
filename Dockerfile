FROM ubuntu:20.04

USER root

RUN  apt-get -y update
RUN  apt-get install -y python3
RUN apt-get install -y sudo

ADD . .

EXPOSE 80

CMD sudo python3 main.py