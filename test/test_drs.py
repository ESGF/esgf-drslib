"""
Specific tests for DRS object.

This module has been started as part of the refactoring to create drslib.drs.BaseDRS.

"""

from drslib.drs import DRS, BaseDRS

class TrivialDRS(BaseDRS):
    DRS_ATTRS = ['foo', 'bar', 'baz']
    PUBLISH_LEVEL = 'bar'

    def _encode_component(self, component):
        if component == 'version':
            return 'v%s' % self.version
        return str(self[component])
    def _decode_component(self, component, value):
        return value

def test_1():
    drs = TrivialDRS(foo='a', bar='b')
    assert drs.is_complete() == False

def test_2():
    drs = TrivialDRS(foo='a', bar='b')
    assert drs.is_publish_level() == True

def test_3():
    drs = TrivialDRS(foo='a', bar='b', baz='c', version=12)
    assert drs.to_dataset_id() == 'a.b'

def test_4():
    drs = TrivialDRS(foo='a', bar='b', baz='c', version=12)    
    assert drs.to_dataset_id(with_version=True) == 'foo.bar.v12'

def test_4():
    drs = TrivialDRS(foo='a', bar='b', baz='c', version=12)    
    assert repr(drs) == '<DRS a.b.v12>'
    
