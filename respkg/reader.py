import json
from datetime import datetime
from StringIO import StringIO
from gzip import GzipFile
from tarfile import TarFile


class RespkgReader( object ):
  def __init__( self, file_name ):
    toptar = GzipFile( file_name, 'r' ).read()
    self.source = TarFile( fileobj=StringIO( toptar ) )

    self.control = json.loads( self.source.extractfile( './CONTROL' ).read() )

  @property
  def name( self ):
    return self.control.get( 'name', None )

  @property
  def version( self ):
    return self.control.get( 'version', None )

  @property
  def description( self ):
    return self.control.get( 'description', None )

  @property
  def created( self ):
    return self.control.get( 'created', datetime( 1980, 1, 1 ) )

  def readInit( self ):
    return self.source.extractfile( './INIT' ).read()

  def extract( self, path ):
    TarFile( fileobj=self.source.extractfile( './DATA' ) ).extractall( path=path )
