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

CHECKSUM_BLOCKSIZE = 2**20

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
        


def calc_md5(path):
    """
    Caluclate the md5 of a file by reading it.

    This function is suitable for use as the checksum_func callout by adding this to metaconfig:

    [DEFAULT]
    checksum_func = drslib.mapfile:calc_md5

    """
    import hashlib

    md5 = hashlib.md5()
    fh = open(path, 'rb')
    while True:
        data = fh.read(CHECKSUM_BLOCKSIZE)
        if not data:
            break
        md5.update(data)
    fh.close()

    return 'MD5', md5.hexdigest()
