FROM zeromqorg/czmq

USER root

RUN apt-get update && apt-get -y install gfortran


WORKDIR /home

RUN mkdir /home/taxsim

COPY ./taxsimlink.c /home/taxsim
#COPY ./taxsim9.for /home/taxsim
COPY ./testfortran.for /home/taxsim

COPY ./data.txt /home/taxsim

WORKDIR /home/taxsim

RUN gcc -c taxsimlink.c -o taxsimlink.o

#RUN gfortran taxsimlink.o taxsim9.for -o linked
RUN gfortran taxsimlink.o testfortran.for -o linked

CMD ["./linked"]
