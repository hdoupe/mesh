library(pbdZMQ)
library(msgpack)
ctxt <- init.context()
socket <- init.socket(ctxt, "ZMQ_REP")
bind.socket(socket, "tcp://*:5555")

individual <- function (x) {
  x + 5
}

corporate <- function (x, y) {
  x + y
}

while (TRUE) {
  req <- unpackMsg(receive.socket(socket, unserialize = FALSE), simplify = FALSE)
  rep <- packMsg(do.call(req[["endpoint"]], req[["contents"]]))
  send.socket(socket, rep, serialize = FALSE)
}
