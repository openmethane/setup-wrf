'''Interpolate the from the global MOZART CTM output to ICs and BCs for CMAQ
'''
import numpy
import datetime
import netCDF4
import os
import exceptions
import shutil
import warnings
import helper_funcs

# def match_two_sorted_arrays(arr1,arr2):
#     result = numpy.zeros(arr2.shape,dtype = numpy.int)
#     for i, v in enumerate(arr2):
#         result[i] = len(arr1) - numpy.searchsorted(arr1, v) - 1
#     return result

def match_two_sorted_arrays(arr1,arr2):
    '''Match up two sorted arrays
    
    Args:
        arr1: A sorted 1D numpy array
        arr2: A sorted 1D numpy array

    Returns: 
        result: numpy integer array with the same dimensions as array arr2, with each element containing the index of arr1 that provides the *closest* match to the given entry in arr2
    '''
    result = numpy.zeros(arr2.shape,dtype = numpy.int)
    for i, v in enumerate(arr2):
        result[i] = len(arr1) - numpy.argmin(numpy.abs(arr1 - v)) - 1
    return result


def extract_and_interpolate_interior(mzspec, ncin, lens, LON, Iz, iMZtime, isAerosol, mz_mw_aerosol, T, P, near_interior):
    '''Interpolate from the MOZART grid to the CMAQ interior points (i.e. the full 3D array) 
    
    Args:
        mzspec: the MOZART species name
        ncin: the connection to the netCDF input file (i.e. the MOZART file)
        lens: dictionary of dimension lengths
        LON: array of longitudes with the same size as the output array
        Iz: array of indices of MOZART levels that correspond to the CMAQ levels
        iMZtime: index of the MOZART time to use
        isAerosol: Boolean (True/False) whether this is an aerosol species or not
        mz_mw_aerosol: molecular weight of the MOZART species
        T: array of temperatures (units = K) from the MOZART output
        P: array of pressures (units = Pa) from the MOZART output
        near_interior: array of indices matching up the MOZART grid-points with CMAQ grid-points

    Returns: 
        out_interior: Gridded MOZART concentrations interpolated to the CMAQ grid
    '''
    #
    out_interior = numpy.zeros((lens['LAY'], LON.shape[0], LON.shape[1]),dtype = numpy.float32)
    #
    if mzspec in ncin.variables.keys():
        varin = ncin.variables[mzspec][iMZtime,:,:,:]
        #
        if isAerosol:
            ##  VMR * P[Pa] / Rgas[J/K/kg] /T[K] * mw_aerosol[g/mole] /mw_air[g/mole] * 1E9[ug/kg]
            Rgas = 286.9969 ## [J/K/kg] (constant)
            mw_aerosol = mz_mw_aerosol[mzspec]
            mw_air = 28.97 ## g/mol (constant)
            varin = varin * P[iMZtime,:,:,:] / Rgas / T[iMZtime,:,:,:] * mw_aerosol / mw_air * 1.0e9
        else:
            varin = varin * 1.0e6 ## convert from VMR to PPMV
        #
        for irow in range(LON.shape[0]):
            for icol in range(LON.shape[1]):
                ix, iy = near_interior[irow,icol,:]
                out_interior[:,irow, icol] = varin[Iz,ix,iy]
    else:
        warnings.warn("Species {} was not found in input MOZART file -- contributions from this variable will be zero...".format(mzspec))
    #
    return out_interior

