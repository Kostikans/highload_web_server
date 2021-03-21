FROM ubuntu:20.04

USER root

RUN  apt-get -y update
RUN  apt-get install -y python3

ADD . .

EXPOSE 80
ENV PYTHONPATH /highload_web_server

CMD python3 main.py