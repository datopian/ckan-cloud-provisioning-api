import sys
from io import StringIO
import threading
import pathlib

from fabric import Connection
import yaml

from .models import create_or_edit, delete, query, User, Instance
from .server_connection import get_connection, execute_remote
from .instance_status_service import cis
from .values import convert_body, kinds


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
                    res = conn.run(f'cd /cca-operator && ./cca-operator.sh ./update-instance.sh "{id_}"')
                else:
                    res = conn.run(f'cd /cca-operator && ./cca-operator.sh ./create-instance.sh "{id_}"')
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
            conn = get_connection()
            res = conn.run(f'cd /cca-operator && ./cca-operator.sh ./delete-instance.sh "{id_}"')
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
    instances = [
        dict(
            id=ret['key'],
            params=ret['value'],
            **status.get(ret['key'], {})
        )
        for ret in query_results['results']
    ]
    
    return dict(
        instances=instances
    )

def create_or_edit_user(id, body):
    ret = create_or_edit(User, id, body)
    return ret

def delete_user(id):
    ret = delete(User, id)
    return ret

def query_users():
    ret = query(User)
    return ret

def instance_kinds():
    return dict(
        kinds=kinds()
    )
