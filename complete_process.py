#!/usr/bin/python
#INPUT THE FULL PATH AND MTL.TXT FILENAME
#User enters the entire path with the filename of the MLT file
#Example DNtoTOAref_Landsat.py C:\\RDSS\\LandsatFiles\\L5035038_03820070519_MTL.txt

#Must have the following python libraries:
#osgeo or gdal
#numpy
#scipy

from osgeo import gdal
import numpy
import sys
import os.path
import os
import datetime
from scipy import weave
from scipy.weave import converters


create_layer_for_vector = True
create_satvi = True
L = 0.1
create_evi_ndvi = True
create_TC = True
create_Till = True
CleanUp = True

print sys.argv[1]

tryval = True
if tryval == True:
#try:
  #extract file information
  fileroot=sys.argv[1].split('_MTL.txt')[0]
  print fileroot
  filebase=fileroot.split('\\')[-1]
  dir1='\\'.join(fileroot.split('\\')[:-1])
  outrootdir=dir1+'\\processed\\'
  
  #Create processed directory, if it doesn't exist
  if os.path.exists(outrootdir) == 0:
    os.mkdir(outrootdir)
  outroot=outrootdir+filebase

  print filebase
  #Determine if it is Landsat 5 or 7
  Landsat = int(filebase[1])
  if Landsat == 5 or Landsat == 4:
    totbands = 7
    locb7 = 6
  elif Landsat == 7:
    totbands = 8
    locb7 = 7

  #Extract coefs, DOY, and sun_elevation from MTL
  lmax= numpy.zeros((totbands),float)
  lmin= numpy.zeros((totbands),float)
  print "outroot", outroot
  print "fileroot", fileroot
  print "Landsat", Landsat

  #open and read MLT file
  f = open(sys.argv[1],'r')
  attribs = f.readlines()
  print len(attribs)
  rad_finished = False
  lmax_finished = False
  lmin_finished = False
  for ilines in attribs:
    if 'ACQUISITION_DATE = ' in ilines:
      adate = ilines.split('=')[1][1:11]
      print "adate", adate
    elif 'SUN_ELEVATION = ' in ilines:
      sun_elev_deg = float(ilines.split('=')[1][0:11])
      print "sun_elev_deg", sun_elev_deg
    elif 'LMAX_BAND7 = ' in ilines and lmax_finished == False:
      lmax[locb7] = float(ilines.split('=')[1])
      print "lmax[locb7]", lmax[locb7]
      lmax_finished = True
    elif 'LMIN_BAND7 = ' in ilines and lmin_finished == False:
      lmin[locb7] = float(ilines.split('=')[1])
      print "lmin[locb7]", lmin[locb7]
      lmin_finished = True
  DOYfromdate = datetime.datetime(int(adate.split('-')[0]),int(adate.split('-')[1]),int(adate.split('-')[2])).timetuple().tm_yday
  print 'DOYfromdate', DOYfromdate
  for inum in range(len(attribs)):
    if 'GROUP = MIN_MAX_RADIANCE' in attribs[inum] and rad_finished == False:
      for jnum in range(totbands-1):
        lmax[jnum] = float(attribs[inum+1+jnum*2].split('=')[1])
        lmin[jnum] = float(attribs[inum+1+jnum*2+1].split('=')[1])
      rad_finished = True
else:
#except:
  print "File or file path provided is not valid."
  sys.exit()

#Calculate angles
sun_zen_deg = 90.0 - sun_elev_deg
theta = numpy.pi * sun_zen_deg / 180.0

#Open file handles
bluebandf=fileroot+'_B10.TIF'
fo_blue=gdal.Open(bluebandf)

greenbandf=fileroot+'_B20.TIF'
fo_green=gdal.Open(greenbandf)
 
redbandf=fileroot+'_B30.TIF'
fo_red=gdal.Open(redbandf)

nirbandf=fileroot+'_B40.TIF'
fo_nir=gdal.Open(nirbandf)

swirbandf=fileroot+'_B50.TIF'
fo_swir=gdal.Open(swirbandf)
proj = fo_swir.GetProjection()
gt = fo_swir.GetGeoTransform()
nx = fo_swir.RasterXSize
ny = fo_swir.RasterYSize

if Landsat == 5 or Landsat == 4:
  swir2bandf=fileroot+'_B70.TIF'
  fo_swir2=gdal.Open(swir2bandf)
  therbandf=fileroot+'_B60.TIF'
  fo_ther=gdal.Open(therbandf)
  fh_array = [fo_blue, fo_green, fo_red, fo_nir, fo_swir, fo_swir2, fo_ther]
  thermal_array = [False, False, False, False, False, False, True]
  nbo=7
