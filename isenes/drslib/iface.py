# BSD Licence
# Copyright (c) 2010, Science & Technology Facilities Council (STFC)
# All rights reserved.
#
# See the LICENSE file in the source distribution of this software for
# the full license text.

"""
Interfaces

"""

class TranslationError(Exception):
    pass

class IDRS(object):
    """
    Represents a DRS entry.  This class maintains consistency between the
    path and filename portion of the DRS.

    @property activity: string
    @property product: string
    @property institute: string
    @property model: string
    @property experiment: string
    @property frequency: string
    @property realm: string
    @property variable: string
    @property table: string of None
    @property ensemble: (r, i, p)
    @property version: integer
    @property subset: (N1, N2, clim) where N1 and N2 are (y, m, d, h) 
        and clim is boolean

    """
    def is_complete(self):
        """Returns boolean to indicate if all components are specified.
        """
        raise NotImplementedError

class ITranslatorContext(object):
    """
    Represents a DRS URL or path being translated

    @ivar path_parts: A list of directories following the DRS prefix
    @ivar file_parts: A list of '_'-separated parts of the filename
    @ivar drs: The DRS of interest
    @ivar table_store: The mip tables being used

    """

    def set_drs_component(self, drs_component, value):
        """
        Set a DRS component checking that the value doesn't conflict with any current value.

        """
        raise NotImplementedError

    def to_string(self):
        """Returns the DRS string.
        """
        raise NotImplementedError


class IComponentTranslator(object):
    """
    Each component is translated by a separate IComponentTranslator object.

    """

    def filename_to_drs(self, context):
        """
        Translate the relevant component of the filename to a drs component.

        @raises TranslationError: if the filename is invalid
        @returns: context

        """
        raise NotImplementedError

    def path_to_drs(self, context):
        """
        Translate the relevant component of the DRS path to a drs component.

        @raises TranslationError: if the path is invalid
        @returns: context

        """
        raise NotImplementedError


    def drs_to_filepath(self, context):
        """
        Sets context.path_parts and context.file_parts for this component.

        @returns: context

        """
        raise NotImplementedError

class ITranslator(object):
    """

    @property prefix: All paths are interpreted as relative to this prefix.
        Generated paths have this prefix added.
    @property translators: A list of translators called in order to handle translation
    @property table_store: A IMIPTableStore instance containing all MIP tables being used.

    """

    def update_drs(self, drs):
        raise NotImplementedError

    def filename_to_drs(self, filename):
        raise NotImplementedError

    def path_to_drs(self, path):
        raise NotImplementedError

    def drs_to_path(self, drs):
        raise NotImplementedError

    def init_drs(self):
        """
        Returns an empty DRS instance initialised for this translator.

        """
        raise NotImplementedError


class IMIPTable(object):
    """
    Hold information from a MIP table.  

    Initially this is used to add MIP table names to DRS filenames.
    Future extensions could read MIP tables and record extra information.
    
    @property name: The name of the MIP table as used in DRS filenames.
    @property variables: A list of variables in this table.
    @property experiments: A list of valid experiment ids for this table.

    """

    def get_variable_attr(self, variable, attr):
        """
        Retrieve an attribute of variable.

        If the attributes isn't in the variable entry the global
        value is returned

        """
        raise NotImplementedError


class IMIPTableStore(object):
    """
    Holds a collection of mip tables.

    @property tables: A mapping of table names to IMIPTable instances

    """

    def add_table(self, filename):
        """
        Read filename as a MIP table and add it to the store.
        
        @return: The added MIPTable instance.

        """
        raise NotImplementedError

    def get_variable_attr(self, table, variable, attr):
        """
        Return the value of a variable's attribute in a given table.

        """
        raise NotImplementedError

    def get_variable_attr_mv(self, table, variable, attr):
        """
        Return the list of values value of a variable's attribute in a 
        given table.

        """
        raise NotImplementedError


    def get_variable_tables(self, variable, **attribute_constraints):
        """
        Return the tables in which a variable has the specified attributes

        """
        raise NotImplementedError

