# I-Remote-Procedure-Call

- Python- Test via:

Terminal window 1:
`python kernel.py`

Terminal window 2:
`python client.py`

- C- Test via:

Terminal window 1:
`docker run -p 5555:5555 -it opensourcepolicycenter/irpc /bin/bash`

In container run:
```
gcc kernel.c -o kernel -lczmq -lzmq
./kernel
```

Terminal window 2:
`python helloworld.py`
