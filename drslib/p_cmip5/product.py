"""
Product deduction module by Martin Juckes with minimal adaption by
Stephen Pascoe.

"""

import logging
log = logging.getLogger(__name__)

class ddsort:
  def __init__(self,ee,k):
    self.k = k
    self.ee = ee

  def cmp(self,x,y):
    return cmp( self.ee[x][self.k], self.ee[y][self.k] )


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
                    config='ini/sample_1.ini'):
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
    self.warning = ''
    self.last_result = 'none'
    self.product = 'none'
    self.ads_product = 'none'


  def ok(self, product, reason):
    self.product = product
    self.reason = reason
    return True

  def not_ok(self, status):
    self.status = status
    return False

  def scan_atomic_dataset(self,dir):
    import glob, string
    if dir[-1] != '/':
      dir += '/'
    fl = map( lambda x: string.split(x, '/')[-1], glob.glob( dir + '*.nc' ) )
    fl.sort()
    if len(fl) == 0:
      self.status = 'no files found in directory %s' % dir
      return False

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
        start_years.append( startyear )
      else:
          self.status = 'filename does not match DRS: %s in %s' % (f,dir)
          return False

      if not has_time and len(fl) > 1:
        self.status = 'error: multiple files in atomic dataset with no temporal subset: %s ' % dir
        return False
      else:
        time_periods.append( (startyear, endyear) )
        if len( year_slices ) == 0 or (startyear != year_slices[-1][0] or endyear != year_slices[-1][1]):
          year_slices.append( (startyear, endyear) )
          nyears += endyear - startyear + 1

      kk +=1
      if kk == 0:
        var, mip, model, expt, ens = tuple( bits[0:5] )
        base = string.join( bits[0:5], '_' )
      elif string.join(bits[0:5],'_') != base:
          self.status = 'error: inconsistent files in %s' % dir
          log.info(base)
          log.info(string.join(bits[0:5],'_'))
          return False

    self.nyears_submitted = nyears
    self.drs = (var, mip, model, expt, ens)
    self.has_time = has_time
    self.time_periods = time_periods
    self.year_slices = year_slices
    self.ads_time_period = ( time_periods[0][0], time_periods[-1][1] )
    self.dir = dir
    self.files = fl
    self.file_start_years = start_years
    assert len(fl) == len(start_years), 'Apparent error in logic scanning atomic dataset'
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
      self.get_slicer()

      if not self.config_loaded:
        self.tsl.load_config()

      if self.model not in self.tsl.cp.sections():
        categ = 'centennial'
      else:
        opts = self.tsl.cp.options( self.model )
        if 'category' not in opts:
          categ = 'centennial'
        categ = self.tsl.cp.get( self.model, 'category' )

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

    if self.rei[1] not in keys:
      self.status = 'Experiment not requested for cfmip'
      log.info(' '.join(self.rei[1],' not in keys:: ',keys))
      return False

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

  def get_slicer(self):
    if not self.have_slicer:
      import p_cmip5_time_slices
      self.tsl = p_cmip5_time_slices.request_time_slice(self)
      self.have_slicer = True

  def in_requested_time(self,start,end):
    if not self.have_slicer:
      import p_cmip5_time_slices
      self.tsl = p_cmip5_time_slices.request_time_slice(self)
      self.have_slicer = True
    return self.tsl.in_requested_time( start, end )
        
  def find_product(self,var,table,expt,model,path,startyear=None,endyear=None,verbose=False):

    if self.last_result[0] != '%s_%s_%s_%s__%s' % (var,table,expt,model,path):
      self.find_product_ads(var,table,expt,model,path,verbose=verbose)
    
    self.ads_product = self.last_result[1]

    if self.ads_product in ['output1','output2']:
        return True
    elif self.ads_product == 'Failed':
        return False
    else:
        if startyear in self.output1_start_years:
          self.product = 'output1'
          return True
        elif startyear in self.file_start_years:
          self.product = 'output2'
          return True
        else:
          return self.not_ok( 'startyear %s does not correspond to file in %s' % (startyear,path) )

###################
  def find_product_ads(self,var,table,expt,model,path,verbose=False):
##
## look to see if all files in the atomic dataset are treated equally'
    if self.find_product_step_one(var,table,expt,model,verbose=verbose):
      self.last_result = ( '%s_%s_%s_%s__%s' % (var,table,expt,model,path), self.product )
      return True

    self.warning = ''
    if self.status == 'Experiment not identified':
      self.warning += 'Experiment [%s] not identified' % self.expt
      return self.ok( 'output1', 'Unrequested experiment -- none replicated' )
    if self.status != 'Need temporal information':
      return False
