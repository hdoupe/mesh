FROM zeromqorg/czmq

USER root

EXPOSE 5555

RUN mkdir /home/irpc

COPY ./irpc/c_rpc/kernel.c /home/irpc

WORKDIR /home/irpc

CMD ["/bin/bash"]
