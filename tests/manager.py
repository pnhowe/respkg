import os
import sqlite3
from respkg import manager

TEST_DB_PATH = '/tmp/respkg_manager_test.db'

def _init_workspace():
  manager.STATE_DB_FILE_NAME = TEST_DB_PATH
  try:
    os.unlink( TEST_DB_PATH )
  except:
    pass

def _dump_tables():
  conn = sqlite3.connect( TEST_DB_PATH )
  result = {}
  cur = conn.cursor()

  cur.execute( 'SELECT "name", "url", "component", "proxy", "pub_key" FROM "repos" ORDER BY "name";' )
  result[ 'repos' ] = [ i for i in cur.fetchall() ]

  cur.execute( 'SELECT "package", "version", "target_dir", "description", "pkg_created" FROM "packages" ORDER BY "package";' )
  result[ 'packages' ] = [ i for i in cur.fetchall() ]

  cur.execute( 'SELECT "package", "file_path", "sha256" FROM "files" ORDER BY "file_path";' )
  result[ 'files' ] = [ i for i in cur.fetchall() ]

  cur.execute( 'SELECT "package", "with" FROM "conflicts" ORDER BY "package", "with";' )
  result[ 'conflicts' ] = [ i for i in cur.fetchall() ]

  cur.execute( 'SELECT "package", "target" FROM "provides" ORDER BY "package", "target";' )
  result[ 'provides' ] = [ i for i in cur.fetchall() ]

  return result

def test_tableinit():
  _init_workspace()
  conn = sqlite3.connect( TEST_DB_PATH )
  dump = '\n'.join( conn.iterdump() )
  conn.close()
  assert dump == 'BEGIN TRANSACTION;\nCOMMIT;'

  manager.RespkgManager._checkDB( TEST_DB_PATH )
  conn = sqlite3.connect( TEST_DB_PATH )
  dump = '\n'.join( conn.iterdump() )
  conn.close()
  print dump
  assert dump == """BEGIN TRANSACTION;
CREATE TABLE "conflicts" (
      "package" char(50) NOT NULL,
      "with" char(50) NOT NULL,
      "created" datetime DEFAULT CURRENT_TIMESTAMP,
      "modified" datetime DEFAULT CURRENT_TIMESTAMP
    );
CREATE TABLE "control" ( "key" text, "value" text );
INSERT INTO "control" VALUES('version','2');
CREATE TABLE "files" (
      "package" char(50) NOT NULL,
      "file_path" char(512) NOT NULL UNIQUE,
      "sha256" char(65) NOT NULL,
      "created" datetime DEFAULT CURRENT_TIMESTAMP,
      "modified" datetime DEFAULT CURRENT_TIMESTAMP
    );
CREATE TABLE "packages" (
      "package" char(50) NOT NULL UNIQUE,
      "version" char(20) NOT NULL,
      "target_dir" char(200) NOT NULL,
      "description" char(250),
      "installed" datetime,
      "pkg_created" datetime,
      "created" datetime DEFAULT CURRENT_TIMESTAMP,
      "modified" datetime DEFAULT CURRENT_TIMESTAMP
  );
CREATE TABLE "provides" (
      "package" char(50) NOT NULL,
      "target" char(50) NOT NULL,
      "created" datetime DEFAULT CURRENT_TIMESTAMP,
      "modified" datetime DEFAULT CURRENT_TIMESTAMP
    );
CREATE TABLE "repos" (
      "name" char(50) NOT NULL UNIQUE,
      "url" char(200) NOT NULL,
      "component" char(50) NOT NULL,
      "proxy" char(200),
      "pub_key" text,
      "created" datetime DEFAULT CURRENT_TIMESTAMP,
      "modified" datetime DEFAULT CURRENT_TIMESTAMP
    );
COMMIT;"""

