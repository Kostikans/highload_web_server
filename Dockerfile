FROM ubuntu:20.04

USER root

RUN apt-get -y update
RUN apt-get install -y sudo
RUN apt-get install -y python3
RUN apt-get -y install python3-pip
RUN pip3 install asyncio

ADD . .

EXPOSE 80

CMD sudo python3 main.py