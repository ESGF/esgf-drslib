#!/usr/bin/python
##
## Code to identify the CMIP5 DRS "product" element based on other DRS elements and selection tables.
##
## Author: Martin Juckes (martin.juckes@stfc.ac.uk)
##
## New in this version:
##   1. cmip5_product.status no longer used
##   2. additional capability to scan previously published data
##   3. option to raise a ProductScopeexception instead of providing "False" return when arguments are inconsistent with selection tables
##   4. cmip5_product.rc has a return code on exit -- each return code coming from a unique line of code.
##   
version = 0.7
version_date = '20101001'


import logging
log = logging.getLogger(__name__)


class ProductScope(Exception):
  def __init__(self,value):
     self.value = value
  def __str__(self):
     return repr(self.value)

class ddsort:
  def __init__(self,ee,k):
    self.k = k
    self.ee = ee

  def cmp(self,x,y):
    return cmp( self.ee[x][self.k], self.ee[y][self.k] )

def arg_string( var,table,expt,model,path,path_output1,path_output2):
   return '%s_%s_%s_%s__%s_%s_%s' % (var,table,expt,model,path,path_output1,path_output2)

def index_last_n_years( n, year_slices ):
    nn = len(year_slices) -1
    ny = 0
    for k in range( len(year_slices) ):
      ny += year_slices[nn][1] - year_slices[nn][0] + 1
      if ny >= n:
        return nn
      nn += -1

    return 0
      
def index_first_n_years( n, year_slices ):
    ny = 0
    for k in range( len(year_slices) ):
      ny += year_slices[k][1] - year_slices[k][0] + 1
      if ny >= n:
        return k

    return len(year_slices) -1

def index_in_list( yl, year_slices ):
    ixl = []
    ny = 0
    for k in range( len(year_slices) ):
      if year_slices[k][0] in yl or year_slices[k][1] in yl:
        ny += year_slices[k][1] - year_slices[k][0] + 1
        ixl.append(k)

    return (ixl,ny)
      
      
import shelve, os

