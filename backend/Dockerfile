FROM python:3.12-alpine

WORKDIR /backend

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONBUFFERED 1

COPY ./requirements.txt /backend/requirements.txt

RUN apk add --no-cache postgresql-libs \
		&& apk add --no-cache --virtual .build-deps gcc musl-dev postgresql-dev \
    && python3 -m pip install -r /backend/requirements.txt --no-cache-dir \
    && apk --purge del .build-deps

COPY . /backend