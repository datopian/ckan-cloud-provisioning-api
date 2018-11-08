import os
from enum import Enum

from flask import Blueprint, request, url_for, session
from flask import redirect, abort
from flask_jsonpify import jsonpify

from . import controllers
from . import models

from auth import Verifyer
from auth.credentials import public_key, db_connection_string


class Permissions(Enum):
    Maintainer = 1
    Admin = 2


def make_blueprint():  # noqa
    """Create blueprint.
    """

    models.setup_engine(db_connection_string)

    # Create instance
    blueprint = Blueprint('ckan_cloud_provisioner', 'ckan_cloud_provisioner')

    # Controller Proxies
    verifyer = Verifyer(public_key=public_key)

    def check_permission(level):
        def decorator(func):
            def wrapper(*args, **kw):
                token = request.values.get('jwt')
                permissions = verifyer.extract_permissions(token)
                if not (permissions is False):
                    if permissions.get('permissions', {}).get('level', 0) >= level.value:
                        return jsonpify(func(*args, **kw))
                abort(403)
            return wrapper
        return decorator


    @check_permission(Permissions.Maintainer)
    def query_instances_():
        return controllers.query_instances()

    @check_permission(Permissions.Maintainer)
    def edit_instance_():
        body = request.json
        id = body['id']
        return controllers.create_or_edit_instance(id, body)

    @check_permission(Permissions.Maintainer)
    def delete_instance_(id):
        return controllers.delete_instance(id)

    @check_permission(Permissions.Admin)
    def query_users_():
        return controllers.query_users()

    @check_permission(Permissions.Admin)
    def edit_user_():
        body = request.json
        id = body['id']
        return controllers.create_or_edit_user(id, body)

    @check_permission(Permissions.Admin)
    def delete_user_(id):
        return controllers.delete_user(id)

    # Register routes
    blueprint.add_url_rule(
        'instances', 'query_instances', query_instances_, methods=['GET'])
    blueprint.add_url_rule(
        'instance', 'edit_instance', edit_instance_, methods=['POST'])
    blueprint.add_url_rule(
        'instance/<id>', 'delete_instance', delete_instance_, methods=['DELETE'])

    blueprint.add_url_rule(
        'users', 'query_users', query_users_, methods=['GET'])
    blueprint.add_url_rule(
        'user', 'edit_user', edit_user_, methods=['POST'])
    blueprint.add_url_rule(
        'user/<id>', 'delete_user', delete_user_, methods=['DELETE'])

    # Return blueprint
    return blueprint
