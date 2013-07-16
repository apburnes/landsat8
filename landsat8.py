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

# Setup file names
fileroot = sys.argv[1].split("_MTL.txt")[0]
filebase = fileroot.split('/')[-1]
dir1='/'.join(fileroot.split('/')[:-1])
outrootdir = dir1 + '/processed/'
print fileroot

#Create 'processed directory', if it does not already exist
if os.path.exists(outrootdir) == 0:
    os.mkdir(outrootdir)
outroot = outrootdir + filebase

# Set metadata MTL variables for verification and data collection
landsat = 'LANDSAT_8'
totbands = 11
locb7 = 7
file_date = 'FILE_DATE = '
sun_elevation = 'SUN_ELEVATION = '
radiance_max_b7 = 'RADIANCE_MAXIMUM_BAND_7 = '
radiance_min_b7 = 'RADIANCE_MINIMUM_BAND_7 = '

#Set bands to respective varables
blueband = fileroot + "_B20.TIF"
greenband = fileroot + "_B30.TIF"
redband = fileroot + "_B40.TIF"
nirband = fileroot + "_B50.TIF"
swir1band = fileroot + "_B60.TIF"
swir2band = fileroot + "_B70.TIF"
panband = fileroot + "_B80.TIF"
cirrusband = fileroot + "_B90.TIF"
tirs1band = fileroot + "_B10.TIF"
tirs2band = fileroot + "_B11.TIF"

# Verify the processed data is from Landsat 8
# Read MTL file for verification
mtl = open(sys.argv[1], 'r')
attribs = mtl.readlines()
print len(attribs)

for ilines in attribs:
    if 'SPACECRAFT_ID = ' in ilines:
        spacecraft_id = ilines.split('=')[1][2:11]
        print spacecraft_id + " is verified."

# Exit system if this is not Landsat 8
if landsat != spacecraft_id:
    print "This is not a Landsat 8 scene and will not be processed. Thank you."
    sys.exit()

print "Landsat 8 scene is now being processed..."

#Extract coefs, DOY, and sun_elevation from MTL
lmax = np.zeros((totbands), float)
lmin = np.zeros((totbands), float)
print "Outroot:", outroot
print "Fileroot:", fileroot

rad_finished = False
lmax_finished = False
lmin_finished = False

#Read and store scene metadata
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

DOYfromdate = datetime.datetime(int(adate.split('-')[0]),int(adate.split('-')[1]),int(adate.split('-')[2])).timetuple().tm_yday
print 'DOY from date: ', DOYfromdate
    
for inum in range(len(attribs)):
    if 'GROUP = MIN_MAX_RADIANCE' in attribs[inum] and rad_finished == False:
        for jnum in range(totbands-1):
            lmax[jnum] = float(attribs[inum+1+jnum*2].split('=')[1])
            lmin[jnum] = float(attribs[inum+1+jnum*2+1].split('=')[1])
        rad_finished = True


