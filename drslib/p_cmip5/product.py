
import shelve, os
import glob, string

import logging
log = logging.getLogger(__name__)

class ddsort:
  def __init__(self,ee,k):
    self.k = k
    self.ee = ee

  def cmp(self,x,y):
    return cmp( self.ee[x][self.k], self.ee[y][self.k] )


class cmip5_product:

  def __init__(self,mip_table_shelve='sh/standard_output_mip', \
                    template='sh/template',\
                    stdo='sh/standard_output',\
                    config='ini/ukmo_sample.ini'):
    self.mip_sh = shelve.open( mip_table_shelve )
    self.tmpl = shelve.open( template )
    self.stdo = shelve.open( stdo )
    self.tmpl_keys = self.tmpl.keys()
    self.tmpl_keys.sort( ddsort(self.tmpl,0).cmp )
    self.pos_in_table = 999
    self.config = config
    self.config_exists = os.path.isfile( config )
    self.config_loaded = False
    self.have_slicer = False

  def scan_atomic_dataset(self,dir):
    if dir[-1] != '/':
      dir += '/'
    fl = map( lambda x: string.split(x, '/')[-1], glob.glob( dir + '*.nc' ) )
    fl.sort()
    kk = -1
    time_periods = []
    for f in fl:
      bits = string.split( f[:-3], '_' )
      if len(bits) == 5:
        has_time = False
      elif len(bits) == 6:
        has_time = True
        tbits = string.split( bits[5], '-' )
        if len(tbits) == 3:
          if tbits[2] != 'clim':
            self.status = 'bad temporal subset: %s in %s' % (f,dir)
            return False
        startyear = int(tbits[0][0:4])
        if len(tbits) > 1:
          endyear = int(tbits[1][0:4])
        else:
          endyear = startyear
      else:
            self.status = 'filename does not match DRS: %s in %s' % (f,dir)
            return False

      if not has_time and len(fl) > 1:
        self.status = 'error: multiple files in atomic dataset with no temporal subset: %s ' % dir
        return False
      else:
        time_periods.append( (startyear, endyear) )

      kk +=1
      if kk == 0:
        var, mip, model, expt, ens = tuple( bits[0:5] )
        base = string.join( bits[0:5], '_' )
      elif string.join(bits[0:5],'_') != base:
          self.status = 'error: inconsistent files in %s' % dir
          log.info(base)
          log.info(string.join(bits[0:5],'_'))
          return False

    self.drs = (var, mip, model, expt, ens)
    self.has_time = has_time
    self.time_periods = time_periods
    self.ads_time_period = ( time_periods[0][0], time_periods[-1][1] )
    self.dir = dir
    self.files = fl
    return True
        
  def check_var(self):
    kk = 0
    for r in self.mip_sh[self.table]:
      kk+=1
      if r[5] == self.var:
        self.vline = r[:]
        self.pos_in_table = kk
        return True

##cross links::  [(u'include Oyr 3D tracers', u'Omon'), (u'include Amon 2D', u'cf3hr'), (u'include Amon 2D', u'cfSites')]

    if self.table in ['Omon','cf3hr','cfsites']:
      if self.table == 'Omon':
        rlist = self.mip_sh['Oyr'][0:43]
      else:
        rlist = self.mip_sh['Amon'][0:51]

      for r in rlist:
        if r[5] == self.var:
          self.vline = r[:]
          self.pos_in_table = 99
          return True

    return False

  def find_rei( self,expt ):
    if expt in self.tmpl_keys:
      self.rei = self.tmpl[expt]
      return True
    else:
      return False

  def priority(self):
    return self.vline[0]
    
  def dimensions(self):
    return self.vline[16]

  def get_request_spec(self):
    tlist = self.stdo[self.request_col]
    if self.rei[0]-2 in tlist.keys():
##
## deal with special case for rcps -- extended version has different spec
##
      if self.expt in ['rcp45','rcp25','rcp86']:
        tli = self.rei[0]-6
      else:
        tli = self.rei[0]-2
      ssp = tlist[tli]
      self.request_spec = ssp

    else:
      self.request_spec = ('none',)

  def in_requested_time(self,start,end):
    if not self.have_slicer:
      import time_slices
      self.tsl = time_slices.request_time_slice(self)
      self.have_slicer = True
    return self.tsl.in_requested_time( start, end )
        
