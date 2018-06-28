FROM heroku/miniconda:3

RUN apt-get update
RUN apt-get install -y \
    git-all build-essential libtool \
    pkg-config autotools-dev autoconf automake cmake \
    uuid-dev libpcre3-dev valgrind

WORKDIR /home

RUN git clone git://github.com/zeromq/libzmq.git && \
cd libzmq && \
./autogen.sh && \
./configure && \
make check && \
make install && \
ldconfig

RUN git clone git://github.com/zeromq/czmq.git && \
cd czmq && \
./autogen.sh && ./configure && make check && \
make install && \
ldconfig
