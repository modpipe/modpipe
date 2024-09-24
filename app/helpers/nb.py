import secrets
import requests
import json
import time

from flask import redirect, request, jsonify, url_for

from app import logs
from app import db
from app.models.database import NightBot as NightBotDB
from app.models.database import Commands as CommandsDB

class NightBot:
    def __init__(self,
                 base_url='https://api.nightbot.tv',
                 authorize_url='https://api.nightbot.tv/oauth2/authorize',
                 token_url='https://api.nightbot.tv/oauth2/token',
                 callback_url=None,
                 scope=None,
                 debug=False):
        self.debug = debug
        self.base_url = base_url
        self.api_base_url = f"{self.base_url}/1"
        self.authorize_url = authorize_url
        self.token_url = token_url
        self.response_type = "code"
        self.code = None
        self.bearer = None
        self.api_user = None
        self.callback_url = callback_url
        self.state = secrets.token_urlsafe(16)
        self.scope = scope if scope else "channel channel_send commands commands_default regulars subscribers"
 
    def get_client_from_db(self,id=None,client={}):
        nightbotdb = db.session.scalar(db.select(NightBotDB).where(NightBotDB.owner == id))
        if nightbotdb:
            client['client_id'] = nightbotdb.client_id
            client['client_secret'] = nightbotdb.client_secret
            client['token'] = nightbotdb.token
            logs.info(client)
            return client
        return False
    
    def store_token_in_db(self,id=None,token=None):
        if id:
            if token:
                nightbotdb = db.session.scalar(db.select(NightBotDB).where(NightBotDB.owner == id))
                if nightbotdb:
                    nightbotdb.token = token
                    db.session.add(nightbotdb)
                    db.session.commit()
                    return True
                return {"error": 'not found'}
            return {"error": 'no token'}
        return {"error": 'not id'}

    def ready(self,
                client={},
                required=['client_id']):
        logs.info(f"required :  {required}")
        logs.info(f"client   :  {client}")
        for item in required:
            if item not in client:
                return False
        return True
    
    def authorize(self,
                  id,
                  required=['client_id'],
                  state=None):
        client = self.get_client_from_db(id)
        if not client:
            return jsonify({"error": "no_client"})
        if "state" in request.args:
                state = request.args['state']
        else:
            state = self.state
        if self.ready(client=client,required=required):
            redirect_url = self.authorize_url
            redirect_url += f"?response_type={self.response_type}"
            redirect_url += f"&client_id={client['client_id']}"
            redirect_url += f"&redirect_uri={self.callback_url}"
            redirect_url += f"&scope={self.scope}"
            redirect_url += f"&state={state}"
            return redirect(redirect_url,code=302)
        else:
            return False
    
    def callback(self,
                 id,
                 required=['client_id','client_secret'],
                 code=None):
        client = self.get_client_from_db(id)
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
            }
            response = requests.post(self.token_url,
                                     data = data,
                                     headers={'Accept': 'application/json'})
            logs.info(f"response  : {response.json()}")

            token = response.json()
            token['renew_before'] = time.time() + token['expires_in']
            token_result = self.store_token_in_db(id=id,token=token)
            logs.info(f"self.state  : {self.state}")
            logs.info(f"state       : {state}")
            if state != self.state:
                redirect_url = f"{state}?auth=true"
                logs.info(f"redirect_url  :  {redirect_url}")
                return redirect(redirect_url)
            return {"token_result": token_result}

        return {"error": "callback not ready"}
    
    def renew_token(self,id):
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

        
    def get_bearer(self,id):
        client = self.get_client_from_db(id=id)
        if client:
            if "renew_before" in client['token']:
                now = time.time()
                logs.info(f"now          :  {now}")
                logs.info(f"renew_before :  {client['token']['renew_before']}")
                if now < client['token']['renew_before']:
                    return client['token']['access_token']
                return False
    




    def api_channel_send(self,id,userid,bearer=None):
        if bearer == False:
            logs.info(f"bearer  :  {bearer}")
            logs.info("No Bearer")
            return {
                "error":"no bearer"
                }
        else:
            logs.info(f"bearer  :  {bearer}")
            logs.info("Bearer Present, continue")
            command = db.session.scalar(db.select(CommandsDB).where(CommandsDB.id == id))
            msg = ""
            if command and command.owner == userid and command.type == "chat_message":
                logs.info("VALID CHANNEL MESSAGE COMMAND")
                msg = command.command
                logs.info(f"msg  : {msg}")
                
            messages = []
            current_message = ""
            chunks = msg.split(" ")
            for chunk in chunks:
                if len(current_message) + len(chunk) + 1 <= 390:
                    current_message += f"{chunk} "
                else:
                    messages.append(current_message)
                    current_message = ""
            if len(current_message) > 0:
                messages.append(current_message)
            

            logs.info(messages)
            for message in messages:
                results = []
                logs.info("###############################")
                url = self.api_base_url+"/channel/send"
                logs.info(f"url         : {url}")
                headers = {"Authorization": f"Bearer {bearer}"}
                logs.info(f"headers     : {headers}")
                data = {"message" : message}
                logs.info(f"message     : {message}")
                api_result = requests.post(url, headers = headers, data = data)
                logs.info(f"api_result  : {api_result}")
                logs.info("###############################")

                results.append(json.loads(api_result.text))
                time.sleep(5.5)
            result = {
                "timeout": command.timeout,
                "status": {
                    "code": 200,
                    "message": "SUCCESS"
                },
                "feedback": f"{command.name} OK",
            }

            # Build Feedback
            return_json = {}
            return_json['id'] = command.id
            return_json['name'] = command.name
            return_json['checkback'] = None
            return_json['result'] = result




            
            return jsonify(return_json)

    def api_send(self,api_model,bearer=None,param=None,data=None):
        if not bearer:
            logs.info("No Bearer")
            return {
                "error":"no bearer"
                }
        else:
            logs.info("Bearer Present, continue")
            logs.info(api_model)
            logs.info(data)
            api_result = None
            if "method" in api_model:
                if api_model['method'] == "GET" or api_model['method'] == "POST":
                    api_model_url = api_model['url'].split(':')
                    try:
                        model_param = data[api_model_url[1]]
                    except:
                        model_param = ""
                    logs.info(f"###param###: {param}")
                    url = f"{self.base_url}{api_model_url[0]}"
                    url = f"{url}{param}" if param else url
                    logs.info(f"###URL###: {url}")
                    if api_model['method'] == "POST":
                        api_result = requests.post(
                            f"{url}",
                            headers = {
                                "Authorization": f"Bearer {bearer}"
                            },
                            data = data
                        )
                    if api_model['method'] == "GET":
                        api_result = requests.get(
                            f"{url}",
                            headers = {
                                "Authorization": f"Bearer {bearer}"
                            },
                        )
                    if api_result:
                        logs.info(api_result)
                        return jsonify(
                            json.loads(
                                api_result.text
                                )
                            )
                    else:
                        return jsonify({"error": "invalid method"})
                else:
                    return jsonify({"error": "invalid method"})
            else:
                return jsonify({"error": "'method' not in 'api_model'"})
