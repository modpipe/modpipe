import os
import logging
import time

from flask import Flask, redirect, url_for
from flask.logging import default_handler
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
app = Flask(__name__)
app.config.from_object(os.environ['APP_SETTINGS'])


# Setup Database
db = SQLAlchemy(app)

# Login Manager
login = LoginManager(app)
login.login_view = 'index'

# Setup logging
logs = logging.getLogger('werkzeug')
# Log to '/data/flask.log'
data_flask_log = logging.FileHandler('/logs/flask.log')
logs.addHandler(data_flask_log)
# Log to 'stderr'
logs.addHandler(default_handler)
logs.info(f"##### app.config #####: {app.config}")
# Routes
from app.blueprints.auth import auth as auth_blueprint
from app.blueprints.modpipe import modpipe as modpipe_blueprint
from app.blueprints.nightbot import nightbot as nightbot_blueprint
from app.blueprints.services import service as services_blueprint
app.register_blueprint(auth_blueprint, url_prefix='/auth')
app.register_blueprint(modpipe_blueprint, url_prefix='/modpipe')
app.register_blueprint(nightbot_blueprint, url_prefix='/nightbot')
app.register_blueprint(services_blueprint, url_prefix='/services')


from app.models import database
with app.app_context():
    db.create_all()
    

@app.template_filter('ctime')
def timectime(s):
    return time.ctime(s)

@app.route('/')
@app.route('/index')
def index():
    return redirect(url_for('modpipe.index').replace('http://','https://'))

