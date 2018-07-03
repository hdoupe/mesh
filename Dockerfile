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


EXPOSE 5566
EXPOSE 5567

RUN mkdir /home/irpc

COPY ./irpc/c_rpc/kernel.c /home/irpc
COPY ./irpc/c_rpc/jsontest.c /home/irpc

WORKDIR /home/irpc

ENV LD_LIBRARY_PATH "/home/cJSON/build/"

RUN gcc kernel.c -o kernel -lczmq -lzmq -lcjson
RUN gcc jsontest.c -o jsontest -lcjson

CMD ["/bin/bash"]
