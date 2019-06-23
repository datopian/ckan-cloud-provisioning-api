import sys
from io import StringIO
import threading
import pathlib
import datetime
import time 

from fabric import Connection
import json
from slugify import slugify

from auth.models import get_user

from .models import create_or_edit, delete, query, User, Instance
from .instance_status_service import CachedInstanceStatus
from .values import convert_body, kinds

cis = None
LOG_PATH = '/var/log/provisioning/'
LOG_SUFFIX = '_create.log'


def init():
    global cis
    cis = CachedInstanceStatus.start_service()


def create_or_edit_instance(id, body):
    # Calculate id if necessary
    if not id:
        title = body.get('params', {}).get('siteTitle')
        if title:
            title = title + ' ' + hex(int(time.time()))[2:]
            id = slugify(title, separator='-', to_lower=True)
            body['id'] = id

    # Convert values
    try:
        values = convert_body(body)
    except ValueError as e:
        return dict(
            success=False,
            errors=str(e)
        )

    # Add record to DB
    ret = create_or_edit(Instance, id, values)
    ret['id'] = id
        
    # is active?
    active = cis.instance_status().get(id, {}) is not None
    # "11fc0a16c05508b19e97de7ccb4451ac50"
    ret['success'], ret['errors'] = run_jenkins(
        "Project Provisioning - new instance",
        VALUES=json.dumps(values, ensure_ascii=True),
        INSTANCE_ID=body['id']
    )
    
    return ret

def delete_instance(id):
    # Delete instance from DB
    ret = delete(Instance, id)

    # # Put file and create instance
    # def executor(id_):
    #     def func():
    #         res = cca_cmd(f'./delete-instance.sh "{id_}"')
    #         return dict(
    #             success=res.ok,
    #             errors=res.stderr
    #         )
    #     return func

    # ret.update(execute_remote(executor(id), cancel_timeout=30))
    return ret

def query_instances():
    global cis

    query_results = query(Instance)

    status = cis.instance_status()
    instances = []
    for ret in query_results['results']:
        params = {}
        value = ret['value']
        for f in ('active', 'status'):
            if f in value:
                del value[f]
        params.update(status.get(ret['key'], {}))
        params.update(ret['value'])
        instances.append(
            dict(
                id=ret['key'],
                kind=params.get('kind'),
                params=params,
                active=params.get('ready'),
            )
        )

    return dict(
        instances=instances
    )

def create_or_edit_user(id, body):
    ret = create_or_edit(User, id, body)
    return ret

def delete_user(id):
    ret = delete(User, id)
    return ret

def query_users(userid):
    user = get_user(userid)
    if user is None: return {}
            
    email = user.get('email')
    if email is None: return {}

    ret = query(User)

    for user in ret['results']:
        user['self'] = user['key'] == email

    return ret

def instance_kinds():
    return dict(
        kinds=kinds()
    )

# def instance_connection_info(id):
#     ret = {}
#     # Put file and create instance
#     def executor(id_):
#         def func():
#             res = cca_cmd(f'./instance-connection-info.sh "{id_}"')
#             passwords = [
#                 line.strip().split(':')[-1].strip()
#                 for line in res.stdout.split('\n')
#                 if 'admin password' in line
#             ]
#             if len(passwords) > 0:
#                 password = passwords[0]
#             else:
#                 password = '<not-set>'
#             try:
#                 log = open(f'{LOG_PATH}{id_}{LOG_SUFFIX}').read().split('\n')
#             except:
#                 log = []
#             return dict(password=password, log=log)
#         return func

#     ret.update(execute_remote(executor(id), cancel_timeout=30, ro_executor=True))
#     return ret        
