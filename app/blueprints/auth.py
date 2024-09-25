import os
import secrets
import requests

from validators import url as validate_url
from time import ctime, time
from urllib.parse import urlencode
from dotenv import load_dotenv
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import and_
from flask_login import login_user, logout_user, login_required, current_user
from flask import Blueprint, redirect, url_for, render_template, flash, abort, \
    session, current_app, request

from app import db
from app import login
from app import logs
from app.models.database import Users
from app.models.database import Groups
from app.helpers.modpipe import get_form_data

auth = Blueprint('auth', __name__)

@login.user_loader
def load_user(id):
    return db.session.get(Users, int(id))

@auth.route('/')
def index():
    return render_template('login.html')


@auth.route('/logout')
def logout():
    logout_user()
    flash('You have been logged out.')
    return redirect(url_for('modpipe.index').replace('http://','https://'))

@auth.route('/authorize/<provider>')
def oauth2_authorize(provider):
    if not current_user.is_anonymous:
        return redirect(url_for('auth.index').replace('http://','https://'))
    provider_data = current_app.config['OAUTH2_PROVIDERS'].get(provider)
    logs.info(f"##### OAUTH2_PROVIDERS['twitch'] #####: {current_app.config['OAUTH2_PROVIDERS'].get('twitch')}")
    if provider_data is None:
        abort(404)

    # Generate a random string for the state parameter
    session['oauth2_state'] = secrets.token_urlsafe(16)

    # Create a query string with all the OAuth2 parameters
    qs = urlencode({
        'client_id': provider_data['client_id'],
        'redirect_uri': url_for('auth.oauth2_callback', provider=provider, _external=True).replace('http://','https://'),
        'response_type': 'code',
        'scope': ' '.join(provider_data['scopes']),
        'state': session['oauth2_state'],
    })
    authorize_url = provider_data['authorize_url'] + '?' + qs
    logs.info(f"##### authorize_url #####:{authorize_url}")

    return redirect(authorize_url)

@auth.route('/callback/<provider>')
def oauth2_callback(provider, new_user=False,):
    if not current_user.is_anonymous:
        return redirect(url_for('auth.index').replace('http://','https://'))
    logs.info(f"##### REQUEST #####: {request}")
    provider_data = current_app.config['OAUTH2_PROVIDERS'].get(provider)
    logs.debug(f"##### PROVIDER_DATA #####: {provider_data}")
    if provider_data is None:
        abort(404)
    
    # If there was an authentication error, flash the error messages and exit
    if 'error' in request.args:
        for k, v in requests.args.items():
            if k.startswith('error'):
                logs.info(f'{k}: {v}')
                flash(f'{k}: {v}')
        return redirect(url_for('auth.index').replace('http://','https://'))
    
    # Make sure the state parameter matches the one we created
    if request.args['state'] != session.get('oauth2_state'):
        logs.info('##### ERROR #####: State Incorrect ###')
        abort(401)
    
    # Make sure the authorization code is present
    if 'code' not in request.args:
        logs.info(f"##### ERROR #####: Authorization Code is NOT PRESENT ###")
        logs.info(f"{request}")
        abort(401)

    # Exchange the authorization code for an access token
    response_data={
        'client_id': provider_data['client_id'],
        'client_secret': provider_data['client_secret'],
        'code': request.args['code'],
        'grant_type': 'authorization_code',
        'redirect_uri': url_for('auth.oauth2_callback', provider=provider, _external=True).replace('http://','https://'),
        }
    response_url = provider_data['token_url']
    response = requests.post(response_url, response_data ,
        headers={'Accept': 'application/json'}
    )
    logs.info(f"##### response #####: {response_url}: {response_data}")
    if response.status_code != 200:
        abort(401)
    oauth2_token = response.json().get('access_token')
    if not oauth2_token:
        abort(401)
    
    # Use the access token to get the user's email address
    headers = {
            'Authorization': 'Bearer ' +oauth2_token,
            'Accept': 'application/json',
        }
    if provider == "twitch":
        headers = {
            'Authorization': 'Bearer ' +oauth2_token,
            'Accept': 'application/json',
            'Client-Id': provider_data['client_id'],
        }
    response = requests.get(provider_data['userinfo']['url'], headers=headers)
    if response.status_code != 200:
        logs.info(f"##### JSON Response #####: {response.json()}")
        abort(401)
    json_response = response.json()
    logs.info(f"##### JSON Response #####: {json_response}")
    email = provider_data['userinfo']['email'](json_response)
    oauth_id = provider_data['userinfo']['id'](json_response)
    username = provider_data['userinfo']['username'](json_response)
    display = provider_data['userinfo']['display'](json_response)
    avatar = provider_data['userinfo']['avatar'](json_response)

    logs.debug(f"##### email #####:\n {email}")
    logs.debug(f"##### Users #####:\n {Users}")

    # Find or create the user in the database
    user = db.session.scalar(db.select(Users).where(and_(Users.email == email,Users.provider == provider)))
    if user is None:
        new_user = True
        user = Users(email=email,
                     provider=provider,
                     oauth_id=oauth_id,
                     username=username,
                     display=display,
                     avatar=avatar,
                     bio=""
                )
    user.last_used = int(time())
    db.session.add(user)
    db.session.commit()

    # Log the user in
    login_user(user)
    # Make sure the user's default groups have been created
    create_user_groups = True if Groups.query.filter_by(owner=current_user.id).first() is None else False
    if create_user_groups:
        logs.info(f"Creating default groups for {current_user.display}")
        for name in ['Owner','Moderator','VIP','Everyone']:
            new_group = Groups(owner=current_user.id,name=name)
            db.session.add(new_group)
            db.session.commit()

    # Onboard User and allow them to edit their profile
    user = db.session.scalar(db.select(Users).where(and_(Users.email == email),Users.provider == provider))
    if new_user:
        return render_template('onboarding.html',user=user)
    else:
        return redirect(url_for('modpipe.dashboard').replace('http://','https://'))


@auth.route('/user')
@login_required
def view_user():
    return render_template('user.html')

@auth.route('/user/edit', methods=['GET'])
@login_required
def edit_user():
    user = db.session.scalar(db.select(Users).where(and_(Users.id == current_user.id,Users.provider == current_user.provider)))
    return render_template('user_form.html', user=user)

@auth.route('/user/update', methods=['POST'])
@login_required
def edit_user_POST():
    fields = ['type','id','groups','username','email','admin','display','avatar','bio', 'onboarding']
    form_data = get_form_data(fields)

    user = db.session.scalar(db.select(Users).where(and_(Users.id == current_user.id,Users.provider == current_user.provider)))
    display_change_date = int(time()) - 2592000
    user.username = f"""{form_data['username']}"""
    user.display = f"""{form_data['display']}"""
    user.avatar = f"""{form_data['avatar']}"""
    user.admin = f"""{form_data['admin']}"""
    user.bio = f"""{form_data['bio']}"""

    db.session.commit()
    if form_data['type'] == "onboarding":
        home = url_for('modpipe.index')
        if current_user.is_authenticated:
            home = url_for('modpipe.dashboard')
        return redirect(f"{home}?welcome")
    return redirect(url_for('auth.edit_user').replace('http://','https://'))