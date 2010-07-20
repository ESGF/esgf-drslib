"""
Generate mapfiles from streams of DRS objects

"""

#!TODO: check againsts similar code in datanode_admin and merge

import sys


def drs_to_id(drs):
    """
    Returns an esgpublish id for this drs object.

    The esgpublish id is a '.'-separated sequence of DRS components
    from the activity to realm level.
    
    """
    return '.'.join([drs.activity,
                     drs.product,
                     drs.institute,
                     drs.model,
                     drs.experiment,
                     drs.frequency,
                     drs.realm])

#!TODO: add callout to get parameters like checksum.
def write_mapfile(stream, fh=sys.stdout):
    """
    Write an esgpublish mapfile from a stream of tuples (filepath, drs).

    """

    for path, drs in stream:
        #!TODO: check field order
        print >>fh, ' | '.join([path, drs_to_id(drs)])
        