####################
####################
  def find_product(self,var,table,expt,model,path,startyear=None,endyear=None):
    if table not in self.mip_sh.keys():
      self.status = 'bad mip table'
      return False

## offset_status has 3 levels: -1: not set, 0: set by default, 1: set using info from configuration file.
    self.offset_status = -1
    self.offset = None
    self.table = table
    self.var = var
    self.expt = expt
    self.model = model
    if not self.check_var():
      res = 'output2'
      reason = 'variable not requested'

    with_dates = startyear != None and endyear != None

    reason = 'default'
    res = 'output1'
    if table == 'Oyr': 
       if self.priority() == 3:
         reason = 'Table %s, priority 3' % table
         res = 'output2' 
    elif table == 'Omon':
       dims = self.dimensions()
       if 'olevel' in dims and not 'basin' in dims and self.priority() >= 2:
         reason = 'Table %s, dims include olevel and not basin, priority >2' % table
         res = 'output2'
    elif table == 'aero':
       if 'alev1' in self.dimensions():
          self.request_col = 'M'
          if self.find_rei(expt ):
            self.get_request_spec()
            if self.request_spec[0] in ['none','all']:
               self.reason = 'Request covers %s of this atomic dataset' % self.request_spec[0]
               self.product = 'output1'
               return True

            if not with_dates:
              self.status = 'start and end year required'
              return False
            if self.in_requested_time(  startyear, endyear):
              if not self.tsl.is_in_requested_time:
               reason = 'Table %s, alevel in dimensions, rei %s, period not requested' % (table, self.rei)
               res = 'output2'
            else:
              self.status =  'Could not identify requested time'
              return False

    elif table == 'day':
       if self.pos_in_table > 10:
         if self.find_rei(expt):
           self.request_col = 'N'
           self.get_request_spec()
           if self.request_spec[0] in ['none','all']:
               self.reason = 'Request covers %s of this atomic dataset' % self.request_spec[0]
               self.product = 'output1'
               return True

           if not with_dates:
              self.status = 'start and end year required'
              return False
           if self.in_requested_time(  startyear, endyear):
             if not self.tsl.is_in_requested_time:
               reason = 'Table %s, var not in 1st 10, rei %s, period not requested' % (table, self.rei)
               res = 'output2'
           else:
              self.status =  'Could not identify requested time'
              return False

    elif table in ['6hrPlev','3hr']:
       if self.find_rei(expt):
         self.request_col = {'3hr':'R', '6hrPlev':'Q'}[table]
         self.get_request_spec()
         if self.request_spec[0] in ['none','all']:
               self.reason = 'Request covers %s of this atomic dataset' % self.request_spec[0]
               self.product = 'output1'
               return True

         if not with_dates:
              self.status = 'start and end year required'
              return False
         if expt in ['piControl']:
            self.scan_atomic_dataset(path)
            if self.ads_time_period[1] - self.ads_time_period[0] < 31:
              self.reason = 'Table %s, expt %s, less than 30 years submitted' % (table,expt)
              self.product = 'output1'
              return True
            log.info('[x2] %s' % (self.ads_time_period[1] - self.ads_time_period[0]))

         if not self.in_requested_time(  startyear, endyear):
              self.status = 'Could not identify requested time'
              return False
         else:
           if not self.tsl.is_in_requested_time:
             if expt in ['piControl']:
                if self.tsl.requested_time_end - self.ads_time_period[0] < 31 and startyear - self.ads_time_period[0] < 31:
                   self.reason = 'Table %s, expt %s, full 30 requested years not submitted -- taking first 30 years submitted'
                   self.product = 'output1'
                   return True
                elif self.ads_time_period[1] - self.tsl.requested_time_start < 31 and self.ads_time_period[1] - startyear < 31:
                   self.reason = 'Table %s, expt %s, full 30 requested years not submitted -- taking last 30 years submitted'
                   self.product = 'output1'
                   return True
                else:
                  log.info('atomic dataset range: %s' % (self.ads_time_period, ))
                  log.info('request: %s' % self.tsl.requested_time_start,self.tsl.requested_time_end)

             reason = '[x1] Table %s, rei %s, period not requested' % (table, self.rei)
             res = 'output2'
       else:
         self.warning += 'Could not identify experiment: %s' % expt

    elif table == 'cfMon':
      self.status = 'Not ready to deal with cfMon data yet'
      return False
    
    self.product = res
    self.reason = reason
    return True

