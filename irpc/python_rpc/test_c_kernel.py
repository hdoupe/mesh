from io import StringIO

from client import Client
from serializers import receive_json, send_json
import pandas as pd

OUTPATH = '../../taxsim/tests/results/{}'

with open('../../taxsim/data/puf_taxsim_small.txt') as f:
    puf_taxsim_small = f.read()
with open('../../taxsim/data/puf_taxsim.txt') as f:
    puf_taxsim = f.read()
with open('../../taxsim/data/puf_taxsim_state_small.txt') as f:
    puf_taxsim_state_small = f.read()
with open('../../taxsim/data/puf_taxsim_state.txt') as f:
    puf_taxsim_state = f.read()
with open('../../taxsim/data/puf_taxsim_bad.txt') as f:
    puf_taxsim_state_bad = f.read()

filenames = ['puf_taxsim_small.txt', 'puf_taxsim.txt',
             'puf_taxsim_state_small.txt', 'puf_taxsim_state.txt']


args = {'mtr_wrt_group': 'detail', 'file_name': 'puf_taxsim.txt'}
endpoint = 'taxsim'


test_cases = {
    'puf_small_buffer': {
        'arg': puf_taxsim_small,
        'out': 'kernel_puf_taxsim_small_buffer.txt'
    },
    'puf_buffer': {
        'arg': puf_taxsim,
        'out': 'kernel_puf_taxsim_buffer.txt'
    },
    'puf_small_filename': {
        'arg': 'puf_taxsim_small.txt',
        'out': 'kernel_puf_taxsim_small_name.txt'
    },
    'puf_filename': {
        'arg': 'puf_taxsim.txt',
        'out': 'kernel_puf_taxsim_name.txt'
    },
    'puf_state_small_buffer': {
        'arg': puf_taxsim_state_small,
        'out': 'kernel_puf_taxsim_state_small_buffer.txt'
    },
    'puf_state_buffer': {
        'arg': puf_taxsim_state,
        'out': 'kernel_puf_taxsim_state_buffer.txt'
    },
    'puf_state_small_filename': {
        'arg': 'puf_taxsim_state_small.txt',
        'out': 'kernel_puf_taxsim_state_small_name.txt'
    },
    'puf_state_filename': {
        'arg': 'puf_taxsim_state.txt',
        'out': 'kernel_puf_taxsim_state_name.txt'
    },
}

for tc in test_cases:
    with Client(health_port='5566', submit_job_port='5567',
                get_job_port='5568') as client:
        args['file_name'] = test_cases[tc]['arg']
        job_id = client.submit(endpoint, args, send_func=send_json)
        result = client.get(job_id, receive_func=receive_json)

        with open(OUTPATH.format(test_cases[tc]['out']), 'w') as f:
            f.write(result)
