from auth.models import get_user

from .blueprint import make_blueprint
from .models import User, query_one


def get_permissions(service, userid):
    print('get_permissions', service, userid)
    if service != 'ckan-cloud-provisioner': return {}
    
    user = get_user(userid)
    if user is None: return {}
            
    email = user.get('email')
    if email is None: return {}
    
    value = query_one(User, email)
    if value is None: return {}

    print('got perm', value)
    return value
