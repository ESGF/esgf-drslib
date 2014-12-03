"""
Implement CORDEX specific DRS scheme.

"""

import re
import os

from drslib.drs import BaseDRS, DRSFileSystem, _ensemble_to_rip, _rip_to_ensemble
from drslib import config
from drslib.exceptions import TranslationError




class SpecsDRS(BaseDRS):
    DRS_ATTRS = [
        'activity', 'product', 'institute', 'model', 'experiment', 'start_date', 
        'frequency', 'realm', 'table', 'variable', 'ensemble', 'subset',
        'extended',
        ]
    PUBLISH_LEVEL = 'ensemble'
    OPTIONAL_ATTRS = ['extended']

    @classmethod
    def _encode_component(klass, component, value):
        from drslib.translate import _from_date

        if value is None:
            return '%'
        elif component == 'realm':
            return value.split(' ')[0]
        elif component == 'ensemble':
            return _ensemble_to_rip(value)
        elif component == 'version':
            return 'v%d' % value
        elif component == 'subset':
            #!TODO: remove duplication in drs.py
            N1, N2, clim = value
            if clim:
                val = '%s-%s-clim' % (_from_date(N1), _from_date(N2))
            else:
                val = '%s-%s' % (_from_date(N1), _from_date(N2))
        elif component == 'start_date':
            return 'S%s' % _from_date(value)
        else:
            return value


    @classmethod
    def _decode_component(cls, component, value):
        from drslib.translate import _to_date
        
        if value == '%':
            ret = None
        elif component == 'ensemble':
            if value == (None, None, None):
                ret = None
            else:
                ret = _rip_to_ensemble(value)
        elif component == 'version':
            if value[0] == 'v':
                ret = int(value[1:])
            else:
                ret = int(value)
        elif component == 'subset':
            N1 = N2 = None
            parts = value.split('-')
            if len(parts) > 3:
                raise ValueError('cannot parse extended component %s' % repr(value))

            N1, N2 = _to_date(parts[0]), _to_date(parts[1])
            if len(parts) == 3:
                clim = parts[2]
                if clim != 'clim':
                    raise ValueError('unsupported extended component %s' % repr(value))
            else:
                clim = None
            ret = (N1, N2, clim)
        elif component == 'start_date':
            mo = re.match(r'S?(\d{8})', value)
            if not mo:
                raise ValueError('Unrecognised start_date %s' % repr(value))

            ret = _to_date(mo.group(1))

        else:
            ret = value
                
        return ret


class SpecsFileSystem(DRSFileSystem):
    drs_cls = SpecsDRS

    def filename_to_drs(self, filename):
        """
        Return a DRS instance deduced from a filename.

        """
        # var_table_model_exptfamily_startdate_ensemble_subset
        # E.g. pr_day_MPI-ESM-LR_decadal_series1_S19610101_r1i1p1_19610101-19701231.nc 

        if self._is_ignored(filename):
            raise TranslationError()

        m = re.match(r'(?P<variable>.*?)_(?P<table>.*?)_(?P<model>.*?)_(?P<experiment>.*?)_(?P<start_date>S\d{8}?)_(?P<ensemble>.*?)(?:_(?P<subset>.*?))?\.nc', filename)
        
        if not m:
            raise TranslationError()

        comp_dict = m.groupdict()

        drs = self.drs_cls(activity='specs')
        for component in ['variable', 'table', 'model', 'experiment', 'start_date',
                          'ensemble', 'subset']:
            comp_val = comp_dict[component]
            if comp_val is not None:
                drs[component] = drs._decode_component(component, comp_val)
            else:
                drs[component] = None

        return drs


    def filepath_to_drs(self, filepath):
        """
        Return a DRS instance deduced from a full path.

        """
        # Split off the variable and version directory then pass
        # the results to other functions
        parts = filepath.split('/')

        version_str, filename = parts[-2:]

        drs = self.filename_to_drs(filename)
        drs.version = drs._decode_component('version', version_str)
        drs.update(self.publication_path_to_drs('/'.join(parts[:-2])))

        return drs

    def drs_to_storage(self, drs):
        return '%s/d%d' % (self.VERSIONING_FILES_DIR, drs.version)

    def storage_to_drs(self, subpath):
        files_dir, subpath2 = subpath.split('/')
        assert subpath2[0] == 'd'

        version = int(subpath2[1:])
        return self.drs_cls(version=version)

    def drs_to_ingest_cache_path(self, drs):
        return os.path.abspath(self.drs_to_publication_path(drs))

    # drs_to_realpath(self, drs): defined in superclass

    def drs_to_linkpath(self, drs, version=None):
        if version is None:
            version = drs.version

        pubpath = self.drs_to_publication_path(drs)
        return os.path.abspath(os.path.join(pubpath, 'v%d' % version))