def test_installing():
  _init_workspace()
  rmgr = manager.RespkgManager()

  assert _dump_tables() == { 'conflicts': [], 'files': [], 'packages': [], 'provides': [], 'repos': [] }

  rmgr.packageInstalled( 'thepackage', '1.0-1', 'the test package', 0, '/', [], [] )

  assert _dump_tables() == { 'conflicts': [],
                             'files': [],
                             'packages': [('thepackage', '1.0-1', '/', 'the test package', 0)],
                             'provides': [],
                             'repos': [] }

  assert rmgr.getInstalledPackages() == [ 'thepackage' ]
  #TODO test rmgr.packageList and getPackage, going to have to deal with the date time stamps

  rmgr.packageInstalled( 'otherpackage', '10.3-123', 'Other Package', 0, '/tmp', [], [] )

  assert _dump_tables() == { 'conflicts': [],
                             'files': [],
                             'packages': [ ( 'otherpackage', '10.3-123', '/tmp', 'Other Package', 0 ), ( 'thepackage', '1.0-1', '/', 'the test package', 0 ) ],
                             'provides': [],
                             'repos': [] }

  assert rmgr.getInstalledPackages() == [ 'otherpackage', 'thepackage' ]

  rmgr.packageInstalled( 'thepackage', '1.0-1', 'the test package', 0, '/', [ 'conflict1', 'conflict2' ], [] )

  assert _dump_tables() == { 'conflicts': [ ('thepackage', 'conflict1'), ('thepackage', 'conflict2') ],
                             'files': [],
                             'packages': [ ( 'otherpackage', '10.3-123', '/tmp', 'Other Package', 0 ), ( 'thepackage', '1.0-1', '/', 'the test package', 0 ) ],
                             'provides': [],
                             'repos': [] }

  assert rmgr.getInstalledPackages() == [ 'otherpackage', 'thepackage' ]

  rmgr.packageInstalled( 'thepackage', '1.0-1', 'the test package', 0, '/', [], [ 'provides1', 'provides2' ] )

  assert _dump_tables() == { 'conflicts': [],
                             'files': [],
                             'packages': [ ( 'otherpackage', '10.3-123', '/tmp', 'Other Package', 0 ), ( 'thepackage', '1.0-1', '/', 'the test package', 0 ) ],
                             'provides': [ ('thepackage', 'provides1'), ('thepackage', 'provides2') ],
                             'repos': [] }

  assert rmgr.getInstalledPackages() == [ 'otherpackage', 'thepackage' ]

  assert rmgr.getInstalledFiles() == []

  rmgr.setFileSum( 'thepackage', '/tmp/thepackage_file_1', '00001111000001111' )
  assert _dump_tables() == { 'conflicts': [],
                             'files': [('thepackage', '/tmp/thepackage_file_1', '00001111000001111')],
                             'packages': [ ( 'otherpackage', '10.3-123', '/tmp', 'Other Package', 0 ), ( 'thepackage', '1.0-1', '/', 'the test package', 0 ) ],
                             'provides': [ ('thepackage', 'provides1'), ('thepackage', 'provides2') ],
                             'repos': [] }
  assert rmgr.getInstalledFiles() == [ '/tmp/thepackage_file_1' ]

  rmgr.setFileSum( 'thepackage', '/tmp/thepackage_file_2', '00002222000001111' )
  assert _dump_tables() == { 'conflicts': [],
                             'files': [('thepackage', '/tmp/thepackage_file_1', '00001111000001111'), ('thepackage', '/tmp/thepackage_file_2', '00002222000001111')],
                             'packages': [ ( 'otherpackage', '10.3-123', '/tmp', 'Other Package', 0 ), ( 'thepackage', '1.0-1', '/', 'the test package', 0 ) ],
                             'provides': [ ('thepackage', 'provides1'), ('thepackage', 'provides2') ],
                             'repos': [] }
  assert rmgr.getInstalledFiles() == [ '/tmp/thepackage_file_1', '/tmp/thepackage_file_2' ]

  rmgr.setFileSum( 'otherpackage', '/tmp/otherpackage_a_file', '12341234' )
  assert _dump_tables() == { 'conflicts': [],
                             'files': [ ( 'otherpackage', '/tmp/otherpackage_a_file', '12341234' ), ('thepackage', '/tmp/thepackage_file_1', '00001111000001111'), ('thepackage', '/tmp/thepackage_file_2', '00002222000001111')],
                             'packages': [ ( 'otherpackage', '10.3-123', '/tmp', 'Other Package', 0 ), ( 'thepackage', '1.0-1', '/', 'the test package', 0 ) ],
                             'provides': [ ('thepackage', 'provides1'), ('thepackage', 'provides2') ],
                             'repos': [] }
  assert rmgr.getInstalledFiles() == [ '/tmp/otherpackage_a_file', '/tmp/thepackage_file_1', '/tmp/thepackage_file_2' ]

  rmgr.setFileSum( 'otherpackage', '/tmp/otherpackage_z_file', '000222' )
  assert _dump_tables() == { 'conflicts': [],
                             'files': [ ( 'otherpackage', '/tmp/otherpackage_a_file', '12341234' ), ( 'otherpackage', '/tmp/otherpackage_z_file', '000222' ), ('thepackage', '/tmp/thepackage_file_1', '00001111000001111'), ('thepackage', '/tmp/thepackage_file_2', '00002222000001111')],
                             'packages': [ ( 'otherpackage', '10.3-123', '/tmp', 'Other Package', 0 ), ( 'thepackage', '1.0-1', '/', 'the test package', 0 ) ],
                             'provides': [ ('thepackage', 'provides1'), ('thepackage', 'provides2') ],
                             'repos': [] }
  assert rmgr.getInstalledFiles() == [ '/tmp/otherpackage_a_file', '/tmp/otherpackage_z_file', '/tmp/thepackage_file_1', '/tmp/thepackage_file_2' ]

  rmgr.setFileSum( 'otherpackage', '/tmp/otherpackage_a_file', '23f23f' )
  assert _dump_tables() == { 'conflicts': [],
                             'files': [ ( 'otherpackage', '/tmp/otherpackage_a_file', '23f23f' ), ( 'otherpackage', '/tmp/otherpackage_z_file', '000222' ), ('thepackage', '/tmp/thepackage_file_1', '00001111000001111'), ('thepackage', '/tmp/thepackage_file_2', '00002222000001111')],
                             'packages': [ ( 'otherpackage', '10.3-123', '/tmp', 'Other Package', 0 ), ( 'thepackage', '1.0-1', '/', 'the test package', 0 ) ],
                             'provides': [ ('thepackage', 'provides1'), ('thepackage', 'provides2') ],
                             'repos': [] }
  assert rmgr.getInstalledFiles() == [ '/tmp/otherpackage_a_file', '/tmp/otherpackage_z_file', '/tmp/thepackage_file_1', '/tmp/thepackage_file_2' ]


