c to convert to f77, comment out open statements and call to date and time
c and fix zeros in format statements 200 and 201 in out. Also change
c format to * for f2c.

      subroutine runmodel() bind (C)
      use iso_c_binding, only: C_CHAR, c_null_char
      implicit none
      print*, 'hey there'
      return
      end subroutine runmodel
