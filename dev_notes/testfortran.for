c to convert to f77, comment out open statements and call to date and time
c and fix zeros in format statements 200 and 201 in out. Also change
c format to * for f2c.
      module model
      use iso_c_binding
      implicit none
C      character*64 fname
      contains
      subroutine runmodel(fname, n) bind (C)
      use iso_c_binding, only: C_CHAR, c_null_char
      integer(c_int), value :: n
      character(kind = c_char) :: fname(n)
C      character*64, intent(in) :: fname
      print*, 'hey there', fname
      return
      end subroutine runmodel
      end module model