elif Landsat == 7:
  swir2bandf=fileroot.split('L71')[0]+'L72'+fileroot.split('L71')[1]+'_B70.TIF'
  fo_swir2=gdal.Open(swir2bandf)
  therbandf=fileroot+'_B61.TIF'
  fo_ther=gdal.Open(therbandf)
  therbandf2=fileroot.split('L71')[0]+'L72'+fileroot.split('L71')[1]+'_B62.TIF'
#  therbandf2=fileroot+'_B62.TIF'
  fo_ther2=gdal.Open(therbandf2)
  fh_array = [fo_blue, fo_green, fo_red, fo_nir, fo_swir, fo_swir2, fo_ther, fo_ther2]
  thermal_array = [False, False, False, False, False, False, True, True]
  nbo=8

nx60 = fo_ther.RasterXSize
ny60 = fo_ther.RasterYSize
if (nx60 == nx) and (ny60 == ny):
  Thermal30 = True
  print "******30 m thermal data"
  if nx % 2 > 0:
    nx = nx - 1
  if ny % 2 > 0:
    ny = ny - 1
  nx60 = nx
  ny60 = ny
else:
  Thermal30 = False
  if nx % 2 > 0:
    nx = nx - 1
  if ny % 2 > 0:
    ny = ny - 1
  nx60 = int(numpy.floor(float(nx)/2.0))
  ny60 = int(numpy.floor(float(ny)/2.0))

print "30 m dimensions",nx, ny
print "60 m dimensions",nx60, ny60

#Read in/write out data in segments
approxsegsize = long(round(5000000/nx))
#Force the segsize to be even, to help with the conversion of 60m data
if approxsegsize % 2 == 0:
  segsize=approxsegsize
else:
  segsize=approxsegsize-1
segments=int(numpy.floor(ny/float(segsize)))
if ny % segsize > 0:
  segments=segments+1
firstseg=0
lastseg=segments

print segsize, segments, firstseg, lastseg

nyo=ny
nxo=nx

#Landsat 5 from header 
if Landsat == 5:
  #From RSE 113 (2009) 893-903; Chander et al.
  E = [1983, 1796, 1536, 1031, 220.0, 83.44]
  #Tasseled Cap From http://www.sjsu.edu/faculty/watkins/tassel.htm
  TCCb = [0.3037, 0.2793, 0.4343, 0.5585, 0.5082, 0.1863]
  TCCg = [-0.2848, -0.2435, -0.5436, 0.7243, 0.0840, -0.1800]
  TCCw = [0.1509, 0.1793, 0.3299, 0.3406, -0.7112, -0.4572]
elif Landsat == 7:
  #Landsat 7 from header/Chander et al. (High Gain)
  #Landsat 7
  E = [1997, 1812, 1533, 1039, 230.8, 84.90]
  #Tasseled Cap From USGS Huang et al. 
  TCCb = [0.3561, 0.3972, 0.3904, 0.6966, 0.2286, 0.1596]
  TCCg = [-0.3344, -0.3544, -0.4556, 0.6966, -0.0242, -0.2630]
  TCCw = [0.2626, 0.2141, 0.0926, 0.0656, -0.7629, -0.5388]
elif Landsat == 4:
  #From RSE 113 (2009) 893-903; Chander et al.
  E = [1983, 1795, 1539, 1028, 219.8, 83.49]
  #Tasseled Cap From http://www.sjsu.edu/faculty/watkins/tassel.htm
  TCCb = [0.3037, 0.2793, 0.4343, 0.5585, 0.5082, 0.1863]
  TCCg = [-0.2848, -0.2435, -0.5436, 0.7243, 0.0840, -0.1800]
  TCCw = [0.1509, 0.1793, 0.3299, 0.3406, -0.7112, -0.4572]

#ALTERNATIVES FOR 4 and 5 ARE HERE http://arsc.arid.arizona.edu/resources/image_processing/vegetation/indices.html



#Thermal coefficients
K1 = 666.09	#from Chander et al. 2009
K2 = 1282.71	#from Chander et al. 2009

gaincoef = numpy.zeros((len(lmax)))
offcoef = numpy.zeros((len(lmax)))

for i in range(len(lmax)):
  gaincoef[i] = (lmax[i] - lmin[i])/255.0
  offcoef[i] = lmin[i]