class cmip5_product:

  def __init__(self,mip_table_shelve='sh/standard_output_mip', \
                    template='sh/template',\
                    stdo='sh/standard_output',\
                    config='ini/sample_1.ini', \
                    override_product_change_warning=False,\
                    policy_opt1='all_rel',not_ok_excpt=False):
    self.mip_sh = shelve.open( mip_table_shelve )
    self.tmpl = shelve.open( template )
    self.stdo = shelve.open( stdo )
    self.tmpl_keys = self.tmpl.keys()
    self.tmpl_keys.sort( ddsort(self.tmpl,0).cmp )
    self.pos_in_table = 999
    self.config = config
    self.config_exists = os.path.isfile( config )
    self.config_loaded = False
    self.policy_opt1=policy_opt1
    self.last_result = ['none','none']
    self.product = 'none'
    self.ads_product = 'none'
    self.override_product_change_warning = override_product_change_warning
    self.not_ok_excpt = not_ok_excpt
    self.ScopeException = ProductScope


  def ok(self, product, reason, rc=None):
    self.product = product
    self.reason = reason
    self.rc = rc
    return True

  def not_ok(self, status,rc):
    self.reason = status
    self.rc = rc
    self.product = 'Failed'
    if self.not_ok_excpt:
      raise self.ScopeException( '%s:: %s' % (rc,status) )
    return False

  def scan_atomic_dataset(self,dir):
    import glob, string
    if dir[-1] != '/':
      dir += '/'
    fl = map( lambda x: string.split(x, '/')[-1], glob.glob( dir + '*.nc' ) )
    if len(fl) == 0:
      return False

    fl.sort()
    if self.path_output1 != None or self.path_output2 != None:
      if self.path_output1 != None:
        fl1b = glob.glob( self.path_output1 + '/*.nc' )
        fl1 = map( lambda x: string.split(x, '/')[-1], glob.glob( self.path_output1 + '/*.nc' ) )
      else:
        fl1 = []

      if self.path_output2 != None:
        fl2 = map( lambda x: string.split(x, '/')[-1], glob.glob( self.path_output2 + '/*.nc' ) )
      else:
        fl2 = []

      if len(fl1) == 0 and len(fl2) == 0:
        log.info( 'output1 and output2 directories are both empty: %s, %s' % (self.path_output1,self.path_output2) )
        self.new_ads = True

      fld = {}
      for f in fl:
        fld[f] = 'N'

      for f in fl1:
        assert f not in fl2, 'Files should not be in output1 and output2: %s, %s' % (self.path_output1,self.path_output2)
        if fld.has_key(f):
          fld[f] = 'R1'
        else:
          fld[f] = 'O1'
      keys = fld.keys()

      for f in fl2:
        if fld.has_key(f):
          fld[f] = 'R2'
        else:
          fld[f] = 'O2'

      fli = fl[:]
      fl = fld.keys()
      fl.sort()
      self.file_dict = fld
     
    kk = -1
    time_periods = []
    year_slices = []
    nyears = 0
    start_years = []
    for f in fl:
      bits = string.split( f[:-3], '_' )
      if len(bits) == 5:
        has_time = False
        nyears = -1
      elif len(bits) == 6:
        has_time = True
        assert bits[5][0] != '-', 'Negative date -- not supported as this version: %s' % bits[5]
        assert string.find( bits[5], '--' ) == -1, 'Negative date -- not supported as this version: %s, %s' % bits[5]
        tbits = string.split( bits[5], '-' )
        if len(tbits) == 3:
          if tbits[2] != 'clim':
            return self.not_ok( 'bad temporal subset: %s in %s' % (f,dir), 'ERR010' )

        assert len( tbits[0] ) in [4,6] or ( len(tbits[0])==6 and tbits[0][-2:] in ['01','02','03','04','05','06','07','08','09','10','11','12'] ), \
            'Date not of form yyyy[mm[dd]]: not supported: %s' % tbits[0]
        startyear = int(tbits[0][0:4])
        if len(tbits) > 1:
          endyear = int(tbits[1][0:4])
        else:
          endyear = startyear
        start_years.append( startyear )
      else:
          return self.not_ok( 'filename does not match DRS: %s in %s' % (f,dir), 'ERR011' )

      if has_time:
        time_periods.append( (startyear, endyear) )
        if len( year_slices ) == 0 or (startyear != year_slices[-1][0] or endyear != year_slices[-1][1]):
          year_slices.append( (startyear, endyear) )
          nyears += endyear - startyear + 1
      elif len(fl) > 1:
          return self.not_ok( 'error: multiple files in atomic dataset with no temporal subset: %s ' % dir, 'ERR012' )

      kk +=1
      if kk == 0:
        var, mip, model, expt, ens = tuple( bits[0:5] )
        base = string.join( bits[0:5], '_' )
      elif string.join(bits[0:5],'_') != base:
          log.info( base )
          log.info( string.join(bits[0:5],'_') )
          return self.not_ok( 'error: inconsistent files in %s' % dir, 'ERR013' )

    self.nyears_submitted = nyears
    self.drs = (var, mip, model, expt, ens)
    self.has_time = has_time
    self.time_periods = time_periods
    self.year_slices = year_slices
    if len( time_periods ) > 0:
      self.ads_time_period = ( time_periods[0][0], time_periods[-1][1] )
    else:
      self.ads_time_period = ( -9999, -9999 )
    self.dir = dir
    self.files = fl
    self.file_start_years = start_years
    assert len(fl) == len(start_years) or len(fl) == 1, 'Apparent error in logic scanning atomic dataset'
    return True
        
  def check_var(self):
    kk = 0
    if self.table == 'cfMon':
## identify start and end of each section, and record in self.table_segment
## 
      segstarts = ['rlu','rsut4co2','rlu4co2','cltisccp']
      segix = []
      kseg = 0
      for r in self.mip_sh[self.table]:
        kk+=1
        if r[5] in segstarts:
          segix.append(kk)
          kseg += 1
        if r[5] == self.var:
          self.vline = r[:]
          self.pos_in_table = kk
          self.table_segment = kseg
          return True
