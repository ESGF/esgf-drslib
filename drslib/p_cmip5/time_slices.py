# BSD Licence
# Copyright (c) 2011, Science & Technology Facilities Council (STFC)
# All rights reserved.
#
# See the LICENSE file in the source distribution of this software for
# the full license text.


import logging
log = logging.getLogger(__name__)

class request_time_slice:

  def __init__(self,parent):
    self.parent=parent
    self.warning = ''

  def in_requested_time(self,start,end):
    self.is_in_requested_time = False
    ssp = self.parent.request_spec

    if ssp[0] in ['list','listrel']:
        if ssp[0] == 'listrel':
          offset = self.get_offset()
          if self.offset_status == -1:
            log.warning('failed to get offset [listrel]')
            return False
        else:
          offset = 0
        for s in ssp[1:]:
          if s[0] == 'year':
            if start-offset == s[1]:
              self.is_in_requested_time = True
              return True
          elif s[0] == 'slice':
            if start-offset <= s[2] and end-offset >= s[1]:
              self.is_in_requested_time = True
              return True

        self.requested_time_end = ssp[-1][-1]
        self.requested_time_start = ssp[1][1]
        self.is_in_requested_time = False
        return True

    elif ssp[0] == 'corres':
      ##  offset = self.get_offset()
        ##if self.offset_status == -1:
        log.warning('not ready for this yet [corres] -- need start time info %s %s ' % (tli, self.parent.request_col))
        return False

    return True

  def load_config(self):
    assert self.parent.config_exists, 'load_config: need a valid configuration file at this point'
    if not self.parent.config_loaded:
        import ConfigParser
        self.cp = ConfigParser.SafeConfigParser()
        self.cp.read( self.parent.config )
        self.parent.config_loaded = True

  def get_offset(self):
    self.load_config()
    self.offset_status = -1
    if not self.parent.model in self.cp.sections():
      self.warning += 'model [%s] not found in configuration file sections: %s, defaulting to 0 offset;;' % (self.parent.model,str(self.cp.sections()) )
      self.offset = 0
      return self.offset
    else:
      opts = self.cp.options( self.parent.model )
      if self.parent.expt == 'piControl':
        if self.parent.table == '3hr':
          if 'year_piControl_spawn_to_1pctCO2' not in opts:
            self.warning += 'start and spawn year info for 1pctCO2 not in configuration file, defaulting to 0 offset'
            self.offset= 0
            self.offset_status = 0
            return self.offset
          else:
            self.offset_status = 1
            self.offset= self.cp.get( self.parent.model, 'year_piControl_spawn_to_1pctCO2' )
            return self.offset
        else:
          if 'year_piControl_spawn_to_historical' not in opts or 'year_start_historical' not in opts:
            self.warning += 'start and spawn year info for historical not in configuration file, please amend configuration file'
            return self.offset
          else:
            self.offset_status = 1
            self.offset= self.cp.get( self.parent.model, 'year_piControl_spawn_to_historical' ) - self.cp.get( self.parent.model, 'year_stat_historical' )
            return self.offset
