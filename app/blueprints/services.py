import os
import validators

from flask_login import login_required, current_user
from flask import Blueprint, redirect, url_for, jsonify, current_app

from app import logs
from app import db
from app import login
from app.models.database import Users
from app.helpers.services import Services


DOMAIN = os.environ.get('DOMAIN') if os.environ.get('DOMAIN') else "example.com"
APP_URL = os.environ.get('APP_URL') if os.environ.get('APP_URL') else f"https://modpipe.{DOMAIN}"

services = Services()

service = Blueprint('services', __name__)

def get_service_config(service,param,requested_param=None):
    logs.info(f"Getting SERVICES from current_app.config")
    if "SERVICES" not in current_app.config:
        logs.info("'SERVICES' not in current_app.config")
    else:
        logs.info(f"Getting {service} config from current_app.config['SERVICES'] ")
        service_config = current_app.config['SERVICES'].get(service)
        logs.info(f"Getting {param} from current_app.config['SERVICES']['{service}']")
        if param not in service_config:
            logs.info(f"ERROR  : {param} not in current_app.config['SERVICES']")
            requested_param =  None
            return None
        requested_param = service_config[param]

        if param == 'scope':
            logs.info(f"INFO  : param is 'scope'")
            if isinstance(requested_param,list):
                scope = ""
                for item in requested_param:
                    scope += f" {item}"
                requested_param = scope.lstrip()
                logs.info(f"param  : {requested_param}")


    logs.info(f"get_service_config() returning  : {requested_param}")
    return requested_param



@login.user_loader
def load_user(id,):
    return db.session.get(Users, int(id))

@service.route('<svc>/oauth/')
@login_required
def service_oauth_init(destination="modpipe.dashboard",redirect_path=None,svc=None,auth_is_setup=True):
    # Get Required Parameters
    logs.info(f"Requesting {svc} scope from 'get_service_config()'")
    scope = get_service_config(svc,'scope')
    logs.info(f"Received scope  : {scope} from 'get_service_config()")
    if scope is None:
        logs.info("ERROR  : Could not get scope")
        redirect_url = f"{url_for(destination)}?error=no_{svc}_scope"
        auth_is_setup = False
    
    logs.info(f"Requesting {svc} authorize_url from 'get_service_config()'")
    auth_base = get_service_config(svc,'authorize_url')
    logs.info(f"Received authorize_url  : {auth_base} from 'get_service_config()")

    if auth_base is None:
        logs.info("ERROR  : Could not get authorize_url")
        redirect_url = f"{url_for(destination)}?error=no_{svc}_authorize_url"
        auth_is_setup = False
    
    logs.info(f"Requesting {svc} callback_url from 'get_service_config()'")
    callback_url = get_service_config(svc,'callback_url')
    logs.info(f"Received callback_url  : {callback_url} from 'get_service_config()")
    
    if callback_url is None:
        logs.info("ERROR  : Could not get callback_url")
        redirect_url = f"{url_for(destination)}?error=no_{svc}_authorize_url"
        auth_is_setup = False
 
    logs.info(f"auth_is_setup  : {auth_is_setup}")
    if auth_is_setup:
        logs.info(f"Getting authorization url for {svc} for id# {current_user.id}")
        logs.info(f"     auth_base  : {auth_base}")
        logs.info(f"     scope      : {scope}")
        result = services.authorize(current_user.id,
                                    service=svc,
                                    auth_base = auth_base,
                                    scope=scope,
                                    callback_url=callback_url)
        logs.info(f"result  : {result}")

        if not isinstance(result, dict):
            result = {
                "result": None,
                "error" : {
                    "type": None,
                    "value": None
                    }
                }
            
        if "result" in result:
            if result['result'] is None:
                redirect_path = f"{url_for(destination)}?error"
                logs.info(f"ERROR: No result from 'services.authorize()'")
                if "error" in result:
                    for arg in result['error']:
                        value = result['error'][arg] if arg is not None else "unknown"
                        redirect_path += f"&{arg}={value}"
                    logs.info(f"ERROR: Redirecting to: {redirect_path}")

        if redirect_path is None:
            redirect_path = result['result']
        redirect_url = redirect_path
        logs.info(f"REDIRECTING TO: {redirect_url}")
    return redirect(redirect_url,code=302)


@service.route('<svc>/oauth/callback')
@login_required
def service_oauth_callback(svc, callback_is_setup=True,destination="modpipe.dashboard"):
    logs.info(f"Requesting {svc} token_url from 'get_service_config()'")
    token_url = get_service_config(svc,'token_url')
    logs.info(f"Received token_url  : {token_url} from 'get_service_config()")

    if token_url is None:
        logs.info("ERROR  : Could not get token_url")
        result = {"error": "could not get token_url"}
        callback_is_setup = False

    logs.info(f"Requesting {svc} callback_url from 'get_service_config()'")
    callback_url = get_service_config(svc,'callback_url')
    logs.info(f"Received callback_url  : {callback_url} from 'get_service_config()")

    if callback_url is None:
        logs.info("ERROR  : Could not get callback_url")
        result = {"error": "could not get callback_url"}
        callback_is_setup = False


    if callback_is_setup:
        logs.info("CALLBACK IS SETUP")
        logs.info(f"Running 'services.callback({current_user.id},service='{svc}',token_url='{token_url}')")
        result = services.callback(current_user.id,
                                   service=svc,
                                   token_url=token_url,
                                   redirect_uri=callback_url
                                ) 
        logs.info(f"services.callback({current_user.id},service='{svc}',token_url='{token_url}') result  : {result}")
    

    if not result:
        result = {'error': "unknown"}

    return result


@service.route('<svc>/oauth/renew')
@login_required
def service_oauth_renew(svc):
    services.renew_token(current_user.id)


@service.route('<svc>/oauth/validate')
@login_required
def service_oauth_validate(svc):
    validate_url = get_service_config(svc,'validate_url')
    validation = services.validate_token(current_user.id,svc, validate_url=validate_url)
    return {"valid" : validation}