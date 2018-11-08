import os
import logging

from flask import Flask
from flask_cors import CORS
from flask_session import Session

os.environ['ALLOWED_SERVICES'] = 'ckan-cloud-provisioner:ckan_cloud_provisioner'

from auth import make_blueprint as auth_blueprint

from ckan_cloud_provisioner import make_blueprint

# Create application
app = Flask(__name__, static_folder=None)

# CORS support
CORS(app, supports_credentials=True)

# Session
session = Session()
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_FILE_DIR'] = '/tmp/sessions'
app.config['SECRET_KEY'] = '-'
session.init_app(app)

# Register blueprints
app.register_blueprint(auth_blueprint(os.environ.get('EXTERNAL_ADDRESS')),
                       url_prefix='/auth/')
app.register_blueprint(make_blueprint(), url_prefix='/api/')


logging.getLogger().setLevel(logging.INFO)

if __name__=='__main__':
    app.run()


















