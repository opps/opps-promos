
.PHONY: install
install:
	pip install -r requirements.txt --use-mirrors
	python setup.py develop
