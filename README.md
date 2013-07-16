# Landsat 8 Scene Processing
### Developing RGB, NDVI, EVI, and SATV


#### Landsat 8 Info
Landsat 8 was launched Febuary 11, 2013 to fill the data gap left by Landsat4/5(RIP) and the partially functioning Landsat 7.  Landsat 8 
provides 11 bands ranging in spectrums from visible light, near infrared, and to thermal energy.

|Band #   |Purpose                                |Resolution  |
|---------|:-------------------------------------:|-----------:|
|1        |Coastal/Aerosol: Deep Blues\Violets    |30m	       |
|2        |Visible Light: Blue                    |30m	       |
|3        |Visible Light: Green                   |30m	       |
|4        |Visible Light: Red                     |30m	       |
|5        |Near Infrared NIR: Vegetation          |30m	       |
|6        |Shortwave Infrared SWIR: Soils\Geology |30m	       |
|7        |Shortwave Infrared SWIR: Soils\Geology |30m	       |
|8        |Panchromatic: RGB Together             |15m	       |
|9	  |High Reflectivity: Cirrus Clouds	  |30m         |
|10       |Thermal Infrared TIRS 1: Heat    	  |100m	       |
|11       |Thermal Infrared TIRS 2: Heat    	  |100m	       |

_Sources:_

[Mapbox: Putting Landsat 8 Bands to Work](http://www.mapbox.com/blog/putting-landsat-8-bands-to-work/)
[USGS: Landsat Data Product](http://landsat.usgs.gov/LDCM_DataProduct.php)
[USGS: Landsat Band Desigination](http://landsat.usgs.gov/band_designations_landsat_satellites.php)
[NASA: Landsat DCM](http://ldcm.gsfc.nasa.gov/index.html)


#### Downloading the Scene Data
1. [USGS: Earth Explorer](http://earthexplorer.usgs.gov/)
2. [USGS: LandsatLook](http://landsatlook.usgs.gov/)
3. [USGS: GLOVIS](http://glovis.usgs.gov)

After the scene has been downloaded, you will have a compressed file ranging from 750mb to a 1gb.
To uncompress the file:

`$ tar -zxvf LC80370372013169LGN00.tar.gz`

The uncompressed bundle produces 13 files: 11 Tiff files for each Band, a BQA Tiff for scene's quality assesment, and a *MTL.txt file with metadata.  The MTL.txt
will be used to complete the calculations in processing a scene correctly.


#### Running the Script
From the terminal, change to the script's directory and use the python interpreter to run the script. Designate the full path of the Landsat's MTL.txt file.

`$ python landsat_proc.py home/landsat/LC80370372013169LGN00_MTL.txt`