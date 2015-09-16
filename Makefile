all:

install:
	mkdir -p $(DESTDIR)var/lib/respkg
	mkdir -p $(DESTDIR)usr/bin
	install -m 755 bin/respkg $(DESTDIR)usr/bin

clean:
	$(RM) -fr build
	$(RM) -f dpkg
	$(RM) -f rpm

full-clean: clean
	$(RM) -fr debian
	$(RM) -fr rpmbuild
	$(RM) -f dpkg-setup
	$(RM) -f rpm-setup

dpkg-distros:
	echo precise trusty

dpkg-requires:
	echo dpkg-dev debhelper cdbs

dpkg-setup:
	./debian-setup
	touch dpkg-setup

dpkg:
	dpkg-buildpackage -b -us -uc
	touch dpkg

dpkg-file:
	echo $(shell ls ../respkg_*.deb)

rpm-distros:
	echo centos6

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
