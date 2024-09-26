import os
import secrets
import requests
import time

from urllib.parse import urlencode
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import and_, or_
from flask_login import current_user, login_required
from flask import Blueprint, redirect, url_for, render_template, flash, abort, jsonify,\
                  session, current_app, request

from app import db
from app import login
from app import logs
from app.models.database import Users as UsersDB
from app.models.database import NightBot as NightBotDB
from app.models.database import Twitch as TwitchDB
from app.models.database import Commands as CommandsDB
from app.models.database import Groups as GroupsDB
from app import app
from app.helpers.modpipe import get_form_data

with app.app_context():
    nightbot_config = current_app.config['NIGHTBOT_OAUTH'] if 'NIGHTBOT_OAUTH' in current_app.config else None

modpipe = Blueprint('modpipe', __name__)

@modpipe.route('/')
def index(welcome=False):
    if current_user.is_authenticated:
        return redirect(url_for('modpipe.dashboard'))
    if 'welcome' in request.args:
        welcome=True
    return render_template('main.html',welcome=welcome)

@modpipe.route('/command/new',methods=['POST'])
@login_required
def command_new(form_data={}):
    fields = ['display_name',
              'type',
              'users',
              'groups',
              'command']
    form_data = get_form_data(fields)
    logs.info(form_data)
    commands = db.session.query(CommandsDB).filter_by(owner=current_user.id).filter_by(name=form_data['display_name']).scalar()
    logs.info(f"Command Exists: {commands}")
    if commands is not None:
        flash(f"This command name already exists.  Changing new command name to {form_data['display_name']}-new")
        form_data['display_name'] = f"{form_data['display_name']}-new"
    new_command = CommandsDB(
                                owner = current_user.id,
                                name = form_data['display_name'],
                                type = form_data['type'],
                                users = form_data['users'],
                                groups = form_data['groups'],
                                command = form_data['command']
                            )
    db.session.add(new_command)
    db.session.commit()
    return redirect(url_for('modpipe.dashboard').replace('http://','https://'))

@modpipe.route('/command/<cmd>/update')
@login_required
def command_update(cmd):
    command = db.session.query(CommandsDB.filter_by(id=cmd)).scalar()
    if command is not None and command.owner == current_user.id:
        fields = ["display_name",
                  "type",
                  "users",
                  "groups",
                  "command",
                  "short_description",
                  "long_description",
                  "timeout"
        ]
        form_data = get_form_data(fields)
        logs.info(form_data)
        for data in ['nightbot_command',
                     'chat_message'
                    ]:
            command.service = "nightbot" if form_data['type'] == "data" else "twitch"
        command.name = form_data['display_name']
        command.type = form_data['type']
        command.users = form_data['users']
        command.groups = form_data['groups']
        command.short_description = form_data['short_description']
        command.long_description = form_data['long_description']
        command.timeout = form_data['timeout']

        db.session.commit()
        return redirect(url_for('modpipe.dashboard').replace('http://','https://'))
    return jsonify({"error": "command not found."})

@modpipe.route('/command/<cmd>')
def command_execute(cmd):
    return_json = {
            "id" : cmd,
            "name" : "Unknown",
            "checkback": "",
            "result": {
                "timeout": 10,
                "status": {
                    "code": 404,
                    "message": "Command Not Found"
                },
                "feedback": "ERROR: Not Found",
            }
        }
    if 'chk' in request.args:
        checkback = request.args['chk']
    else:
        checkback = None
    if checkback:
        command = db.session.scalar(db.select(CommandsDB).where(CommandsDB.id == cmd))
        if command and command.owner == current_user.id:
            if command.type == "chat_message":
                return redirect(f'/nightbot/api/channel/send/{cmd}')
            
            # Build Feedback
            return_json['id'] = cmd
            return_json['name'] = command.name
            return_json['checkback'] = checkback
            return_json['result'] = {
                "timeout": command.timeout,
                "status": {
                    "code": 200, # Use HTTP Codes for success / failure messages???
                    "message": "SUCCESS" # Plain Text Error Message
                },
                "feedback": f"{command.name} OK",
            }
        else:
            return_json['id'] = cmd
            return_json['name']
        
    return jsonify(return_json)
    