print "gain",gaincoef
print "offset",offcoef

#Re-order the gaincoef and offcoef to match fh_array
#B, G, R, N, S1, T1, (T2), S2
#B, G, R, N, S1, S2, T1, (T2)
if Landsat == 5 or Landsat == 4:
  ogaincoef = gaincoef[[0,1,2,3,4,6,5]]
  ooffcoef = offcoef[[0,1,2,3,4,6,5]]
elif Landsat == 7:
  ogaincoef = gaincoef[[0,1,2,3,4,7,5,6]]
  ooffcoef = offcoef[[0,1,2,3,4,7,5,6]]


#ratio of mean sun-earth distance
#(this cancels out for NDVI, but should be used for TOA reflectance
#of individual bands)
d = (1.0 - 0.016729 * numpy.cos(numpy.pi* 0.9856 * (DOYfromdate -4.0)/180.0))


print "E", E
print "Lmax", lmax
print "Lmin", lmin
print "d", d


FORMAT = 'GTiff'
DATATYPE = gdal.GDT_Int16
OPTIONS = []
YSIZE = ny
XSIZE = nx
NBANDS = nbo

outfilenameTOA=outroot+'_TOAref_wthermal.tif'
outfilenameTOAg=outroot+'_TOAref_wthermal_g.tif'
driver = gdal.GetDriverByName(FORMAT)
tfh = driver.Create(outfilenameTOA, XSIZE, YSIZE, NBANDS, DATATYPE, OPTIONS)
tfh.SetProjection(proj)
tfh.SetGeoTransform(gt)

if create_layer_for_vector == True:
  FORMAT = 'GTiff'
  DATATYPE = gdal.GDT_Int16
  OPTIONS = []
  YSIZE = ny
  XSIZE = nx
  NBANDS = 1

  outfilename=outroot+'_for_vector.tif'
  driver = gdal.GetDriverByName(FORMAT)
  tvfh = driver.Create(outfilename, XSIZE, YSIZE, NBANDS, DATATYPE, OPTIONS)
  tvfh.SetProjection(proj)
  tvfh.SetGeoTransform(gt)
  tvband = tvfh.GetRasterBand(1)

if create_satvi == True:
  FORMAT = 'GTiff'
  DATATYPE = gdal.GDT_Int16
  OPTIONS = []
  YSIZE = ny
  XSIZE = nx
  NBANDS = 1

  outfilenameS=outroot+'_satvi.tif'
  outfilenameSg=outroot+'_satvi_g.tif'
  driver = gdal.GetDriverByName(FORMAT)
  tsfh = driver.Create(outfilenameS, XSIZE, YSIZE, NBANDS, DATATYPE, OPTIONS)
  tsfh.SetProjection(proj)
  tsfh.SetGeoTransform(gt)
  tsband = tsfh.GetRasterBand(1)

if create_evi_ndvi == True:
  FORMAT = 'GTiff'
  DATATYPE = gdal.GDT_Int16
  OPTIONS = []
  YSIZE = ny
  XSIZE = nx
  NBANDS = 2

  outfilenameEN=outroot+'_evi_ndvi.tif'
  outfilenameENg=outroot+'_evi_ndvi_g.tif'
  driver = gdal.GetDriverByName(FORMAT)
  tenfh = driver.Create(outfilenameEN, XSIZE, YSIZE, NBANDS, DATATYPE, OPTIONS)
  tenfh.SetProjection(proj)
  tenfh.SetGeoTransform(gt)
  tenband = tenfh.GetRasterBand(1)
  tenband2 = tenfh.GetRasterBand(2)

if create_TC == True:
  FORMAT = 'GTiff'
  DATATYPE = gdal.GDT_Int16
  OPTIONS = []
  YSIZE = ny
  XSIZE = nx
  NBANDS = 3

  outfilenameTC=outroot+'_tasseled.tif'
  outfilenameTCg=outroot+'_tasseled_g.tif'
  driver = gdal.GetDriverByName(FORMAT)
  tTCfh = driver.Create(outfilenameTC, XSIZE, YSIZE, NBANDS, DATATYPE, OPTIONS)
  tTCfh.SetProjection(proj)
  tTCfh.SetGeoTransform(gt)
  tTCband = tTCfh.GetRasterBand(1)
  tTCband2 = tTCfh.GetRasterBand(2)
  tTCband3 = tTCfh.GetRasterBand(3)

