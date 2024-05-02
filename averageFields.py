import netCDF4
import numpy
import argparse

parser = argparse.ArgumentParser(description='Average times over wrfout file.')
parser.add_argument('-i','--input', help='Input filepath')
parser.add_argument('-o','--output', help='Output filepath')
parser.add_argument('-t','--time', help='Output time-string (format %Y-%m-%d_%H:%M:%S)')

args = parser.parse_args()
inFile  = args.input
outFile = args.output
outputTime = args.time

dimensions = {}
variables = {}
attributes = {}
src = netCDF4.Dataset(inFile)
# Get the dimensions of the file
for name, dim in src.dimensions.items():
    dimlen = len(dim)
    ##
    dimensions[name] = dimlen

# Get the global attributes
attributes['global'] = {a:src.getncattr(a) for a in src.ncattrs()}
# Get the metadata about the variables
for name, var in src.variables.items():
    if '_FillValue' in var.ncattrs():
        fill_value = var.getncattr('_FillValue')
    else:
        fill_value = None
    ##
    variables[name] = {'dtype' : var.dtype, 'dimensions' : var.dimensions, 'fill_value' : fill_value}
    variables[name]['dimlens'] = numpy.array([ dimensions[dim] if dimensions[dim] is not None else 1 for dim in variables[name]['dimensions'] ])
    attributes[name] = {a:var.getncattr(a) for a in var.ncattrs()}


##
variables['Times']['dimlens'][0] = 1
ntimes = dimensions['Time']
fntimes = float(ntimes)
## average to a _single_ time-step
dimensions['Time'] = 1

average = {}
for name in variables.keys():
    if name != 'Times':
        average[name] = numpy.zeros(variables[name]['dimlens'])
for name in variables.keys():
    if name != 'Times':
        iTime = [idim for idim,dim in enumerate(variables[name]['dimensions']) if dim == 'Time']
        if len(iTime) == 0:
            average[name] = src.variables[name][:]
        elif len(iTime) == 1:
            iTime = iTime[0]
            average[name] = src.variables[name][:].mean(axis = iTime, keepdims = True)
        else:
            raise RuntimeError("Multiple matches for the Time dimension for variable {}".format(name))
        
src.close()

## create an output file
trg = netCDF4.Dataset(outFile,mode = 'w')
for dim in dimensions.keys():
    res = trg.createDimension(dim, dimensions[dim])
##
res = trg.setncatts(attributes['global'])
##
for name in variables.keys():
    ## set up the variables
    res = trg.createVariable(name,
                             variables[name]['dtype'].str[1:],
                             variables[name]['dimensions'],
                             zlib = (variables[name]['dtype'].str[1:] == 'f4'),
                             fill_value = variables[name]['fill_value'])
    trg.variables[name].setncatts(attributes[name])
    ## write out the data
    if name == 'Times':
        trg.variables[name][:] = numpy.array([c for c in outputTime], dtype='|S1').reshape(variables[name]['dimlens'])
    else:
        trg.variables[name][:] = average[name]
##
trg.close()
            
