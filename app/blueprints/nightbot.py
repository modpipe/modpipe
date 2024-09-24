from flask_sqlalchemy import SQLAlchemy
from flask_login import login_user, logout_user, login_required, current_user
from flask import Blueprint, redirect, url_for, render_template, flash, abort, \
    session, current_app, request, jsonify

from app import logs
from app import db
from app import login
from app.models.database import Users
from app.models.database import NightBot as NightbotDB
from app.models.database import Commands as CommandsDB

from app.models.api import API as api_model
from app.helpers.nb import NightBot
nb = NightBot(callback_url='https://modpipe.jeandr.net/nightbot/oauth/callback')
api = api_model()

nightbot = Blueprint('nightbot', __name__)

@login.user_loader
def load_user(id):
    return db.session.get(Users, int(id))

@nightbot.route('/oauth/')
@login_required
def nightbot_oauth_init():
    result = nb.authorize(current_user.id)
    if result:
        return result
    return jsonify({'error':'not configured'})

@nightbot.route('/oauth/callback')
@login_required
def nightbot_oauth_callback():
    result = nb.callback(current_user.id)
    logs.info(f"result  : {result}")
    if result:
        return result
    return jsonify({'error': result})

@nightbot.route('/oauth/renew')
@login_required
def nightbot_oauth_renew():
    nb.renew_token(current_user.id)

@nightbot.route('/bearer')
@login_required
def nightbot_show_bearer():
    return jsonify(nb.get_bearer(current_user.id))

@nightbot.route('/command/<cmd>')
@login_required
def nightbot_command_test(cmd):
    if 'auth' in request.args:
        if request.args['auth'] == 'true':
            bearer = nb.get_bearer(current_user.id)
            if bearer:
                return bearer
    redirect_url = url_for('nightbot.nightbot_oauth_init')+f"?state=/nightbot/command/{cmd}"
    logs.info(f"redirect_url  : {redirect_url}")
    return redirect(redirect_url)



# Default API Route
@nightbot.route('/api', defaults={'category': None,'command':None,'cmd_var':None})
@nightbot.route('/api/<category>', defaults={'command':None,'cmd_var':None})
@nightbot.route('/api/<category>/<command>',defaults={'cmd_var':None})
@nightbot.route('/api/<category>/<command>/<cmd_var>')
def api_catchall(category,command,cmd_var):
    logs.info(f"category         : {category}")
    logs.info(f"command          : {command}")
    logs.info(f"cmd_var          : {cmd_var}")
    logs.info(f"current_user.id  : {current_user.id}")
    bearer = nb.get_bearer(current_user.id)
    logs.info(bearer)
    if not bearer:
        redirect_url = url_for('nightbot.nightbot_oauth_init')+f"?state={request.path}"
        logs.info(f"redirect_url  : {redirect_url}")
        return redirect(redirect_url)
    else:
        # Channel
        if category == "channel":
            logs.info("CATEGORY channel")
            if command == "send":
                    logs.info("CHANNEL SEND")
                    return nb.api_channel_send(cmd_var,current_user.id,bearer=bearer)
            if command == "join":
                # Join Channel
                return nb.api_send(
                    api.channel_join,
                    bearer=bearer,
                    param = None,
                    data = None
                )
            if command == "part":
                # Leave Channel
                return nb.api_send(
                    api.channel_part,
                    bearer=bearer,
                    param = None,
                    data = None
                )
            if not command:
                # Get Channel details
                return nb.api_send(
                    api.channel,
                    bearer=bearer,
                    param = None,
                    data = None
                )
        
        # Commands
        elif category == "commands":
            if not command:
                # Get Custom Commands
                if cmd_var:
                    # Get Custom Command by ID
                    return nb.api_send(
                        api.custom_command_get,
                        bearer=bearer,
                        param = cmd_var,
                        data = None
                    )
                else:
                    # Get All Custom Commands
                    return nb.api_send(
                        api.custom_commands_get_all,
                        bearer=bearer,
                        data = None
                    )
            if command == "default":
                if cmd_var:
                    return nb.api_send(
                        api.default_command_get,
                        bearer=bearer,
                        param = cmd_var,
                        data = None
                    )
                if not cmd_var:
                    return nb.api_send(
                        api.default_commands_get_all,
                        bearer=bearer,
                        param = None,
                        data = None
                    )
        # Me
        elif category == "me":
            logs.info(f"api.me  : {api.me}")
            return nb.api_send(
                api.me,
                bearer=bearer,
                data = None
            )
            
        else:
            path = f"/api"
            for value in [category,command,cmd_var]:
                path = f"{path}/{value}" if value else path
            return {"error" : "not implemented"}
