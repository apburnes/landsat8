#!/usr/bin/python

#Input the path and the file name to execute the script.
#IE: landsat_proc.py ~/share/landsat/L5035038_03820070519_MTL.txt

#import the python libraries:

from osgeo import gdal
import numpy as np
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
creat_TC = True
create_Till = True
CleanUp = True

print sys.argv[1]

tryval = True
if tryval == True:
    #Extract file info and setup path names
    fileroot = sys.argv[1].split("_MTL.txt")[0]
    print fileroot
    filebase = fileroot.split('/')[-1]
    dir1='/'.join(fileroot.split('/')[:-1])
    outrootdir = dir1 + '/processed/'

    #Create 'processed directory', if not existing
    if os.path.exists(outrootdir) == 0:
        os.mkdir(outrootdir)
    outroot = outrootdir + filebase

    #Determine the landsat data {5, 7, or 8}
    if int(filebase[2]) == 8:
        totbands = 11;
        locb7 = 7
        Landsat = int(filebase[2])
        file_date = 'FILE_DATE = '
        sun_elevation = 'SUN_ELEVATION = '
        radiance_max_b7 = 'RADIANCE_MAXIMUM_BAND_7 = '
        radiance_min_b7 = 'RADIANCE_MINIMUM_BAND_7 = '
    elif int(filebase[1]) == 5 or 4:
        totbands = 7
        locb7 = 6
        Landsat = int(filebase[1])
        file_date = 'PRODUCT_CREATION_TIME = '
        sun_elevation = 'SUN_ELEVATION = '
        radiance_max_b7 = 'LMAX_BAND7 = '
        radiance_min_b7 = 'LMIN_BAND7 = '
    elif int(filebase[1]) == 7:
        totbands = 8
        locb7 = 7
        Landsat = int(filebase[1])
        file_date = 'PRODUCT_CREATION_TIME = '
        sun_elevation = 'SUN_ELEVATION = '
        radiance_max_b7 = 'LMAX_BAND7 = '
        radiance_min_b7 = 'LMIN_BAND7 = '

    #Extract coefs, DOY, and sun_elevation from MTL
    lmax = np.zeros((totbands), float)
    lmin = np.zeros((totbands), float)
    print "Outroot:", outroot
    print "Fileroot:", fileroot
    print "Landsat:", Landsat

    #open and read MLT file
    f = open(sys.argv[1], 'r')
    attribs = f.readlines()
    print len(attribs)
    
    rad_finished = False
    lmax_finished = False
    lmin_finished = False

    for ilines in attribs:
        if file_date in ilines:
            adate = ilines.split('=')[1][1:11]
            print "Aquistion Date:", adate
        elif sun_elevation in ilines:
            sun_elev_deg = float(ilines.split('=')[1])
            print "Sun Elevation Degree:", sun_elev_deg
        elif radiance_max_b7 in ilines and lmax_finished == False:
            lmax[locb7] = float(ilines.split('=')[1])
            print "L Max [Locb7]:", lmax[locb7]
            lmax_finished = True
        elif radiance_min_b7 in ilines and lmin_finished == False:
            lmin[locb7] = float(ilines.split('=')[1])
            print "L MIN [locb7]:", lmin[locb7]
            lmin_finished = True
        DOYfromdate = datetime.datetime(int(adate.split))