def extract_and_interpolate_boundary(mzspec, ncin, lens, LONP, Iz, iMZtime_for_each_CMtime, isAerosol, mz_mw_aerosol, T, P, near_boundary):
    '''Interpolate from the MOZART grid to the CMAQ boundary points 
    
    Args:
        mzspec: the MOZART species name
        ncin: the connection to the netCDF input file (i.e. the MOZART file)
        lens: dictionary of dimension lengths
        LONP: array of longitudes of CMAQ boundary points with the same size as the output array
        Iz: array of indices of MOZART levels that correspond to the CMAQ levels
        iMZtime_for_each_CMtime: index of the MOZART time to use, one entry for each CMAQ time
        isAerosol: Boolean (True/False) whether this is an aerosol species or not
        mz_mw_aerosol: molecular weight of the MOZART species
        T: array of temperatures (units = K) from the MOZART output
        P: array of pressures (units = Pa) from the MOZART output
        near_boundary: array of indices matching up the MOZART grid-points with CMAQ boundary grid-points

    Returns: 
        out_boundary: Gridded MOZART concentrations interpolated to the CMAQ boundary grid points
    '''
    #
    iCMtime = 0
    iMZtime = iMZtime_for_each_CMtime[iCMtime]
    #
    ntime = 1
    out_boundary = numpy.zeros((ntime,lens['LAY'],LONP.shape[0]),dtype = numpy.float32)
    #
    if mzspec in ncin.variables.keys():
        varin = ncin.variables[mzspec][iMZtime,:,:,:]
        #
        if isAerosol:
            ##  VMR * P[Pa] / Rgas[J/K/kg] /T[K] * mw_aerosol[g/mole] /mw_air[g/mole] * 1E9[ug/kg]
            Rgas = 286.9969 ## [J/K/kg] (constant)
            mw_aerosol = mz_mw_aerosol[mzspec]
            mw_air = 28.97 ## g/mol (constant)
            varin = varin * P[iMZtime,:,:,:] / Rgas / T[iMZtime,:,:,:] * mw_aerosol / mw_air * 1.0e9
        else:
            varin = varin * 1.0e6 ## convert from VMR to PPMV
        #
        for iperim in range(LONP.shape[0]):
            ix, iy = near_boundary[iperim,:]
            ## for iCMtime, iMZtime in enumerate(iMZtime_for_each_CMtime):
            out_boundary[iCMtime,:,iperim] = varin[Iz,ix,iy]
    else:
        warnings.warn("Species {} was not found in input MOZART file -- contributions from this variable will be zero...".format(mzspec))
    #
    return out_boundary

def populate_interior_variable(ncouti, cmspec, out_interior, coef):
    '''Populate an interior variable (i.e. for the IC file)
    
    Args:
        ncouti: connection to the output file for the initial conditions
        cmspec: the name of the CMAQ species
        out_interior: numpy array of concentrations at interior points
        coef: Coefficient to multiply the values by

    Returns: 
        Nothing
    '''
    ncouti.variables[cmspec][:] = ncouti.variables[cmspec][:]+numpy.fmax(out_interior[:]*coef,1.0e-30)

def populate_boundary_variable(ncoutb, cmspec, out_boundary, coef):
    '''Populate an boundary variable (i.e. for the BC file)
    
    Args:
        ncoutb: connection to the output file for the boundary conditions
        cmspec: the name of the CMAQ species
        out_boundary: numpy array of concentrations at boundary points
        coef: Coefficient to multiply the values by

    Returns: 
        Nothing
    '''
    ncoutb.variables[cmspec][:] = ncoutb.variables[cmspec][:]+numpy.fmax(out_boundary[:]*coef,1.0e-30)

def print_interior_variable(cmspec, out_interior, factor):
    '''Print the mean value of a interior variable
    
    Args:
        cmspec: Name of the CMAQ species
        out_interior: numpy array of concentrations at interior points
        factor: Coefficient to multiply the values by

    Returns: 
        Nothing

    '''
    print "{:20} {:.3e}".format(cmspec, out_interior[0,:,:].mean()*factor)

def print_boundary_variable(cmspec, out_boundary, factor):
    '''Print the mean value of a boundary variable
    
    Args:
        cmspec: Name of the CMAQ species
        out_boundary: numpy array of concentrations at boundary points
        factor: Coefficient to multiply the values by

    Returns: 
        Nothing

    '''
    print "{:20} {:.3e}".format(cmspec, out_boundary[:,0,:].mean()*factor)


