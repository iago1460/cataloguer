FROM python:3.9.5-alpine3.13

RUN apk add --no-cache jpeg-dev zlib-dev build-base g++ freetype-dev
RUN apk add --no-cache --virtual .build-deps gcc musl-dev libffi-dev tzdata

COPY ./requirements*.txt /
RUN pip3 install -r /requirements.txt

COPY ./catalogue /srv/catalogue

WORKDIR /srv/

ENV PYTHONUNBUFFERED 1

ENTRYPOINT [ "python3", "-m", "catalogue"]
