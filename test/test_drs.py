"""
Specific tests for DRS object.

This module has been started as part of the refactoring to create drslib.drs.BaseDRS.

"""

from drslib.drs import BaseDRS

class TrivialDRS(BaseDRS):
    DRS_ATTRS = ['foo', 'bar', 'baz']
    PUBLISH_LEVEL = 'bar'
    OPTIONAL_ATTRS = []

    @classmethod
    def _encode_component(self, component, value):
        if component == 'version':
            return 'v%s' % value
        return str(value)

    @classmethod
    def _decode_component(klass, component, value):
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
    assert drs.to_dataset_id(with_version=True) == 'a.b.v12'

def test_5():
    drs = TrivialDRS(foo='a', bar='b', baz='c', version=12)    
    assert repr(drs) == '<DRS a.b.v12>'
    
def test_6():
    # Test drs update
    drs1 = TrivialDRS(foo='a')
    drs2 = TrivialDRS(bar='b')

    drs1.update(drs2)

    assert drs1.foo == 'a'
    assert drs1.bar == 'b'

