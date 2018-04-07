#!/usr/bin/env python3

from motionless import DecoratedMap, AddressMarker

if __name__ == '__main__':
	dmap = DecoratedMap( )
	dmap.add_marker( AddressMarker( 'Brown', label='1' ) )
	dmap.add_marker( AddressMarker( 'Cornell', label='2' ) )
	dmap.add_marker( AddressMarker( 'Dartmouth', label='3' ) )
	print( dmap.generate_url() )