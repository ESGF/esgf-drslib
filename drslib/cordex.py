"""
Implement CORDEX specific DRS scheme.

"""

from drslib.drs import BaseDRS, DRSFileSystem, _ensemble_to_rip, _rip_to_ensemble
from drslib import config




class CordexDRS(DRS):
    DRS_ATTRS = [
        'activity', 'domain', 'institute', 'gcm_model', 'experiment', 'ensemble', 
        'rcm_model', 'rcm_version', 'frequency', 'variable', 'subset', 'extended',
        ]
    PUBLISH_LEVEL = 'variable'
    OPTIONAL_ATTRS = ['extended']

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
        
        if val == '%':
            ret = None
        elif attr is 'ensemble':
            if val == (None, None, None):
                ret = None
            else:
                ret = _rip_to_ensemble(val)
        elif attr is 'version':
            if val[0] == 'v':
                ret = int(val[1:])
            else:
                ret = int(val)
        elif attr is 'subset':
            parts = val.split('-')
            if len(parts) > 3:
                raise ValueError('cannot parse extended component %s' % repr(val))
                N1, N2 = _to_date(parts[0]), _to_date(parts[1])
            if len(parts) == 3:
                clim = parts[2]
                if clim != 'clim':
                    raise ValueError('unsupported extended component %s' % repr(val))
            else:
                clim = None
            val = (N1, N2, clim)
        else:
            ret = val
                
        return ret


class CordexFileSystem(DRSFileSystem):
    drs_cls = CordexDRS

    def filename_to_drs(self, filename):
        """
        Return a DRS instance deduced from a filename.

        """
        # VariableName_Domain_GCMModelName_CMIP5ExperimentName_CMIP5EnsembleMember_RCMModelName_RCMVersionID_Frequency_StartTime-EndTime.nc 
        m = re.match(r'(?P<variable>.*)_(?P<domain>.*)_(?P<gcm_model>.*)_(?P<experiment>.*)_(?P<ensemble>.*)_(?P<rcm_model>.*)_(?P<rcm_version>.*)_(?P<frequency>.*)_(?P<subset>.*)\.nc', filename)
        
        assert m
        comp_dict = m.groupdict()

        drs = self.drs_cls()
        for component in ['variable', 'domain', 'gcm_model', 'experiment',
                          'ensemble', 'rcm_model', 'rcm_version', 'frequency', 
                          'subset']:
            drs[component] = drs._encode_component(component, comp_dict[component])

        return drs


    def filepath_to_drs(self, filepath):
        """
        Return a DRS instance deduced from a full path.

        """
        raise NotImplementedError


    def drs_to_storage(self, drs):
        return 'd%d' % drs.version

    def storage_to_drs(self, subpath):
        assert subpath[0] == 'd'

        version = int(subpath[1:])
        return self.drs_cls(version=version)


