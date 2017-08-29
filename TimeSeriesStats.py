## Time_series=group
## Time_series_statistics=name
##ts_layer=raster
##Use_nodata=boolean False
##nodata=Number 0
##output_layer=output_raster

from qgis.core import *
from PyQt4.QtCore import *
from processing.core.GeoAlgorithmExecutionException import GeoAlgorithmExecutionException
import os.path
import numpy
try:
    from osgeo import gdal
except:
    import gdal

def changeFilenameSuffix(fname, suffix):
    root, ext = os.path.splitext(fname)
    return '{}_{}{}'.format(root, suffix, ext)

inlayer = processing.getObject(ts_layer)
if not inlayer.isValid():
    raise GeoAlgorithmExecutionException("Could not open input raster")

nb = inlayer.bandCount()
nl = inlayer.height()
ns = inlayer.width()
fileInfo = QFileInfo(inlayer.dataProvider().dataSourceUri())

fid = gdal.Open( fileInfo.absoluteFilePath(), gdal.GA_ReadOnly)

drv = gdal.GetDriverByName('GTiff')
outDsMinMax = drv.Create( changeFilenameSuffix( str(output_layer), 'minmax'), ns, nl, 2, fid.GetRasterBand(1).DataType, options=['compress=lzw','bigtiff=YES'] )
if outDsMinMax is None:
    raise GeoAlgorithmExecutionException("Error when creating minmax output file")
outDsFloat = drv.Create( changeFilenameSuffix( str(output_layer), 'float'), ns, nl, 2, gdal.GDT_Float32, options=['compress=lzw','bigtiff=YES'] )
if outDsFloat is None:
    raise GeoAlgorithmExecutionException("Error when creating float output file")

outDsMinMax.SetProjection( fid.GetProjection() )
outDsMinMax.SetGeoTransform( fid.GetGeoTransform() )
outDsFloat.SetProjection( fid.GetProjection() )
outDsFloat.SetGeoTransform( fid.GetGeoTransform() )

process=0
for il in xrange(nl):
    if int(100*il/nl) - process >= 10:
        process = int(100*il/nl)
        QgsMessageLog.logMessage('{} %'.format(process), 'TimeSeriesStats', QgsMessageLog.INFO)
    data = numpy.zeros( (ns, nb) )
    for ib in range(nb):
        data[:, ib] = numpy.ravel( fid.GetRasterBand(ib+1).ReadAsArray(0, il, ns, 1) )
        
    if Use_nodata:
        wtp = numpy.full((ns, nb), True, dtype=bool)
        thisMin = numpy.zeros(ns) + nodata
        thisMax = numpy.zeros(ns) + nodata
        thisMean = numpy.zeros(ns) + nodata
        thisStd = numpy.zeros(ns) + nodata
        for ii in xrange(ns):
            wtp = data[ii, :] != nodata
            if wtp.any():
                thisMin[ii] = data[ii, wtp].min()
                thisMax[ii] = data[ii, wtp].max()
                thisMean[ii] = data[ii, wtp].mean()
                thisStd[ii] = data[ii, wtp].std()
    else:
        thisMin = numpy.min(data, 1)
        thisMax = numpy.max(data, 1)
        thisMean = numpy.mean(data, 1)
        thisStd = numpy.std(data, 1)
        
    outDsMinMax.GetRasterBand(1).WriteArray( thisMin.reshape(1, -1), 0, il )
    outDsMinMax.GetRasterBand(2).WriteArray( thisMax.reshape(1, -1), 0, il )
    outDsFloat.GetRasterBand(1).WriteArray( thisMean.reshape(1, -1), 0, il )
    outDsFloat.GetRasterBand(2).WriteArray( thisStd.reshape(1, -1), 0, il )


QgsMessageLog.logMessage('Processing done', 'TimeSeriesStats', QgsMessageLog.INFO)