##
## go into deeper analysis
    self.path = path
    if self.find_product_slice():
      self.last_result = ( '%s_%s_%s_%s__%s' % (var,table,expt,model,path), self.product )
      return True
    else:
      self.last_result = ( '%s_%s_%s_%s__%s' % (var,table,expt,model,path), 'Failed' )
      return False

####################
####################
  def find_product_step_one(self,var,table,expt,model,verbose=False):
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
    self.verbose = verbose

    if not self.check_var():
      return self.ok( 'output2', 'variable not requested' )
    if verbose and table == 'cfMon':
      log.info(' '.join('find_product_step_one::', var, self.table_segment))

    if table == 'Oyr': 
       if self.priority() == 3:
         return self.ok( 'output2', 'Table %s, priority 3' % table )
       else:
         return self.ok( 'output1', 'Table %s, priority < 3' % table )

    elif table == 'Omon':
       dims = self.dimensions()
       if 'basin' in dims:
         return self.ok( 'output1', 'Table %s, with basin in dimensions' % table )
       elif 'olevel' in dims and self.priority() >= 2:
         return self.ok( 'output2', 'Table %s, 3d, priority >=2' % table )
       else:
         return self.ok( 'output1', 'Table %s, priority %s, dims %s' % (table,self.priority(),str(dims)) )
    elif table == 'aero' and 'alev1' not in self.dimensions():
         return self.ok( 'output1', 'Table %s, dims %s' % (table,str(self.dimensions())) )
    elif table == 'day' and self.pos_in_table <= 10:
         return self.ok( 'output1', 'Table %s, in first 10 variables' % table )

    if verbose:
       log.info('need to identify experiment')

    if not self.find_rei(expt ):
            return self.ok( 'output1','EXPERIMENT NOT IDENTIFIED' )

    if table in ['aero','day','6hrPlev','3hr']:
         self.request_col = {'aero':'M','day':'N', '3hr':'R', '6hrPlev':'Q'}[table]
         self.get_request_spec()
         if self.request_spec[0] in ['none','all']:
             return self.ok( 'output1', 'Request covers %s of this atomic dataset' % self.request_spec[0] )

    elif table == 'cfMon':
         self.get_cfmip_request_spec()
         if self.request_spec[0] in ['none','all']:
             return self.ok( 'output1', 'Request covers %s of this atomic dataset' % self.request_spec[0] )
         
    return self.not_ok( 'Need temporal information' )
    

  def find_product_slice(self):

    res = 'output1'
    reason = 'default'

    self.scan_atomic_dataset(self.path)

    if self.verbose:
       log.info('find_product_slice: years requested: %s, years submitted: %s' % (self.nyears_requested, self.nyears_submitted))

    if self.nyears_submitted > 0:
      assert self.nyears_requested >= 0, 'find_product_slice: Should not reach here with nyears_requested < 0'

      if self.nyears_submitted < (self.nyears_requested + 6):
           return self.ok( 'output1',  \
            'years submitted (%s) not greater than 5 + years requested (%s)' % (self.nyears_submitted,self.nyears_requested) )

    if self.expt in ['midHolocene','lgm'] and self.table == '6hrPlev':
### take last 35 years
      return self.select_last( 35, 'output1' )

    if len(self.expt) > 7 and self.expt[0:7] == 'decadal':
      time_datum = int( self.expt[7:11] )
      if time_datum in [1960, 1980, 2005]:
         requested_years = map( lambda x: x+time_datum, [10,20,30] )
      else:
         requested_years = (time_datum + 10, )

      if self.verbose:
         log.info('Experiment %s, time dataum %s' % (self.expt, self.time_datum ))

      return self.select_year_list( requested_years, 'output1' )

