#! /bin/csh -f
########################################################################
source TEMPLATE/setcase.csh
## Directory setups
setenv PRJ TEMPLATE
setenv PROMPTFLAG N
set nDaysPerMcipFile = 1

# Program directory
setenv PROG   emproc
setenv EXEDIR $MGNEXE
setenv EXE    $EXEDIR/$PROG

setenv SCRATCHDIR TEMPLATE
setenv MCIPDIR TEMPLATE

# Input map data directory
setenv INPDIR TEMPLATE

# MCIP input directory
setenv METDIR $MCIPDIR

# Intermediate file directory
setenv INTDIR $SCRATCHDIR

# Output directory
setenv OUTDIR TEMPLATE

# Log directory
setenv LOGDIR $SCRATCHDIR/$PROG
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
setenv RLENG `echo "$nDaysPerMcipFile*24" | bc | xargs printf "%0.2i0000" `
########################################################################

########################################################################
# Set up for MEGAN
setenv RUN_MEGAN   Y       # Run megan?


# By default MEGAN will use data from MGNMET unless specify below
setenv ONLN_DT     Y       # Use online daily average temperature
                           # No will use from EFMAPS

setenv ONLN_DS     Y       # Use online daily average solar radiation
                           # No will use from EFMAPS

# Grid definition
setenv GRIDDESC $MCIPDIR/GRIDDESC
setenv GDNAM3D TEMPLATE

# EFMAPS
setenv EFMAPS $INPDIR/EFMAPS.${PRJ}_${dom}.ncf

# PFTS16
setenv PFTS16 $INPDIR/PFTS16.${PRJ}_${dom}.ncf

# LAIS46
setenv LAIS46 $INPDIR/LAIS46.${PRJ}_${dom}.ncf

# MGNMET
setenv MGNMET $OUTDIR/MET.MEGAN.$GDNAM3D.${SDATE}.ncf

# Output
setenv MGNERS $OUTDIR/ER.$GDNAM3D.${SDATE}.ncf

########################################################################
## Run MEGAN
if ( $RUN_MEGAN == 'Y' ) then
   rm -f $MGNERS
   time $EXE
endif

@ JD++
end  # End while JD
