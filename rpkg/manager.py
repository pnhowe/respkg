import sqlite3

STATE_DB_FILE_NAME = '/var/lib/rpkg/manager.db'

class RpkgManager( object ):
  def __init__( self ):
    self._checkDB( STATE_DB_FILE_NAME ) # check db before we connect to it
    self.conn = sqlite3.connect( STATE_DB_FILE_NAME )

  def _checkDB( self, state_db ):
    conn = sqlite3.connect( state_db )
    cur = conn.cursor()
    cur.execute( 'SELECT COUNT(*) FROM "sqlite_master" WHERE type="table" and name="control";' )
    ( count, ) = cur.fetchone()
    if count == 0:
      conn.execute( 'CREATE TABLE "control" ( "key" text, "value" text );' )
      conn.commit()
      conn.execute( 'INSERT INTO "control" VALUES ( "version", "1" );' )
      conn.commit()

    cur = conn.cursor()
    cur.execute( 'SELECT "value" FROM "control" WHERE "key" = "version";' )
    ( version, ) = cur.fetchone()
    if version < '2':
      conn.execute( """CREATE TABLE "packages" (
      "package" char(50) NOT NULL,
      "version" char(20) NOT NULL,
      "description" char(250) NOT NULL,
      "installed" datetime,
      "pkg_created" datetime,
      "created" datetime DEFAULT CURRENT_TIMESTAMP,
      "modified" datetime DEFAULT CURRENT_TIMESTAMP
  );""" )

      conn.execute( """CREATE TABLE "repos" (
      "name" char(50) NOT NULL,
      "url" char(200) NOT NULL,
      "pub_key" text,
      "last_checked" datetime,
      "created" datetime DEFAULT CURRENT_TIMESTAMP,
      "modified" datetime DEFAULT CURRENT_TIMESTAMP
    );""" )

    #TODO: make package.package and repo.name unique

    conn.execute( 'UPDATE "control" SET "value" = "2" WHERE "key" = "version";' )
    conn.commit()

  def getInstalledPackages( self ):
    result = {}
    cur = self.conn.cursor()
    cur.execute( 'SELECT "package", "version", "description", "installed", "pkg_created", "modified", "created" FROM "packages";'  )
    for ( package, version, description, installed, pkg_created, modified, created ) in cur.fetchall():
      result[ str( package ) ] = { 'version': str( version ), 'description': str( description ), 'installed': installed, 'pkg_create': pkg_created, 'modified': modified, 'created': created }

    cur.close()

    return result

  def packageInstalled( self, name, version, description, pkg_created ):
    cur = self.conn.cursor()
    cur.execute( 'SELECT COUNT(*) FROM "packages" WHERE "package" = "%s";' % name )
    ( count, ) = cur.fetchone()
    if count == 0:
      cur.execute( 'INSERT INTO "packages" ( "package", "version", "description", "installed", "pkg_created" ) VALUES ( ?, ?, ?, CURRENT_TIMESTAMP, ? );', ( name, version, description, pkg_created ) )

    else:
      cur.execute( 'UPDATE "packages" SET "version"=?, "description"=?, "pkg_created"=?, "installed"=CURRENT_TIMESTAMP, "modified"=CURRENT_TIMESTAMP WHERE "package"=?;', ( version, description, pkg_created, name ) )

    cur.commit()
    self.conn.commit()

  def getPackage( self, name ):
    result = {}
    cur = self.conn.cursor()
    cur.execute( 'SELECT "version", "description", "installed", "pkg_created", "modified" FROM "packages" WHERE "package" = "%s";' % name )
    ( version, description, installed, pkg_created, modified ) = cur.fetchone()
    result = { 'version': str( version ), 'description': str( description ), 'installed': installed, 'pkg_create': pkg_created, 'modified': modified }
    cur.close()

    return result

  def addRepo( self, name, url, pub_key ):
    cur = self.conn.cursor()
    cur.execute( 'SELECT COUNT(*) FROM "repo" WHERE "name" = "%s";' % name )
    ( count, ) = cur.fetchone()
    if count == 1:
      cur.close()
      raise Exception( 'repo name "%s" allready in use' % name )

    cur.execute( 'INSERT INTO "repo" ( "name", "url", "pub_key" ) VALUES ( ?, ?, ? );', ( name, url, pub_key ) )

    cur.close()
    self.conn.commit()

  def repoList( self ):
    result = {}
    cur = self.conn.cursor()
    cur.execute( 'SELECT "name", "url", "pub_key", "last_checked", "modified", "created" from "repos";' )
    for ( name, url, pub_key, last_checked, modified, created ) in cur.fetchall():
      result[ str( name ) ] = { 'url': str( url ), 'has_key': bool( pub_key ), 'last_checked': last_checked, 'modified': modified, 'created': created }

    cur.close()

    return result

  def getRepoPackages( self, name ):
    pass
