#!/usr/bin/python
"""
initialise the drslib.p_cmip5 module.

"""

import os, sys
import xlrd, string, shelve
import re, glob
from whichdb import whichdb

import logging
log = logging.getLogger(__name__)

from drslib.config import table_path, table_path_csv

# Shelve version is designed to enable drslib to detect when the user needs to upgrade
# their shelves using "drstool init".  A value of 0 implies pre-versioning and is compatible
# with shelve versions up to this point.  A value greater than 0 requires the file SHELVE_VERSION_FILE
# to be present in the shelve directory containing the version.  If they don't match _find_shelves() will
# complain
SHELVE_VERSION = 1
SHELVE_VERSION_FILE = 'VERSION'

STANDARD_OUTPUT_XLS = 'standard_output_17Sep2010_mod.xls'
STANDARD_OUTPUT_XLS = 'standard_output_mod.xls'
TEMPLATE_XLS = 'CMIP5_archive_size_template.xls'
TEMPLATE_MAPPINGS = 'expt_id_mapping.txt'
TEMPLATE_SHELVE = 'template'
STDO_SHELVE = 'standard_output'
STDO_MIP_SHELVE = 'standard_output_mip'

re_cmor_mip = re.compile( 'variable_entry:(?P<var>.*?):::(?P<misc>.*?)dimensions:(?P<dims>.*?):::' )

CMOR_TABLE_DIR = table_path
CMOR_TABLE_CSV_DIR = table_path_csv
CMIP5_REQUEST_XLS ='/home/martin/python/cmip5/work2/esgf-drslib-p_cmip5-d324c7c/drslib/p_cmip5/xls/'

re_cmor_mip2 = re.compile( 'dimensions:(?P<dims>.*?):::' )

day_f10 = ['huss','tasmax','tasmin','tas','pr','psl','sfcWind','tossq','tos','omldamax']

def scan_table(mip,dir=CMOR_TABLE_DIR):
  ll = open( '%s/CMIP5_%s' % (dir, mip), 'r' ).readlines()

  lll = map( string.strip, ll )
  ssss = string.join( lll, ':::' )
  vitems = string.split( ssss, ':::variable_entry:' )[1:]

  ee = []
  for i in vitems:
    b1 = string.split( i, ':::')[0]
    var = string.strip( b1 )
    mm = re_cmor_mip2.findall( i )
    if len(mm) == 1:
      ds = string.split( string.strip(mm[0]) )
    elif len(mm) == 0:
      ds = 'scalar'
    else:
      log.warn(  'Mistake?? in scan_table %s' % str(mm) )
      ds = mm
      raise 'Mistake?? in scan_table %s' % str(mm)
    ee.append( (var,ds) )
  return tuple( ee )

def get_priority( v, lll ):
    kseg = 0
    for l in lll:
       if string.find( l, ',%s,' % v) != -1:
         return (string.split( l, ',' )[0], kseg)
       if l[0:8] == 'priority':
         kseg +=1
    return (None,None)

def scan_table_csv(mip,ee,dir=CMOR_TABLE_CSV_DIR):
  ll = open( os.path.join(dir, '%s.csv' % mip), 'r' ).readlines()

## strip out white space, so that variable can be identified unambiguously by ',var,'
  lll = map( lambda x: string.replace( string.strip(x), ' ',''), ll )
  vlist = map( lambda x: x[0], ee )

  ee2 = []
  for x in ee:
    p,kseg = get_priority( x[0], lll )
    if mip == 'day' and x[0] in day_f10:
      flag1 = 1
    else:
      flag1 = 0
    ee2.append( (x[0],x[1],p,flag1,kseg) )
  return tuple( ee2 )

usage = """usage: %prog [shelve-dir]

shelve-dir: Destination of data files of CMIP5 standard output and archive size.
"""
def _find_shelves(shelve_dir):
    """
    Return the location of CMIP5 shelve files as a dictionary.

    """

    _check_shelve_version(shelve_dir)

    # Locations of shelve files
    template = os.path.join(shelve_dir, TEMPLATE_SHELVE)
    stdo = os.path.join(shelve_dir, STDO_SHELVE)
    stdo_mip = os.path.join(shelve_dir, STDO_MIP_SHELVE)

    assert whichdb(template)
    assert whichdb(stdo)
    assert whichdb(stdo_mip)

    return dict(template=template, stdo=stdo, stdo_mip=stdo_mip)

