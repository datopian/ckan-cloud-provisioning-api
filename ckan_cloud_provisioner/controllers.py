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
from .jenkins_connection import run_jenkins
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
    ret['active'] = cis.instance_status().get(id, {}) is not None
    ret['success'], ret['errors'] = run_jenkins(
        "Provisioning - new instance",
        VALUES=json.dumps(values, ensure_ascii=True),
        INSTANCE_ID=body['id']
    )
    
    return ret

def delete_instance(id):
    # Delete instance from DB
    ret = delete(Instance, id)

    ret['success'], ret['errors'] = run_jenkins(
        "Provisioning - delete instance",
        INSTANCE_ID=id
    )
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

