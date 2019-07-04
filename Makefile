# keep in sync with: https://github.com/kitconcept/buildout/edit/master/Makefile

version = 3.7

all: .installed.cfg
	bin/test

.installed.cfg: bin/buildout *.cfg
	bin/buildout

bin/buildout: bin/pip
	bin/pip install --upgrade pip
	bin/pip install -r requirements.txt
	@touch -c $@

build-plone-5.2: .installed.cfg
	bin/pip install --upgrade pip
	bin/pip install -r requirements.txt
	bin/buildout -c plone-5.2.x.cfg

build-py3:
	virtualenv --python=python3 .
	bin/pip install --upgrade pip
	bin/pip install -r requirements.txt
	bin/buildout -c plone-5.2.x.cfg

bin/python bin/pip:
	python$(version) -m venv .

release:
	bin/fullrelease

clean:
	git clean -Xdf

.PHONY: all clean