@modpipe.route('/dashboard')
@login_required
def dashboard(nightbot_data={},twitch_data={}):
    nightbotdb = NightBotDB.query.filter_by(owner=current_user.id).scalar()
    nightbot_exists = nightbotdb is not None
    twitchdb = TwitchDB.query.filter_by(owner=current_user.id).scalar()
    twitch_exists = twitchdb is not None
    commands = CommandsDB.query.filter_by(owner=current_user.id).all()
    command_types = [
        "chat_message",
        "nightbot_command",
        "commercial",
        "winner",
        "game"
    ]
    groups = GroupsDB.query.filter_by(owner=current_user.id).all()
    logs.debug(f"TWITCH: {twitchdb}")
    logs.debug(f"TWITCH EXISTS: {twitch_exists}")
    logs.debug(f"NIGHTBOT: {nightbotdb}")
    logs.debug(f"NIGHTBOT EXISTS: {nightbot_exists}")
    
    if nightbot_exists:
        nightbot_data['display_name'] = nightbotdb.displayName
        nightbot_data['client_id'] = nightbotdb.client_id
        nightbot_data['client_secret'] = nightbotdb.client_secret
        renew_before = False
        if nightbotdb.token:
            if "renew_before" in nightbotdb.token:
                renew_before = nightbotdb.token['renew_before']
            else:
                renew_before = False
        if renew_before:
            nightbot_data['renew_date'] = time.strftime('%Y-%m-%d %H:%M:%S',time.gmtime(renew_before))

    if twitch_exists:
        twitch_data['display_name'] = twitchdb.displayName
        twitch_data['client_id'] = twitchdb.client_id
        twitch_data['client_secret'] = twitchdb.client_secret
        twitch_data['token'] = twitchdb.token
        renew_before = twitchdb.token['renew_before'] if "renew_before" in twitchdb.token else False
        if renew_before:
            twitch_data['renew_date'] = time.strftime('%Y-%m-%d %H:%M:%S',time.gmtime(renew_before))
        else:
            twitch_data['renew_date'] = False

    logs.debug(f"NIGHTBOT DATA: {nightbot_data}")
    logs.debug(f"TWITCH DATA  : {twitch_data}")


    return render_template('dashboard.html',nightbot_data=nightbot_data,twitch_data=twitch_data,commands=commands,command_types=command_types,groups=groups)

@modpipe.route('/config', methods=['GET'])
@login_required
def config(nightbot_data={},twitch_data={}):
    nightbotdb = NightBotDB.query.filter_by(owner=current_user.id).scalar()
    nightbot_exists = nightbotdb is not None
    twitchdb = TwitchDB.query.filter_by(owner=current_user.id).scalar()
    twitch_exists = twitchdb is not None
    logs.debug(f"TWITCH: {twitchdb}")
    logs.debug(f"TWITCH EXISTS: {twitch_exists}")
    logs.debug(f"NIGHTBOT: {nightbotdb}")
    logs.debug(f"NIGHTBOT EXISTS: {nightbot_exists}")
    
    if nightbot_exists:
        nightbot_data['display_name'] = nightbotdb.displayName
        nightbot_data['client_id'] = nightbotdb.client_id
        nightbot_data['client_secret'] = nightbotdb.client_secret

    if twitch_exists:
        twitch_data['display_name'] = twitchdb.displayName
        twitch_data['client_id'] = twitchdb.client_id
        twitch_data['client_secret'] = twitchdb.client_secret


    logs.debug(f"NIGHTBOT DATA: {nightbot_data}")
    logs.debug(f"TWITCH DATA  : {twitch_data}")


    return render_template('config.html',nightbot_data=nightbot_data,twitch_data=twitch_data)

@modpipe.route('/config/<service_type>', methods=['POST'])
@login_required
def config_save(service_type):
    fields = ['display_name','client_id','client_secret','description']
    fields = [f"{service_type}_{val}" for val in fields]
    form_data = get_form_data(fields)
    if service_type == "nightbot":
        if db.session.query(NightBotDB).filter_by(id=current_user.id).first() is not None:
            service = db.session.scalar(db.select(NightBotDB).where(NightBotDB.owner == current_user.id))
        else:
            service = NightBotDB(owner=current_user.id)
    elif service_type == 'twitch':
        if db.session.query(TwitchDB).filter_by(id=current_user.id).first() is not None:
            service = db.session.scalar(db.select(TwitchDB).where(TwitchDB.owner == current_user.id))
        else:
            service = TwitchDB(owner=current_user.id)
    service.name = service_type
    service.displayName = form_data[f'{service_type}_display_name']
    service.avatar = ""
    service.admin = True
    service.client_id = form_data[f'{service_type}_client_id']
    service.client_secret = form_data[f'{service_type}_client_secret']
    db.session.add(service)
    db.session.commit()
    return redirect(f"{url_for('modpipe.dashboard').replace('http://','https://')}?config")