def interpolateFromMozartToCmaqGrid(dates, doms, mech, inputMozartFile, templateIconFiles, templateBconFiles, specTableFile, metDir, ctmDir, GridNames, mcipsuffix, forceUpdate, defaultSpec = 'O3'):
    '''Function to interpolate the from the global MOZART CTM output to ICs and BCs for CMAQ
    
    Args:
        dates: list of datetime objects, one per date MCIP and CCTM output should be defined
        doms: list of domain names (e.g. ['d01', 'd02'] )
        mech: name of chemical mechanism to appear in filenames
        inputMozartFile: Output from MOZART to use for boundary and initial conditions
        templateIconFiles: list of filenames for template ICON files
        templateBconFiles: list of filenames for template BCON files
        specTableFile: speciation file, mapping MOZART to CMAQ (CBM05) species
        metDir: base directory for the MCIP output
        ctmDir: base directory for the CCTM inputs and outputs
        GridNames: list of MCIP map projection names (one per domain)
        mcipsuffix: Suffix for the MCIP output files
        forceUpdate: Boolean (True/False) for whether we should update the output if it already exists
        defaultSpec: A species that is known to exist in the MOZART files (defaults to 'O3'), used for checking dimension information

    Returns: 
        Nothing

    '''
    ##
    f = open(specTableFile, "r")
    line = f.readline()
    species_map = []
    MZspecies_dict = {}
    ind = 0
    for line in f:
        if len(line) <= 1:
            continue
        words = line.split(";")
        MZspec = words[0].strip()
        CMspec = [s.strip() for s in words[2].split(",")]
        coef = [float(s) for s in words[3].split(",")]
        isAerosol = [((s[0] == 'A') and (s[-1] in ['I','J','K'])) or (s in ['ASEACAT', 'ASOIL']) for s in CMspec]
        species_map.append({'MZspec':MZspec, 'CMspec':CMspec, 'coef':coef, 'isAerosol':isAerosol })
        MZspecies_dict[MZspec] = ind
        ind = ind + 1

    f.close()

    ALL_CM_SPEC = sum([s['CMspec'] for s in species_map],[])
    ALL_CM_SPEC = list(set(ALL_CM_SPEC))
    ALL_CM_SPEC.sort()

    mz_mw_aerosol = {
        'CB1_VMR_inst': 12.,
        'CB2_VMR_inst': 12.,
        'DUST1': 34.,
        'DUST2': 34.,
        'DUST3': 34.,
        'DUST4': 34.,
        'NH4NO3_VMR_inst': 80.0,
        'NH4_VMR_inst': 18.0,
        'OC1_VMR_inst': 12.0,
        'OC2_VMR_inst': 12.0,
        'SA1_VMR_inst': 58.,
        'SA2_VMR_inst': 58.,
        'SA3_VMR_inst': 58.,
        'SA4_VMR_inst': 58.,
        'SO4_VMR_inst': 96.0,
        'SOA_VMR_inst': 144.0,
        'so4_a1':96.0,
        'so4_a2':96.0,
        'so4_a3':96.0,     
        'soa1_a1':144.,        
        'soa1_a2':144.,         
        'soa2_a1':144., 
        'soa2_a2':144.,
        'soa3_a1':144.,
        'soa3_a2':144.,                
        'soa4_a1':144.,  
        'soa4_a2':144., 
        'soa5_a1':144.,  
        'soa5_a2':144.,                                
        'bc_a1':12.,  
        'bc_a4':12., 
        'dst_a1':34.,                               
        'dst_a2':34.,
        'dst_a3':34.,
        'NH4':18.}

    ncPR = netCDF4.Dataset(templateIconFiles[0], 'r', format='NETCDF4')
    PR_MZ = {}
    PR_AE = {}
    for v in ncPR.variables.keys():
        if ncPR.variables[v].units.strip() == u"ppmV":
            PR_MZ[v] = ncPR.variables[v][0,:,0,0]
        elif ncPR.variables[v].units.strip() == u"micrograms/m**3":
            PR_AE[v] = ncPR.variables[v][0,:,0,0]

    PR_vars = PR_MZ.keys() + PR_AE.keys()
    ncPR.close()

    ALLSPEC = PR_vars + ALL_CM_SPEC
    ALLSPEC = list(set(ALLSPEC))
    ALLSPEC.sort()

    nvars = len(PR_vars)

    ## if we aren't forcing an update, check whether files exist and
    ## return early if possible
    if not forceUpdate:
        allFilesExist = True
        for idate, date in enumerate(dates):
            yyyymmdd_dashed = date.strftime('%Y-%m-%d')
            do_ICs = (idate == 0)
            for idom,dom in enumerate(doms):
                grid = GridNames[idom]
                chemdir = '{}/{}/{}'.format(ctmDir,yyyymmdd_dashed,dom)
                do_BCs = (dom == doms[0])
                ##
                outBCON = '{}/BCON.{}.{}.{}.nc'.format(chemdir,dom,grid,mech)
                outICON = '{}/ICON.{}.{}.{}.nc'.format(chemdir,dom,grid,mech)
                ##
                if do_BCs and (not os.path.exists(outBCON)):
                    allFilesExist = False
                ##
                if do_ICs and (not os.path.exists(outICON)):
                    allFilesExist = False
                ##
        ##
        if allFilesExist:
            return

    ##
    for idate, date in enumerate(dates):
        yyyymmdd_dashed = date.strftime('%Y-%m-%d')
        do_ICs = (idate == 0)
        for idom,dom in enumerate(doms):
            grid = GridNames[idom]
            mcipdir = '{}/{}/{}'.format(metDir,yyyymmdd_dashed,dom)
            chemdir = '{}/{}/{}'.format(ctmDir,yyyymmdd_dashed,dom)
            do_BCs = (dom == doms[0])

            if not (do_ICs or do_BCs):
                continue

            croFile = '{}/GRIDCRO2D_{}'.format(mcipdir,mcipsuffix[idom])
            dotFile = '{}/GRIDDOT2D_{}'.format(mcipdir,mcipsuffix[idom])
            bdyFile = '{}/GRIDBDY2D_{}'.format(mcipdir,mcipsuffix[idom])
            metFile = '{}/METCRO3D_{}'.format(mcipdir,mcipsuffix[idom])
            srfFile = '{}/METCRO2D_{}'.format(mcipdir,mcipsuffix[idom])
            outBCON = '{}/BCON.{}.{}.{}.nc'.format(chemdir,dom,grid,mech)
            outICON = '{}/ICON.{}.{}.{}.nc'.format(chemdir,dom,grid,mech)
            templateIconFile = templateIconFiles[idom]
            templateBconFile = templateBconFiles[idom]

            if do_BCs:
                if os.path.exists(outBCON):
                    os.remove(outBCON)
                shutil.copyfile(templateBconFile,outBCON)
                print "copy {} to {}".format(templateBconFile,outBCON)

            if do_ICs:
                if os.path.exists(outICON):
                    os.remove(outICON)
                shutil.copyfile(templateIconFile,outICON)
                print "copy {} to {}".format(templateIconFile,outICON)

            print dotFile
            ncdot= netCDF4.Dataset(dotFile, 'r', format='NETCDF4')
            nccro= netCDF4.Dataset(croFile, 'r', format='NETCDF4')
            ncbdy= netCDF4.Dataset(bdyFile, 'r', format='NETCDF4')
            ncmet= netCDF4.Dataset(metFile, 'r', format='NETCDF4')
            ncsrf= netCDF4.Dataset(srfFile, 'r', format='NETCDF4')
            ncin = netCDF4.Dataset(inputMozartFile, 'r', format='NETCDF4')

            if do_BCs:
                print "write BCs to file: ",outBCON
                ncoutb=netCDF4.Dataset(outBCON, 'r+', format='NETCDF4')
                all_vars = ncoutb.variables.keys()[1:]
                nvars = len(all_vars)

            if do_ICs:
                print "write ICs to file: ",outICON
                ncouti=netCDF4.Dataset(outICON, 'r+', format='NETCDF4')
                all_vars = ncoutb.variables.keys()[1:]
                nvars = len(all_vars)

            lens = dict()
            for k in nccro.dimensions.keys():
                lens[k] = len(nccro.dimensions[k])

            lens['PERIM'] = len(ncbdy.dimensions['PERIM'])
            lens['LAY'] = len(ncmet.dimensions['LAY'])
            lens['VAR'] = nvars
            lens['TSTEP'] = 1

            LAT  = nccro.variables['LAT'][:].squeeze()
            LON  = nccro.variables['LON'][:].squeeze()
            LATP = ncbdy.variables['LAT'][:].squeeze()
            LONP = ncbdy.variables['LON'][:].squeeze()
            LWMASK_BDY = ncbdy.variables['LWMASK'][:].squeeze()
            LWMASK_CRO = nccro.variables['LWMASK'][:].squeeze()
            sigma= ncmet.getncattr('VGLVLS')
            sigmah = (sigma[1:] + sigma[:-1])/2.0 ## half levels
            mtop = ncmet.getncattr('VGTOP')
            hyam = ncin.variables['hyam'][:]
            hybm = ncin.variables['hybm'][:]
            hyai = ncin.variables['hyai'][:]
            hybi = ncin.variables['hybi'][:]
            P0 = ncin.variables['P0'][:]
            PS = ncin.variables['PS'][:]
            T = ncin.variables['T'][:]
            #