if create_Till == True:
  FORMAT = 'GTiff'
  DATATYPE = gdal.GDT_Int16
  OPTIONS = []
  YSIZE = ny
  XSIZE = nx
  NBANDS = 3

  outfilenameTill=outroot+'_tillage.tif'
  outfilenameTillg=outroot+'_tillage_g.tif'
  driver = gdal.GetDriverByName(FORMAT)
  tTillfh = driver.Create(outfilenameTill, XSIZE, YSIZE, NBANDS, DATATYPE, OPTIONS)
  tTillfh.SetProjection(proj)
  tTillfh.SetGeoTransform(gt)
  tTillband = tTillfh.GetRasterBand(1)
  tTillband2 = tTillfh.GetRasterBand(2)
  tTillband3 = tTillfh.GetRasterBand(3)

# C code to handle transition from 60 m to 30 m for Thermal Bands
code = """
	int i, j;
        int y30, x30;
        for (j=0;j<uny60;j++) {
          y30 = j*2;
          for (i=0;i<unx60;i++) {
            x30 = i*2;
            outdata(y30,x30) = banddata_toar(j,i);
            outdata(y30+1,x30) = banddata_toar(j,i);
            outdata(y30+1,x30+1) = banddata_toar(j,i);
            outdata(y30,x30+1) = banddata_toar(j,i);
          }
        }
	#"""

for iseg in range(firstseg,lastseg):
  startval=iseg*segsize
  endval=iseg*segsize+segsize
  usesegsize = segsize
  if endval > ny:
    #Should be ny-startval-1 or just ny-startval
    usesegsize = ny-startval-1
    if usesegsize % 2 > 0:
      usesegsize = usesegsize - 1

  print iseg+1, " of ",segments, " segment(s)"
  segcount=0
  if Thermal30 == True:
    for jband in range(len(fh_array)):
      banddata = fh_array[jband].ReadAsArray(0,startval,nx,usesegsize).astype(float)
      banddata_rad = banddata*ogaincoef[jband]+ooffcoef[jband]
      ibanddata = numpy.zeros((usesegsize,nx),int)
      if thermal_array[jband] == False:
        banddata_toar = d**2 * numpy.pi * banddata_rad/(E[jband]*numpy.cos(theta))
        ibanddata[:,:] = numpy.round(banddata_toar[:,:] * 10000)
      elif thermal_array[jband] == True:
        banddata_toar = K2 / numpy.log(K1/banddata_rad + 1.0)      
        ibanddata[:,:] = numpy.round((banddata_toar[:,:] - 273.15) * 100)
      tband = tfh.GetRasterBand(jband+1)
      tband.WriteArray(ibanddata,0,startval)
      if (create_satvi == True or create_evi_ndvi == True or create_TC == True) and jband == 2:
        red = banddata_toar
      elif (create_evi_ndvi == True or create_TC == True or create_Till == True) and jband == 0:
        blue = banddata_toar
      elif (create_evi_ndvi == True or create_TC == True) and jband == 3:
        nir = banddata_toar
      elif (create_satvi == True or create_TC == True or create_Till == True) and jband == 4:
        swir1 = banddata_toar
      elif (create_satvi == True or create_TC == True or create_Till == True) and jband == 5:
        swir2 = banddata_toar
      elif (create_TC == True or create_Till == True) and jband == 1:
        green = banddata_toar
  else:
    for jband in range(len(fh_array)):
      if thermal_array[jband] == False:
        banddata = fh_array[jband].ReadAsArray(0,startval,nx,usesegsize).astype(float)
        banddata_rad = banddata*ogaincoef[jband]+ooffcoef[jband]
        ibanddata = numpy.zeros((usesegsize,nx),int)
        banddata_toar = d**2 * numpy.pi * banddata_rad/(E[jband]*numpy.cos(theta))
        ibanddata[:,:] = numpy.round(banddata_toar[:,:] * 10000)
        tband = tfh.GetRasterBand(jband+1)
        tband.WriteArray(ibanddata,0,startval)
      elif thermal_array[jband] == True:
        unx60 = int(nx60)
        uny60 = int(numpy.floor(usesegsize/2.0))
        #Will this skip a value?
        startval60 = int(numpy.floor(startval/2.0))
#        print iseg+1, jband, unx60, uny60, startval60, nx, usesegsize, startval
        banddata = fh_array[jband].ReadAsArray(0,startval60,unx60,uny60).astype(float)
        banddata_rad = banddata*ogaincoef[jband]+ooffcoef[jband]
        banddata_toar = K2 / numpy.log(K1/banddata_rad + 1.0)      
        outdata = numpy.zeros((uny60*2,unx60*2),float)
