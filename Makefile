init:
	sh sh/init.sh

lint:
	flake8
	isort .
	black .