def _check_shelve_version(shelve_dir):
    version_file = os.path.join(shelve_dir, SHELVE_VERSION_FILE)
    if os.path.exists(version_file):
        shelve_version = int(open(version_file).read().strip())
    else:
        shelve_version = 0

    log.info('Shelve version detected as %d' % shelve_version)

    if shelve_version != SHELVE_VERSION:
        raise Exception("Your shelve directory version is incompatible with this version of drslib"
                        "Please run 'drs_tool init' to reconstruct your shelves")

def init(shelve_dir,mip_dir,mip_csv_dir=None,xls_dir=None):
    """
    Create the shelve files needed to run p_cmip5.

    """

    if xls_dir == None:
      xls_dir = os.path.join(os.path.dirname(__file__), 'xls')
    if mip_csv_dir == None:
      if mip_dir[-1] == '/':
        mip_csv_dir = mip_dir[0:-1] + '_csv'
      else:
        mip_csv_dir = mip_dir + '_csv'

    stdo_xls = os.path.join(xls_dir, STANDARD_OUTPUT_XLS)
    template_xls = os.path.join(xls_dir, TEMPLATE_XLS)
    template_map = os.path.join(xls_dir, TEMPLATE_MAPPINGS)

    if not os.path.exists(shelve_dir):
        os.makedirs(shelve_dir)

    # Locations of shelve files
    template = os.path.join(shelve_dir, TEMPLATE_SHELVE)
    stdo = os.path.join(shelve_dir, STDO_SHELVE)
    stdo_mip = os.path.join(shelve_dir, STDO_MIP_SHELVE)

    ri = request_importer(template=template_xls, cmip5_stdo=stdo_xls)
    ri.import_template(template,expt_mapping_file=template_map)
    ri.import_standard_output(stdo)

    mi = mip_importer_rev(mip_dir,mip_csv_dir)
    mi.imprt(mip=stdo_mip)
    
    version_file = os.path.join(shelve_dir, SHELVE_VERSION_FILE)
    fh = open(version_file, 'w')
    print >>fh, SHELVE_VERSION
    fh.close()

#---------------------------------------------------------------------------
# Martin's code below this point with a few non-functional changes

def helper_year( val ):
  if type( val ) == type( 1. ):
    return int(val)
  elif type(val) in [type('x'), type(u'x')]:
    if string.strip(val) == '':
      return None
    if val[-1] == '*':
      val = val[:-1]
    return int(val)
  else:
    log.info(val)
    assert False, 'bad place to be'

class workflow:
  def __init__(self,name='fred',states=[]):
    self.statuses = {}
    for s in states:
      self.statuses[s] = ['all',None]
    self.name = name
    self.status = None
    self.ltypes = [type(()), type([])]


  def add(self, name, allowed='all', disallowed=None ):
    rv=1
    message = 'ok'
    if not( allowed in ['all',None] or type(allowed) in self.ltypes):
      rv = 0
      message = 'allowed: argument not valid'
    if not( disallowed in ['all',None] or type(disallowed) in self.ltypes):
      rv = 0
      message = 'disallowed: argument not valid'

    if rv == 0:
      return (rv,message)

    if (allowed,disallowed) in ( ['all',None],[None,'all'] ):
      rv=1
    elif (allowed == 'all' and disallowed != None) or (disallowed == 'all' and allowed != None):
      rv=0
      message = 'if allowed or disallowed is "all", the other must be None'
    elif type(allowed) in self.ltypes and type(disallowed) in self.ltypes:
      for a in allowed:
        if a in disallowed:
          rv = 0
          message = 'allowed and disallowed should not overlap'

    if rv != 0:
      self.statuses[name] = (allowed,disallowed)
    return (rv,message)

  def set(self,next):
    if self.allowed( next ):
      self.status = next
    else:
      log.info('%s %s' % (self.status, next))
      raise Exception('failed to set [%s] %s --> %s' % (self.name,self.status, next) )

  def reset(self):
    self.status = None

  def allowed(self,next):
    if next not in self.statuses.keys():
      return False

    if self.status == None:
      return True

    if self.statuses[self.status][1] == 'all':
      return False

    if self.statuses[self.status][0] == 'all':
      return True
 
    if type(self.statuses[self.status][0]) in self.ltypes:
      if next in self.statuses[self.status][0]:
         return True
  
    if type(self.statuses[self.status][1]) in self.ltypes:
      if next in self.statuses[self.status][1]:
         return False

    log.info('%s %s' % (self.status, next))
    log.info(self.statuses[self.status])
    raise Exception('cant determine whether allowed')
 

