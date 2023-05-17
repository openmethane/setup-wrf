#! /bin/csh -f
########################################################################
source TEMPLATE/setcase.csh
## Directory setups
setenv PRJ TEMPLATE
setenv PROMPTFLAG N

# Program directory
setenv PROG   mgn2mech
setenv EXEDIR $MGNEXE
setenv EXE    $EXEDIR/$PROG

# Input map data directory
setenv INPDIR $MGNINP

# Intermediate file directory
setenv INTDIR $SCRATCHDIR

# Output directory
setenv OUTDIR TEMPLATE

# MCIP input directory
setenv MCIPDIR TEMPLATE
setenv METDIR $MCIPDIR
setenv GRIDDESC $MCIPDIR/GRIDDESC

# Log directory
setenv LOGDIR $MGNLOG/$PROG
if ( ! -e $LOGDIR ) mkdir -p $LOGDIR
########################################################################

set dom = TEMPLATE
set STJD = TEMPLATE
set EDJD = TEMPLATE
set JD = $STJD
while ($JD <= $EDJD)
########################################################################
# Set up time and date to process
setenv SDATE $JD        #start date
setenv STIME 0
setenv RLENG 240000
setenv TSTEP 10000
########################################################################

########################################################################
# Set up for MECHCONV
setenv RUN_SPECIATE   Y    # run MG2MECH

setenv RUN_CONVERSION Y    # run conversions?
                           # run conversions MEGAN to model mechanism
                           # units are mole/s

setenv SPCTONHR       N    # speciation output unit in tonnes per hour
                           # This will convert 138 species to tonne per
                           # hour or mechasnim species to tonne per hour.
                           
# If RUN_CONVERSION is set to "Y", one of mechanisms has to be selected.
setenv MECHANISM TEMPLATE
#setenv MECHANISM    RADM2
#setenv MECHANISM    RACM
#setenv MECHANISM    CBMZ
#setenv MECHANISM    CB05
#setenv MECHANISM    CB6
#setenv MECHANISM    SOAX
#setenv MECHANISM    SAPRC99
#setenv MECHANISM    SAPRC99Q
#setenv MECHANISM    SAPRC99X

# Grid name
setenv GDNAM3D TEMPLATE

# EFMAPS NetCDF input file
setenv EFMAPS  $INPDIR/EFMAPS.${PRJ}_${dom}.ncf

# PFTS16 NetCDF input file
setenv PFTS16  $INPDIR/PFTS16.${PRJ}_${dom}.ncf

# MEGAN ER filename
setenv MGNERS $OUTDIR/ER.$GDNAM3D.${SDATE}.ncf

# Output filename
setenv MGNOUT $OUTDIR/MEGANv2.10.$GDNAM3D.$MECHANISM.$SDATE.ncf

########################################################################
## Run speciation and mechanism conversion
if ( $RUN_SPECIATE == 'Y' ) then
   rm -f $MGNOUT
   $EXE
endif

@ JD++
end  # End while JD
