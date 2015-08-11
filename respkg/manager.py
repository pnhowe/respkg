import urllib2
import httplib
import socket
import json
import sqlite3

STATE_DB_FILE_NAME = '/var/lib/respkg/manager.db'

__VERSION__ = "0.1"

class RsepkgManager( object ):
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
      "package" char(50) NOT NULL UNIQUE,
      "version" char(20) NOT NULL,
      "target_dir" char(200) NOT NULL,
      "description" char(250),
      "installed" datetime,
      "pkg_created" datetime,
      "created" datetime DEFAULT CURRENT_TIMESTAMP,
      "modified" datetime DEFAULT CURRENT_TIMESTAMP
  );""" )

      conn.execute( """CREATE TABLE "repos" (
      "name" char(50) NOT NULL UNIQUE,
      "url" char(200) NOT NULL,
      "component" char(50) NOT NULL,
      "proxy" char(200),
      "pub_key" text,
      "created" datetime DEFAULT CURRENT_TIMESTAMP,
      "modified" datetime DEFAULT CURRENT_TIMESTAMP
    );""" )

    #TODO: make package.package and repo.name unique

    conn.execute( 'UPDATE "control" SET "value" = "2" WHERE "key" = "version";' )
    conn.commit()

  def _getHTTP( self, path, proxy, target_file=None ):
    if proxy:
      opener = urllib2.build_opener( urllib2.ProxyHandler( { 'http': proxy, 'https': proxy } ) )
    else:
      opener = urllib2.build_opener( urllib2.ProxyHandler( {} ) ) # no proxying, not matter what is in the enviornment

    opener.addheaders = [ ( 'User-agent', 'respkg %s' % __VERSION__ ) ]

    try:
      resp = opener.open( path )

    except urllib2.HTTPError, e:
      if e.code == 404:
        print '"%s" not found' % path
        return None

      if e.code == 500:
        print 'Server Error retreiving "%s"' % path
        return None

    except urllib2.URLError, e:
      print 'URLError Requesting "%s", "%s"' % ( path, e.reason )

    except httplib.HTTPException, e:
      print 'HTTPException Requesting "%s", "%s"' % ( path, e.message )
      return None

    except socket.error as e:
      print 'Socket Error Requesting "%s", errno: %s, "%s"' % ( path, e.errno, e.message )
      return None

    if target_file:
      buff = resp.read( 40960 )
      while( buff ):
        target_file.write( buff )
        buff = resp.read( 40960 )

      return True

    else:
      return resp.read()

  def _getManafest( self, url, component, proxy ):
    path = '%s/_repo_%s/MANIFEST_none--all.json' % ( url, component )
    manifest = self._getHTTP( path, proxy )
    if manifest is None:
      return None

    try:
      return json.loads( manifest )
    except ValueError:
      print 'Manafest at "%s" is not valid JSON' % path
      return None

    return None

  def _getPackageFile( self, repo_url, file, proxy ):
    path = '%s/%s' % ( repo_url, file )
    tmpfile = open( '/tmp/respkgdownload.tmp', 'w' )
    rc = self._getHTTP( path, proxy, tmpfile )
    if rc is None:
      return None

    tmpfile.close()

    return '/tmp/respkgdownload.tmp'

  def packageList( self ):
    result = {}
    cur = self.conn.cursor()
    cur.execute( 'SELECT "package", "version", "target_dir", "description", "installed", "pkg_created", "modified", "created" FROM "packages";'  )
    for ( package, version, target_dir, description, installed, pkg_created, modified, created ) in cur.fetchall():
      result[ str( package ) ] = { 'version': str( version ), 'target_dir': str( target_dir ), 'description': str( description ), 'installed': installed, 'pkg_created': pkg_created, 'modified': modified, 'created': created }

    cur.close()

    return result

  def packageInstalled( self, name, version, description, pkg_created, target_dir ):
    cur = self.conn.cursor()
    cur.execute( 'SELECT COUNT(*) FROM "packages" WHERE "package" = "%s";' % name )
    ( count, ) = cur.fetchone()
    if count == 0:
      cur.execute( 'INSERT INTO "packages" ( "package", "version", "target_dir", "description", "installed", "pkg_created" ) VALUES ( ?, ?, ?, ?, CURRENT_TIMESTAMP, ? );', ( name, version, target_dir, description, pkg_created ) )

    else:
      cur.execute( 'UPDATE "packages" SET "version"=?, "target_dir"=?, "description"=?, "pkg_created"=?, "installed"=CURRENT_TIMESTAMP, "modified"=CURRENT_TIMESTAMP WHERE "package"=?;', ( version, target_dir, description, pkg_created, name ) )

    cur.close()
    self.conn.commit()

  def getPackage( self, name ):
    result = {}
    cur = self.conn.cursor()
    cur.execute( 'SELECT "version", "target_dir", "description", "installed", "pkg_created", "modified" FROM "packages" WHERE "package" = "%s";' % name )
    try:
      ( version, target_dir, description, installed, pkg_created, modified ) = cur.fetchone()
    except TypeError:
      return None

    result = { 'version': str( version ), 'target_dir': str( target_dir ), 'description': str( description ), 'installed': installed, 'pkg_create': pkg_created, 'modified': modified }
    cur.close()

    return result

  def addRepo( self, name, url, component, proxy ):
    if self._getManafest( url, component, proxy ) is None:
      print 'Error adding repo'
      return None

    cur = self.conn.cursor()
    cur.execute( 'SELECT COUNT(*) FROM "repos" WHERE "name" = "%s";' % name )
    ( count, ) = cur.fetchone()
    if count == 1:
      cur.close()
      raise Exception( 'repo name "%s" allready in use' % name )

    cur.execute( 'INSERT INTO "repos" ( "name", "url", "component", "proxy" ) VALUES ( ?, ?, ?, ? );', ( name, url, component, proxy ) )

    cur.close()
    self.conn.commit()

  def setRepoKey( self, name, pub_key ):
    cur = self.conn.cursor()
    cur.execute( 'SELECT COUNT(*) FROM "repos" WHERE "name" = "%s";' % name )
    ( count, ) = cur.fetchone()
    if count != 1:
      cur.close()
      raise Exception( 'repo named "%s" not found' )

    cur.execute( 'UPDATE "repos" SET "pub_key"="?" WHERE "name"="?";', name, pub_key )

    cur.close()
    self.conn.commit()

  def getManafest( self, name ):
    cur = self.conn.cursor()
    cur.execute( 'SELECT "url", "component", "proxy", "pub_key" FROM "repos" WHERE "name" = "%s";' % name )
    ( url, component, proxy, pub_key ) = cur.fetchone()
    cur.close()

    return self._getManafest( url, component, proxy )

  def getPackageFile( self, repo_name, package_name, version=None ):
    manafest = self.getManafest( repo_name )
    try:
      package = manafest[ package_name ]
    except KeyError:
      print 'Package "%s" not found in manafest' % package_name
      return False



    return self._getPackageFile( repo_url, file_name, proxy )

  def repoList( self ):
    result = {}
    cur = self.conn.cursor()
    cur.execute( 'SELECT "name", "url", "component", "pub_key", "proxy", "modified", "created" from "repos";' )
    for ( name, url, component, pub_key, proxy, modified, created ) in cur.fetchall():
      result[ str( name ) ] = { 'url': str( url ), 'component': str( component ), 'has_key': bool( pub_key ), 'proxy': str( proxy ), 'modified': modified, 'created': created }

    cur.close()

    return result

  def getRepoPackages( self, name ):
    pass
