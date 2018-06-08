import json
import os
from datetime import datetime
from gzip import GzipFile
from tarfile import TarFile, TarInfo
from io import BytesIO


class RespkgBuilder( object ):
  def __init__( self ):
    self.control = {
                     'respkg_version': '1',
                     'created': datetime.utcnow().isoformat()
                   }
    self.init = None
    self.data = None

  def write( self, file_name ):
    if not self.data or not os.path.isdir( self.data ):
      raise Exception( 'Must set data before building' )

    gzfile = GzipFile( file_name, 'w' )
    tar = TarFile( fileobj=gzfile, mode='w' )

    buff = BytesIO( json.dumps( self.control ).encode() )
    info = TarInfo( name='./CONTROL' )
    info.size = buff.getbuffer().nbytes
    tar.addfile( tarinfo=info, fileobj=buff )

    if self.init is not None:
      buff = BytesIO( self.init.encode() )
      info = TarInfo( name='./INIT' )
      info.size = buff.getbuffer().nbytes
      tar.addfile( tarinfo=info, fileobj=buff )

    data = BytesIO()
    datatar = TarFile( fileobj=data, mode='w' )
    datatar.add( self.data, '/' )
    datatar.close()
    data.seek( 0 )

    info = TarInfo( name='./DATA' )
    info.size = data.getbuffer().nbytes
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

  @property
  def depends( self ):
    return self.control.get( 'depends', [] )

  @depends.setter
  def depends( self, value ):
    if isinstance( value, basestring ):
      self.control[ 'depends' ] = [ value ]
    elif isinstance( value, list ): #TODO: make sure every member of the list is a string
      self.control[ 'depends' ] = value
    else:
      raise TypeError( 'depends must be a string or list' )

  @property
  def conflicts( self ):
    return self.control.get( 'conflicts', [] )

  @conflicts.setter
  def conflicts( self, value ):
    if isinstance( value, basestring ):
      self.control[ 'conflicts' ] = [ value ]
    elif isinstance( value, list ): #TODO: make sure every member of the list is a string
      self.control[ 'conflicts' ] = value
    else:
      raise TypeError( 'conflicts must be a string or list' )

  @property
  def provides( self ):
    return self.control.get( 'provides', [] )

  @provides.setter
  def provides( self, value ):
    if isinstance( value, basestring ):
      self.control[ 'provides' ] = [ value ]
    elif isinstance( value, list ): #TODO: make sure every member of the list is a string
      self.control[ 'provides' ] = value
    else:
      raise TypeError( 'provides must be a string or list' )

  def setInit( self, value ):
    self.init = value
