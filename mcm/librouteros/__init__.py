# -*- coding: UTF-8 -*-

'''
from librouteros import connect
api = connect( '1.1.1.1', 'admin', 'password' )
api.run('/ip/address/print')
'''


from logging import getLogger, NullHandler
from socket import create_connection, error as SOCKET_ERROR, timeout as SOCKET_TIMEOUT
from binascii import unhexlify, hexlify
from hashlib import md5
try:
    from collections import ChainMap
except ImportError:
    from mcm.tools import ChainMap

from mcm.librouteros.exceptions import ConnError, CmdError, LoginError
from mcm.librouteros.connections import ReaderWriter
from mcm.librouteros.api import Api

NULL_LOGGER = getLogger( 'api_null_logger' )
NULL_LOGGER.addHandler( NullHandler() )



def connect( host, user, pw, **kwargs ):
    '''
    Connect and login to routeros device.
    Upon success return a Connection class.

    host
        Hostname to connecto to. May be ipv4,ipv6,FQDN.
    user
        Username to login with.
    pw
        Password to login with. Defaults to be empty.
    timout
        Socket timeout. Defaults to 10.
    port
        Destination port to be used. Defaults to 8728.
    logger
        Logger instance to be used. Defaults to an empty logging instance.
    saddr
        Source address to bind to.
    '''

    defaults = { 'timeout' : 10,
                'port' : 8728,
                'saddr' : '',
                'logger' : NULL_LOGGER
                }

    arguments = ChainMap(kwargs, defaults)

    try:
        sock = create_connection( ( host, arguments['port'] ), arguments['timeout'], ( arguments['saddr'], 0 ) )
    except ( SOCKET_ERROR, SOCKET_TIMEOUT ) as error:
        raise ConnError( error )

    rwo = ReaderWriter( sock, arguments['logger'] )
    api = Api( rwo )

    try:
        snt = api.run( '/login' )
        chal = snt[0]['ret']
        encoded = _encode_password( chal, pw )
        api.run( '/login', {'name':user, 'response':encoded} )
    except ( ConnError, CmdError ) as error:
        rwo.close()
        raise LoginError( error )

    return api



def _encode_password( chal, password ):

    chal = chal.encode( 'UTF-8', 'strict' )
    chal = unhexlify( chal )
    password = password.encode( 'UTF-8', 'strict' )
    md = md5()
    md.update( b'\x00' + password + chal )
    password = hexlify( md.digest() )
    password = '00' + password.decode( 'UTF-8', 'strict' )

    return password


