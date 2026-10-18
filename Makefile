VENV := .venv
TAILWIND := ./tailwindcss

.PHONY: install css watch run migrate makemigrations test check

install:
	$(VENV)/bin/pip install -r requirements.txt

css:
	$(TAILWIND) -i static/css/input.css -o static/css/app.css --minify

watch:
	$(TAILWIND) -i static/css/input.css -o static/css/app.css --watch

run:
	$(VENV)/bin/python manage.py runserver

migrate:
	$(VENV)/bin/python manage.py migrate

makemigrations:
	$(VENV)/bin/python manage.py makemigrations

check:
	$(VENV)/bin/python manage.py check

test:
	$(VENV)/bin/python manage.py test
