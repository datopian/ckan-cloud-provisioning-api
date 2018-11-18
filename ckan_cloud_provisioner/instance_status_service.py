import threading
import yaml
import time
from fabric import Connection

from .server_connection import get_connection

class CachedInstanceStatus(threading.Thread):

    def __init__(self):
        super().__init__(name='instance-status', daemon=True)
        self.status = {}
        self.lock = threading.Lock()
    
    def run(self):
        while True:
            try:
                res = get_connection().run(f'cd /cca-operator && ./cca-operator.sh ./list-instances.sh', hide='both')
                with self.lock:
                    self.status = yaml.load(res.stdout)
                print(self.status)
            except Exception as e:
                print(e)
            time.sleep(60)

    def instance_status(self):
        ret = None
        with self.lock:
            ret = self.status
        return ret


cis = CachedInstanceStatus()
cis.start()