def test_conflicts():
  _init_workspace()
  rmgr = manager.RespkgManager()

  assert _dump_tables() == { 'conflicts': [], 'files': [], 'packages': [], 'provides': [], 'repos': [] }

  rmgr.packageInstalled( 'thepackage', '1.0-1', 'the test package', 0, '/', [ 'conflict1', 'conflict2' ], [ 'provide1', 'provide2' ] )
  rmgr.packageInstalled( 'otherpackage', '1.0-1', 'the other test package', 0, '/', [ 'ocon1', 'ocon2', 'ocon3' ], [ 'oprov1', 'oprov2', 'oprov3' ] )

  assert _dump_tables() == { 'conflicts': [ ('otherpackage', 'ocon1'), ('otherpackage', 'ocon2'), ('otherpackage', 'ocon3'), ('thepackage', 'conflict1'), ('thepackage', 'conflict2') ],
                             'files': [],
                             'packages': [ ('otherpackage', '1.0-1', '/', 'the other test package', 0), ('thepackage', '1.0-1', '/', 'the test package', 0) ],
                             'provides': [ ('otherpackage', 'oprov1'), ('otherpackage', 'oprov2'), ('otherpackage', 'oprov3'), ('thepackage', 'provide1'), ('thepackage', 'provide2') ],
                             'repos': [] }

  assert rmgr.checkConflicts( 'newpkg', [] ) is False
  assert rmgr.checkConflicts( 'newpkg', [ 'newcon1' ] ) is False
  assert rmgr.checkConflicts( 'newpkg', [ 'thepackage' ] ) is True
  assert rmgr.checkConflicts( 'newpkg', [ 'otherpackage' ] ) is True
  assert rmgr.checkConflicts( 'newpkg', [ 'newcon1', 'otherpackage' ] ) is True
  assert rmgr.checkConflicts( 'newpkg', [ 'newcon1', 'newcon2' ] ) is False
  assert rmgr.checkConflicts( 'ocon1', [ 'newcon1', 'newcon2' ] ) is True
  assert rmgr.checkConflicts( 'ocon1', [ 'thepackage' ] ) is True
  assert rmgr.checkConflicts( 'ocon1', [ 'thepackage', 'newcon2'  ] ) is True
  assert rmgr.checkConflicts( 'newpkg', [ 'conflict1', 'newcon2'  ] ) is False


