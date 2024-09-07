from flask import request, redirect, url_for

from app import app
from app.helpers.nightbot import NightBot
from app.models.api import API as api_model
api = api_model()

# NightBot OAuth2
nb = NightBot(
                base_url='https://api.nightbot.tv',
                authorize_url='https://api.nightbot.tv/oauth2/authorize',
                token_url='https://api.nightbot.tv/oauth2/token',
                callback_url='https://main.nightbot.jeandr.net//oauth/token',
                scope=None,
                debug=False
                )

@app.route('/')
@app.route('/index')
def index():
    return redirect(url_for('modpipe.index').replace('http://','https://'))

@app.route('/config')
def config():
    return "Config Page will go here"

# OAuth Routes
@app.route('/oauth/initiate')
def oauth_initiate():
    return nb.oauth2_authorize()

@app.route('/oauth/token')
def oauth_token():
    return nb.oauth2_token()


# API Routes

# Default API Route
@app.route('/api', defaults={'category': None,'command':None,'cmd_var':None})
@app.route('/api/<category>', defaults={'command':None,'cmd_var':None})
@app.route('/api/<category>/<command>',defaults={'cmd_var':None})
@app.route('/api/<category>/<command>/<cmd_var>')
def api_catchall(category,command,cmd_var):
    # Channel
    if category == "channel":
        if command == "send":
            if cmd_var:
                nb.channel_send_from_file(cmd_var)
            else:
                nb.channel_send()
        if command == "join":
            # Join Channel
            return nb.api_send(
                api.channel_join,
                param = None,
                data = None
            )
        if command == "part":
            # Leave Channel
            return nb.api_send(
                api.channel_part,
                param = None,
                data = None
            )
        if not command:
            # Get Channel details
            return nb.api_send(
                api.channel,
                param = None,
                data = None
            )
    
    # Commands
    if category == "commands":
        if not command:
            # Get Custom Commands
            if cmd_var:
                # Get Custom Command by ID
                return nb.api_send(
                    api.custom_command_get,
                    param = cmd_var,
                    data = None
                )
            else:
                # Get All Custom Commands
                return nb.api_send(
                    api.custom_commands_get_all,
                    data = None
                )
        if command == "default":
            if cmd_var:
                return nb.api_send(
                    api.default_command_get,
                    param = cmd_var,
                    data = None
                )
            if not cmd_var:
                return nb.api_send(
                    api.default_commands_get_all,
                    param = None,
                    data = None
                )
    # Me
    if category == "me":
        return nb.api_send(
            api.me,
            data = None
        )
        
    else:
        path = f"/api"
        for value in [category,command,cmd_var]:
            path = f"{path}/{value}" if value else path
        return {"error" : "not implemented"}
