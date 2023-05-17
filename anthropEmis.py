'''Convert anthropogenic emissions from WRF-CHEM to CMAQ, and merge with other sources
'''

import numpy
import datetime
import netCDF4
import os
import copy
import warnings

def checkIfMergedEmisFileExists(date, dom, ctmDir):
    '''Function to check if a merged emission file exists

    Args:
        date: the date in question (a datetime-object)
        dom: the domain in question 
        ctmDir: base directory for the CCTM inputs and outputs
        mech: name of chemical mechanism to appear in filenames
    
    Returns:
        Boolean (True/False) indicating whether the file exists
    '''
    yyyymmdd_dashed = date.strftime('%Y-%m-%d')
    chemdir = '{}/{}/{}'.format(ctmDir,yyyymmdd_dashed,dom)
    outputEmis  = '{}/merged_emis_{}_{}.nc'.format(chemdir,yyyymmdd_dashed,dom)
    result = os.path.exists(outputEmis)
    ##
    return result

def anthropEmis(dom, grid, run, date, nx_wrf, ny_wrf, nx_cmaq, ny_cmaq, ix0, iy0, mech, inFolder, addMegan, addFires, conversionTableFile, ctmDir, metDir, mcipsuffix, mechMEGAN):
    '''Function to convert anthropogenic emissions from WRF-CHEM to CMAQ, and merge with other sources

    Args:
        dom: the domain in question 
        grid: name of the grid, appears in some filenames
        run: name of the simulation, appears in some filenames
        date: the date of in question (a datetime-object)
        nx_wrf: length of the x-dimension for the WRF grid
        ny_wrf: length of the y-dimension for the WRF grid
        nx_cmaq: length of the x-dimension for the CMAQ grid
        ny_cmaq: length of the y-dimension for the CMAQ grid
        ix0: the index in the WRF grid of the first CMAQ grid-point in the x-direction
        iy0: the index in the WRF grid of the first CMAQ grid-point in the y-direction
        mech: name of chemical mechanism to appear in filenames
        inFolder: folder containing the wrfchemi_* anthropogenic emission files
        addMegan: Boolean (True/False) whether MEGAN biogenic emissions should be included
        addFires:  Boolean (True/False) whether GFAS fire emissions should be included
        conversionTableFile: path to the WRF-CHEM to CMAQ speciation table
        ctmDir: base directory for the CCTM inputs and outputs
        metDir: base directory for the MCIP output
        mcipsuffix: Suffix for the MCIP output files
        mechMEGAN: name of chemical mechanism given to MEGAN (should be one of: RADM2, RACM, CBMZ, CB05, CB6, SOAX, SAPRC99, SAPRC99Q, SAPRC99X)

    Returns:
        Nothing

    '''

    print "\t\tInitialisation (deal with dates and paths)"
    attrnames = ['IOAPI_VERSION', 'EXEC_ID', 'FTYPE', 'CDATE', 'CTIME', 'WDATE', 'WTIME',
                 'SDATE', 'STIME', 'TSTEP', 'NTHIK', 'NCOLS', 'NROWS', 'NLAYS', 'NVARS',
                 'GDTYP', 'P_ALP', 'P_BET', 'P_GAM', 'XCENT', 'YCENT', 'XORIG', 'YORIG',
                 'XCELL', 'YCELL', 'VGTYP', 'VGTOP', 'VGLVLS', 'GDNAM', 'UPNAM', 'VAR-LIST', 'FILEDESC']
    unicodeType = type(u'foo')

    ##
    Date = datetime.datetime(date.year, date.month, date.day, 0, 0, 0) 
    nextDate = Date + datetime.timedelta(days = 1)
    ##
    nextDate = date + datetime.timedelta(days = 1)
    Hours = [Date + datetime.timedelta(seconds = 3600*h) for h in range(25)]
    ##
    ## cmaqDate = date.strftime('%Y%m%d%H')
    yyyyjjj = date.strftime('%Y%j')
    # mcipDate = mcipDates[idate].strftime('%Y%m%d%H')
    wrfDate = date.strftime('%Y-%m-%d_%H:%M:%S')
    nextWrfDate = nextDate.strftime('%Y-%m-%d_%H:%M:%S')
    yyyymmdd_dashed = date.strftime('%Y-%m-%d')
    chemdir = '{}/{}/{}'.format(ctmDir,yyyymmdd_dashed,dom)
    mcipdir = '{}/{}/{}'.format(metDir,yyyymmdd_dashed,dom)
    croFile = '{}/GRIDCRO2D_{}'.format(mcipdir, mcipsuffix)
    metFile = '{}/METCRO3D_{}'.format(mcipdir, mcipsuffix)

    ## find the appropriate WRFCHEMI file in infolder
    files = os.listdir(inFolder)
    wrffiles = [ f for f in files if f.find('wrfchemi_') >= 0]
    wrfdates = [ datetime.datetime.strptime(f[13:],'%Y-%m-%d_%H:%M:%S') for f in wrffiles ]
    wrfdates = list(set(wrfdates))
    wrfdates.sort()
    diffTimes = numpy.array([(wrfdates[i+1] - wrfdates[i]).seconds + (wrfdates[i+1] - wrfdates[i]).days*24*60*60 for i in range(len(wrfdates)-1)])
    ##if diffTimes.min() == 3600 and diffTimes.max() == 3600:
    freq = 'hourly'
    ##elif diffTimes.min() == (24*3600) and diffTimes.max() == (24*3600):
      ##  freq = 'daily'
    ##else:
      ##  raise RuntimeError('Could not establish frequency of emission inputs ...')
    ##

    print "\t\tDeal with speciation"
    ##
    conversionTable = {'WRFCHEMNAME' : [],
                       'CMAQNAME' : [],
                       'isAerosol': []}
    otherAE = []
    otherGC = []
    organicsTable = {'fraction': [],
                    'molwgt': [],
                    'CMAQNAME': []}
    WRF_CHEM_VOC_spec = []
    ##
    f = open(conversionTableFile)
    lines = f.readlines()
    f.close()
    ## remove '\n' from each line
    lines = [l.strip() for l in lines ]
    ## remove comment lines
    lines = [l for l in lines if l[0] != '#']
    ## remove the header line
    lines = lines[1:]
    for line in lines:
        ## split by ';' instances
        parts  = line.split(';')
        ## remove leading/trailing white space
        parts  = [ p.strip() for p in parts ]
        WRFCHEMNAME = parts[0]
        CMAQNAME = parts[1]
        fraction = parts[2]
        molwgt = parts[3]
        isAerosol = (parts[4] == 'True')
        isVOC = (parts[5] == 'True')
        ## comments = parts[6]
        if WRFCHEMNAME != '-' and CMAQNAME != '-' :
            conversionTable['WRFCHEMNAME'].append(WRFCHEMNAME)
            conversionTable['CMAQNAME'].append(CMAQNAME)
            conversionTable['isAerosol'].append(isAerosol)
        elif WRFCHEMNAME == '-' and fraction != '-' and molwgt != '-' and isVOC and (not isAerosol):
            organicsTable['CMAQNAME'].append(CMAQNAME)
            organicsTable['molwgt'].append(float(molwgt))
            organicsTable['fraction'].append(float(fraction)) 
        elif CMAQNAME == '-' and isVOC and (not isAerosol):
            WRF_CHEM_VOC_spec.append(WRFCHEMNAME)
        elif WRFCHEMNAME == '-' and fraction == '-' and molwgt == '-' and (not isVOC) and isAerosol:
            otherAE.append(CMAQNAME)
        elif WRFCHEMNAME == '-' and fraction == '-' and molwgt == '-' and (not isVOC) and (not isAerosol):
            otherGC.append(CMAQNAME)
        else:
            raise RuntimeError('Cannot classify line "{}" in species conversion table file {}'.format(line, conversionTableFile))


    print "\t\tConnect to input files"
    
    WRFCHEMSAMPLESPEC = conversionTable['WRFCHEMNAME'][0]
        
    ncin = []
    filenamein = [''] * len(Hours)
    if freq == 'hourly':
        iWrf = numpy.zeros(len(Hours),dtype = numpy.int32)
        for iD, D in enumerate(Hours):
            tdiffDays = numpy.array([(wrfdate - D).days + (wrfdate - D).seconds/(3600.0*24.0) for wrfdate in wrfdates])
            if any(tdiffDays == 0):
                iWrf[iD] = numpy.where(tdiffDays == 0)[0][0]
            else:
                isMod7 = numpy.where((tdiffDays % 7) == 0)[0]
                iWrf[iD] = isMod7[numpy.argmin(numpy.abs(tdiffDays[isMod7]))]
            ##
            wrfDate = wrfdates[iWrf[iD]].strftime('%Y-%m-%d_%H:%M:%S')
            inputEmis = '{}/wrfchemi_{}_{}'.format(inFolder,dom,wrfDate)
            filenamein[iD] = inputEmis
        ##
        ## print filenamein[0]
        nc0 = netCDF4.Dataset(filenamein[0], 'r', format='NETCDF4')
        nLayWrf = len(nc0.dimensions['emissions_zdim'])
        Shape = list(nc0.variables[WRFCHEMSAMPLESPEC].shape)
        WRFCHEM_vars = nc0.variables.keys()
        Shape[0] = 25
        nc0.close()
    elif freq == 'daily':
        iWrf = numpy.zeros(2,dtype = numpy.int32)
        for iD, D in enumerate([Date, nextDate]):
            tdiffDays = numpy.array([(wrfdate - D).days for wrfdate in wrfdates])
            if any(tdiffDays == 0):
                iWrf[iD] = numpy.where(tdiffDays == 0)[0][0]
            else:
                isMod7 = numpy.where((tdiffDays % 7) == 0)[0]
                iWrf[iD] = isMod7[numpy.argmin(numpy.abs(tdiffDays[isMod7]))]
                print "Date {} not in list of wrfchemi files, using nearest mod-7 equivalent ({}), tdiff = {}".format(date.strftime('%Y-%m-%d'), wrfdates[iWrf[iD]].strftime('%Y-%m-%d'),tdiffDays[iWrf[iD]])
        ## 
        wrfDate = wrfdates[iWrf[0]].strftime('%Y-%m-%d_%H:%M:%S')
        nextWrfDate = wrfdates[iWrf[1]].strftime('%Y-%m-%d_%H:%M:%S')
        ##
        inputEmis = '{}/wrfchemi_{}_{}'.format(inFolder,dom,wrfDate)
        nextInputEmis = '{}/wrfchemi_{}_{}'.format(inFolder,dom,nextWrfDate)
        ncin.append(netCDF4.Dataset(inputEmis, 'r', format='NETCDF4'))
        ncin.append(netCDF4.Dataset(nextInputEmis, 'r', format='NETCDF4'))
        WRFCHEM_vars = ncin[0].variables.keys()
        nLayWrf = len(ncin[0].dimensions['emissions_zdim'])
    ##

    outputEmis  = '{}/mergedEmis_{}_{}_{}.nc'.format(chemdir,yyyymmdd_dashed,dom,mech)
    nccro= netCDF4.Dataset(croFile, 'r', format='NETCDF4')
    ncmet= netCDF4.Dataset(metFile, 'r', format='NETCDF4')
    if os.path.exists(outputEmis):
        os.remove(outputEmis)

    ncout = netCDF4.Dataset(outputEmis, 'w', format='NETCDF4')

    lens = dict()
    for k in nccro.dimensions.keys():
        lens[k] = len(nccro.dimensions[k])

    lens['LAY'] = len(ncmet.dimensions['LAY'])
    lens['TSTEP'] = 25 ## hourly timesteps, plus one at the end

    LAT  = nccro.variables['LAT'][:].squeeze()
    LON  = nccro.variables['LON'][:].squeeze()
    ix1 = ix0 + nx_cmaq
    iy1 = iy0 + ny_cmaq

    
    WRF_CHEM_VOC_spec_tmp = []
    WRF_CHEM_VOC_spec
    for spec in WRF_CHEM_VOC_spec:
        if not (spec in WRFCHEM_vars):
            warnings.warn("Species {} was listed in the species conversion table ({}) as one of the WRF VOCs, but not found in the emissions file - it will be ignored ".format(spec, conversionTableFile))
        else:
            WRF_CHEM_VOC_spec_tmp.append(spec)
    
    del WRF_CHEM_VOC_spec
    WRF_CHEM_VOC_spec = WRF_CHEM_VOC_spec_tmp
    
    conversionTableTmp = {'WRFCHEMNAME' : [],
                          'CMAQNAME' : [],
                          'isAerosol': []}
    for ispec,spec in enumerate(conversionTable['WRFCHEMNAME']):
        if not (spec in WRFCHEM_vars):
            warnings.warn("Species {} was listed in the species conversion table ({}) as one of the directly convertable species, but not found in the emissions file - it will be ignored ".format(spec, conversionTableFile))
        else:
            conversionTableTmp['WRFCHEMNAME'].append(conversionTable['WRFCHEMNAME'][ispec])
            conversionTableTmp['CMAQNAME'].append(conversionTable['CMAQNAME'][ispec])
            conversionTableTmp['isAerosol'].append(conversionTable['isAerosol'][ispec])
            
    del conversionTable
    conversionTable = conversionTableTmp
    
    otherSpecies = otherAE + otherGC

    nspecSimple = len(conversionTable['CMAQNAME'])
    nspecOrganic = len(organicsTable['CMAQNAME'])
    nspec = nspecSimple + nspecOrganic

    specnames = conversionTable['CMAQNAME'] + organicsTable['CMAQNAME'] + otherSpecies

    if addFires:
        inFire  = '{}/fire_emis_{}.nc'.format(chemdir,dom)
        ncfire = netCDF4.Dataset(inFire, 'r', format='NETCDF4')
        fireSpec = ncfire.variables.keys()
        fireSpec = [s for s in fireSpec if s != 'TFLAG']
        unseenFireSpec = [s for s in fireSpec if not (s in specnames)]
    else:
        fireSpec = []
        unseenFireSpec = []

    specnames = specnames + unseenFireSpec

    area_km_2 = nccro.getncattr('XCELL') * nccro.getncattr('YCELL') / 1.0e6 ## grid area in km^2
    area_m_2 = nccro.getncattr('XCELL') * nccro.getncattr('YCELL') ## grid area in m^2
    hours_per_sec = 1.0/3600.0
    g_per_ug = 1.0/1000.0

    if addMegan:
        prefix = 'MEGANv2.10'
        meganfile = '{}/{}.{}.{}.{}.ncf'.format(chemdir, prefix, grid, mechMEGAN, yyyyjjj)
        if not os.path.exists(meganfile):
            raise RuntimeError('megan file {} not found ...'.format(meganfile))
        ncmeg = netCDF4.Dataset(meganfile, 'r', format='NETCDF4')

    #  unit conversion 
    #
    # CMAQ units (gas) = WRF-CHEM units (gas)  * factor
    # moles/s/gridcell = (moles/hr)      * (hr/s) / gridcell
    #                  = (moles/hr/km^2) * (hr/s) * (km^2/gridcell)
    #                  = (moles/hr/km^2) * (1/3600) * (DX*DY/1e6)
    #
    # CMAQ units (PM)  = WRF-CHEM units (PM) * factor
    # g/s/gridcell     = (ug/m2/s) * (g/ug)  * (m2/gridcell)
    #                  = (ug/m2/s) * (1.0e-6)  * (DX*DY)

    print "\t\tDeal with direct conversion between species"

    emisOut = {}
    templateValues = numpy.zeros((lens['TSTEP'],lens['LAY'],lens['ROW'],lens['COL']), dtype = numpy.float32)
    for ispec in range(nspecSimple):
        WRFCHEMNAME = conversionTable['WRFCHEMNAME'][ispec]
        CMAQNAME = conversionTable['CMAQNAME'][ispec]
        isAerosol = conversionTable['isAerosol'][ispec]
        
        emisOut[CMAQNAME] = {'isAerosol':isAerosol, 'values':copy.copy(templateValues)}
        if isAerosol:
            factor = area_m_2 * g_per_ug
        else:
            factor = hours_per_sec * area_km_2
        ##
        if freq == 'hourly':
            for ihour in range(25):
                ncin = netCDF4.Dataset(filenamein[ihour], 'r', format='NETCDF4')
                emisOut[CMAQNAME]['values'][ihour,0:nLayWrf,:,:] = ncin.variables[ WRFCHEMNAME][:,:,ix0:ix1,iy0:iy1]*factor
                ncin.close()
        elif freq == 'daily':
            emisOut[CMAQNAME]['values'][0:24,0:nLayWrf,:,:] = ncin[0].variables[ WRFCHEMNAME][:,:,ix0:ix1,iy0:iy1]*factor
            emisOut[CMAQNAME]['values'][  24,0:nLayWrf,:,:] = ncin[1].variables[WRFCHEMNAME][0,:,ix0:ix1,iy0:iy1]*factor
        ##

    print "\t\tAdd VOCs"
    ##
    first = True
    if freq == 'hourly':
        for WRFCHEMNAME in WRF_CHEM_VOC_spec:
            if first:
                VOC_sum  = numpy.zeros(Shape,dtype = numpy.float32)
            for ihour in range(25):
                ncin = netCDF4.Dataset(filenamein[ihour], 'r', format='NETCDF4')
                VOC_sum[ihour,:,:,:]  = VOC_sum[ihour,:,:,:] + ncin.variables[WRFCHEMNAME][0,:,:,:]
                ncin.close()
            ##
    elif freq == 'daily':
        for WRFCHEMNAME in WRF_CHEM_VOC_spec:
            if first:
                VOC_sum  = numpy.zeros(ncin[0].variables[WRFCHEMNAME].shape,dtype = numpy.float32)
                VOC_sum2 = numpy.zeros(ncin[0].variables[WRFCHEMNAME].shape,dtype = numpy.float32)
                first = False
            VOC_sum  = VOC_sum + ncin[0].variables[ WRFCHEMNAME][:]
            VOC_sum2 = VOC_sum2 + ncin[1].variables[WRFCHEMNAME][:]

    for ispec in range(nspecOrganic):            
        CMAQNAME = organicsTable['CMAQNAME'][ispec]
        ## the organic species are all in the gas-phase - use the gas-phase conversion factor
        isAerosol = False
        factor = hours_per_sec * area_km_2
        ##
        emisOut[CMAQNAME] = {'isAerosol':isAerosol, 'values':copy.copy(templateValues)}
        if freq == 'hourly':
            emisOut[CMAQNAME]['values'][:,0:nLayWrf,:,:] = VOC_sum[ :,:,ix0:ix1,iy0:iy1]*factor*organicsTable['fraction'][ispec]
        elif freq == 'daily':
            emisOut[CMAQNAME]['values'][0:24,0:nLayWrf,:,:] = VOC_sum[ :,:,ix0:ix1,iy0:iy1]*factor*organicsTable['fraction'][ispec]
            emisOut[CMAQNAME]['values'][  24,0:nLayWrf,:,:] = VOC_sum2[0,:,ix0:ix1,iy0:iy1]*factor*organicsTable['fraction'][ispec]
        ##

    print "\t\tAdd 'other species'"        
    for spec in otherSpecies:
        if spec in emisOut.keys():
            warnings.warn("Species {} was listed in the species conversion table ({}) as one of the variables to initialise to zero, but it was already found in the emissions file - no new variable will be added... ".format(spec, conversionTableFile))
        else:
            isAerosol = (spec in otherAE)
            emisOut[spec] = {'isAerosol':isAerosol, 'values':copy.copy(templateValues)}

    print "\t\tAdd MEGAN"
    if addMegan:
        excludeSpec = ['GDAY','NR','CH4','TFLAG']
        for spec in ncmeg.variables.keys():
            if not (spec in excludeSpec ):
                if not ( spec in emisOut.keys() ):
                    isAerosol = (spec[0] == 'A') and (spec[-1] in ['I', 'J', 'K']) 
                    emisOut[spec] = {'isAerosol':isAerosol, 'values':copy.copy(templateValues)}
                ##
                emisOut[spec]['values'][0:24,0,:,:] = emisOut[spec]['values'][0:24,0,:,:] + ncmeg.variables[spec][0:24,0,:,:]
                emisOut[spec]['values'][24,0,:,:]   = emisOut[spec]['values'][24,0,:,:]   + ncmeg.variables[spec][23,0,:,:]

    print "\t\tAdd fires"
    if addFires:
        for spec in fireSpec:
            if not ( spec in emisOut.keys() ):
                isAerosol = (spec[0] == 'A') and (spec[-1] in ['I', 'J', 'K'])
                emisOut[spec] = {'isAerosol':isAerosol, 'values':copy.copy(templateValues)}
                ##
            fireVar = ncfire.variables[spec][0,:,:,:]
            for ihour in range(25):
                emisOut[spec]['values'][ihour,:,:,:] = emisOut[spec]['values'][ihour,:,:,:] + fireVar
            ##
        ##
        ncfire.close()

    print "\t\tWrite output to file"

    nvar = len(emisOut.keys())
    lens['VAR'] = nvar
    
    for k in nccro.dimensions.keys():
        res = ncout.createDimension(k, lens[k])
    
    ## define the time variable and set its values
    res = ncout.createVariable('TFLAG', 'i4', ('TSTEP','VAR','DATE-TIME',))
    ncout.variables['TFLAG'].setncattr('long_name',"{:<16}".format('TFLAG'))
    ncout.variables['TFLAG'].setncattr('units',"<YYYYDDD,HHMMSS>")
    ncout.variables['TFLAG'].setncattr('var_desc',"Timestep-valid flags:  (1) YYYYDDD or (2) HHMMSS ")
    Date = datetime.datetime(date.year, date.month, date.day, 0, 0, 0)
    Times = [Date + datetime.timedelta(seconds = h*3600) for h in range(25)] 
    YYYYJJJ = numpy.array([ t.year*1000 + t.timetuple().tm_yday for t in Times ], dtype = numpy.int32)
    HHMMSS =  numpy.array([ t.hour*10000 + t.minute*100 + t.second for t in Times ], dtype = numpy.int32)
    
    for ispec in range(nvar):
        ncout.variables['TFLAG'][:,ispec,0] = YYYYJJJ
        ncout.variables['TFLAG'][:,ispec,1] = HHMMSS

    
    for spec in emisOut.keys():
        res = ncout.createVariable(spec, 'f4', ('TSTEP', 'LAY', 'ROW', 'COL'), zlib = True)
        ncout.variables[spec].setncattr('long_name',"{:<16}".format(spec))
        ncout.variables[spec].setncattr('var_desc',"{:<80}".format("Emissions of %s" % spec))
        if emisOut[spec]['isAerosol']:
            ncout.variables[spec].setncattr('units',"{:<16}".format("g/s"))
        else:
            ncout.variables[spec].setncattr('units',"{:<16}".format("moles/s"))
        ncout.variables[spec][:] = emisOut[spec]['values']

    for a in attrnames:
        val = nccro.getncattr(a)
        if type(val) == unicodeType:
            val = str(val)
        ##
        ncout.setncattr(a,val)

    VarString = "".join([ "{:<16}".format(k) for k in emisOut.keys()])
    ncout.setncattr('VAR-LIST',VarString)
    ncout.setncattr('NVARS',numpy.int32(nvar))
    ncout.setncattr('HISTORY',"")
    ncout.setncattr('NLAYS',numpy.int32(lens['LAY']))
    ncout.setncattr('SDATE',numpy.int32(YYYYJJJ[0]))
    ncout.setncattr('TSTEP',numpy.int32(10000))
    ncout.setncattr('VGLVLS',ncmet.getncattr('VGLVLS')[:lens['LAY']])
    ncout.setncattr('VGTOP',ncmet.getncattr('VGTOP'))

    ncout.close()
    ncmet.close()
    if freq == 'daily':
        for iNC in range(len(ncin)):
            ncin[iNC].close()
    ##
    nccro.close()

    return ;

