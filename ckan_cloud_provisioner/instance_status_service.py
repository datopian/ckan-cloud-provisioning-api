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
                res = get_connection().run(f'./cca-operator.sh ./list-instances.sh', hide='both')
                status = yaml.load(res.stdout.split('------')[0])
                for k, v in status.items():
                    res = get_connection().run(f'./cca-operator.sh ./get-instance-values.sh "{k}"', hide='both')
                    instance_values = yaml.load(res.stdout)
                    instance_values.update(v)
                    v.update(instance_values)
                with self.lock:
                    self.status = status
                print(self.status)
            except Exception as e:
                print(e)
            time.sleep(60)

    def instance_status(self):
        ret = None
        with self.lock:
            ret = self.status
        return ret

    @staticmethod
    def start_service():
        cis = CachedInstanceStatus()
        cis.start()
        return cis
