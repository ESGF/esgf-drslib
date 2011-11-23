#!/usr/bin/python
## Code to identify the CMIP5 DRS "product" element based on other DRS elements and selection tables.
## Author: Martin Juckes (martin.juckes@stfc.ac.uk)
## New in this version:
##   1. cmip5_product.status no longer used
##   2. additional capability to scan previously published data
##   3. option to raise a ProductScopeexception instead of providing "False" return when arguments are inconsistent with selection tables
##   4. cmip5_product.rc has a return code on exit -- each return code coming from a unique line of code.
## 20101004 [0.8]: -- fixed bug which failed on all tables among the special cases.
##                 -- fixed scan_atomic_dataset to scan only files matching variable, table, and experiment.
##                        there is an option to turn this of (and scan all files in a directory), without which the legacy test suite will fail.
## 20101005 [0.9]: -- fixed code to deal with file time spans not aligned with calendar years.
## 20101022 [1.0]: -- added capability to extract base time from time units of netcdf files.
##                 -- fixed bug affecting 1pctCO2, abrupt4xCO2.
##                 -- fixed bug affecting response when a product change is implied.
##                 -- changed configuration file variables to be more consistent with terminology used in data request.
##                 -- made return codes more specific for OK300...
##                 -- fixed bug: offset relative to start years omitted year "1" (by starting with offset 1)
##                 -- fixed bug: piControl, decadal, aero data was using wrong offset
##                 -- changed names to be consistent with MIP tables (Co2,co2 --> CO2, volcano2010 --> volcIn2010 -- see expt_id_mappings.txt
##                 -- added code to deal with volcIn2010, aero option (previously overlooked)
## 20110201        -- debugged atomic dataset scanning to get robust estimate of nyears_submitted
##                 -- debugged support for "corresponding"
## 20110428        -- debugged logic on 1pctCO2, 3hr data -- added no_exception arcgument to select_year_list to allow ERR00##                     to be caught by calling routine.
## 20110613        -- debugged select_year_list to deal with case when data file spans time range greater than requested period
## 20111118        -- fixed bug issuing false warning for piControl, cfMon data after using incorrect date offset.
## 20111121        -- fixed bug (typo) at line 630 (y_ec2h --> y_ec2eh); 
##                    fixed bug in find_rei: was not idenyfying centennial 1pctCO2 experiment correctly, going to decadal version instead.
##                    fixed bug in init.py, creating record in wrong format in standard_ouput shelve
##                    cleared up logic on "last xx" decisions.
##   
version = 1.5
version_date = '20111121'
import logging
log = logging.getLogger(__name__)
import re, string

class ProductException(Exception):
  pass

class DebugException(ProductException):

  def __init__(self,tup):
    self.tup = tup

  def __str__(self):
    for t in self.tup:
      print t
    return repr(self.tup)

class ProductScope(ProductException):
  def __init__(self,value):
     self.value = value
  def __str__(self):
     return repr(self.value)

class ProductDetectionError(ProductException):
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
  def __init__(self,mip_table_shelve='sh/standard_output_mip_rev', \
                    template='sh/template',\
                    stdo='sh/standard_output',\
                    config='ini/sample_1.ini', \
                    override_product_change_warning=False,\
                    cmip5_sanity_check=True,\
                    policy_opt1='all_rel',not_ok_excpt=False):
    self.mip_table_shelve = mip_table_shelve
    self.mip_sh = shelve.open( mip_table_shelve, flag='r' )
    self.tmpl = shelve.open( template, flag='r' )
    self.stdo = shelve.open( stdo, flag='r' )
    self.tmpl_keys = self.tmpl.keys()
    self.tmpl_keys.sort( ddsort(self.tmpl,0).cmp )
    self.pos_in_table = 999
    self.config = config
    self.config_exists = os.path.isfile( config )
    self.config_loaded = False
    self.uid = 'uid-unset'
    self.policy_opt1=policy_opt1
    self.last_result = ['none','none']
    self.product = 'none'
    self.ads_product = 'none'
    self.override_product_change_warning = override_product_change_warning
    self.not_ok_excpt = not_ok_excpt
    self.ScopeException = ProductScope
    self.warning = "this is a depricated variable"
    if cmip5_sanity_check:
      self.cmip5_sanity_check()