##
##
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
    if expt in ['piControl','historical','amip']:
      ##self.get_slicer()

      if not self.config_loaded:
        self.load_config()

      if self.model not in self.cp.sections():
        categ = 'centennial'
      else:
        opts = self.cp.options( self.model )
        if 'category' not in opts:
          categ = 'centennial'
        categ = self.cp.get( self.model, 'category' )

      if categ == 'centennial':
        k1 = { 'piControl':'piControl+', 'historical':'historical+', 'amip':'amip+' }[expt]
      else:
        k1 = expt

    else:
      k1 = expt

    if k1 in self.tmpl_keys:
      self.rei = self.tmpl[k1]
      return True
    else:
      return False

  def priority(self):
    return self.vline[0]
    
  def dimensions(self):
    return self.vline[16]

  def get_cfmip_request_spec(self):
    keys = self.stdo['cfmip'].keys()
    log.debug( 'get_cfmip_request_spec: %s' % self.rei[1] )

    if self.rei[1] not in keys:
      log.info( '%s not in keys:: %s' % (self.rei[1],str(keys)) )
      return self.ok( 'output1', 'Experiment %s not requested for cfmip' % self.rei[1], 'OK011' )

    ll = self.stdo['cfmip'][self.rei[1]]
    slice_list = ll[self.table_segment-1]

    if len(slice_list) == 0:
      self.request_spec = ('none',)
      self.nyears_requested = -1
    else:
      if slice_list[0][0] < 500:
         self.request_spec = ('listrel',)
      else:
         self.request_spec = ('list',)
      nyears = 0
      self.requested_years_list = []
      for s in slice_list:
         nyears += s[1] - s[0] + 1
         for y in range( s[0], s[1]+1):
              self.requested_years_list.append( y )
      self.nyears_requested = nyears
    return False
        
  def get_request_spec(self):
    tlist = self.stdo[self.request_col]
    self.requested_years_list = []
    if self.rei[0]-2 in tlist.keys():
##
      tli = self.rei[0]-2
      ssp = tlist[tli]
      self.request_spec = ssp

      assert ssp[0] in ['list','listrel','corres','none','all'], 'unexpected ssp[0]:: %s [%s,%s]' % (str( ssp[0] ),self.expt,self.table)

      if ssp[0] in ['list','listrel']:
        nyears = 0
        for s in ssp[1:]:
          assert s[0] in ['year','slice'], 'Unexpected time specification %s' % str(s[0])
          if s[0] == 'year':
            nyears += 1
            self.requested_years_list.append( s[1] )
          elif s[0] == 'slice':
            nyears += s[2] - s[1] + 1
            for y in range( s[1], s[2]+1):
              self.requested_years_list.append( y )

        self.nyears_requested = nyears

    else:
      self.request_spec = ('none',)
      self.nyears_requested = -1

  def load_config(self):
    assert self.config_exists, 'load_config: need a valid configuration file at this point'
    if not self.config_loaded:
        import ConfigParser
        self.cp = ConfigParser.SafeConfigParser()
        self.cp.read( self.config )
        self.config_loaded = True

  def find_product(self,var,table,expt,model,path,startyear=None,endyear=None,verbose=False, \
                  path_output1=None, path_output2=None):

    if self.last_result[0] != arg_string( var,table,expt,model,path,path_output1,path_output2):
      self.find_product_ads(var,table,expt,model,path,verbose=verbose, path_output1=path_output1, path_output2=path_output2)
    self.ads_new = path_output1 == None and path_output2 == None
    
    self.ads_product = self.last_result[1]

    assert self.last_result[1] in ['output1','output2','Failed','split','output1*','output2*','split*'], 'ERR901: Result [%s] not in accepted range' % self.last_result[1]

    if self.ads_product in ['output1','output2','output1*','output2*']:
        return True
    elif self.ads_product == 'Failed':
        return False
    else:
        if startyear in self.output1_start_years:
          self.product = 'output1'
          if self.product_change_warning:
            self.product += '*'
          return True
        elif startyear in self.file_start_years:
          self.product = 'output2'
          if self.product_change_warning:
            self.product += '*'
          return True
        else:
          return self.not_ok( 'startyear %s does not correspond to file in %s' % (startyear,path), 'ERR001' )

###################
  def find_product_ads(self,var,table,expt,model,path,verbose=False, \
                  path_output1=None, path_output2=None):
##
    if self.last_result[0] == arg_string( var,table,expt,model,path,path_output1,path_output2):
      return True
    self.path_output1 = path_output1
    self.path_output2 = path_output2
    self.ads_new = path_output1 == None and path_output2 == None

