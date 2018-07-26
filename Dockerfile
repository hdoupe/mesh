FROM zeromqorg/czmq

USER root

WORKDIR /home

#install cJSON
RUN git clone https://github.com/DaveGamble/cJSON
RUN cd cJSON && \
    mkdir build && \
    cd build && \
    cmake .. && \
    make && \
    make install

RUN apt-get update && apt-get -y install gfortran valgrind

EXPOSE 5566
EXPOSE 5567

RUN mkdir /home/irpc

COPY ./irpc/c_rpc/kernel.c /home/irpc
COPY ./taxsim/taxsim9.for /home/irpc
COPY ./taxsim/data/puf_taxsim.txt /home/irpc

WORKDIR /home/irpc

ENV LD_LIBRARY_PATH "/home/cJSON/build/"

RUN gcc -c kernel.c -o kernel.o -g

RUN gfortran kernel.o taxsim9.for -o linked -lczmq -lzmq -lcjson -g


CMD ["/bin/bash"]
