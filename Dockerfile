FROM python:3.7-buster

WORKDIR /usr/src
RUN apt-get update && \
    apt-get install -y libsndfile1-dev libgl1 libjack-jackd2-dev && \
    apt-get clean
COPY requirements.txt /usr/src
RUN pip3 install -r requirements.txt
COPY . /usr/src/
RUN python3 setup.py install