## look to see if all files in the atomic dataset are treated equally'
    self.rc = 'UNSET'
    if self.find_product_step_one(var,table,expt,model,verbose=verbose):
      self.last_result = ( arg_string( var,table,expt,model,path,path_output1,path_output2), self.product )
      return True

    if self.reason == 'Experiment not identified':
      log.warn( 'Experiment [%s] not identified' % self.expt )
      return self.ok( 'output1', 'Unrequested experiment -- none replicated', 'OK001' )

    if self.reason != 'Need temporal information':
      return False
##
## go into deeper analysis
    self.path = path
    if self.find_product_slice():
      self.last_result = ( arg_string( var,table,expt,model,path,path_output1,path_output2), self.product )
      return True
    else:
      self.last_result = ( arg_string( var,table,expt,model,path,path_output1,path_output2), 'Failed' )
      return False

####################
####################
  def find_product_step_one(self,var,table,expt,model,verbose=False):
    if table not in self.mip_sh.keys():
      return self.not_ok( 'Bad mip table:: %s ' % table, 'ERR008' )

## offset_status has 3 levels: -1: not set, 0: set by default, 1: set using info from configuration file.
    self.offset_status = -1
    self.offset = None
    self.table = table
    self.var = var
    self.expt = expt
    self.model = model
    self.verbose = verbose

    if not self.check_var():
      return self.ok( 'output2', 'variable not requested', 'OK002' )
    if verbose and table == 'cfMon':
      log.info( 'find_product_step_one:: %s,  %s' % (var, self.table_segment ) )

    if table == 'Oyr': 
       if self.priority() == 3:
         return self.ok( 'output2', 'Table %s, priority 3' % table, 'OK003' )
       else:
         return self.ok( 'output1', 'Table %s, priority < 3' % table )

    elif table == 'Omon':
       dims = self.dimensions()
       if 'basin' in dims:
         return self.ok( 'output1', 'Table %s, with basin in dimensions' % table, 'OK004.1' )
       elif 'olevel' in dims and self.priority() >= 2:
         return self.ok( 'output2', 'Table %s, 3d, priority >=2' % table, 'OK004.2' )
       else:
         return self.ok( 'output1', 'Table %s, priority %s, dims %s' % (table,self.priority(),str(dims)), 'OK004.3' )
    elif table == 'aero' and 'alev1' not in self.dimensions():
         return self.ok( 'output1', 'Table %s, dims %s' % (table,str(self.dimensions())), 'OK005' )
    elif table == 'day' and self.pos_in_table <= 10:
         return self.ok( 'output1', 'Table %s, in first 10 variables' % table, 'OK006' )

    if verbose:
       log.info( 'need to identify experiment' )

    if not self.find_rei(expt ):
            return self.ok( 'output1','EXPERIMENT NOT IDENTIFIED', 'OK007' )

    if table in ['aero','day','6hrPlev','3hr']:
         self.request_col = {'aero':'M','day':'N', '3hr':'R', '6hrPlev':'Q'}[table]
         self.get_request_spec()
         if self.request_spec[0] in ['none','all']:
             return self.ok( 'output1', 'Request covers %s of this atomic dataset' % self.request_spec[0], 'OK008.1' )

    elif table == 'cfMon':
         if self.get_cfmip_request_spec():
             return True

         if self.request_spec[0] in ['none','all']:
             return self.ok( 'output1', 'Request covers %s of this atomic dataset' % self.request_spec[0], 'OK008.2' )
         
    return self.not_ok( 'Need temporal information', 'ERR004' )
    

  def find_product_slice(self):

    res = 'output1'
    reason = 'default'

    if not self.scan_atomic_dataset(self.path):
       return self.not_ok( 'Could not scan atomic dataset %s' % self.path, 'ERR006' )


    if len(self.files) == 1 and not self.has_time:
       return self.ok( 'output1', 'Singleton file with no time info', 'OK012' )

    if self.verbose:
       log.info( 'find_product_slice: years requested: %s, years submitted: %s' % (self.nyears_requested, self.nyears_submitted) )

    assert self.nyears_requested > 0, 'find_product_slice: Should not reach here with nyears_requested <= 0'
    assert self.nyears_submitted > 0, 'find_product_slice: Should not reach here with nyears_submitted <= 0'

    if self.policy_opt1 == 'all' and self.not_enough_years():
        return self.ok( 'output1',  \
            'years submitted (%s) not greater than 5 + years requested (%s)' % (self.nyears_submitted,self.nyears_requested), 'OK009.1' )

    if self.expt in ['midHolocene','lgm'] and self.table == '6hrPlev':
