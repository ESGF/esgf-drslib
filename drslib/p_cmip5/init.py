# BSD Licence
# Copyright (c) 2011, Science & Technology Facilities Council (STFC)
# All rights reserved.
#
# See the LICENSE file in the source distribution of this software for
# the full license text.

"""
initialise the drslib.p_cmip5 module.

"""

import os, sys
import xlrd, string, shelve
import whichdb

import logging
log = logging.getLogger(__name__)


STANDARD_OUTPUT_XLS = 'standard_output_17Sep2010_mod.xls'
STANDARD_OUTPUT_XLS = 'standard_output_mod.xls'
TEMPLATE_XLS = 'CMIP5_archive_size_template.xls'
TEMPLATE_MAPPINGS = 'expt_id_mapping.txt'
TEMPLATE_SHELVE = 'template'
STDO_SHELVE = 'standard_output'
STDO_MIP_SHELVE = 'standard_output_mip'

usage = """usage: %prog [shelve-dir]

shelve-dir: Destination of data files of CMIP5 standard output and archive size.
"""

def _find_shelves(shelve_dir):
    """
    Return the location of CMIP5 shelve files as a dictionary.

    """
    # Locations of shelve files
    template = os.path.join(shelve_dir, TEMPLATE_SHELVE)
    stdo = os.path.join(shelve_dir, STDO_SHELVE)
    stdo_mip = os.path.join(shelve_dir, STDO_MIP_SHELVE)

    assert whichdb.whichdb(template) != None
    assert whichdb.whichdb(stdo) != None
    assert whichdb.whichdb(stdo_mip) != None

    return dict(template=template, stdo=stdo, stdo_mip=stdo_mip)


def init(shelve_dir,xls_dir=None):
    """
    Create the shelve files needed to run p_cmip5.

    """

    if xls_dir == None:
      xls_dir = os.path.join(os.path.dirname(__file__), 'xls')
    stdo_xls = os.path.join(xls_dir, STANDARD_OUTPUT_XLS)
    template_xls = os.path.join(xls_dir, TEMPLATE_XLS)
    template_map = os.path.join(xls_dir, TEMPLATE_MAPPINGS)

    if not os.path.exists(shelve_dir):
        os.makedirs(shelve_dir)

    # Locations of shelve files
    template = os.path.join(shelve_dir, TEMPLATE_SHELVE)
    stdo = os.path.join(shelve_dir, STDO_SHELVE)
    stdo_mip = os.path.join(shelve_dir, STDO_MIP_SHELVE)

    mi = mip_importer(stdo_xls)
    ri = request_importer(template=template_xls, cmip5_stdo=stdo_xls)
    ri.import_template(template,expt_mapping_file=template_map)
    ri.import_standard_output(stdo)
    #!TODO: Extra argument x1_sh not supported yet.  What's it for?
    mi.imprt(stdo_mip)
    

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
               if r == 69 and colh[kkk] == 'M':
                 ll1 = []
                 for y in [1850, 1870, 1890, 1900,1910,1920,1930,1940, 1950, 1960, 1970, 1980,1990 , 2000, 2010, 2020, 2040, 2060, 2080, 2100]:
                   ll1.append( ('year',y) )
               else:
                 ll1 = { 'N':('slice',1986,2005), 'Q':('slice',1979,2008), 'R':('slice',111,140) }[colh[kkk]]
               ee[r] =  ['listrel',ll1]
               log.info('corres:: row %s, col %s' % ( oo.row(r)[0].value, colh[kkk] ))
             elif string.find( item, 'last') != -1:
               ee[r] =  ['corres',ll1]
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
                   log.info('%s %s', (bits,b))
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


class mip_importer:

  def __init__(self,input_xls):
##file = '/data/synced/home_projects/processing/standard_output_x1.xls'
##file = '/data/synced/home_projects/isenes/standard_output_17Sep2010.xls'
    self.input_xls = input_xls

  def imprt(self,mip='sh/standard_output_mip',x1_sh=None):
    book = xlrd.open_workbook( self.input_xls )

    log.info(book.sheet_names())

    wf = workflow(states=['wait','items','title'])
    wf.add( 'wait', allowed=['title'], disallowed=['wait','items'] )
    wf.add( 'items', allowed=['wait','title'], disallowed=['items'] )
    wf.add( 'title', allowed=['items','title'], disallowed=['wait'] )

    sns = book.sheet_names()[2:-2]
    
    x1 = x1_sh != None
    if x1:
      sh = shelve.open( x1_sh, 'n' )
      ##sh = shelve.open( 'standard_output_x1', 'n' )
    sh_mip = shelve.open( mip, 'n' )

    ktt = 0
    title = None
    qrows = []
    for sn in sns:
    
      wf.name = sn
      qrows_mip=[]
      wf.reset()
      wf.set( 'wait' )
      this = book.sheet_by_name(sn)
    
      kt=0
      kp=0
      kkkk = -1
      ilist = this.col(0)[:]
      for i in ilist:
        kkkk += 1
        v = i.value
        if wf.status == 'items':
          if string.strip( str( v ) ) == '':
            wf.set( 'wait' )
            log.info(kk)
          else:
            kk+=1
    
        if type(v) == type(u'x'):
          if string.find( v, 'CMOR Table') != -1 or string.find( v, 'Ocean layer depth field requested only from models ') != -1 or string.find(v,'on ocean grid') != -1:
            log.info(v)
            kt+=1
            kk = 0
            wf.set( 'title' )
            if title != None:
              if x1:
                sh[str(ktt)] = ( (title, this_sn), qrows[:] )
              ktt+=1
            title = v
            this_sn = sn
            qrows = []
          if string.find( v, 'priority') != -1:
            kp+=1
            wf.set( 'items' )

        if type(v) == type(0.):
          if wf.status == 'title':
             if v == 0.:
               wf.set( 'items' )
               kp +=1
             else:
               raise Exception('dodgy transition')
          elif v == 0.:
            log.info('%s %s' % (wf.status, i))
            log.info(kkkk)
            log.info(this.row(kkkk-1))
            log.info(this.row(kkkk))
            log.info(this.row(kkkk+1))
            log.info(this.col(0))
            raise Exception('dodgy status')
          elif wf.status in ('items','wait'):
            qrows.append( map( lambda x: x.value, this.row(kkkk) ) )
            qrows_mip.append( map( lambda x: x.value, this.row(kkkk) ) )

      if kp != kt:
            log.info('mismatch in heading count %s %s' % (kp,kt))
            log.info(this.col(0))
    
      if title != None and len(qrows) != 0:
         if x1:
            sh[str(ktt)] = ( (title,this_sn), qrows[:] )
         ktt+=1
         qrows = []
      if len(qrows) != 0:
         raise Exception('bad len')
      sh_mip[str(sn)] = qrows_mip[:]

    log.info(len(qrows))
    if x1:
      sh.close()
    sh_mip.close()