#        outdata = numpy.zeros((usesegsize,nx),float)
        weave.inline(code, ['banddata_toar', 'outdata', 'uny60', 'unx60'], \
		     type_converters=converters.blitz, verbose=0)
      #HOW DO WE CONVERT TO 30 M?
        ioutdata = numpy.zeros((uny60*2,unx60*2),int)
#        ioutdata = numpy.zeros((usesegsize,nx),int)
        ioutdata[:,:] = numpy.round((outdata[:,:] - 273.15) * 100)
        tband = tfh.GetRasterBand(jband+1)
        tband.WriteArray(ioutdata,0,startval)
      if (create_satvi == True or create_evi_ndvi == True or create_TC == True) and jband == 2:
        red = banddata_toar
      elif (create_evi_ndvi == True or create_TC == True or create_Till == True) and jband == 0:
        blue = banddata_toar
      elif (create_evi_ndvi == True or create_TC == True) and jband == 3:
        nir = banddata_toar
      elif (create_satvi == True or create_TC == True or create_Till == True) and jband == 4:
        swir1 = banddata_toar
      elif (create_satvi == True or create_TC == True or create_Till == True) and jband == 5:
        swir2 = banddata_toar
      elif (create_TC == True or create_Till == True) and jband == 1:
        green = banddata_toar

  if create_satvi == True:
    (m,n) = numpy.where((red > 0.0) & (swir1 > 0.0) & (swir2 > 0.0))
    satvi = numpy.zeros((usesegsize,nx),float)
    satvi[m,n] = (1.0 + L) * (swir1[m,n] - red[m,n]) / (swir1[m,n] + red[m,n] + L) - swir2[m,n]/2.0
    isatvi = numpy.zeros((usesegsize,nx),int)
    isatvi[:,:] = numpy.round(satvi[:,:]*10000.0)
    tsband.WriteArray(isatvi,0,startval)

  if create_evi_ndvi == True:
    (m,n) = numpy.where((red > 0.0) & (nir > 0.0) & (blue > 0.0))
    evi = numpy.zeros((usesegsize,nx),float)
    ndvi = numpy.zeros((usesegsize,nx),float)
    evi[m,n] = 2.5 * (nir[m,n] - red[m,n]) / (nir[m,n] + 6.0 * red[m,n] - 7.5 * blue[m,n] + 1.0)
    ndvi[m,n] = (nir[m,n] - red[m,n]) / (nir[m,n] + red[m,n])
    ievi = numpy.zeros((usesegsize,nx),int)
    indvi = numpy.zeros((usesegsize,nx),int)
    ievi[:,:] = numpy.round(evi[:,:]*10000.0)
    indvi[:,:] = numpy.round(ndvi[:,:]*10000.0)
    tenband.WriteArray(ievi,0,startval)
    tenband2.WriteArray(indvi,0,startval)

  if create_TC == True:
    (m,n) = numpy.where((red > 0.0) & (nir > 0.0) & (blue > 0.0) & (green > 0.0) & (swir1 > 0) & (swir2 > 0))
    brightness = numpy.zeros((usesegsize,nx),float)
    greenness = numpy.zeros((usesegsize,nx),float)
    wetness = numpy.zeros((usesegsize,nx),float)
    brightness[m,n] = TCCb[0] * blue[m,n] + TCCb[1] * green[m,n] + TCCb[2] * red[m,n] + TCCb[3] * nir[m,n] + TCCb[4] * swir1[m,n] + TCCb[5] * swir2[m,n]
    greenness[m,n] = TCCg[0] * blue[m,n] + TCCg[1] * green[m,n] + TCCg[2] * red[m,n] + TCCg[3] * nir[m,n] + TCCg[4] * swir1[m,n] + TCCg[5] * swir2[m,n]
    wetness[m,n] = TCCw[0] * blue[m,n] + TCCw[1] * green[m,n] + TCCw[2] * red[m,n] + TCCw[3] * nir[m,n] + TCCw[4] * swir1[m,n] + TCCw[5] * swir2[m,n]
    ibrightness = numpy.zeros((usesegsize,nx),int)
    igreenness = numpy.zeros((usesegsize,nx),int)
    iwetness = numpy.zeros((usesegsize,nx),int)
    ibrightness[:,:] = numpy.round(brightness[:,:]*10000.0)
    igreenness[:,:] = numpy.round(greenness[:,:]*10000.0)
    iwetness[:,:] = numpy.round(wetness[:,:]*10000.0)
    tTCband.WriteArray(ibrightness,0,startval)
    tTCband2.WriteArray(igreenness,0,startval)
    tTCband3.WriteArray(iwetness,0,startval)

  if create_Till == True:
    (m,n) = numpy.where((blue > 0.0) & (green > 0.0) & (swir1 > 0) & (swir2 > 0))
    CRC = numpy.zeros((usesegsize,nx),float)
    CRCm = numpy.zeros((usesegsize,nx),float)
    NDTI = numpy.zeros((usesegsize,nx),float)
    CRC[m,n] = (swir1[m,n] - blue[m,n]) / (swir1[m,n] + blue[m,n])
    CRCm[m,n] = (swir1[m,n] - green[m,n]) / (swir1[m,n] + green[m,n])
    NDTI[m,n] = (swir1[m,n] - swir2[m,n]) / (swir1[m,n] + swir2[m,n])
    iCRC = numpy.zeros((usesegsize,nx),int)
    iCRCm = numpy.zeros((usesegsize,nx),int)
    iNDTI = numpy.zeros((usesegsize,nx),int)
    iCRC[:,:] = numpy.round(CRC[:,:]*10000.0)
    iCRCm[:,:] = numpy.round(CRCm[:,:]*10000.0)
    iNDTI[:,:] = numpy.round(NDTI[:,:]*10000.0)
    tTillband.WriteArray(iCRC,0,startval)
    tTillband2.WriteArray(iCRCm,0,startval)
    tTillband3.WriteArray(iNDTI,0,startval)

  if create_layer_for_vector == True:
    zerosdata = numpy.zeros((usesegsize,nx),int)
    tvband.WriteArray(zerosdata,0,startval)

