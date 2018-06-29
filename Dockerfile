FROM zeromqorg/czmq

USER root

#install msgpack
RUN git clone https://github.com/msgpack/msgpack-c.git
RUN cd msgpack-c/ && \
    cmake . && \
    make && \
    make install


EXPOSE 5566
EXPOSE 5567

RUN mkdir /home/irpc

COPY ./irpc/c_rpc/kernel.c /home/irpc

WORKDIR /home/irpc

RUN gcc kernel.c -o kernel -lczmq -lzmq

CMD ["/bin/bash"]