### take last 35 years
      return self.select_last( 35, 'output1', rc = 'OK200.01' )

    if len(self.expt) > 7 and self.expt[0:7] == 'decadal':
      time_datum = int( self.expt[7:11] )
      if time_datum in [1960, 1980, 2005]:
         requested_years = map( lambda x: x+time_datum, [10,20,30] )
      else:
         requested_years = (time_datum + 10, )

      if self.verbose:
         log.info( 'Experiment %s, time dataum %s' % (self.expt, self.time_datum ) )

      return self.select_year_list( requested_years, 'output1' )

##
## load module to deal with time slices in the variable request
##
    ##self.get_slicer()

    if self.request_spec[0] == 'listrel':
      if self.policy_opt1 == 'all_rel' and self.not_enough_years():
         return self.ok( 'output1',  \
            'years submitted (%s) not greater than 5 + years requested (%s)' % (self.nyears_submitted,self.nyears_requested), 'OK009.2' )

      if not self.config_loaded:
        self.tsl.load_config()

      if (self.expt == 'piControl' and self.table in ['aero','day','6hrPlev'] ) or \
         (self.expt == 'esmControl' and self.table in ['aero','day'] ):

        if self.model not in self.cp.sections():
          return self.not_ok( 'Need to have model in configuration file, to specify start of %s run' % {'piControl':'historical', 'esmPiControl':'esmHistorical'}[self.expt], 'ERR002' )

        if self.expt == 'piControl':
          y_pic2h = int( self.cp.get( self.model, 'year_picontrol_spawn_to_historical' ) )
          y_hist0 = int( self.cp.get( self.model, 'year_historical_start' ) )
          offset = y_pic2h - y_hist0
        else:
          y_ec2eh = int( self.cp.get( self.model, 'year_esmControl_spawn_to_esmHistorical' ) )
          y_ehist0 = int( self.cp.get( self.model, 'year_esmHistorical_start' ) )
          offset = y_ec2h - y_ehist0

        requested_years = map( lambda x: x + offset, self.requested_years_list )
        return self.select_year_list( requested_years, 'output1' )

      elif (self.table == '3hr' and self.expt in ['1pctCo2','abrupt4xco2'] ):
        opts = self.cp.options( self.model )
        if self.expt == '1pctCo2' and 'year_1pctCo2_start' in opts:
           offset = int( self.cp.get( self.model, 'year_1pctCo2_start' ) )
        elif self.expt == 'abrupt4xco2' and 'year_abrupt4xco2_start' in opts:
           offset = int( self.cp.get( self.model, 'year_abrupt4xco2_start' ) )
        else:
           offset = None

        if offset != None:
           if self.expt == '1pctCo2':
              requested_years = map( lambda x: offset + 110 + x, range(30) )
              nrq  = 30
           else:
              requested_years = map( lambda x: offset + x, range(5) ) + \
                              map( lambda x: offset + 120 + x, range(30) )
              nrq = 35
           if self.select_year_list( requested_years, 'output1', force_complete = True ):
              return True

        if self.expt == '1pctCo2':
          return self.select_last( 30, 'output1' )
        else:
          self.select_first( 5, 'output1' )
          return self.select_last( 30, 'output1', append=True )

      elif (self.expt == 'piControl' and self.table == '3hr'):
        opts = self.cp.options( self.model )
        if 'year_1pctCo2_start' in opts:
            offset = int( self.cp.get( self.model, 'year_1pctCo2_start' ) )
            requested_years = map( lambda x: offset + x, self.requested_years_list )
            if self.select_year_list( requested_years, 'output1', force_complete = True ):
                  return True

        return self.select_last( 35, 'output1' )
          

      elif self.table in ['cfMon']:
        if self.rei[1] in ['6.2a', '6.2b', '6.3-E', '6.4a', '6.4b', '6.7a', '6.7b', '6.7c']:
          return self.select_first( self.nyears_requested, 'output1' )
        elif self.rei[1] in ['5.4-l', '5.5-l', '6.1', '6.3']:

          if self.rei[1] in ['6.1', '6.3']:
            opts = self.cp.options( self.model )

