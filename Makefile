SHELL=/usr/bin/bash

all: update start

app:
	@systemctl restart gunicorn
	@systemctl restart gunicorn.socket

debug:
	@python manage.py runserver 0.0.0.0:8080

start: app

update: install
	@pybabel compile -f -d locales -D bot

install:
	@pip install -r requirements.txt

.PHONY: all app start update install