class request_importer:

  def __init__(self, template='CMIP5_template.xls', cmip5_stdo='xls' ):
    if not os.path.isfile(template):
      log.info('need a valid template file')
      raise Exception('bad arg')
    if not os.path.isfile(cmip5_stdo):
      log.info('need a valid standard output file')
      raise Exception('bad arg')

    self.template = template
    self.cmip5_stdo = cmip5_stdo

  def import_template(self,out='sh/template',expt_mapping_file='expt_id_mapping.txt'):
    mappings = {}
    assert os.path.isfile(expt_mapping_file), 'Cannot find expt_mapping_file %s' % expt_mapping_file
    ii = open(expt_mapping_file).readlines()
    for l in ii:
      bits = string.split( string.strip( l ) )
      mappings[bits[0]] = bits[1]
    
    sh = shelve.open( out, 'n' )
    book = xlrd.open_workbook( self.template )
    sheet = book.sheet_by_name('template')
    ydec = [1965, 1970, 1975, 1985, 1990, 1995, 2000, 2001, 2002, 2003, 2004, 2006, 2007, 2008, 2009, 2010]
    y30 = [1960, 1980, 2005]

    this_row = sheet.row(41)
    k0 = string.strip( str(this_row[10].value ) )
    assert k0 == 'decadalXXXX*', 'key should be decadalXXXX*: %s' % k0
    for y in ydec:
      key = 'decadal%4.4i' % y
      sh[key] = (41, '1.1',str(this_row[0].value), str(this_row[1].value))

    this_row = sheet.row(42)
    for y in y30:
      key = 'decadal%4.4i' % y
      sh[key] = (42, '1.2',str(this_row[0].value), str(this_row[1].value))

    this_row = sheet.row(49)
    k0 = string.strip( str(this_row[10].value ) )
    assert k0 == 'noVolcano', 'key should be noVolcano: %s' % k0
    for y in ydec + y30:
      key = 'noVolc%4.4i' % y
      sh[key] = (49, '1.3',str(this_row[0].value), str(this_row[1].value))

    histVars = ['Nat', 'Ant', 'GHG', 'SD', 'SI', 'SA', 'TO', 'SO', 'Oz', 'LU', 'Sl', 'Vl', 'SS', 'Ds', 'BC', 'MD', 'OC', 'AA']
    this_row = sheet.row(93)
    k0 = string.strip( str(this_row[10].value ) )
    assert k0 == 'historical???', 'key should be historical???: %s' % k0
    for v in histVars:
      if v not in ['GHG','Nat']:
        key = 'historical%s' % y
        sh[key] = (93, '7.3',str(this_row[0].value), str(this_row[1].value))

    rl1 = range(46,52) + range(56,97) + range(100,110)
    for r in rl1:
      this_row = sheet.row(r)
      key = string.strip( str(this_row[10].value ) )
      if key in mappings.keys():
        key = mappings[key]
      while key in sh.keys():
          key += '+'
      sh[key] = (r,str(this_row[2].value), str(this_row[0].value), str(this_row[1].value))
    sh.close()


  def import_standard_output(self, out='sh/standard_output'):
    sh = shelve.open( out, 'n' )
    book = xlrd.open_workbook( self.cmip5_stdo )
    self.import_other(sh,book)
    self.import_cfmip(sh,book)
    sh.close()

  def import_other(self,sh,book):
    oo = book.sheet_by_name('other output')
    rl1 = range(39,51) + range(54,95) + range(98,108)
    colh = ['M','N','Q','R']
    kkk = 0
    for col in [12,13,16,17]:
      ee = {}
      for r in rl1:
        iv = oo.row(r)[col].value
        if type(iv) == type(1.):
          ee[r] = ['list',('year',iv) ]
        ##if type(iv) in ( type('x'), "<type 'unicode'>"):
        else:
          item = string.strip(iv)
          if item == '':
             ee[r] = ('none',)
          elif item == 'all':
             ee[r] = ('all',)
          else:
             item = string.replace( item, '&', '' )
             item = string.replace( item, 'years', '' )
             item = string.replace( item, 'Years', '' )
             item = string.replace( item, 'Year', '' )
             item = string.replace( item, 'year', '' )
             item = string.replace( item, 'and', '' )
             item = string.replace( item, 'possibly', '' )
             item = string.strip( item )

             if string.find( item, 'eq') != -1:
               this_type = 'listrel'
               item = string.replace( item, 'eq', '' )
               log.info('listrel:: row %s [%s], col %s' % ( oo.row(r)[0].value, r, colh[kkk] ))
               log.info(item)
             else:
               this_type = 'list'
             bits = string.split( item, ',' )

             if string.find( item, 'corresp') != -1:
               assert r in [54,69], 'Only expecting corres in piControl r=%s' % r
               ll1 = ['listrel']
               if r == 69 and colh[kkk] == 'M':
                 for y in [1850, 1870, 1890, 1900,1910,1920,1930,1940, 1950, 1960, 1970, 1980,1990 , 2000, 2010, 2020, 2040, 2060, 2080, 2100]:
                   ll1.append( ('year',y) )
               else:
                 ll1.append(  { 'N':('slice',1986,2005), 'Q':('slice',1979,2008), 'R':('slice',111,140) }[colh[kkk]] )
               ee[r] =  ll1
               log.info('corres:: row %s, col %s' % ( oo.row(r)[0].value, colh[kkk] ))
             elif string.find( item, 'last') != -1:
               ee[r] =  ['corres',('year',-30)]
             else:
               ll = [this_type]
               for b in bits:
                 if string.find( b, ':' ) != -1:
                   st,en,dd = map( int, string.split(b,':') )
                   for y in range(st,en+1,dd):
                     ll.append( ('year',y) )
                 elif string.find( b, '-' ) !=-1:
                   st,en = map( int, string.split(b,'-') )
                   ll.append( ('slice',st,en) )
                 else:
                   log.info('%s %s' % (bits,b) )
                   ll.append( ('year',int(b)) )
               ee[r] = ll
   
 
      sh[colh[kkk]] = ee
      kkk +=1
         
  def import_cfmip(self,sh,book):
    oo = book.sheet_by_name('CFMIP output')
    rl1 = range(6,27)
    ee = {}
