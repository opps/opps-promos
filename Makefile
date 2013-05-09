
.PHONY: install
install:
	pip install -r requirements.txt --use-mirrors
	python setup.py develop

.PHONY: tx
tx:
	mkdir -p opps/promos/locale/en_US/LC_MESSAGES
	touch opps/promos/locale/en_US/LC_MESSAGES/django.po
	tx set --auto-remote https://www.transifex.com/projects/p/opps/resource/promos/
	tx set --auto-local -r opps.promos "opps/promos/locale/<lang>/LC_MESSAGES/django.po" --source-language=en_US --source-file "opps/promos/locale/en_US/LC_MESSAGES/django.po" --execute
	tx pull -f