## for 6.1, 6.3 -- try to use offsets specified in configuration file
##
          if self.rei[1] == '6.1' and 'year_1pctCo2_start' in opts:
            offset = int( self.cp.get( self.model, 'year_1pctCo2_start' ) )
          elif self.rei[1] ==  '6.3' and 'year_abrupt4xco2_start' in opts:
            offset = int( self.cp.get( self.model, 'year_abrupt4xco2_start' ) )
          else:
            offset == None

          if offset != None:
              requested_years = map( lambda x: offset + x, self.requested_years_list )
              if self.select_year_list( requested_years, 'output1', force_complete = True ):
                  return True

## return years requested relative to first year if number submitted is greater than 145

          if self.nyears_submitted > 145:
             offset = self.ads_time_period[0]
             requested_years = map( lambda x: offset + x, self.requested_years_list )
             if self.select_year_list( requested_years, 'output1', force_complete = True ):
                  return True

## return last 25 years if none of the above apply

          return self.select_last( 25, 'output1' )
        elif self.rei[1] in ['3.1']:
          opts = self.cp.options( self.model )
          y_pic2h = int( self.cp.get( self.model, 'year_picontrol_spawn_to_historical' ) )
          y_hist0 = int( self.cp.get( self.model, 'year_historical_start' ) )
          offset = y_pic2h - y_hist0
          requested_years = map( lambda x: x + offset, self.requested_years_list )

          if self.select_year_list( requested_years, 'output1', force_complete = True ):
            return True

          if self.table_segment == 2:
            return self.select_first( 25, 'output1' )
          else:
            self.select_first( 25, 'output1' )
            return self.select_last( 25, 'output1', append=True )

        else:
          return self.ok( 'output1', 'experiment not requested for cfmip', 'OK010' )
      return self.not_ok( 'listrel option not picked up for processing %s,%s' % (self.table,self.expt), 'ERR003' )
##
## selected time slices with absolute dates
##
    elif self.table in ['aero','3hr','day','6hrPlev','cfMon']:
      assert self.request_spec[0] != 'listrel', 'find_product_slice[e3]: should not have listrel here'
      return self.select_year_list( self.requested_years_list, 'output1' )

    else:
      return self.not_ok( 'table %s not given in this method ' % self.table, 'ERR101' )

    self.reason = reason
    self.product = res
    return True

  def check_time_slices(self):
    for k in range( len( self.year_slices ) -1 ):
       if self.year_slices[k+1][0] <= self.year_slices[k][1]:
          return self.not_ok( 'Overlapping time segments in submitted data', 'ERR009' )

