def get_permissions(service, userid):
    from .models import User, query_one
    from auth.models import get_user

    if service != 'ckan-cloud-provisioner': return {}
    
    user = get_user(userid)
    if user is None: return {}
            
    email = user.get('email')
    if email is None: return {}
    
    value = query_one(User, email, case_sensitive=False)
    if value is None: return {}

    return value
