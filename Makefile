# keep in sync with: https://github.com/kitconcept/buildout/edit/master/Makefile

version = 2.7

all: .installed.cfg
	bin/test

update:
	wget -O Makefile https://raw.githubusercontent.com/kitconcept/buildout/master/Makefile
	wget -O requirements.txt https://raw.githubusercontent.com/kitconcept/buildout/master/requirements.txt

.installed.cfg: bin/buildout *.cfg
	bin/buildout

bin/buildout: bin/pip
	bin/pip install --upgrade pip
	bin/pip install -r requirements.txt
	@touch -c $@

build-plone-4.3: .installed.cfg
	bin/pip install --upgrade pip
	bin/pip install -r requirements.txt
	bin/buildout -c plone-4.3.x.cfg

build-plone-5.0: .installed.cfg
	bin/pip install --upgrade pip
	bin/pip install -r requirements.txt
	bin/buildout -c plone-5.0.x.cfg

build-plone-5.1: .installed.cfg
	bin/pip install --upgrade pip
	bin/pip install -r requirements.txt
	bin/buildout -c plone-5.1.x.cfg

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
	virtualenv --clear --python=python$(version) .

test:
	bin/test

release:
	bin/fullrelease

clean:
	git clean -Xdf

.PHONY: all clean