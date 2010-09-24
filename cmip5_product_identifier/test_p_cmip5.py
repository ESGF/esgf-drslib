#!/usr/bin/python

import p_cmip5_v4 as p

def test(var, mip, expt,startyear=2050,endyear=2050,path = '/tmp'  ):
    model = 'HADCM3'
    if pc.find_product( var, mip, expt,model,path,startyear=startyear,endyear=endyear):
      print var,',',mip,',',expt,startyear,endyear,':: ',pc.product, pc.reason 
      oo.write( '%s,%s,%s,%s,%s,%s,"%s",\n' % (var,mip,expt,startyear,endyear,pc.product,pc.reason) )
    else:
      print 'FAILED:: ',pc.status,':: ',var,',',mip,',',expt
      oo.write( '%s,%s,%s,%s,%s,%s,"%s",\n' % (var,mip,expt,startyear,endyear,'FAILED',pc.status) )

oo = open( 'test_p_cmip5_out.csv', 'w' )
pc = p.cmip5_product()
for var in ['tas','pr','ua']:
  for mip in ['3hr','day']:
    test( var, mip, 'rcp45',startyear=2050,endyear=2050 )

path = './tmp/tas/r2p1i1/'
path3 = './tmp/tas/r3p1i1/'
test( 'tas', '3hr', 'rcp45', startyear=2090, endyear=2090 )
test( 'tas', '3hr', 'piControl', startyear=2090, endyear=2090, path=path )
test( 'tas', '3hr', 'piControl', startyear=2090, endyear=2090, path=path3 )
test( 'tas', '3hr', 'historical', startyear=1990, endyear=1990 )
test( 'intpdiaz', 'Omon', 'rcp45',startyear=2050,endyear=2050 )
test( 'intpp', 'Omon', 'rcp45',startyear=2050,endyear=2050 )
test( 'sconcno3', 'aero', 'piControl', startyear=2050,endyear=2050 )
test( 'rlu', 'cfMon', 'AMIP', startyear=2000, endyear=2000 )