##
## perform simple sanity checks to help detection of configuration errors
##
  def cmip5_sanity_check(self):
    log.info( 'Performing CMIP5 sanity checks (cmip5_sanity_check=True)' )
    req_vars = { '6hrPlev':'psl', 'day':'tas' }
    for tab in ['6hrPlev','day']:
      if not self.mip_sh.has_key( tab ):
        raise ProductDetectionError( 'MIP table shelve [%s] does not contain CMIP5 required table %s' % (self.mip_table_shelve, tab ) )
      self.table = tab
      self.var = req_vars[tab]
      if not self.check_var():
        raise ProductDetectionError( 'MIP table [%s] in does not contain CMIP5 requested variable %s' % (tab,self.mip_table_shelve, self.var ) )

  def ok(self, product, reason, rc=None):
    self.product = product
    self.reason = reason
    self.rc = rc
    log.info( '--- %s: %s: %s: %s' % ( self.rc, self.product, self.uid, self.reason ) )
    return True

  def not_ok(self, status,rc,no_except=False):
    self.reason = status
    self.rc = rc
    self.product = 'Failed'
    log.info( '--- %s: %s: %s: %s' % ( self.rc, self.product, self.uid, self.reason ) )
    if self.not_ok_excpt and not no_except:
      raise self.ScopeException( '%s:: %s' % (rc,status) )
    return False

  def scan_atomic_dataset(self,dir):
    import glob, string
    if dir[-1] != '/':
      dir += '/'
    assert os.path.isdir( dir ),'Attempt to scan a non-existent directory: %s' % dir
    if self.selective_ads_scan:
      fpat = '%s_%s_%s_%s_*.nc' % (self.var,self.table,self.model,self.expt)
    else:
      fpat = '*.nc' 
    fl = map( lambda x: string.split(x, '/')[-1], glob.glob( dir + fpat ) )
    assert len(fl) != 0,'No files matching %s found in %s' % (fpat,self.path)
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
    years_present = []
    time_tuples = []
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
        #
        # Time parsing re-implemented by spascoe
        #
        tbits = string.split( bits[5], '-' )
        year_re = re.compile(r'(\d\d\d\d)(\d\d)?(\d\d)?(\d\d)?(\d\d)?')
        mo = year_re.match(tbits[0])
        assert mo, 'Start Date not of form yyyy[mm[dd[hh[mm]]]]: not supported: %s' % tbits[0]
        startyear = int(mo.group(1))
        assert mo.group(2) in ['01','02','03','04','05','06','07','08','09','10','11','12'], 'Unsupported date %s: yyyymm, mm should be month' % tbits[0]
        start_tuple = mo.groups()
        if len(tbits) > 1:
          mo = year_re.match(tbits[1])
          assert mo, 'End Date not of form yyyy[mm[dd[hh[mm]]]]: not supported: %s' % tbits[1]
          endyear = int(mo.group(1))
          end_tuple = mo.groups()
        else:
          endyear = startyear
          end_tuple = start_tuple
        start_years.append( startyear )
      else:
          return self.not_ok( 'filename does not match DRS: %s in %s' % (f,dir), 'ERR011' )

      if has_time:
        time_periods.append( (startyear, endyear) )
        for thisy in range( startyear, endyear+1):
          if thisy not in years_present:
             years_present.append( thisy)

        if len( year_slices ) == 0 or (startyear != year_slices[-1][0] or endyear != year_slices[-1][1]):
          year_slices.append( (startyear, endyear) )
          time_tuples.append( (start_tuple, end_tuple) )
          if len( start_tuple) ==1:
            nyears += endyear - startyear + 1
          else:
            nyears += endyear - startyear
            startm = int(start_tuple[1])
            if len( end_tuple ) == 5 and end_tuple[2] == '01' and end_tuple[3] == '00' and end_tuple[4] == '00':
              endm = int(end_tuple[1]) - 1
              if endm == 0:
                endm = 12
                nyears += -1
            else:
              endm = int(end_tuple[1])

            if endm > startm:
              nyears += 1
 
            
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
    self.nyears_submitted = len( years_present )
    self.drs = (var, mip, model, expt, ens)
    self.has_time = has_time
    self.time_periods = time_periods
    self.time_tuples = time_tuples
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
       return self.check_var_rev()

  def check_var_rev(self):
    kk = 0
    for r in self.mip_sh[self.table]:
      kk+=1
      if r[0] == self.var:
        self.vline = r[:]
        self.pos_flag = r[3]
        self.table_segment = r[4]
        if self.table_segment == None:
          self.table_segment = 0
## interim solution, to change way 1st 10 variables in day table are flagged.
        if self.pos_flag == 1:
          self.pos_in_table = 5
        else:
          self.pos_in_table = 99
        return True

    return False


  def find_rei( self,expt ):
      
    ##if expt == ['piControl','historical','amip']:
    k1 = expt
    self.category = 'centennial'
    if expt in ['piControl','1pctCO2']:
## need configuration file for branch -- if table is in [aero, day, 6hrPlev, 3hr]
      if not self.config_loaded:
        self.load_config()

## default to centennial
      if self.model not in self.cp.sections():

        log.warn( 'Model %s is not in configuration file -- category defaulting to centennial' % self.model )
        categ = 'centennial'
      else:
        opts = self.cp.options( self.model )
        if 'category' not in opts:
          log.warn( 'Category is not specified for model %s in configuration file -- defaulting to centennial' % self.model )
          categ = 'centennial'
        categ = self.cp.get( self.model, 'category' )

## centennial versions of experiments distinguished from decadal in shelve by an appended '+' on key.

      if categ == 'centennial':
        k1 += '+'
      self.category = categ
      
    if k1 in self.tmpl_keys:
      self.rei = self.tmpl[k1]
      return True
    else:
      return False

  def priority(self):
      return int(float(self.vline[2]))
    
  def dimensions(self):
      return self.vline[1]

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
#
      self.requested_years_list = []
      for s in slice_list:
         if s[1] != s[0]:
           self.requested_years_list.append( s[0] - 1 )
         for y in range( s[0], s[1]+1):
              self.requested_years_list.append( y )
         if s[1] != s[0]:
           self.requested_years_list.append( s[1] + 1 )
      self.nyears_requested = len( self.requested_years_list )
    return False
        
  def get_request_spec(self):
    tlist = self.stdo[self.request_col]
    self.requested_years_list = []
    if self.rei[0]-2 in tlist.keys():
      tli = self.rei[0]-2
      ssp = tlist[tli]
      self.request_spec = ssp
      assert ssp[0] in ['list','listrel','corres','none','all'], 'unexpected ssp[0]:: %s [%s,%s]' % (str( ssp[0] ),self.expt,self.table)
      if ssp[0] in ['list','listrel','corres']:
        nyears = 0
        for s in ssp[1:]:
          ##assert s[0] in ['year','slice'], 'Unexpected time specification %s' % str(s[0])
          if s[0] not in ['year','slice']:
            raise DebugException(  ('Unexpected time specification %s' % str(s[0]), \
                                    'Request col = %s' % self.request_col, \
                                    'ssp = %s' % str(ssp) ) )
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

  def find_product(self,var,table,expt,model,path,startyear=None,verbose=False, \
                  path_output1=None, path_output2=None,selective_ads_scan=True):
    self.uid = string.join( [var,table,expt,model], '_' )
    if self.last_result[0] != arg_string( var,table,expt,model,path,path_output1,path_output2):
      self.find_product_ads(var,table,expt,model,path,verbose=verbose, path_output1=path_output1, \
                  path_output2=path_output2,selective_ads_scan=selective_ads_scan)
    self.ads_new = path_output1 == None and path_output2 == None
    
    self.ads_product = self.last_result[1]
    self.selective_ads_scan=selective_ads_scan
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
                  path_output1=None, path_output2=None, selective_ads_scan=True):
    self.uid = string.join( [var,table,expt,model], '_' )
    self.selective_ads_scan=selective_ads_scan
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
      return self.ok( 'output2', 'variable [%s] not requested in table %s' % (var,table), 'OK002' )
    if table not in ['Oyr','Omon','aero','day','6hrPlev','3hr','cfMon']:
       return self.ok( 'output1', 'Table is all in output1', 'OK013' )
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
         
    return self.not_ok( 'Need temporal information', 'ERR004', no_except=True )

  def _get_file_base_year(self):
    ##try:
      ##import cdms
    ##except:
      import os, string, re
      fpath = '%s/%s' % (self.path,self.files[0])
      os.popen( 'ncdump -h %s | grep time:units > ncdump_tmp.txt' % fpath ).readlines()
      ii = open( 'ncdump_tmp.txt' ).readlines()
      if len(ii) == 0:
         raise self.ScopeException( '%s:: %s %s' % ('ERR201','ncdump of file failed:', fpath) )
      mm = re.findall( 'days since ([\d]{4})-', ii[0] )
      if len(mm) != 1:
         raise self.ScopeException( '%s:: %s' % ('ERR202','Failed to interpret ncdump output') )
      self.base_year = int(mm[0])
    
  def find_product_slice(self):
    res = 'output1'
    reason = 'default'
    if not self.scan_atomic_dataset(self.path):
       return False

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
      return self.select_year_list( requested_years, 'output1', rc='OK300.01' )

