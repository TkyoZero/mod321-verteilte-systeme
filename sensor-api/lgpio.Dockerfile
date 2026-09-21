FROM python:3.12

RUN apt-get update

RUN apt install -y swig python3-dev

RUN pip install setuptools

COPY ./lg.zip .

RUN unzip lg.zip

WORKDIR /lg

RUN make

RUN make install

RUN pip install smbus paho-mqtt rpi-lgpio

RUN pip install dht11 --no-deps

WORKDIR /usr/src/app