tfh = None

for jband in range(len(fh_array)):
  fh_array[jband] = None

if create_layer_for_vector == True:
  tvfh = None

if create_satvi == True:
  tsfh = None

if create_evi_ndvi == True:
  tenfh = None

if create_TC == True:
  tTCfh = None

if create_Till == True:
  tTillfh = None

if CleanUp == True:
    print 'Compressing files ...'
    cmd = 'gdal_translate -co "compress=lzw" ' + outfilenameTOA + ' ' + outfilenameTOAg
    status = os.system(cmd)
    if status > 0:
      print '*****Trouble with compressing TOA****'
    else:
      if create_satvi == True:
        trouble = False
        cmd2 = 'gdal_translate -co "compress=lzw" ' + outfilenameS + ' ' + outfilenameSg
        status2 = os.system(cmd2)
        if status2 > 0:
          print '*****Trouble with compressing SATVI****'
          trouble = True
      if create_evi_ndvi == True and trouble == False:
        cmd3 = 'gdal_translate -co "compress=lzw" ' + outfilenameEN + ' ' + outfilenameENg
        status3 = os.system(cmd3)
        if status3 > 0:
          print '*****Trouble with compressing EVI NDVI****'
      if create_TC == True and trouble == False:
        cmd4 = 'gdal_translate -co "compress=lzw" ' + outfilenameTC + ' ' + outfilenameTCg
        status4 = os.system(cmd4)
        if status4 > 0:
          print '*****Trouble with compressing TC****'
      if create_Till == True and trouble == False:
        cmd5 = 'gdal_translate -co "compress=lzw" ' + outfilenameTill + ' ' + outfilenameTillg
        status5 = os.system(cmd5)
        if status5 > 0:
          print '*****Trouble with compressing Till****'

    print 'Removing old files ...'
    cmd = 'del ' + outfilenameTOA
    status = os.system(cmd)
    if status > 0:
      print '*****Trouble with removing TOA****'
    else:
      if create_satvi == True:
        trouble = False
        cmd2 = 'del ' + outfilenameS
        status2 = os.system(cmd2)
        if status2 > 0:
          print '*****Trouble with removing SATVI****'
          trouble = True
      if create_evi_ndvi == True and trouble == False:
        cmd3 = 'del ' + outfilenameEN
        status3 = os.system(cmd3)
        if status3 > 0:
          print '*****Trouble with removing EVI NDVI****'
      if create_TC == True and trouble == False:
        cmd4 = 'del ' + outfilenameTC
        status4 = os.system(cmd4)
        if status4 > 0:
          print '*****Trouble with removing TC****'
      if create_Till == True and trouble == False:
        cmd5 = 'del ' + outfilenameTill
        status5 = os.system(cmd5)
        if status5 > 0:
          print '*****Trouble with removing Till****'