#            base_MZ_time = datetime.datetime(1,1,1,0,0,0)
#            daysSinceBase = ncin.variables['time'][:] - 366.0
#            MZdates = [base_MZ_time + datetime.timedelta(days=t) for t in list(daysSinceBase)]
            base_MZ_time = datetime.datetime(2021,6,1,0,0,0)
            daysSinceBase = ncin.variables['time'][:] - 366.0
            MZdates = [base_MZ_time + datetime.timedelta(days=t) for t in list(daysSinceBase)]
            #
            latmz= ncin.variables['lat'][:].squeeze()
            lonmz= ncin.variables['lon'][:].squeeze()
            PSURF= ncsrf.variables['PRSFC'][:].squeeze()
            TFLAG= ncsrf.variables['TFLAG'][:,0,:].squeeze()
            yyyy =  TFLAG[:,0] / 1000
            jjj  =  TFLAG[:,0] % 1000
            hh   =  TFLAG[:,1] / 10000
            mm   = (TFLAG[:,1] - hh*10000) / 100
            ss   =  TFLAG[:,1] % 100
            ntimemod = len(yyyy)
            timesmod = [datetime.datetime(yyyy[i],1,1,0,0,0) + datetime.timedelta(days = float(jjj[i] - 1) + float(hh[i])/24.0 + float(mm[i])/(24.0 * 60.0) + float(ss[i])/(24.0 * 60.0 * 60.0)) for i in range(ntimemod)]
            itimes = numpy.where([t.date() == date.date() for t in timesmod])[0]
            itime0 = itimes[0]
            itime1 = itimes[-1]+2
            timesmod = timesmod[itime0:itime1]
            TFLAG = TFLAG[itime0:itime1]

            ## populate the pressure array
            P = numpy.zeros(T.shape)
            for itime in range(len(MZdates)):
                for irow  in range(len(latmz)):
                    for icol in range(len(lonmz)):
                        P[itime,:,irow,icol] = hyam * P0 + hybm * PS[itime,irow,icol]

            LATMZ = numpy.zeros((len(latmz), len(lonmz)))
            LONMZ = numpy.zeros((len(latmz), len(lonmz)))
            for irow in range(len(latmz)):
                LONMZ[irow,:] = lonmz

            for icol in range(len(lonmz)):
                LATMZ[:,icol] = latmz

            near_interior = numpy.zeros((LON.shape[0], LON.shape[1], 2),dtype = numpy.int)
            near_boundary = numpy.zeros((LONP.shape[0], 2),dtype = numpy.int)

            for irow in range(LON.shape[0]):
                for icol in range(LON.shape[1]):
                    dists = helper_funcs.getDistanceFromLatLonInKm(LAT[irow,icol],LON[irow,icol],LATMZ,LONMZ)
                    minidx = numpy.argmin(dists)
                    ix, iy = numpy.unravel_index(minidx, LONMZ.shape)
                    near_interior[irow,icol,0] = ix
                    near_interior[irow,icol,1] = iy

            for iperim in range(LONP.shape[0]):
                dists = helper_funcs.getDistanceFromLatLonInKm(LATP[iperim],LONP[iperim],LATMZ,LONMZ)
                minidx = numpy.argmin(dists)
                ix, iy = numpy.unravel_index(minidx, LONMZ.shape)
                near_boundary[iperim,0] = ix
                near_boundary[iperim,1] = iy

            ## prepare initial conditions
            if do_ICs:
                itimestart = [it for it, t in enumerate(timesmod) if t == date][0]

            iMZtime_for_each_CMtime = numpy.zeros((len(timesmod)),dtype = numpy.int)
            for itime, time in enumerate(timesmod):
                dtime = numpy.array([((time - t).total_seconds())/(24.0*60.0*60.0) for t in MZdates])
                if all(dtime < 0.0):
                    imin = numpy.argmin(numpy.abs(dtime))
                    iMZtime_for_each_CMtime[itime] = imin
                    warnings.warn("All dates were negative for date {}, using nearest match: {}".format(date.strftime('%Y-%m-%d %H:%M:%S'),MZdates[imin].strftime('%Y-%m-%d %H:%M:%S')))
                else:
                    iMZtime_for_each_CMtime[itime] = numpy.where(dtime >= 0)[0][-1]

            itimestart = [it for it, t in enumerate(timesmod) if t == date][0]
            iMZtime = iMZtime_for_each_CMtime[0]

            # To calculate pressure of each model grid box:
            # pres_Pa[ilon, ilat, ilev, itim] = hyam[ilev] * P0 + hybm[ilev] * PS[ilon, ilat, itim]
            # To calculate pressure at interfaces of each model grid box:
            # pres_int_Pa[ilon, ilat, ilev, itim] = hyai[ilev] * P0 + hybi[ilev] * PS[ilon, ilat, itim]

            ## interpolation from GEOS-CHEM to CMAQ levels
            if not ('Iz' in vars() or 'Iz' in globals()):
                irow = LON.shape[0]-1
                icol = LON.shape[1]-1
                itime = 0
                PRES_CM = (PSURF[itime,irow,icol] - mtop) * sigma +  mtop
                PRES_CM[0] = PSURF[itime,irow,icol]
                PRES_CM = (PRES_CM[1:] + PRES_CM[:-1]) / 2.0
                # PRES_MZ = Ap +  Bp * PSURF[itime,irow,icol]
                PRES_MZm = hyam * P0 + hybm * PSURF[itime,irow,icol]
                PRES_MZr = PRES_MZm[::-1]
                Iz = match_two_sorted_arrays(PRES_MZr,PRES_CM)

            ## set the values to zero for species that we *WILL* interpolate to
            for spec in ALL_CM_SPEC:
                if do_ICs:
                    if not spec in ncouti.variables.keys():
                        warnings.warn("Species {} was not found in template CMAQ IC file -- creating blank variable...".format(spec))
                        isnetcdf4 = (ncouti.data_model == 'NETCDF4')
                        ncouti.createVariable(varname = spec, datatype = 'f4', dimensions = ncouti.variables[defaultSpec].dimensions, zlib = isnetcdf4)
                        ncouti.long_name = '{:16}'.format(spec)
                        ncouti.units     = '{:16}'.format('ppmV')
                        ncouti.var_desc  = '{:80}'.format('Variable ' + spec)
                    ncouti.variables[spec][:] = 0.0
                if do_BCs:
                    if not spec in ncoutb.variables.keys():
                        warnings.warn("Species {} was not found in template CMAQ BC file -- creating blank variable...".format(spec))
                        isnetcdf4 = (ncoutb.data_model == 'NETCDF4')
                        ncoutb.createVariable(varname = spec, datatype = 'f4', dimensions = ncoutb.variables[defaultSpec].dimensions, zlib = isnetcdf4)
                        ncoutb.long_name = '{:16}'.format(spec)
                        ncoutb.units     = '{:16}'.format('ppmV')
                        ncoutb.var_desc  = '{:80}'.format('Variable ' + spec)
                    ncoutb.variables[spec][:] = 0.0


            nspec = len(species_map)
            for ispec in range(nspec):
                MZspec = species_map[ispec]['MZspec']
                CMspec = species_map[ispec]['CMspec']
                coefs = species_map[ispec]['coef']
                isAerosol = species_map[ispec]['isAerosol']
                if isAerosol[0]:
                    Factor = 1.0 ## keep as ug/m3
                else:
                    Factor = 1.0e3 ## convert from ppm to ppb
                ##
                nCMspec = len(CMspec)
                if do_ICs:
                    out_interior = extract_and_interpolate_interior(MZspec, ncin, lens, LON, Iz, iMZtime, isAerosol[0], mz_mw_aerosol, T, P, near_interior)
                    print_interior_variable(MZspec, out_interior, Factor)
                ##
                if do_BCs:
                    out_boundary = extract_and_interpolate_boundary(MZspec, ncin, lens, LONP, Iz, iMZtime_for_each_CMtime, isAerosol[0], mz_mw_aerosol, T, P, near_boundary)
                    print_boundary_variable(MZspec, out_boundary, Factor)
                ##
                for jspec in range(nCMspec):
                    cmspec = CMspec[jspec]
                    coef = coefs[jspec]
                    if do_ICs:
                        populate_interior_variable(ncouti, cmspec, out_interior, coef)
                    ##
                    if do_BCs:
                        populate_boundary_variable(ncoutb, cmspec, out_boundary, coef)

            if do_ICs:
                ncouti.close()
            if do_BCs:
                ncoutb.close()

            ncdot.close()
            nccro.close()
            ncbdy.close()
            ncmet.close()
            ncsrf.close()
            ncin.close()


