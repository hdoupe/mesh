FROM zeromqorg/czmq

USER root

WORKDIR /home

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
COPY ./irpc/c_rpc/msgpacktest.c /home/irpc

WORKDIR /home/irpc

# necessary to resolve msgpack error:
# error while loading shared libraries: libmsgpackc.so.2: cannot open shared object file: No such file or directory
ENV LD_LIBRARY_PATH "/usr/local/lib"

RUN gcc kernel.c -o kernel -lczmq -lzmq
RUN gcc msgpacktest.c -lmsgpackc -o msgpacktest

CMD ["/bin/bash"]