##
## load module to deal with time slices in the variable request
##
    self.get_slicer()

    if self.request_spec[0] == 'listrel':
      if not self.config_loaded:
        self.tsl.load_config()

      if (self.expt == 'piControl' and self.table in ['aero','day','6hrPlev'] ) or \
         (self.expt == 'esmControl' and self.table in ['aero','day'] ):

        if self.model not in self.tsl.cp.sections():
          return self.not_ok( 'need to have model in configuration file, to specify start of %s run' % {'piControl':'historical', 'esmPiControl':'esmHistorical'}[self.expt] )

        if self.expt == 'piControl':
          y_pic2h = int( self.tsl.cp.get( self.model, 'year_picontrol_spawn_to_historical' ) )
          y_hist0 = int( self.tsl.cp.get( self.model, 'year_historical_start' ) )
          offset = y_pic2h - y_hist0
        else:
          y_ec2eh = int( self.tsl.cp.get( self.model, 'year_esmControl_spawn_to_esmHistorical' ) )
          y_ehist0 = int( self.tsl.cp.get( self.model, 'year_esmHistorical_start' ) )
          offset = y_ec2h - y_ehist0

        requested_years = map( lambda x: x + offset, self.requested_years_list )
        return self.select_year_list( requested_years, 'output1' )

      elif (self.table == '3hr' and self.expt in ['1pctCo2','abrupt4xco2'] ):
        opts = self.tsl.cp.options( self.model )
        if self.expt == '1pctCo2' and 'year_1pctCo2_start' in opts:
           offset = int( self.tsl.cp.get( self.model, 'year_1pctCo2_start' ) )
        elif self.expt == 'abrupt4xco2' and 'year_abrupt4xco2_start' in opts:
           offset = int( self.tsl.cp.get( self.model, 'year_abrupt4xco2_start' ) )
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
        opts = self.tsl.cp.options( self.model )
        if 'year_1pctCo2_start' in opts:
            offset = int( self.tsl.cp.get( self.model, 'year_1pctCo2_start' ) )
            requested_years = map( lambda x: offset + x, self.requested_years_list )
            if self.select_year_list( requested_years, 'output1', force_complete = True ):
                  return True

        return self.select_last( 35, 'output1' )
          

      elif self.table in ['cfMon']:
        if self.rei[1] in ['6.2a', '6.2b', '6.3-E', '6.4a', '6.4b', '6.7a', '6.7b', '6.7c']:
          return self.select_first( self.nyears_requested, 'output1' )
        elif self.rei[1] in ['5.4-l', '5.5-l', '6.1', '6.3']:

          if self.rei[1] in ['6.1', '6.3']:
            opts = self.tsl.cp.options( self.model )

## for 6.1, 6.3 -- try to use offsets specified in configuration file
##
          if self.rei[1] == '6.1' and 'year_1pctCo2_start' in opts:
            offset = int( self.tsl.cp.get( self.model, 'year_1pctCo2_start' ) )
          elif self.rei[1] ==  '6.3' and 'year_abrupt4xco2_start' in opts:
            offset = int( self.tsl.cp.get( self.model, 'year_abrupt4xco2_start' ) )
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
          opts = self.tsl.cp.options( self.model )
          y_pic2h = int( self.tsl.cp.get( self.model, 'year_picontrol_spawn_to_historical' ) )
          y_hist0 = int( self.tsl.cp.get( self.model, 'year_historical_start' ) )
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
          return self.ok( 'output1', 'experiment not requested for cfmip' )
      return self.not_ok( 'listrel option not picked up for processing %s,%s' % (self.table,self.expt) )
##
## selected time slices with absolute dates
##
    elif self.table in ['aero','3hr','day','6hrPlev','cfMon']:
      assert self.request_spec[0] != 'listrel', 'find_product_slice[e3]: should not have listrel here'
      return self.select_year_list( self.requested_years_list, 'output1' )

    else:
      self.status = 'table %s not given in this method ' % self.table
      return False

    self.reason = reason
    self.product = res
    return True

  def check_time_slices(self):
    for k in range( len( self.year_slices ) -1 ):
       if self.year_slices[k+1][0] <= self.year_slices[k][1]:
          self.status = 'Overlapping time segments in submitted data'
          return False

## if time slices appear OK, return True
    return True

  def select_last( self, n, product, append=False ):
    if not self.check_time_slices():
      return False

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
      self.reason += '; last %s years assigned to %s ' % (n,product)
    else:
      self.reason = 'last %s years assigned to %s ' % (n,product)
    return self.__assign_selected_files( fs, product, fns, append=append )
    
  def select_first( self, n, product ):
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

    self.reason = 'first %s years assigned to %s ' % (n,product)
    return self.__assign_selected_files( fs, product, fns )

  def select_year_list( self, yl, product, force_complete=False ):
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
      self.status = 'not all years requested have been found'
      self.res = {'fs':fs, 'fns':fns, 'ny':ny, 'yl':yl }
      return False

    self.reason = 'selected years [%s/%s] assigned to %s ' % (ny,len(yl),product)
    return self.__assign_selected_files( fs, product, fns )

  def __assign_selected_files( self, fs, product, fns, append=False ):
    other = {'output1':'output2', 'output2':'output1' }[product]

    if append:
      self.output1_files += { product:fs, other:fns }['output1']
      self.output2_files += { product:fs, other:fns }['output2']
    else:
      self.output1_files = { product:fs, other:fns }['output1']
      self.output2_files = { product:fs, other:fns }['output2']

    self.output1_start_years = []
    for f in self.output1_files:
      self.output1_start_years.append( self.file_start_years[ self.files.index(f) ] )
    self.product = 'split'
    return True
    
