RESourcePacKaGe
===============

respkg is a light packager.  The Package contains an archive that is extracted into the target filesystem as well as an init script that is executed after extraction.  There is no rollback, nor advanced error handeling, nor uninstall.  It does however offer checksum validation of extracted files.
The target usage is for bundeling resources in a distro agnostic format.  Making is lighter and easier to implement than maintaing distro specific pacakges, and adds an post extraction script (init script) over a traditaional .tar.?? file.

The respkg utility understands a JSON repo as implemneted by Packrat (https://github.com/pnhowe/packrat) to enable central storage of the resource pacakges.


Usage
-----

Building a Package
------------------

Building::

  respkg --build diskimages_0.1.respkg --name diskimages --verion 0.1 --description "Demo Disk Images" --init-script load_init.sh -d images


Installing a Package
--------------------

Installing::

  respkg --install diskimages_0.1.respkg

Other
-----

List installed::

  respkg --list

Verify the Checksums of the locally installed files::

  respkg --check-installed

Installing from Repo
--------------------

First add a repo to the local database::

  respkg --add-repo repo http://repo/json/prod/ main

Now you can install from that named repo::

  respkg --from-repo repo base-config