#
# for each row, check for non-zero date ranges, and append to list. NB there may be multiple
# rows for each experiment.
#
    for r in rl1:
      this_row = oo.row(r)
      expt_nn = str(this_row[2].value)
      if string.strip( expt_nn ) != '':
        this_ee = ee.get( expt_nn, [ [],[],[],[] ] )
        for kseg in range(4):
          if str( this_row[3+kseg*2].value ) != '':
            y0 = helper_year( this_row[3+kseg*2].value )
            y9 = helper_year( this_row[4+kseg*2].value )
            if y0 != None:
                this_ee[kseg].append( (y0,y9) )
        ee[expt_nn] = this_ee
   
    log.info('putting cfmip in shelve')
    sh['cfmip'] = ee
         

##
## reads all user entered data into a dictionary.
##



class mip_importer_rev:

  def __init__(self,mip_dir,mip_csv_dir,mip_tables=None):
    self.input_mip_dir = mip_dir
    self.input_mip_csv_dir = mip_csv_dir
    assert os.path.isdir( self.input_mip_dir ), 'Specified input MIP table directory not found: %s' % self.input_mip_dir
    assert os.path.isdir( self.input_mip_csv_dir ), 'Specified input MIP csv directory not found: %s' % self.input_mip_csv_dir
    fl = glob.glob( self.input_mip_dir + '/CMIP5_*' )
    if mip_tables == None:
      self.mip_tables = []
      for f in fl:
        self.mip_tables.append( string.replace( string.split(f,'/')[-1], 'CMIP5_', '' ) )
    else:
      self.mip_tables = mip_tables
      for t in mip_tables:
         assert os.path.isfile( '%s/CMIP5_%s' % (self.input_mip_dir,t) ), 'File CMIP5_%s not found in %s' % (t,self.input_mip_dir)

  def imprt(self,mip='sh/standard_output_mip',return_as_dict=False):

    if return_as_dict:
      sh_mip = {}
    else:
      sh_mip = shelve.open( mip, 'n' )

    for t in self.mip_tables:
      ee = scan_table( t )
      if t == 'grids':
         ee2 = []
         for e in ee:
           ee2.append( (e[0],e[1], None, 0, None ) )
      else:
        ee2 = scan_table_csv(t,ee)
        if t == 'Omon':
          ee3 = scan_table_csv('Oyr',ee)
          ee4 = []
          for k in range(len(ee2)):
            assert len(ee2[k]) == 5, 'Bad ee2 element %s,%s' % (k, ee2[k] )
            if ee2[k][2] != None:
              ee4.append( ee2[k] )
            else:
              assert ee2[k][0] == ee3[k][0], 'mismatch at %s, %s, %s' % (k,str(ee2[k]),str(ee3[k]))
              ee4.append( (ee2[k][0],ee2[k][1], ee3[k][2], ee2[k][3], None ) )
          ee2 = ee4

      sh_mip[t] = ee2

    if return_as_dict:
      return sh_mip
    else:
      sh_mip.close()
      return None

