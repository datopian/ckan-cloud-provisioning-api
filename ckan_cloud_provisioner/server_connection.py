from io import StringIO
import os
import sys
import time
import logging

import fabric
from paramiko import RSAKey
from concurrent.futures import ThreadPoolExecutor, TimeoutError
from queue import Queue, Empty

from .config import instance_manager, default_timeout, default_cancel_timeout

private_ssh_key = os.environ['PRIVATE_SSH_KEY']

private_ssh_key = StringIO(private_ssh_key)
private_ssh_key = RSAKey.from_private_key(private_ssh_key)


def get_connection():
    return fabric.Connection(instance_manager, connect_kwargs=dict(pkey=private_ssh_key))

def cca_cmd(cmd, out_stream=None):
    options = dict(
        pty=True
        out_stream=out_stream
    )
    return get_connection().run(f'./cca-operator.sh {cmd}', **options)

server_executor = ThreadPoolExecutor(max_workers=1)
task_canceller = ThreadPoolExecutor(max_workers=1)

def cancel(q: Queue, timeout):
    def func():
        try:
            q.get(timeout=timeout)
            logging.error('COMPLETED SUCCESSFULLY!')
        except Empty:
            logging.error('CANCELLING!')
            get_connection().run('ps -ef | grep cca-operator | grep -v server | grep -v grep | cut -c1-6 | xargs kill -9')
    return func


def combined(q, inner):
    def func():
        ret = inner()
        q.put(True)
        return ret
    return func

def execute_remote(func, cancel_timeout=default_cancel_timeout):
    try:
        q = Queue()
        res = server_executor.submit(combined(q, func))
        task_canceller.submit(cancel(q, cancel_timeout))
        ret = res.result(timeout=default_timeout)
        return ret
    except TimeoutError:
        return {}
    except Exception as e:
        return dict(
            success=False,
            errors=str(e)
        )


def ping():
    def func():
        try:
            ping = get_connection().run('echo ping', hide='both')
            logging.error('PING RESULT %r', ping.stdout)
            logging.error('PING ERRORS %r', ping.stderr)
        except Exception as e:
            logging.error('PING ERROR %r', e)

    execute_remote(func)

ping()