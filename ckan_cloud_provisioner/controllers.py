import sys
from io import StringIO
import threading
import pathlib

from fabric import Connection
import yaml

from auth.models import get_user

from .models import create_or_edit, delete, query, User, Instance
from .server_connection import get_connection, execute_remote, cca_cmd
from .instance_status_service import CachedInstanceStatus
from .values import convert_body, kinds

cis = None


def init():
    global cis
    cis = CachedInstanceStatus.start_service()


def create_or_edit_instance(id, body):
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
    
    # Prepare values yaml
    values_file = StringIO()
    yaml.dump(values, stream=values_file)
    values_file.seek(0)
    
    # is active?
    active = cis.instance_status().get(id, {}).get('active', False)

    # Put file and create instance
    def executor(id_, active_, values_file_):
        def func():
            try:
                conn = get_connection()
                res = conn.put(values_file_, f'/etc/ckan-cloud/{id_}_values.yaml')
                if active_:
                    res = cca_cmd(f'./update-instance.sh "{id_}"')
                else:
                    res = cca_cmd(f'./create-instance.sh "{id_}"')
                return dict(
                    success=res.ok,
                    errors=res.stderr
                )
            except Exception as e:
                print(e, file=sys.stderr)
                return dict(
                    success=False,
                    errors=str(e)
                )
        return func
    
    ret.update(execute_remote(executor(id, active, values_file)))
    return ret

def delete_instance(id):
    # Delete instance from DB
    ret = delete(Instance, id)

    # Put file and create instance
    def executor(id_):
        def func():
            res = cca_cmd(f'./delete-instance.sh "{id_}"')
            return dict(
                success=res.ok,
                errors=res.stderr
            )
        return func

    ret.update(execute_remote(executor(id)))
    return ret

def query_instances():
    global cis

    query_results = query(Instance)

    status = cis.instance_status()
    instances = []
    for ret in query_results['results']:
        params = {}
        params.update(status.get(ret['key'], {}))
        params.update(ret['value'])
        instances.append(
            dict(
                id=ret['key'],
                kind=params.get('kind'),
                params=params,
                active=params.get('active'),
                status=params.get('ckanPhase'),
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

def instance_connection_info(id):
    ret = {}
    # Put file and create instance
    def executor(id_):
        def func():
            res = cca_cmd(f'./instance-connection-info.sh "{id_}"')
            passwords = [
                line.strip().split(':')[-1].strip()
                for line in res.stdout.split('\n')
                if 'admin password' in line
            ]
            if len(passwords) > 0:
                return dict(password=passwords[0])
            else:
                return {}
        return func

    ret.update(execute_remote(executor(id)))
    return ret        
