FROM python:3.8

WORKDIR /usr/src/pythonserver
COPY requirements.txt  requirements.txt
RUN pip install -r requirements.txt
COPY . .

CMD python3 main.py

EXPOSE 80