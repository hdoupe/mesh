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

RUN apt-get update && apt-get -y install gcc gfortran valgrind

EXPOSE 5566
EXPOSE 5567

RUN mkdir /home/irpc

COPY ./irpc/c_rpc/kernel.c /home/irpc
COPY ./taxsim/taxsim9.for /home/irpc
COPY ./taxsim/taxsim9_unmodified.for /home/irpc

COPY ./taxsim/data/puf_taxsim_state_small.txt /home/irpc

WORKDIR /home/irpc

ENV LD_LIBRARY_PATH "/home/cJSON/build/"

RUN gcc -c kernel.c -o kernel.o -g
RUN gfortran kernel.o taxsim9.for -o linked -lczmq -lzmq -lcjson -g

RUN gfortran taxsim9_unmodified.for -o taxsim9_unmod

CMD ["/bin/bash"]
