#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Created on Thu Nov  3 11:56:48 2011

The main program. The program takes 3 files as input:
    
    #. The red band (any GDAL-compatible format will do)
    #. the near-infrarred band (again as above)
    #. An output file name
    
dditionally, one can specify the output format. By default, we use  GeoTIFF.


@author: Jose Gómez-Dans (UCL/NCEO) - j.gomez-dans@ucl.ac.uk
"""
import os
import sys
import optparse

import numpy as np

from osgeo import gdal

def calculate_ndvi ( red_filename, nir_filename ):
    """
    A function to calculate the Normalised Difference Vegetation Index
    from red and near infrarred reflectances. The reflectance data ought to
    be present on two different files, specified by the varaibles 
    `red_filename` and `nir_filename`. The file format ought to be
    recognised by GDAL
    """
    
    g_red = gdal.Open ( red_filename )
    red = g_red.ReadAsArray()
    g_nir = gdal.Open ( nir_filename )
    nir = g_nir.ReadAsArray()
    if ( g_red.RasterXSize != g_nir.RasterXSize ) or \
            ( g_red.RasterYSize != g_nir.RasterYSize ):
        print "ERROR: Input datasets do't match!"
        print "\t Red data shape is %dx%d" % ( red.shape )
        print "\t NIR data shape is %dx%d" % ( nir.shape )
        
        sys.exit ( -1 )
    passer = np.logical_and ( red > 1, nir > 1 )
    ndvi = np.where ( passer,  (1.*nir - 1.*red ) / ( 1.*nir + 1.*red ), -999 )
    return ndvi
    
def save_raster ( output_name, raster_data, dataset, driver="GTiff" ):
    """
    A function to save a 1-band raster using GDAL to the file indicated
    by ``output_name``. It requires a GDAL-accesible dataset to collect 
    the projection and geotransform.
    """

    # Open the reference dataset
    g_input = gdal.Open ( dataset )
    # Get the Geotransform vector
    geo_transform = g_input.GetGeoTransform ()
    x_size = g_input.RasterXSize # Raster xsize
    y_size = g_input.RasterYSize # Raster ysize
    srs = g_input.GetProjectionRef () # Projection
    # Need a driver object. By default, we use GeoTIFF
    if driver == "GTiff":
        driver = gdal.GetDriverByName ( driver )
        dataset_out = driver.Create ( output_name, x_size, y_size, 1, \
                gdal.GDT_Float32, ['TFW=YES', \
                'COMPRESS=LZW', 'TILED=YES'] )
    else:
        driver = gdal.GetDriverByName ( driver )
        dataset_out = driver.Create ( output_name, x_size, y_size, 1, \
                gdal.GDT_Float32 )
        
    dataset_out.SetGeoTransform ( geo_transform )
    dataset_out.SetProjection ( srs )
    dataset_out.GetRasterBand ( 1 ).WriteArray ( \
            raster_data.astype(np.float32) )
    dataset_out.GetRasterBand ( 1 ).SetNoDataValue ( float(-999) )
    dataset_out = None

if __name__ == "__main__":
    
    arg_parser = optparse.OptionParser()
    arg_parser.add_option( '-r', '--red', dest="red_fname", \
            help="The RED data" )
    arg_parser.add_option( '-n', '--nir', dest="nir_fname", \
            help="The NIR data" )
    arg_parser.add_option( '-o', '--output', dest="out_fname", \
            help="The output dataset" )
    arg_parser.add_option( '-f', '--format', dest="out_format", \
            default="GTiff", help="Output format" ) 
    options, extra_junk = arg_parser.parse_args ()
                
    if not os.path.exists ( options.red_fname ):
        print "ERROR: The red filename %s does not exist" % options.red_fname
        sys.exit ( -1 )
    if not os.path.exists ( options.nir_fname ):
        print "ERROR: The nir filename %s does not exist" % options.nir_fname
        sys.exit ( -1 )
    if os.path.exists ( options.out_fname):
        print "ERROR: The output filename %s does already exist" % \
            options.out_fname
        print "\t Select a different one, or delete the file."
        sys.exit ( -1 )
        
        
    c_ndvi = calculate_ndvi ( options.red_fname, options.nir_fname )
    save_raster ( options.out_fname, c_ndvi, options.red_fname, \
            driver=options.out_format )
