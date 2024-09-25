import os
import logging
from time import ctime
from flask import Flask, redirect, url_for
from flask.logging import default_handler
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import event
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
app.register_blueprint(auth_blueprint, url_prefix='/auth')
app.register_blueprint(modpipe_blueprint, url_prefix='/modpipe')
app.register_blueprint(nightbot_blueprint, url_prefix='/nightbot')


from app.models import database
with app.app_context():
    db.create_all()

@app.template_filter('ctime')
def timectime(s):
    return ctime(s)

@app.route('/')
@app.route('/index')
def index():
    return redirect(url_for('modpipe.index').replace('http://','https://'))

@event.listens_for(database.Groups.__table__, 'after_create')
def create_groups(*args, **kwargs):
    # This creates default groups in the database
    db.session.add(database.Groups(owner = 0,name = "owner"))
    db.session.add(database.Groups(owner = 0,name = "moderator"))
    db.session.add(database.Groups(owner = 0,name = "vip"))
    db.session.add(database.Groups(owner = 0,name = "everyone"))

    db.session.commit()

@event.listens_for(database.Commands.__table__, 'after_create')
def create_commands(*args, **kwargs):
    # This creates default commands in the database
    pass