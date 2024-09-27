import secrets
import requests
import json
import time

from flask import redirect, request, jsonify, url_for

from app import logs
from app import db
from app.models.database import Twitch as TwitchDB
from app.models.database import Commands as CommandsDB
from app.models.database import NightBot as NightBotDB

class Services:
    def __init__(
            self,
            base_url="",
            api_url="",
            token_url="",
            debug=False
    ):
        self.debug = debug
        self.base_url = base_url
        self.api_url = api_url
        self.token_url = token_url
        self.state = secrets.token_urlsafe(16)

    def ready(self,
                client={},
                required=['client_id']):
        logs.info(f"required :  {required}")
        logs.info(f"client   :  {client}")
        for item in required:
            if item not in client:
                return False
        return True
    
    def get_client_from_db(self,
                           id=None,
                           service=None,
                           client={}
                           ):
        if service is None:
            return False
        if service == "twitch":
            database = TwitchDB.query.filter_by(owner=id).scalar()
        elif service == "nightbot":
            database = NightBotDB.query.filter_by(owner=id).scalar()
        
        logs.info(f"{service} db query  : {database}")
        if database is None:
            return False
        client['client_id'] = database.client_id
        client['client_secret'] = database.client_secret
        client['token'] = database.token
        logs.info(client)
        return client
    
    def store_token_in_db(
                            self,
                            id=None,
                            token=None,
                            service=None,
                            return_value={"error":"unknown"}
                            ):
        
        logs.info(f"{service}  : Storing token in database")
        logs.info(f"    TOKEN  : {token}")
        
        
        if not id:
            return_value = {"error": "user id not provided"}
        else:
            if service is None or service == "":
                return_value = {"error": "Setup Error - No Service Defined"}
            elif service == "twitch":
                database = TwitchDB.query.filter_by(owner=id).scalar()
            elif service == "nightbot":
                database = NightBotDB.query.filter_by(owner=id).scalar()
            else:
                return_value = {"error": f"{service} not supported"}

            if not database:
                return_value = {"error": f"no {service} database"}
            else:
                if not token:
                    return_value = {"error": "no token"}
                else:
                    database.token = token
                    db.session.add(database)
                    db.session.commit()
                    return_value = True

        return return_value

    def authorize(self,
                  id,
                  service=None,
                  required=['client_id'],
                  state=None,
                  auth_base=None,
                  scope=None,
                  callback_url=None,
                  response_type="code"
                  ):
        logs.info(f"Getting {service} client for ID# {id}")
        client = self.get_client_from_db(id,service=service)
        logs.info(f"result  : {client}")

        if client is not None and scope is not None:
            if "state" in request.args:
                    state = request.args['state']
            else:
                state = self.state

            if self.ready(client=client,required=required):
                redirect_url = auth_base
                redirect_url += f"?response_type={response_type}"
                redirect_url += f"&client_id={client['client_id']}"
                redirect_url += f"&redirect_uri={callback_url}"
                redirect_url += f"&scope={scope}"
                redirect_url += f"&state={state}"
                return {
                        "result": redirect_url,
                        "error" : {
                                "type": None,
                                "value": None
                        }
                        }
            else:
                return {
                        "result": None,
                        "error" : {
                            "type"  : "config",
                            "value" : "invalid"
                            }
                        }
            
        if client is None or client == "":
            return {
                    "result": None,
                    "error" : {
                        "type" :    "config",
                        "value" :   "client_missing"
                        }
                    }
        if scope is None or scope == "":
            return {
                    "result": None,
                    "error": {
                        "type" :    "config",
                        "value" :   "scope_missing"
                    }
            }
        return None
    
    def callback(self,
                 id,
                 service=None,
                 required=['client_id','client_secret'],
                 code=None,
                 token_url=None,
                 redirect_uri=None
                 ):
        if service is None:
            return {
                    "error": {
                        "type"  : "fatal",
                        "value" : "unsupported"
                        }
                    }
        logs.info(f"running services.get_client_from_db({id},service='{service}')")
        client = self.get_client_from_db(id,service=service)
        logs.info(f"result  : {client}")

        if self.ready(client=client,required=required):
            if "code" in request.args:
                code = request.args['code']
            if "state" in request.args:
                state = request.args['state']
            data = {
                "client_id"     : client['client_id'],
                "client_secret" : client['client_secret'],
                "code"          : code,
                "grant_type"    : "authorization_code",
                "redirect_uri"  : redirect_uri
            }
            headers = {'Accept': 'application/json'}
            logs.info(f"sending token request to {token_url}")
            logs.info(f"     data  : {data}")
            logs.info(f"  headers  : {headers}")
            response = requests.post(   
                                    token_url,
                                    data = data,
                                    headers = headers
                                    )
            token = response.json()
            logs.info(f"TOKEN response from {service} : {token}")

            token['renew_before'] = time.time() + token['expires_in']
            logs.info(f"Storing in {service} database  : {token}")
            token_result = self.store_token_in_db(id=id,token=token,service=service)
            logs.info(f"self.state  : {self.state}")
            logs.info(f"state       : {state}")
            if state != self.state:
                redirect_url = state
                redirect_url = f"{state}&" if "?" in redirect_url else "?"
                redirect_url += "auth=true"
                logs.info(f"redirect_url  :  {redirect_url}")
                return redirect(redirect_url)
            return {"token_result": token_result}

        return {"error": "callback not ready"}
    
    def renew_token(self,
                    id,
                    service=None
                    ):
        client = self.get_client_from_db(id=id)
        if not client['error']:
            data = {
                        "client_id": client['client_id'],
                        "client_secret": client['client_secret'],
                        "grant_type": "refresh_token",
                        "redirect_uri": self.callback_url,
                        "refresh_token": client['token']['refresh_token']
                    }
            token = json.loads(
                requests.post(self.token_url, data = data)
            )
            token['renew_before'] = time.time() + client['token']['expires_in']
            client['token'] = token
            self.store_token_in_db(id,token=token)

        
    def get_bearer(self,
                   id,
                   service=None):
        client = self.get_client_from_db(id=id)
        if client:
            if "renew_before" in client['token']:
                now = time.time()
                logs.info(f"now          :  {now}")
                logs.info(f"renew_before :  {client['token']['renew_before']}")
                if now < client['token']['renew_before']:
                    return client['token']['access_token']
                return False
    
    def validate_token(self,
                       id,
                       service=None
                       ):
        client = self.get_client_from_db(id=id)
        if client:
            pass


