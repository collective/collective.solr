# convenience makefile to boostrap & run buildout

version = 3.7

all: .installed.cfg
	bin/test

.installed.cfg: bin/buildout *.cfg
	bin/buildout

bin/buildout: bin/pip
	bin/pip install -r requirements.txt
	@touch -c $@

bin/python bin/pip:
	python$(version) -m venv .

clean:
	git clean -Xdf

.PHONY: all clean
