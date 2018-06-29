library(pbdZMQ)
library(msgpack)
ctxt <- init.context()
socket <- init.socket(ctxt, "ZMQ_REP")
bind.socket(socket, "tcp://*:5555")

while (TRUE) {
  cat("Client command:  ")
  msg <- unpackMsg(receive.socket(socket, unserialize = FALSE))

  cat(msg, "\n")
  send.socket(socket, packMsg("Message received!"), serialize = FALSE)
}

