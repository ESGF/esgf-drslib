"""
Implement CORDEX specific DRS scheme.

"""

import re
import os

from drslib.drs import BaseDRS, DRSFileSystem, _ensemble_to_rip, _rip_to_ensemble
from drslib import config
from drslib.exceptions import TranslationError



class CordexDRS(BaseDRS):
    DRS_ATTRS = [
        'activity', 'product', 'domain', 'institute', 'gcm_model', 'experiment', 
        'ensemble', 'rcm_model', 'rcm_version', 'frequency', 'variable', 'subset', 
        'extended',
        ]
    PUBLISH_LEVEL = 'variable'
    OPTIONAL_ATTRS = ['extended']
    DRS_JSON_MAP = {
        'driving_model': 'gcm_model',
        'model_version': 'rcm_version',
        'model': 'rcm_model',
        }

    @classmethod
    def _encode_component(klass, component, value):
        from drslib.translate import _from_date

        if value is None:
            return '%'
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
        else:
            ret = value
                
        return ret


class CordexFileSystem(DRSFileSystem):
    drs_cls = CordexDRS

    def filename_to_drs(self, filename):
        """
        Return a DRS instance deduced from a filename.

        """
        
        if self._is_ignored(filename):
            raise TranslationError()

        # VariableName_Domain_GCMModelName_CMIP5ExperimentName_CMIP5EnsembleMember_RCMModelName_RCMVersionID_Frequency_StartTime-EndTime.nc 
        m = re.match(r'(?P<variable>.*?)_(?P<domain>.*?)_(?P<gcm_model>.*?)_(?P<experiment>.*?)_(?P<ensemble>.*?)_(?P<institute>.*?)-(?P<rcm_model>.*?)_(?P<rcm_version>.*?)_(?P<frequency>.*?)(?:_(?P<subset>.*?))?\.nc', filename)
        if not m:
            raise TranslationError()

        comp_dict = m.groupdict()

        drs = self.drs_cls(activity='cordex')
        for component in ['variable', 'domain', 'gcm_model', 'experiment',
                          'ensemble', 'institute', 'rcm_model', 'rcm_version', 'frequency', 
                          'subset']:
            comp_val = comp_dict[component]
            
            if component == 'rcm_model' and comp_val is not None:
                drs[component] = "%s-%s" % (comp_dict['institute'], comp_dict['rcm_model'])
            elif comp_val is not None:
                drs[component] = drs._decode_component(component, comp_val)

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