## override shelf spec.
    override_shelf = (self.table == '3hr' and self.expt in ['1pctCO2','abrupt4xCO2'] ) or (self.expt == 'volcIn2010' and self.table == 'aero')
    
       ##rspec = list( self.request_spec[0] )
       ##rspec[0] = 'listrel'
       ##self.request_spec = tuple( rspec )

## load module to deal with time slices in the variable request
    if self.request_spec[0] == 'listrel' or override_shelf:
      if override_shelf:
        self.nyears_requested = 30
      if self.policy_opt1 == 'all_rel' and self.not_enough_years():
         return self.ok( 'output1',  \
            'years submitted (%s) not greater than 5 + years requested (%s)' % (self.nyears_submitted,self.nyears_requested), 'OK009.2' )

      if not self.config_loaded:
        self.load_config()
      if (self.expt == 'piControl' and self.table in ['aero','day','6hrPlev'] ) or \
         (self.expt == 'esmControl' and self.table in ['aero','day'] ):
        if self.model not in self.cp.sections():
          return self.not_ok( 'Need to have model in configuration file, to specify start of %s run' % {'piControl':'historical', 'esmControl':'esmHistorical'}[self.expt], 'ERR002' )
        if self.expt == 'piControl':
          if self.category == 'centennial':
            y_pic2h = int( self.cp.get( self.model, 'branch_year_picontrol_to_historical' ) )
            y_hist0 = int( self.cp.get( self.model, 'base_year_historical' ) )
            offset = y_pic2h - y_hist0
          else:
            offset = self._get_base_year( self.expt )
            offset += -1
        else:
          y_ec2eh = int( self.cp.get( self.model, 'branch_year_esmControl_to_esmHistorical' ) )
          y_ehist0 = int( self.cp.get( self.model, 'base_year_esmHistorical' ) )
          offset = y_ec2eh - y_ehist0
        requested_years = map( lambda x: x + offset, self.requested_years_list )
        return self.select_year_list( requested_years, 'output1', rc='OK300.02' )
      elif (self.table == '3hr' and self.expt in ['1pctCO2','abrupt4xCO2'] ):
        offset = self._get_base_year( self.expt )
        assert offset != None, 'offset not found for %s, %s, %s' % (self.model, self.expt, self.table)

        if self.expt == '1pctCO2':
              requested_years = map( lambda x: offset + 110 + x, range(30) )
              nrq  = 30
        else:
              requested_years = map( lambda x: offset + x, range(5) ) + \
                              map( lambda x: offset + 120 + x, range(30) )
              nrq = 35
        if self.select_year_list( requested_years, 'output1', force_complete = True, rc='OK300.03', no_except=True ):
              return True
## if not all years found, take first and last submitted as appropriate.
        if self.rc == 'ERR005':
          if self.expt == '1pctCO2':
            return self.select_last( 30, 'output1', rc='OK200.02' )
          else:
            self.select_first( 5, 'output1' )
            return self.select_last( 30, 'output1', append=True, rc='OK200.03' )
## if select_year_list has failed for some other reason (e.g. product change flagged) return false.
        else: 
          assert not self.not_ok_excpt, '%s:: Not all requested years found'
          return False

      elif (self.expt == 'piControl' and self.table == '3hr'):
        offset = self._get_base_year( '1pctCO2' )
        if offset != None:
            requested_years = map( lambda x: offset - 1 + x, self.requested_years_list )
            result = self.select_year_list( requested_years, 'output1', force_complete = True, rc='OK300.04' )
            if self.rc != 'ERR005':
                  return result
        return self.select_last( 35, 'output1', rc='OK200.04' )
          
      elif (self.expt == 'volcIn2010' and self.table == 'aero'):
        offset = self._get_base_year( self.expt, config_needed=False )
        assert offset != None, 'Failed to get base year from file for volcIn2010'
        requested_years = [offset+9,]
        return self.select_year_list( requested_years, 'output1', force_complete = True, rc='OK300.09' )
      elif self.table in ['cfMon']:
        if self.rei[1] in ['6.2a', '6.2b', '6.3-E', '6.4a', '6.4b', '6.7a', '6.7b', '6.7c']:
          return self.select_first( self.nyears_requested, 'output1' )
        elif self.rei[1] in ['5.4-l', '5.5-l', '6.1', '6.3']:
## for 6.1, 6.3 -- try to use offsets specified in configuration file
          if self.rei[1] in ['6.1','6.3']:
            assert self.expt in [ '1pctCO2', 'abrupt4xCO2'], 'ERR920: Unexpected expt (%s) at this point' % self.expt
            offset = self._get_base_year( self.expt )
          else:
            offset == None

          if offset != None:
              requested_years = map( lambda x: offset - 1 + x, self.requested_years_list )
              result =  self.select_year_list( requested_years, 'output1', force_complete = True, rc='OK300.05' )
              if self.rc != 'ERR005':
                  return result
