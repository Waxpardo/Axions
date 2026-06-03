ccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc
c      written by the UFO converter
ccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc

      SUBROUTINE COUP1( )

      IMPLICIT NONE

      INCLUDE 'model_functions.inc'
      INCLUDE '../vector.inc'


      DOUBLE PRECISION PI, ZERO
      PARAMETER  (PI=3.141592653589793D0)
      PARAMETER  (ZERO=0D0)
      INCLUDE 'input.inc'
      INCLUDE 'coupl.inc'
      GC_4 = -(MDL_EE*MDL_COMPLEXI)
      GC_17 = -(MDL_EE__EXP__2*MDL_COMPLEXI*MDL_KB)/(8.000000D+00
     $ *MDL_FA*PI**2)-(MDL_EE__EXP__2*MDL_COMPLEXI*MDL_KW)/(8.000000D
     $ +00*MDL_FA*PI**2)
      GC_40 = (MDL_EE*MDL_COMPLEXI*MDL_SW)/MDL_CW
      GC_43 = -(MDL_CW*MDL_EE*MDL_COMPLEXI)/(2.000000D+00*MDL_SW)
     $ +(MDL_EE*MDL_COMPLEXI*MDL_SW)/(2.000000D+00*MDL_CW)
      GC_45 = -(MDL_CW*MDL_EE__EXP__2*MDL_COMPLEXI*MDL_KW)/(8.000000D
     $ +00*MDL_FA*PI**2*MDL_SW)+(MDL_EE__EXP__2*MDL_COMPLEXI*MDL_KB
     $ *MDL_SW)/(8.000000D+00*MDL_CW*MDL_FA*PI**2)
      END
