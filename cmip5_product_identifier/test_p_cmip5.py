#!/usr/bin/python

import p_cmip5_v5 as p

pc = p.cmip5_product()
pc2 = p.cmip5_product( config='ini/sample_2.ini')

def test(var, mip, expt,startyear=None,endyear=None,path = '/tmp', verbose=False, pci=pc, tab='    '  ):
  model = 'HADCM3'

  if startyear == None:
    if pci.find_product_ads( var, mip, expt,model,path, verbose=verbose ):
      print tab,var,',',mip,',',expt,path,':: ',pci.product, pci.reason 
      oo.write( '%s,%s,%s,%s,%s,"%s",\n' % (var,mip,expt,path,pci.product,pci.reason) )
      if pci.product == 'split':
        if len( pci.output1_files ) == 0:
          print tab,' ***** NO FILES FOUND'
        else:
          print tab,'    --> output1: %s .... %s' % (pci.output1_files[0],pci.output1_files[-1])
    else:
      print tab,'FAILED:: ',pci.status,':: ',var,',',mip,',',expt
      oo.write( '%s,%s,%s,%s,%s,"%s",\n' % (var,mip,expt,path,'FAILED',pci.status) )
  else:
    if pci.find_product( var, mip, expt,model,path,startyear=startyear, verbose=verbose):
      print tab,var,',',mip,',',expt,path,startyear,':: ',pci.product, pci.reason 
      oo.write( '%s,%s,%s,%s,%s,,%s%s,"%s",\n' % (var,mip,expt,path,startyear,endyear,pci.product,pci.reason) )
    else:
      print tab,'FAILED:: ',pci.status,':: ',var,',',mip,',',expt
      oo.write( '%s,%s,%s,%s,%s,%s,%s,"%s",\n' % (var,mip,expt,path,startyear,endyear,'FAILED',pci.status) )
  if pci.warning != '':
     print tab, 'WARNING:: ', pci.warning

oo = open( 'test_p_cmip5_out.csv', 'w' )


for var in ['tas','pr','ua']:
  for mip in ['3hr','day']:
    test( var, mip, 'rcp45',startyear=2050,endyear=2050, path='./tmp/a_2010_2020' )

path = './tmp/tas/r2p1i1/'
path3 = './tmp/tas/r3p1i1/'
verbose = False
test( 'tas', '3hr', 'rcp45', startyear=2090, endyear=2090, path='./tmp/a_2010_2020', verbose=True )
test( 'tas', '3hr', 'rcp60', startyear=2090, endyear=2090, path='./tmp/a_2010_2020', verbose=True )
print '3d aero field'
test( 'sconcdust', 'aero', 'rcp85', startyear=2090, endyear=2090, path='./tmp/a_2010_2020', verbose=True )
test( 'rhs', 'day', 'historical', path='./tmp/a_2005_2100', verbose=verbose )
test( 'rhs', 'day', 'historicalxxx', path='./tmp/a_2005_2100', verbose=verbose )
test( 'rhs', 'day', 'historical', path='./tmp/a_1930_2000', verbose=verbose )
test( 'rhs', 'day', 'historical', path='./tmp/a_1930_2000', verbose=verbose, pci=pc2 )
test( 'rhs', 'day', 'piControl', path='./tmp/a_1930_2000', verbose=verbose )
print 'test using sample_2.ini, in which there is a 30 year offset between dating in historical and piControl'
test( 'rhs', 'day', 'piControl', path='./tmp/a_1930_2000', verbose=verbose, pci=pc2 )
test( 'tas', '3hr', 'piControl', path='./tmp/a_2005_2100')
test( 'tas', '3hr', 'historical', startyear=1990, endyear=1990, path='./tmp/a_2010_2020' )
test( 'tasxx', '3hr', 'rcp45', startyear=2090, endyear=2090 )
test( 'intpdiaz', 'Omon', 'rcp45',startyear=2050,endyear=2050, path='./tmp/a_2010_2020' )
test( 'intpp', 'Omon', 'rcp45',startyear=2050,endyear=2050, path='./tmp/a_2010_2020' )
test( 'sconcno3', 'aero', 'piControl', startyear=2050,endyear=2050, path='./tmp/a_2010_2020' )
test( 'ta', '6hrPlev', 'midHolocene', path='./tmp/a_2010_2020' )
test( 'ta', '6hrPlev', 'midHolocene', path='./tmp/a_2005_2100' )
test( 'emioa', 'aero', 'decadal2005', path='./tmp/a_2005_2100' )
test( 'sconcnh4', 'aero', 'decadal2005', path='./tmp/a_2005_2100' )
test( 'sconcnh4', 'aero', 'decadal2005', startyear=2010, path='./tmp/a_2005_2100' )
test( 'sconcnh4', 'aero', 'decadal2005', startyear=2015, path='./tmp/a_2005_2100' )
test( 'sconcnh4', 'aero', 'decadal2005', startyear=2045, path='./tmp/a_2005_2100' )
test( 'sconcnh4', 'aero', 'decadal2001', path='./tmp/a_2005_2100' )
print 'cfMon, section 1'
test( 'rlu', 'cfMon', 'amip', startyear=2000, endyear=2000, path='./tmp/a_1930_2000' )
print 'cfMon, section 2'
test( 'rlut4co2', 'cfMon', 'amip', startyear=2000, endyear=2000, path='./tmp/a_1930_2000' )
print 'cfMon, section 3'
test( 'rlu4co2', 'cfMon', 'amip', startyear=2000, endyear=2000, path='./tmp/a_1930_2000' )
test( 'rlu4co2', 'cfMon', 'piControl', startyear=2000, endyear=2000, path='./tmp/a_2010_2020' )
print 'cfMon, section 4'
test( 'clisccp', 'cfMon', 'amip', startyear=2000, endyear=2000, path='./tmp/a_2010_2020' )
test( 'clisccp', 'cfMon', 'piControl', startyear=2000, endyear=2000, path='./tmp/a_2010_2020' )
test( 'clisccp', 'cfMon', 'abrupt4xco2', startyear=2000, endyear=2000, path='./tmp/a_2010_2020' )