## return years requested relative to first year if number submitted is greater than 145
          if self.nyears_submitted > 145:
             offset = self.ads_time_period[0]
             requested_years = map( lambda x: offset - 1 + x, self.requested_years_list )
             result = self.select_year_list( requested_years, 'output1', force_complete = True, rc='OK300.06' )
             if self.rc != 'ERR005':
                  return result
## return last 25 years if none of the above apply
          return self.select_last( 25, 'output1', rc='OK200.05' )
##  NB '3.1' === piControl
        elif self.rei[1] in ['3.1']:
          opts = self.cp.options( self.model )
## try to apply offset from base_year of 1pctCO2 expt.
          if 'base_year_1pctCO2' in opts:
            y_pic2h = int( self.cp.get( self.model, 'base_year_1pctCO2' ) )
          ##y_hist0 = int( self.cp.get( self.model, 'base_year_historical' ) )
            offset = y_pic2h
            requested_years = map( lambda x: x + offset, self.requested_years_list )
            result = self.select_year_list( requested_years, 'output1', force_complete = True, rc='OK300.07' )
            if self.rc != 'ERR005':
                  return result

## if above does not work, return first 25 or first plus last 25.
          if self.table_segment == 2:
            return self.select_first( 25, 'output1' )
          else:
            self.select_first( 25, 'output1' )
            return self.select_last( 25, 'output1', append=True, rc='OK200.06' )
        else:
          return self.ok( 'output1', 'experiment not requested for cfmip', 'OK010' )

      return self.not_ok( 'listrel option not picked up for processing %s,%s' % (self.table,self.expt), 'ERR003' )
## selected time slices with absolute dates
    elif self.table in ['aero','3hr','day','6hrPlev','cfMon']:
      assert self.request_spec[0] != 'listrel', 'find_product_slice[e3]: should not have listrel here'
      return self.select_year_list( self.requested_years_list, 'output1', rc='OK300.08' )
    else:
      return self.not_ok( 'table %s not given in this method ' % self.table, 'ERR101' )
    self.reason = reason
    self.product = res
    return True

  def _check_time_slices(self):
    for k in range( len( self.year_slices ) -1 ):
       for j in range( len( self.time_tuples[k] ) ):
         if self.time_tuples[k+1][0] < self.time_tuples[k][1]:
           return self.not_ok( 'Overlapping time segments in submitted data', 'ERR009' )
## if time slices appear OK, return True
    return True

  def select_last( self, n, product, append=False, rc='OK200' ):
    if not self._check_time_slices():
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
    if not self._check_time_slices():
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

  def select_year_list( self, yl, product, force_complete=False, rc='OK300', no_except=False ):
    if not self._check_time_slices():
      return False

    assert product in ['output1', 'output2'], 'bad product: %s' % str(product)
    ixy, ny = index_in_list( yl, self.year_slices )
    fs = []
    fns = []
    for k in range( len(self.files) ):
       kdone = False
       for y in yl:
         if not kdone:
           if y in range( self.time_periods[k][0],self.time_periods[k][1]+1 ):
              fs.append( self.files[k] )
              kdone = True

       if not kdone:
         if self.time_periods[k][1] in yl or self.time_periods[k][0] in yl:
           fs.append( self.files[k] )
         else:
           fns.append( self.files[k] )

    if force_complete and not ny == len(yl):
      self.res = {'fs':fs, 'fns':fns, 'ny':ny, 'yl':yl }
      return self.not_ok( 'Not all years requested have been found', 'ERR005', no_except=no_except )

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

  def _get_base_year( self, expt, config_needed=True ):
     if self.model in self.cp.sections():
       opts = self.cp.options( self.model )
       if expt == '1pctCO2' and 'base_year_1pctCO2' in opts:
           return int( self.cp.get( self.model, 'base_year_1pctCO2' ) )
       elif expt == 'abrupt4xCO2' and 'base_year_abrupt4xCO2' in opts:
           return int( self.cp.get( self.model, 'base_year_abrupt4xCO2' ) )
       elif expt == 'piControl' and 'base_year_piControl' in opts:
           return int( self.cp.get( self.model, 'base_year_piControl' ) )

     else:
       assert not config_needed, 'Model %s not found in configuration file' % self.model
       
     if expt == self.expt:
       self._get_file_base_year()
       base = self.base_year
     else:
        base = None
     return base
