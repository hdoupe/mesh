c to convert to f77, comment out open statements and call to date and time
c and fix zeros in format statements 200 and 201 in out. Also change
c format to * for f2c.
      module model
      use iso_c_binding
      implicit none
C      character*64 fname
      contains
      subroutine runmodel(c_fname, fnamesize, c_arg, argsize,
     + c_buffer, buffersize) bind (C)
      use iso_c_binding, only: C_CHAR, c_null_char
      integer :: i
      integer(c_int), value :: fnamesize
      character(kind = c_char) :: c_fname(fnamesize)
      character(:), allocatable :: fname
      integer(c_int), value :: argsize
      character(kind = c_char) :: c_arg(argsize)
      character(:), allocatable :: arg
      integer(c_int), value :: buffersize
      character(kind = c_char) :: c_buffer(buffersize)
      character(len=buffersize) :: fbuffer


      allocate(character(fnamesize) :: fname)
      allocate(character(argsize) :: arg)

      forall (i = 1:fnamesize) fname(i:i) = c_fname(i)
      forall (i = 1:argsize) arg(i:i) = c_arg(i)

      fbuffer = "hellothere"//c_null_char
      do i = 1, len_trim(fbuffer)
          print *, i, c_buffer
          c_buffer(i) = fbuffer(i:i)
      end do

      print*, 'hey there', fname, arg
      open(0,file=fname, status='old')
      return
      end subroutine runmodel
      end module model
