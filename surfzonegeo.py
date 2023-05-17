# -*- coding: utf-8 -*-
"""Set up the 'surf zone' file for the sea salt emission module of CMAQ

The module contains two functions, one to check whether the surf zone
files exist, and another to create them if need be. This relies on the
python module ogr, which builds upon the gdal geoprocessing software
suite.
"""

from osgeo import ogr
import numpy
import datetime
import netCDF4
import os

def checkSurfZoneFilesExist(ctmDir, doms):
    """Check whether the 'surf zone' files exist

    The surf zone files are assumed to live within the directory given
    in the argument 'ctmDir', and follow the naming convention:
        '{}/surfzone_{}.nc'.format(ctmDir,dom)
    where dom is one of the domains (e.g. 'd01')

    Args:
        ctmDir: the directory containing the CTM inputs and outputs
        doms: a list of the domain names (e.g. ['d01','d02'] )

    Returns:
        A single boolean (i.e. True or False) value, indicating if all
        the files expected were found.
    """
    
    print("Check whether surf zone files exist...")
    filesExist = True
    for idom,dom in enumerate(doms):
        outfile = '{}/surfzone_{}.nc'.format(ctmDir,dom)
        if not os.path.exists(outfile):
            filesExist = False
    print("\t... the result is {}".format(filesExist))
    return filesExist
    
