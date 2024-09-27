import os
basedir = os.path.abspath(os.path.dirname(__file__))


class Config(object):
    USERNAME = os.environ.get('USERNAME')
    DOMAIN = os.environ.get('DOMAIN')
    DEBUG = False
    TESTING = False
    CSRF_ENABLED = True
    SECRET_KEY = "CHANGE_THIS"
    BASE_URL = f"https://modpipe.{DOMAIN}"

    # DATABASE
    SQLALCHEMY_DATABASE_URI = os.environ['DATABASE_URL']
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # OAUTH2
    OAUTH2_PROVIDERS = {
        'twitch': {
            'client_id':        os.environ.get('TWITCH_CLIENT_ID'),
            'client_secret':    os.environ.get('TWITCH_CLIENT_SECRET'),
            'authorize_url':    'https://id.twitch.tv/oauth2/authorize',
            'token_url':        'https://id.twitch.tv/oauth2/token',
            'userinfo': {
                        'url':          'https://api.twitch.tv/helix/users',
                        'email':        lambda json: json['data'][0]['email'],
                        'id':           lambda json: json['data'][0]['id'],
                        'username':     lambda json: json['data'][0]['login'],
                        'display':      lambda json: json['data'][0]['display_name'],
                        'avatar':       lambda json: json['data'][0]['profile_image_url'],
            },
            'scopes': ['user:read:email',
                       'user:read:chat',
                       'user:read:broadcast',
            ],
        },

        'google': {
            'client_id':        os.environ.get('GOOGLE_CLIENT_ID'),
            'client_secret':    os.environ.get('GOOGLE_CLIENT_SECRET'),
            'authorize_url':    'https://accounts.google.com/o/oauth2/auth',
            'token_url':        'https://accounts.google.com/o/oauth2/token',
            'userinfo': {
                        'url':          'https://www.googleapis.com/oauth2/v3/userinfo',
                        'email':        lambda json: json['email'],
                        'id':           lambda json: json['sub'],
                        'username':     lambda json: json['email'],
                        'display':      lambda json: json['name'],
                        'avatar':       lambda json: json['picture'],
            },
            'scopes': ['https://www.googleapis.com/auth/userinfo.email',
                       'https://www.googleapis.com/auth/userinfo.profile',
            ],
        },

        'github': {
            'client_id':        os.environ.get('GITHUB_CLIENT_ID'),
            'client_secret':    os.environ.get('GITHUB_CLIENT_SECRET'),
            'authorize_url':    'https://github.com/login/oauth/authorize',
            'token_url':        'https://github.com/login/oauth/access_token',
            'userinfo': {
                        'url':          'https://api.github.com/user',
                        'email':        lambda json: json['email'],
                        'id':           lambda json: json['id'],
                        'username':     lambda json: json['login'],
                        'display':      lambda json: json['name'],
                        'avatar':       lambda json: json['avatar_url']
            },
            'scopes': ['user:email',
                       'read:user',
            ],
        },
        
    }

    SERVICES = {
        "nightbot":{
            'authorize_url':    'https://api.nightbot.tv/oauth2/authorize',
            'token_url':        'https://api.nightbot.tv/oauth2/token',
            'callback_url':    f'{os.environ.get("APP_URL")}/services/nightbot/oauth/callback',
            'scope':           [
                                    'channel',
                                    'channel_send',
                                    'commands',
                                    'commands_default',
                                    'regulars',
                                    'subscribers'
                                ],
        },
        "twitch":{
            'authorize_url':    'https://id.twitch.tv/oauth2/authorize',
            'token_url':        'https://id.twitch.tv/oauth2/token',
            'callback_url':    f'{os.environ.get("APP_URL")}/services/twitch/oauth/callback',
            'scope':           [
                                    'user:read:email',
                                    'user:read:chat',
                                    'user:read:broadcast',
                                ]
        }
    }


class ProductionConfig(Config):
    DEBUG = False

class StagingConfig(Config):
    DEVELOPMENT = True
    DEBUG = True

class DevelopmentConfig(Config):
    DEVELOPMENT = True
    DEBUG = True

class TestingConfig(Config):
    TESTING = True