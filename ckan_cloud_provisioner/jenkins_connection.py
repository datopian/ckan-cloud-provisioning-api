import os
import requests
from requests.auth import HTTPBasicAuth
import json
import yaml

JENKINS_ENDPOINT = os.environ['JENKINS_ENDPOINT']
JENKINS_USER = os.environ['JENKINS_USER']
JENKINS_TOKEN = os.environ['JENKINS_TOKEN']

def run_jenkins(job, **params):
    body=dict(
            parameter=[
                dict(name=k, value=v)
                for k, v
                in params.items()
            ]
    )
    resp = requests.post(
        f'{JENKINS_ENDPOINT}/job/{job}/build',
        auth=HTTPBasicAuth(JENKINS_USER, JENKINS_TOKEN),
        data=dict(
            json=json.dumps(body)
        )
    )
    return resp.status_code in (
        requests.codes.ok, requests.codes.created
    ), resp.text

def instance_status():
    resp = requests.get(
        f'{JENKINS_ENDPOINT}/job/Provisioning%20-%20instance%20status/lastSuccessfulBuild/consoleText',
        auth=HTTPBasicAuth(JENKINS_USER, JENKINS_TOKEN),
    )
    resp = resp.text.split('---')[1].split('\nFinished: ')[0]
    resp = yaml.load(resp)
    return resp

if __name__ == '__main__':
    r = run_jenkins('test_test', param1='David', param2='Moshe')
    print(r)
    r = instance_status()
    print(r)
