#!/bin/csh
#
# MET2MGN v2.10 
# --
#
#
# TPAR2IOAPI v2.03a 
# --added 26-category landuse capability for mm5camx (number of landuse categories defined by NLU) 
# --added capability for LATLON and UTM projections
# --added capability for MCIP v3.3 input (2m temperatures)
# --bug in PAR processing subroutine fixed where first few hours in GMT produced zero PAR
# --added code to fill missing par data (if valid data exists for the hours surrounding it)
#
# TPAR2IOAPI v2.0
# --added capability for MM5 or MCIP input
# 
#
#        RGRND/PAR options:
#           setenv MM5RAD  Y   Solar radiation obtained from MM5
#           OR 
#           setenv MCIPRAD Y   Solar radiation obtained from MCIP
#                  --MEGAN will internally calculate PAR for each of these options and user needs to  
#                    specify `setenv PAR_INPUT N' in the MEGAN runfile
#           OR
#           setenv SATPAR Y (satellite-derived PAR from UMD GCIP/SRB files)
#                  --user needs to specify `setenv PAR_INPUT Y' in the MEGAN runfile
#
#        TEMP options:
#           setenv CAMXTEMP Y         2m temperature, calculated from mm5camx output files
#           OR
#           setenv MM5MET  Y         2m temperature, calculated from MM5 output files
#                                     Note: 2m temperature is calculated since the P-X/ACM PBL
#                                     MM5 configuration (most commonly used LSM/PBL scheme for AQ 
#                                     modeling purposes) does not produce 2m temperatures.
#           OR
#           setenv MCIPMET Y         temperature obtained from MCIP
#              -setenv TMCIP  TEMP2   2m temperature, use for MCIP v3.3 or newer
#              -setenv TMCIP  TEMP1P5 1.5m temperature, use for MCIP v3.2 or older
#
#        TZONE   time zone for input mm5CAMx files 
#        NLAY    number of layers contained in input mm5CAMx files 
#        NLU     number of landuse categories contained in CAMx landuse file 
#

############################################################



############################################################
# Episodes
############################################################
set dom = TEMPLATE
set STJD = TEMPLATE
set EDJD = TEMPLATE

setenv EPISODE_SDATE TEMPLATE
setenv EPISODE_STIME TEMPLATE
set nDaysPerMcipFile = 1

############################################################
#set for grid
############################################################
setenv MCIPDIR TEMPLATE
setenv GRIDDESC $MCIPDIR/GRIDDESC
setenv GDNAM3D TEMPLATE
setenv MCIPSUFFIX TEMPLATE


############################################################
# Setting up directories and common environment variable
############################################################
source TEMPLATE/setcase.csh
setenv SCRATCHDIR TEMPLATE

setenv PROG met2mgn
setenv EXE $MGNEXE/$PROG

set logdir = $SCRATCHDIR/$PROG
if ( ! -e $logdir) mkdir -p $logdir

set INPPATH     = $MCIPDIR
set OUTPATH = TEMPLATE
if (! -e $OUTPATH) mkdir $OUTPATH

setenv PFILE $OUTPATH/PFILE
rm -fv $PFILE

############################################################
# Looping
############################################################
set JDATE = $STJD
echo $JDATE
# date -u -d '2011-01-01 + 031 days' +%Y%j
set Y4 = `echo $JDATE | cut -c 1-4`
set Y2 = `echo $JDATE | cut -c 3-4`
set J3 = `echo $JDATE | cut -c 5-7`
set MM = `date -u -d "$Y4-01-01 + $J3 days - 1 day" +%m`
set DD = `date -u -d "$Y4-01-01 + $J3 days - 1 day" +%d`
set Y4m1 = `date -u -d "$Y4-01-01 + $J3 days - 2 days" +%Y`
set Y2m1 = `date -u -d "$Y4-01-01 + $J3 days - 2 days" +%y`
set MMm1 = `date -u -d "$Y4-01-01 + $J3 days - 2 days" +%m`
set DDm1 = `date -u -d "$Y4-01-01 + $J3 days - 2 days" +%d`
set JDATE2 = `date -u -d "$Y4-$MM-$DD + $nDaysPerMcipFile days - 1 day" +%Y%j`
@ jdy  = $JDATE - 2000000
@ jdy2  = $JDATE2 - 2000000
setenv STDATE ${jdy}00
setenv ENDATE ${jdy2}23

while ($JDATE <= $EDJD)

setenv EPISODE_SDATE $JDATE
setenv EPISODE_STIME  000000    
rm -fv $PFILE

setenv METPATH TEMPLATE/${Y4}-${MM}-${DD}/${dom}

#TEMP/PAR input choices

#set if using MM5 output files
setenv MM5MET N
setenv MM5RAD N
#setenv numMM5 2
#setenv MM5file1 /pete/pete5/fcorner/met/links/MMOUT_DOMAIN1_G$Y4$MM$DD
#setenv MM5file2 /pete/pete5/fcorner/met/links/MMOUT_DOMAIN1_G$Y4$MM$DD

#set if using UMD satellite PAR data
set PARDIR = $MGNINP/PAR
setenv SATPAR N
set satpar1 = "$PARDIR/$Y2m1${MMm1}par.h"
set satpar2 = "$PARDIR/$Y2${MM}par.h"

if ($satpar1 == $satpar2) then
  setenv numSATPAR 1
  setenv SATPARFILE1 $satpar2
else
  setenv numSATPAR 2
  setenv SATPARFILE1 $satpar1
  setenv SATPARFILE2 $satpar2
endif

#set if using MCIP output files
setenv MCIPMET Y
setenv TMCIP  TEMP2          #MCIP v3.3 or newer
#setenv TMCIP  TEMP1P5       #MCIP v3.2 or older

setenv MCIPRAD Y 
if ($JDATE == $EPISODE_SDATE) then
  setenv METCRO2Dfile1 $METPATH/METCRO2D_$MCIPSUFFIX
else
  setenv METCRO2Dfile1 $METPATH/METCRO2D_$MCIPSUFFIX
  setenv METCRO2Dfile2 $METPATH/METCRO2D_$MCIPSUFFIX
endif
setenv METCRO3Dfile  $METPATH/METCRO3D_$MCIPSUFFIX
setenv METDOT3Dfile  $METPATH/METDOT3D_$MCIPSUFFIX

setenv OUTFILE $OUTPATH/MET.MEGAN.$GDNAM3D.$JDATE.ncf
rm -rf $OUTFILE

$EXE

set Y4m1 = $Y4
set Y2m1 = $Y2
set MMm1 = $MM
set DDm1 = $DD
set Y4 = `date -u -d "$Y4m1-$MMm1-$DDm1 + $nDaysPerMcipFile days" +%Y`
set Y2 = `date -u -d "$Y4m1-$MMm1-$DDm1 + $nDaysPerMcipFile days" +%y`
set MM = `date -u -d "$Y4m1-$MMm1-$DDm1 + $nDaysPerMcipFile days" +%m`
set DD = `date -u -d "$Y4m1-$MMm1-$DDm1 + $nDaysPerMcipFile days" +%d`
set J3 = `date -u -d "$Y4-$MM-$DD" +%j`
set JDATE = `date -u -d "$Y4-$MM-$DD" +%Y%j`
set JDATE2 = `date -u -d "$Y4-$MM-$DD + $nDaysPerMcipFile days - 1 day" +%Y%j`
echo $JDATE
@ jdy  = $JDATE - 2000000
@ jdy2  = $JDATE2 - 2000000
setenv STDATE ${jdy}00
setenv ENDATE ${jdy2}23


end  # End while JDATE
