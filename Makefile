DISTRO := $(shell lsb_release -si | tr A-Z a-z)
DISTRO_MAJOR_VERSION := $(shell lsb_release -sr | cut -d. -f1)
DISTRO_NAME := $(shell lsb_release -sc | tr A-Z a-z)
VERSION := $(shell head -n 1 debian-common/changelog | awk '{match( $$0, /\(.+?\)/); print substr( $$0, RSTART+1, RLENGTH-2 ) }' | cut -d- -f1 )

all:
	./setup.py build

install:
	mkdir -p $(DESTDIR)/var/lib/respkg
	mkdir -p $(DESTDIR)/usr/bin
	install -m 755 bin/respkg $(DESTDIR)/usr/bin

ifeq (ubuntu, $(DISTRO))
	./setup.py install --root $(DESTDIR) --install-purelib=/usr/lib/python3/dist-packages/ --prefix=/usr --no-compile -O0
else
	./setup.py install --root $(DESTDIR) --prefix=/usr --no-compile -O0
endif

version:
	echo $(VERSION)

clean:
	./setup.py clean
	$(RM) -fr build
	$(RM) -f dpkg
	$(RM) -f rpm
ifeq (ubuntu, $(DISTRO))
	dh_clean || true
endif

dist-clean: clean
	$(RM) -fr debian
	$(RM) -fr rpmbuild
	$(RM) -f dpkg-setup
	$(RM) -f rpm-setup

test-distros:
	echo ubuntu-xenial

test-requires:
	echo flake8 python3-pytest python3-pytest-cov

test:
	py.test-3 --cov=respkg --cov-report html --cov-report term -x

lint:
	flake8 --ignore=E501,E201,E202,E111,E126,E114,E402,W605 --statistics .

dpkg-distros:
	echo ubuntu-trusty ubuntu-xenial ubuntu-bionic

dpkg-requires:
	echo dpkg-dev debhelper python3-dev python3-setuptools

dpkg-setup:
	./debian-setup
	touch dpkg-setup

dpkg:
	dpkg-buildpackage -b -us -uc
	touch dpkg

dpkg-file:
	echo $(shell ls ../respkg_*.deb)

rpm-distros:
	echo centos-6 centos-7

rpm-requires:
	echo rpm-build

rpm-setup:
	./rpmbuild-setup
	touch rpm-setup

rpm:
	rpmbuild -v -bb rpmbuild/config.spec
	touch rpm

rpm-file:
	echo $(shell ls rpmbuild/RPMS/*/respkg-*.rpm)

.PHONY: all clean full-clean dpkg-distros dpkg-requires dpkg-file rpm-distros rpm-requires rpm-file
