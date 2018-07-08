c to convert to f77, comment out open statements and call to date and time
c and fix zeros in format statements 200 and 201 in out. Also change
c format to * for f2c.
      module model
      use iso_c_binding
      implicit none
C      character*64 fname
      contains
      subroutine runmodel(fname, fnamesize, arg, argsize) bind (C)
      use iso_c_binding, only: C_CHAR, c_null_char
      integer(c_int), value :: fnamesize
      character(kind = c_char) :: fname(fnamesize)
      integer(c_int), value :: argsize
      character(kind = c_char) :: arg(argsize)
      print*, 'hey there', fname, arg
      return
      end subroutine runmodel
      end module model
