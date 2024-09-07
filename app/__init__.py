import os
import logging
from time import ctime
from flask import Flask, current_app
from flask.logging import default_handler
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
app = Flask(__name__)
app.config.from_object(os.environ['APP_SETTINGS'])


app.config.update(
    OAUTH2_PROVIDERS = {
        'twitch': {
            'client_id': os.environ.get('TWITCH_CLIENT_ID'),
            'client_secret': os.environ.get('TWITCH_CLIENT_SECRET'),
            'authorize_url': 'https://id.twitch.tv/oauth2/authorize',
            'token_url': 'https://id.twitch.tv/oauth2/token',
            'userinfo': {
                'url': 'https://api.twitch.tv/helix/users',
                'email': lambda json: json[0]['email'],
                'id': lambda json: json[0]['id'],
                'username': lambda json: json[0]['login'],
                'display': lambda json: json[0]['display_name'],
                'avatar': lambda json: json[0]['profile_image_url'],
            }
        },

        'google': {
            'client_id': os.environ.get('GOOGLE_CLIENT_ID'),
            'client_secret': os.environ.get('GOOGLE_CLIENT_SECRET'),
            'authorize_url': 'https://accounts.google.com/o/oauth2/auth',
            'token_url': 'https://accounts.google.com/o/oauth2/token',
            'userinfo': {
                'url': 'https://www.googleapis.com/oauth2/v3/userinfo',
                'email': lambda json: json['email'],
                'username': lambda json: json['email'],
            },
            'scopes': ['https://www.googleapis.com/auth/userinfo.email',
                        'https://www.googleapis.com/auth/userinfo.profile',
            ],
        },

        'github': {
            'client_id': os.environ.get('GITHUB_CLIENT_ID'),
            'client_secret': os.environ.get('GITHUB_CLIENT_SECRET'),
            'authorize_url': 'https://github.com/login/oauth/authorize',
            'token_url': 'https://github.com/login/oauth/access_token',
            'userinfo': {
                'url': 'https://api.github.com/user',
                'email': lambda json: json[0]['email'],
                'id': lambda json: json[0]['id'],
                'username': lambda json: json[0]['login'],
                'display': lambda json: json[0]['name'],
                'avatar': lambda json: json[0]['avatar_url']
            },
            'scopes': ['user:email',
                        'read:user',
            ],
        },
    }
,
    NIGHTBOT_OAUTH = {
        'authorize_url':    'https://api.nightbot.tv/oauth2/authorize',
        'token_url':        'https://api.nightbot.tv/oauth2/authorize',
        'callback_url':     f'{os.environ.get("APP_URL")}/nightbot/callback',
    }
)

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
from app import routes
from app.blueprints.auth import auth as auth_blueprint
from app.blueprints.modpipe import modpipe as modpipe_blueprint
app.register_blueprint(auth_blueprint, url_prefix='/auth')
app.register_blueprint(modpipe_blueprint, url_prefix='/modpipe')


from app.models import database
with app.app_context():
    db.create_all()

@app.template_filter('ctime')
def timectime(s):
    return ctime(s)

