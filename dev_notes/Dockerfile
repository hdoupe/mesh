FROM zeromqorg/czmq

USER root

RUN apt-get update && apt-get -y install gfortran


WORKDIR /home

RUN mkdir /home/taxsim

COPY ./testfortran.for /home/taxsim
COPY ./taxsimlink.c /home/taxsim

WORKDIR /home/taxsim

RUN gcc -c taxsimlink.c -o taxsimlink.o
# RUN gfortran -c taxsim9.for -o taxsim9_mod.o
RUN gfortran -c testfortran.for -o testfortran.o

CMD ["/bin/bash"]
