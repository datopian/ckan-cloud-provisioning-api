import sys
import os
from ckan_cloud_provisioner.models import create_or_edit, User, setup_engine
from ckan_cloud_provisioner.blueprint import Permissions


if __name__ == '__main__':
    if len(sys.argv) > 1:
        print('Adding admin user', sys.argv[1])
        setup_engine(os.environ.get('DATABASE_URL'))
        create_or_edit(User, sys.argv[1], dict(level=Permissions.Admin.value))