if __name__ == '__main__':
  import sys
  if len( sys.argv ) != 3:
     print 'usage: init.py go <dir>'
     sys.exit(0)

  init( sys.argv[2],CMOR_TABLE_DIR, xls_dir=CMIP5_REQUEST_XLS )

  sh = shelve.open( sys.argv[2] + '/standard_output_mip', 'r' )
  tlist = ['cf3hr', 'cfSites', 'Oyr','Omon','aero','day','6hrPlev','3hr','cfMon']
  print sh.keys(), len(sh.keys())
  for t in tlist:
    l1 = sh[t]
    ee = scan_table( t )
    ee2 = scan_table_csv(t,ee)
    if t in ['Omon','cf3hr','cfSites']:
      if t == 'Omon':
         t2 = 'Oyr'
      else:
         t2 = 'Amon'
      ee3 = scan_table_csv(t2,ee)
      ee4 = []
      for k in range(len(ee2)):
        assert len(ee2[k]) == 5, 'Bad ee2 element %s,%s' % (k, ee2[k] )
        if ee2[k][2] != None:
          ee4.append( ee2[k] )
        else:
          assert ee2[k][0] == ee3[k][0], 'mismatch at %s, %s, %s' % (k,str(ee2[k]),str(ee3[k]))
          ee4.append( (ee2[k][0],ee2[k][1], ee3[k][2], ee2[k][3] ) )
      ee2 = ee4
      
    kkk = 0
    kk1 = 0
    for e in ee2:
      if e[2] == None:
        kkk += 1
      if e[3] == 1:
        kk1 += 1

    print t, len(ee), len(ee2), len(l1), kkk, kk1
    if kkk > 0:
       print '==================================='
       for e in ee2:
         if e[2] == None:
           print e
       print '==================================='
       
    if t == 'day' and kk1 != 10:
      print 'error',ee2[0:10]
    if t == 'day':
      print ee2[0:10]

    if len(ee) != len(l1):
      eevl = []
      for e in ee:
        eevl.append( e[0] )
      knf = 0
      kmd = []
      for i in range(len(l1)):
          rold = l1[i]
          vold = string.strip(rold[5])
          if vold not in eevl:
            print t,':: not found: ',vold
            knf += 1
          else:
            kmd.append( eevl.index( vold ) )
      knmd = []
      for i in range(len(eevl)):
           if i not in kmd:
             knmd.append( eevl[i] )
      knmd.sort()
      print knmd
    else:
      for i in range(len(l1)):
          rold = l1[i]
          rnew = ee[i]
          if rnew[0] != rold[5]:
            print t,i,rnew[0],rold[5]

