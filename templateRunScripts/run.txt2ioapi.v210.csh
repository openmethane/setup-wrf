#! /bin/csh -f
########################################################################
## Common setups
source TEMPLATE/setcase.csh

setenv PRJ TEMPLATE
setenv DOM TEMPLATE
setenv MCIPDIR TEMPLATE

setenv PROMPTFLAG N
setenv PROG   txt2ioapi
setenv EXEDIR $MGNEXE
setenv EXEC   $EXEDIR/$PROG
setenv GRIDDESC $MCIPDIR/GRIDDESC
setenv GDNAM3D TEMPLATE

## File setups
## Inputs
setenv EFSTXTF $MGNINP/EF210_${PRJ}_${DOM}.csv
setenv PFTTXTF $MGNINP/PFT210_${PRJ}_${DOM}.csv
setenv LAITXTF $MGNINP/LAI210_${PRJ}_${DOM}.csv
## Outputs
setenv EFMAPS  $MGNINP/EFMAPS.${PRJ}_${DOM}.ncf
setenv PFTS16  $MGNINP/PFTS16.${PRJ}_${DOM}.ncf
setenv LAIS46  $MGNINP/LAIS46.${PRJ}_${DOM}.ncf

## Run control
setenv RUN_EFS T       # [T|F]
setenv RUN_LAI T       # [T|F]
setenv RUN_PFT T       # [T|F]
########################################################################





## Run TXT2IOAPI
rm -f $EFMAPS $LAIS46 $PFTS16
if ( ! -e $MGNLOG/$PROG ) mkdir -p $MGNLOG/$PROG
$EXEC | tee $MGNLOG/$PROG/log.run.$PROG.${PRJ}_${DOM}.txt
