#
setenv SCRATCHDIR TEMPLATE
setenv MGNHOME TEMPLATE
setenv CTMDIR TEMPLATE
setenv MGNSRC $MGNHOME/src
setenv MGNLIB $MGNHOME/lib
setenv MGNEXE $MGNHOME/bin
setenv MGNRUN $CTMDIR #
setenv MGNINP $CTMDIR # 
setenv MGNOUT $CTMDIR #
setenv MGNINT $SCRATCHDIR #
setenv MGNLOG $CTMDIR #

if ( ! -e $MGNINP ) then
   mkdir -p $MGNINP/MAP
   mkdir -p $MGNINP/MGNMET
   mkdir -p $MGNINP/PAR
endif
if ( ! -e $MGNINT ) mkdir -p $MGNINT
if ( ! -e $MGNLOG ) mkdir -p $MGNLOG