def setupSurfZoneFiles(metDir, ctmDir, doms, date, mcipsuffix, shapefiles):
    """Set up the 'surf zone' files

    The surf zone files contain two fields - the OCEAN field,
    indicating the fraction of each grid-cell covered by ocean, and
    the SURF field, indicating the fraction of each grid-cell covered
    by the 'surf zone'. The surf zone is defined here to be an
    approximate 50 m buffer from the coast, which follows Neumann et
    al. (2016, ACP). One surf zone file is created per domain. The
    surf zone is calcculated as follows.
        1. Find the extent of the domain
        2. Find all land-masses that intersect with the domain
           (defined in the shapefiles)
        3. Define a 50 m buffer zone around each land-mass, then
           subtract the land-mass itself (this gives the surf zone)
        4. Find the fraction overlap for each gridcell for all surf
           zones
    
    The open ocean zone is defined as follows
        1. Find the extent of the domain
        2. Subtract any land-masses that intersect with the
           domain. The remainder is assumed to be ocean. 
        3. Find the fraction overlap for each gridcell and the ocean
           area

    The surf zone files created within the directory given in the
    argument 'ctmDir', and follow the naming convention:
        '{}/surfzone_{}.nc'.format(ctmDir,dom)
    where dom is one of the domains (e.g. 'd01')

    Args:
        metDir: The parent directory for MCIP output. 
        ctmDir: The parent directory for CCTM inputs/outputs.
        doms: a list of the domain names (e.g. ['d01','d02'] )
        date: a datetime.date object
        mcipsuffix: the list of suffices of the MCIP output (one entry per domain)
        shapefiles: a list of paths to coastline shapefiles (one entry per domain)

    Returns:
        Nothing is returned. If no error is thrown, successful
        completion can be assumed.
    """
    
    ndoms = len(doms)
    yyyymmdd_dashed = date.strftime('%Y-%m-%d')
    ##
    attrnames = ['IOAPI_VERSION', 'EXEC_ID', 'FTYPE', 'CDATE', 'CTIME', 'WDATE', 'WTIME',
                 'SDATE', 'STIME', 'TSTEP', 'NTHIK', 'NCOLS', 'NROWS', 'NLAYS', 'NVARS',
                 'GDTYP', 'P_ALP', 'P_BET', 'P_GAM', 'XCENT', 'YCENT', 'XORIG', 'YORIG',
                 'XCELL', 'YCELL', 'VGTYP', 'VGTOP', 'VGLVLS', 'GDNAM', 'UPNAM', 'VAR-LIST', 'FILEDESC']
    unicodeType = type('foo')
    ##
    for idom,dom in enumerate(doms):
        print(dom)
        croFile = '{}/{}/{}/GRIDCRO2D_{}'.format(metDir,yyyymmdd_dashed,dom,mcipsuffix[idom])
        dotFile = '{}/{}/{}/GRIDDOT2D_{}'.format(metDir,yyyymmdd_dashed,dom,mcipsuffix[idom])
        outfile = '{}/surfzone_{}.nc'.format(ctmDir,dom)
        ncdot= netCDF4.Dataset(dotFile, 'r', format='NETCDF4')
        nccro= netCDF4.Dataset(croFile, 'r', format='NETCDF4')
        LAT  = nccro.variables['LAT'][:].squeeze()
        LON  = nccro.variables['LON'][:].squeeze()
        LATD = ncdot.variables['LATD'][:].squeeze()
        LOND = ncdot.variables['LOND'][:].squeeze()
        LATD = LATD.astype(float)
        LOND = LOND.astype(float)

        
        print("create domain boundary and expanded version")
        # Define the domain boundary
        ring = ogr.Geometry(ogr.wkbLinearRing)
        ring.AddPoint(LOND[ 0, 0], LATD[ 0, 0])
        ring.AddPoint(LOND[-1, 0], LATD[-1, 0])
        ring.AddPoint(LOND[-1,-1], LATD[-1,-1])
        ring.AddPoint(LOND[ 0,-1], LATD[ 0,-1])
        ring.AddPoint(LOND[ 0, 0], LATD[ 0, 0])
        domainBoundary = ogr.Geometry(ogr.wkbPolygon)
        domainBoundary.AddGeometry(ring)

        # define an expanded domain boundary (to account for curvature
        # effects using different map projections), which have all the
        # "land" chunks taken out of it - this then becomes the "ocean"
        ring = ogr.Geometry(ogr.wkbLinearRing)
        ring.AddPoint(LOND[ 0, 0]-20, LATD[ 0, 0]-20)
        ring.AddPoint(LOND[-1, 0]-20, LATD[-1, 0]+20)
        ring.AddPoint(LOND[-1,-1]+20, LATD[-1,-1]+20)
        ring.AddPoint(LOND[ 0,-1]+20, LATD[ 0,-1]-20)
        ring.AddPoint(LOND[ 0, 0]-20, LATD[ 0, 0]-20)
        ocean = ogr.Geometry(ogr.wkbPolygon)
        ocean.AddGeometry(ring)

        ## create a connection to the shapefile
        print("Read shapefile")
        driver = ogr.GetDriverByName("ESRI Shapefile")
        dataSource = driver.Open(shapefiles[idom], 0)
        layer = dataSource.GetLayer()

        ## an array to store the "surf zone" geometry objects
        intersectingGeoms = []

        ## Set the buffer zone in units of decimal degrees. The
        ## assumption here is that one degree of latitude or longitude
        ## is equal to 100km (this is approximate). Multiply by 0.01
        ## and you get a buffer of 1km. Multiply again by 0.05 and you
        ## get a buffer of 50m, which follows Neumann et al. (2016, ACP)
        ## http://www.atmos-chem-phys.net/16/2921/2016/acp-16-2921-2016.pdf
        ## -- also check the supplementary info
        bufferDistance = 0.01*0.05

        ## loop over the land areas
        for ifeature,feature in enumerate(layer):
            ## extract the geometry of the land area
            geom = feature.GetGeometryRef()
            ## check if it interesects with our domain
            if geom.Intersect(domainBoundary):
                ## if so, subtract this area from the interatively updated "ocean" region
                ocean = ocean.Difference(geom)
                ## define a buffer region, expanding the land area by the buffer distance (50 m)
                buffered = geom.Buffer(bufferDistance)
                ## remove the land area from the buffer region, creating the "surf zone"
                bufferZone = buffered.Difference(geom)
                ## check that the surf zone intersects the domain - if so, keep track of it
                if bufferZone.Intersect(domainBoundary):
                    intersectingGeoms.append(bufferZone)

        print("Calculate OPEN and SURF")
        OPEN = numpy.zeros(LAT.shape,dtype = numpy.float32)
        SURF = numpy.zeros(LAT.shape,dtype = numpy.float32)
        ## loop over the grid cells in the domain
        for i in range(LAT.shape[0]):
            for j in range(LAT.shape[1]):
                ## define the grid cell as a geometry object
                cell = ogr.Geometry(ogr.wkbLinearRing)
                cell.AddPoint(LOND[i  ,j  ], LATD[i  ,j  ])
                cell.AddPoint(LOND[i+1,j  ], LATD[i+1,j  ])
                cell.AddPoint(LOND[i+1,j+1], LATD[i+1,j+1])
                cell.AddPoint(LOND[i  ,j+1], LATD[i  ,j+1])
                cell.AddPoint(LOND[i  ,j  ], LATD[i  ,j  ])
                Cell = ogr.Geometry(ogr.wkbPolygon)
                Cell.AddGeometry(cell)
                ## calculate its area (in units of decimal degrees squared)
                cellArea = Cell.Area()
                ## if it overlaps with the "ocean" region...
                if Cell.Intersect(ocean):
                    ## ...then calculate the area that they overlap,
                    ## and then the proportion overlapping...
                    oceanArea = Cell.Intersection(ocean).Area()
                    propsea = oceanArea/cellArea
                else:
                    ## .. otherwise, the proportion overlapping the
                    ## open ocean is set to zero
                    propsea = 0.0
                ##
                ## Initially, we assume that there is no surf zone in
                ## the cell
                propsurf = 0.0
                ## loop over surf zones that intersect the domain
                for bufferZone in intersectingGeoms:
                    ## check if this particular surf zone overlaps with the grid cell
                    if Cell.Intersect(bufferZone):
                        ## if so, then calculate the area of intersection
                        bufferArea = Cell.Intersection(bufferZone).Area()
                        ## and use this to update the proportion of surf zone in the cell
                        propsurf = propsurf + bufferArea/cellArea
                ##
                SURF[i,j] = propsurf
                OPEN[i,j] = propsea

        print("Write to file")
        lens = {}
        for k in list(nccro.dimensions.keys()):
            lens[k] = len(nccro.dimensions[k])

        nlay = 1
        nvar = 2
        lens['VAR'] = nvar
        lens['LAY'] = nlay

        ncout = netCDF4.Dataset(outfile, 'w', format='NETCDF4')
        outdims = dict()

        for k in list(ncdot.dimensions.keys()):
            outdims[k] = ncout.createDimension(k, lens[k])

        simpleFields = dict(OPEN = 1.0e-30,
                            SURF = 1.0e-30,)

        ## all IOAPI files require a TFLAG variable, even if they are static in time
        outvars = dict()
        outvars['TFLAG'] = ncout.createVariable('TFLAG', 'i4', ('TSTEP','VAR','DATE-TIME',))
        for k in list(simpleFields.keys()):
            outvars[k] = ncout.createVariable(k, 'f4', ('TSTEP', 'LAY', 'ROW', 'COL'), zlib = True, shuffle = False)
            outvars[k].setncattr('long_name',"{:<16}".format(k))
            outvars[k].setncattr('units',"{:<16}".format("UNKNOWN"))
            outvars[k].setncattr('var_desc',"{:<80}".format(k))

        outvars['OPEN'][:] = OPEN
        outvars['SURF'][:] = SURF

        for a in attrnames:
            val = nccro.getncattr(a)
            if type(val) == unicodeType:
                val = str(val)
            ##
            ncout.setncattr(a,val)

        ncout.variables['TFLAG'][:] = 0
        outvars['TFLAG'].setncattr('long_name',"{:<16}".format('TFLAG'))
        outvars['TFLAG'].setncattr('units',"<YYYYDDD,HHMMSS>")
        outvars['TFLAG'].setncattr('var_desc',"Timestep-valid flags:  (1) YYYYDDD or (2) HHMMSS                                ")
        ## set variables required for IOAPI
        VarString = "".join([ "{:<16}".format(k) for k in list(simpleFields.keys()) ])
        ncout.setncattr('VAR-LIST',VarString)
        ncout.setncattr('NVARS',numpy.int32(len(simpleFields)))
        ncout.setncattr('HISTORY',"")
        ncout.setncattr('VGTYP',numpy.int32(1))
        ncout.setncattr('NLAYS',numpy.int32(nlay))
        ncout.setncattr('SDATE',numpy.int32(-635))
        ncout.setncattr('VGLVLS',numpy.array([1., 0.],dtype = numpy.float32))


        ncout.close()
        ncdot.close()
        nccro.close()

