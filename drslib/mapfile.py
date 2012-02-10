# BSD Licence
# Copyright (c) 2011, Science & Technology Facilities Council (STFC)
# All rights reserved.
#
# See the LICENSE file in the source distribution of this software for
# the full license text.

"""
Generate mapfiles from streams of DRS objects

"""

#!TODO: check againsts similar code in datanode_admin and merge

import stat, os


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
                     drs.realm,
                     drs.table,
                     'r%di%dp%d' % drs.ensemble])

def write_mapfile(stream, fh, checksum_func=None):
    """
    Write an esgpublish mapfile from a stream of tuples (filepath, drs).

    :param checksum_func: A callable of one argument (path) which returns (checksum_type, checksum) or None

    """

    for path, drs in stream:
        file_stat = os.stat(path)
        size = file_stat[stat.ST_SIZE]
        mtime = file_stat[stat.ST_MTIME]

        params = [drs_to_id(drs), path, str(size), "mod_time=%f"%float(mtime)]

        if checksum_func:
            ret = checksum_func(path)
            if ret is not None:
                checksum_type, checksum = ret
                params.append('checksum_type=%s' % checksum_type)
                params.append('checksum=%s' % checksum)

        print >>fh, ' | '.join(params)
        
