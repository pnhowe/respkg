import json
import os
from datetime import datetime
from StringIO import StringIO
from gzip import GzipFile
from tarfile import TarFile, TarInfo


class RpkgBuilder( object ):
  def __init__( self ):
    self.control = {
                     'created': datetime.utcnow().isoformat()
                   }
    self.init = ''
    self.data = None

  def write( self, file_name ):
    if not self.data or not os.path.isdir( self.data ):
      raise Exception( 'Must set data before building' )

    data = StringIO()
    datatar = TarFile( fileobj=data, mode='w' )
    datatar.add( self.data, '/' )
    datatar.close()
    data.seek( 0 )

    gzfile = GzipFile( file_name, 'w' )
    tar = TarFile( fileobj=gzfile, mode='w' )

    buff = StringIO( json.dumps( self.control ) )
    info = TarInfo( name='./CONTROL' )
    info.size = buff.len
    tar.addfile( tarinfo=info, fileobj=buff )

    buff = StringIO( self.init )
    info = TarInfo( name='./INIT' )
    info.size = buff.len
    tar.addfile( tarinfo=info, fileobj=buff )

    info = TarInfo( name='./DATA' )
    info.size = data.len
    tar.addfile( tarinfo=info, fileobj=data )

    tar.close()
    gzfile.close()

  @property
  def name( self ):
    return self.control.get( 'name', None )

  @name.setter
  def name( self, value ):
    self.control[ 'name' ] = value

  @property
  def version( self ):
    return self.control.get( 'version', None )

  @version.setter
  def version( self, value ):
    self.control[ 'version' ] = value

  @property
  def description( self ):
    return self.control.get( 'description', None )

  @description.setter
  def description( self, value ):
    self.control[ 'description' ] = value

  @property
  def created( self ):
    return self.control.get( 'created', datetime( 1980, 0, 0 ) )

  @created.setter
  def created( self, value ):
    self.control[ 'created' ] = value.isoformat()

  def setInit( self, value ):
    self.init = value
