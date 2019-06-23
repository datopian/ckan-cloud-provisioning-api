import threading
import yaml
import time
from fabric import Connection

from .jenkins_connection import instance_status

class CachedInstanceStatus(threading.Thread):

    def __init__(self):
        super().__init__(name='instance-status', daemon=True)
        self.status = {}
        self.lock = threading.Lock()
    
    def run(self):
        while True:
            try:
                status = instance_status()
                with self.lock:
                    self.status = status
                print(self.status)
            except Exception as e:
                print(e)
            time.sleep(10)

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
