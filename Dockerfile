FROM ubuntu:20.04

USER root

RUN  apt-get -y update
RUN  apt-get install -y python3

ADD . .

EXPOSE 80
RUN pip3 install -r requirements.txt

CMD python3 main.py