## if time slices appear OK, return True
    return True

  def select_last( self, n, product, append=False, rc='OK200' ):
    if not self.check_time_slices():
      return False

    assert rc[0:5] == 'OK200', 'Bad use of select_last return code: %s' % rc
    assert product in ['output1', 'output2'], 'bad product: %s' % str(product)

    ixy = index_last_n_years( n, self.year_slices )
    if ixy == 0:
      self.product = product
      self.reason = 'all submitted years in last %s' % n
      return True

    ystart = self.year_slices[ixy][0]

    fs = []
    fns = []
    for k in range( len(self.files) ):
       if self.time_periods[k][0] >= ystart:
         fs.append( self.files[k] )
       else:
         fns.append( self.files[k] )

    if append:
      reason = self.reason + '; last %s years assigned to %s ' % (n,product)
    else:
      reason = 'last %s years assigned to %s ' % (n,product)

    return self.__assign_selected_files( fs, product, fns, reason, rc=rc, append=append )
    
  def select_first( self, n, product, rc='OK100' ):
    if not self.check_time_slices():
      return False

    assert product in ['output1', 'output2'], 'bad product: %s' % str(product)

    ixy = index_first_n_years( n, self.year_slices )
    if ixy == len(self.year_slices)-1:
      self.product = product
      self.reason = 'all submitted years in first %s' % n
      return True

    yend = self.year_slices[ixy][1]

    fs = []
    fns = []
    for k in range( len(self.files) ):
       if self.time_periods[k][1] <= yend:
         fs.append( self.files[k] )
       else:
         fns.append( self.files[k] )

    reason = 'first %s years assigned to %s ' % (n,product)
    return self.__assign_selected_files( fs, product, fns, reason, rc=rc )

  def select_year_list( self, yl, product, force_complete=False, rc='OK300' ):
    if not self.check_time_slices():
      return False

    assert product in ['output1', 'output2'], 'bad product: %s' % str(product)

    ixy, ny = index_in_list( yl, self.year_slices )

    fs = []
    fns = []
    for k in range( len(self.files) ):
       if self.time_periods[k][1] in yl or self.time_periods[k][0] in yl:
         fs.append( self.files[k] )
       else:
         fns.append( self.files[k] )

    if force_complete and not ny == len(yl):
      self.res = {'fs':fs, 'fns':fns, 'ny':ny, 'yl':yl }
      return self.not_ok( 'Not all years requested have been found', 'ERR005' )

    reason = 'selected years [%s/%s] assigned to %s ' % (ny,len(yl),product)
    return self.__assign_selected_files( fs, product, fns, reason, rc=rc )

  def __assign_selected_files( self, fs, product, fns, reason, rc='OK400', append=False ):
    other = {'output1':'output2', 'output2':'output1' }[product]

    if append:
      self.output1_files += { product:fs, other:fns }['output1']
      self.output2_files += { product:fs, other:fns }['output2']
    else:
      self.output1_files = { product:fs, other:fns }['output1']
      self.output2_files = { product:fs, other:fns }['output2']

    self.product_change_warning = False
    if not self.ads_new:
      nerr = [0,0,0,0]
      nt = 0
      ferr =[ [],[],[],[] ]
      ixr = { 'O1':0, 'O2':1, 'R1':2, 'R2':3 }
      for f in self.output1_files:
         if self.file_dict[f] in ['O2','R2']:
           ix = ixr[self.file_dict[f]]
           nerr[x] += 1
           ferr[x].append(f)
           nt += 1
      for f in self.output2_files:
         if self.file_dict[f] in ['O1','R1']:
           ix = ixr[self.file_dict[f]]
           nerr[ix] += 1
           ferr[ix].append(f)
           nt += 1
      self.product_change_warning = nt != 0
      if self.product_change_warning:
        log.warn( 'New data triggers change in product of already published data: O1 %s, O2 %s, R1 %s, R2 %s' % tuple(nerr) )
        emsg = ['Files in output1 moved to output2: %s', 'Files in output2 moved to output1: %s', \
                'Files in output1 updated into output2: %s', 'Files in output2 unpated into output1: %s' ]
        for i in range(4):
           if nerr[i] > 0:
             log.warn( emsg[i] % nerr[i] )

        self.output1_remove = []
        self.output2_remove = []
        self.output1_to_output2 = []
        self.output2_to_output1 = []
        fp = []
        for f in self.output1_files:
          if self.file_dict[f] in ['O2','R2']:
            if self.file_dict[f] == 'O2':
              self.output2_to_output1.append(f)
            else:
              self.output2_remove.append(f)
        for f in fp:
            self.output1_files.pop( self.output1_files.index(f) )
        fp = []
        for f in self.output2_files:
          if self.file_dict[f] in ['O1','R1']:
            if self.file_dict[f] == 'O1':
              self.output1_to_output2.append(f)
            else:
              self.output1_remove.append(f)
        for f in fp:
            self.output2_files.pop( self.output2_files.index(f) )
        if not self.override_product_change_warning:
           return self.not_ok( 'Republish data in atomic dataset or re-run with override_product_change_warning=True', 'ERR007' )

    self.output1_start_years = []
    for f in self.output1_files:
      self.output1_start_years.append( self.file_start_years[ self.files.index(f) ] )
    if self.product_change_warning:
      return self.ok( 'split*', reason, rc )
    else:
      return self.ok( 'split', reason, rc )
    
  def not_enough_years(self):
      return self.nyears_submitted < (self.nyears_requested + 6)