def test_depends():
  _init_workspace()
  rmgr = manager.RespkgManager()

  assert _dump_tables() == { 'conflicts': [], 'files': [], 'packages': [], 'provides': [], 'repos': [] }

  rmgr.packageInstalled( 'thepackage', '1.0-1', 'the test package', 0, '/', [ 'conflict1', 'conflict2' ], [ 'provide1', 'provide2' ] )
  rmgr.packageInstalled( 'otherpackage', '1.0-1', 'the other test package', 0, '/', [ 'ocon1', 'ocon2', 'ocon3' ], [ 'oprov1', 'oprov2', 'oprov3' ] )

  assert _dump_tables() == { 'conflicts': [ ('otherpackage', 'ocon1'), ('otherpackage', 'ocon2'), ('otherpackage', 'ocon3'), ('thepackage', 'conflict1'), ('thepackage', 'conflict2') ],
                             'files': [],
                             'packages': [ ('otherpackage', '1.0-1', '/', 'the other test package', 0), ('thepackage', '1.0-1', '/', 'the test package', 0) ],
                             'provides': [ ('otherpackage', 'oprov1'), ('otherpackage', 'oprov2'), ('otherpackage', 'oprov3'), ('thepackage', 'provide1'), ('thepackage', 'provide2') ],
                             'repos': [] }

  assert rmgr.checkDepends( 'newpkg', [] ) is True
  assert rmgr.checkDepends( 'thepackage', [] ) is True
  assert rmgr.checkDepends( 'newpkg', [ 'thepackage' ] ) is True
  assert rmgr.checkDepends( 'newpkg', [ 'ocon1' ] ) is False
  assert rmgr.checkDepends( 'newpkg', [ 'thestuff' ] ) is False
  assert rmgr.checkDepends( 'newpkg', [ 'oprov1' ] ) is True
  assert rmgr.checkDepends( 'thepackage', [ 'oprov1' ] ) is True
  assert rmgr.checkDepends( 'thepackage', [ 'thestuff' ] ) is False
  assert rmgr.checkDepends( 'thepackage', [ 'thestuff', 'oprov1' ] ) is False
  assert rmgr.checkDepends( 'thepackage', [ 'thestuff', 'mostuff' ] ) is False
  assert rmgr.checkDepends( 'thepackage', [ 'provide2', 'oprov1' ] ) is True
  assert rmgr.checkDepends( 'newpkg', [ 'provide2', 'oprov1' ] ) is True


def test_repos():
  _init_workspace()


if __name__ == '__main__':
  print 'best when executed like: py.test -x %s' % __file__
  for i in dir():
    if i.startswith( 'test_' ):
      globals()[i]()
