import requests
import json
import os.path as path
import re
import secrets
from time import sleep
from sys import stderr
from flask import Flask, redirect, request, jsonify
from app import logs


class NightBot:
    def __init__(self,
                 base_url='https://api.nightbot.tv',
                 authorize_url='https://api.nightbot.tv/oauth2/authorize',
                 token_url='https://api.nightbot.tv/oauth2/token',
                 callback_url=None,
                 scope=None,
                 debug=False):
        ''' NightBot API Helper Class
            ### inputs ###
            app_url: base hosted app's url **must be https
                     ex...  https://nightbot.example.com
            client_id: client id from nightbot
            client_secret: client secret from nightbot
            scope: necessary only if you want to limit scope of the app.
                   otherwise it uses all scopes.
            debug: will output debug information to stderr

            base_url (str): base uri of NightBot's API Server
            api_base_url: base uri of api
            authorize_url: url to authenticate via oauth2
            token_url: url to retrieve oauth2 token
            redirect_uri: OAUTH2 Redirect URI - MUST BE REGISTERED WITH NIGHTBOT APP
            scope: scopes we are requesting access to
        '''
        self.debug = debug
        self.base_url = base_url
        self.api_base_url = f"{self.base_url}/1"
        self.authorize_url = authorize_url
        self.token_url = token_url
        self.response_type = "code"
        self.code = None
        self.token = {}
        self.bearer = None
        self.api_user = None
        self.callback_url = callback_url

        # DANGER: EVERYTHING BELOW THIS LINE NEEDS TO BE NOT HARD CODED!!! It should be provided by the user
        # NOTE: For those trying to find data leaks, the creds are changed after each test.  Whatever is in GitHub is an old rotated secret.
        self.redirect_uri = self.callback_url
        self.state = secrets.token_urlsafe(16)
        self.scope = scope if scope else "channel channel_send commands commands_default regulars subscribers"

    def logging(self,log):
        if self.debug:
            logs.info(log)

    def ready(self,client={},required=['client_id']):
        ''' Checks to see if 'client_id' and 'client_secret' are provided
        '''
        for requirement in required:
            if requirement in client and client[requirement]:
                pass
            else: 
                return False
        return True
        
    def index(self):
        ''' Generates the index page
        '''
        if self.bearer:
            return "Already Authorized"
        else:
            return "<a href='/oauth/initiate'>LOGIN</a>"

    # Authentication
    def oauth2_authorize(self,client_id=None):
        ''' Authenticates with NightBot API via OAUTH2
        '''
        client = {"client_id": client_id}
        required = ['client_id']
        if self.ready(client=client, required=required):
            ''' If 'client_id' is provided we authenticate, otherwise we send the user to /config
            '''
            self.logging("AUTHORIZE READY")
            redirect_url = f"{self.authorize_url}?response_type={self.response_type}"
            redirect_url += f"&client_id={client_id}&redirect_uri={self.redirect_uri}"
            redirect_url += f"&scope={self.scope}&state={self.state}"
            self.logging(redirect_url)
            return redirect( redirect_url, code=302)
        else:
            self.logging("AUTHORIZE NOT READY")
            return redirect("/config", code=302)

    def oauth2_callback(self,client_id=None,client_secret=None,code=None):
        ''' Retrieves access_token from NightBot.
                NOTES:
                    - Need to store more info about the token including when it will expire, refresh code, etc.
                    - Should we automatically get a refresh token prior to expiration or require user interaction?
        '''
        client = {"client_id":client_id,"client_secret":client_secret}
        required = ['client_id','client_secret']
        if self.ready(client=client,required=required):
            if "code" in request.args:
                self.code = request.args['code']
                data = {
                    "client_id"      : client_id,
                    "client_secret"  : client_secret,
                    "code"           : code,
                    "grant_type"     : "authorization_code"
                }
                self.logging(self.token_url)
                self.logging(code)
                self.logging(data)
                x = requests.post(self.token_url, data = data)
                self.token = json.loads(x.text)
                self.logging(self.token)
                if "access_token" in self.token:
                    self.bearer= self.token["access_token"]
                    self.headers = {
                        "Authorization": f"Bearer {self.bearer}"
                    }
                return redirect('/', code=302)
            else:
                return jsonify("ERROR: NO TOKEN")
        else:
            self.logging("CALLBACK NOT READY")
            return redirect("/config", code=302)
        
    # API - /1/me
    def get_me(self):
        ''' NightBot API Endpoint /me: Provides authenticated user information
                NOTES:
                    - For now it just returns the JSON provided by the API
                    - Should display user info in a clear way
        '''
        if not self.headers:
            return redirect('/', code=302)
        else:
            api_result = requests.get(
                f"{self.api_base_url}/me",
                headers = self.headers
                )
            self.api_user = json.loads(api_result.text)
            
            return jsonify(self.api_user)
    
    def channel_send(self):
        ''' Sends a test message to make sure things are working
        '''
        if not self.headers:
            return redirect('/', code=302)
        else:
            data = {
                "message"        : "This is a test of channel send from NightBot-Web."
            }
            api_result = requests.post(
                f"{self.api_base_url}/channel/send",
                headers = self.headers,
                data = data
                )
            result_json = json.loads(api_result.text)
            return jsonify(result_json)
    
    def channel_send_from_file(self,msg):
        ''' Sends a message stored in a file
                NOTES:
                    - Splits messages into 390 character chunks to stay under the 400 character limit.
                    - Need to refine for different use cases
        '''
        if not self.headers:
            return redirect('/',code=302)
        else:
            message_source = f"/data/messages/{msg}"
            if not path.exists(message_source):
                return f"{message_source} does not exist"
            else:
                with open(message_source) as message_file:
                    message = []
                    for line in message_file:
                        message.append(line)
                if not message:
                    return "Message could not be read."
                else:
                    text = ""
                    msg_queue = []
                    for line in message:
                        new_line = f"{text} {line}"
                        if len(new_line) <= 390:
                            text = new_line
                        else:
                            msg_queue.append(text)
                            text = line
                    if len(text) > 0:
                        msg_queue.append(text)
                    for line in msg_queue:
                        results = []
                        api_result = requests.post(
                            f"{self.api_base_url}/channel/send",
                            headers = self.headers,
                            data = {
                                "message" : line
                            }
                        )
                        results.append(json.loads(api_result.text))
                        sleep(5.5)
                    return jsonify(results)
                

    def verify_model(self,api_model,param=None,data=None):
        
        # We aren't using this yet, so we will return true until we enable it.
        return True

    def api_send(self,api_model,param=None,data=None):
        if not self.bearer:
            self.logging("No Bearer")
            return {
                "error":"no bearer"
                }
        else:
            self.logging("Bearer Present, continue")
            self.logging(api_model)
            self.logging(data)
            api_result = None
            if "method" in api_model:
                if api_model['method'] == "GET" or api_model['method'] == "POST":
                    api_model_url = api_model['url'].split(':')
                    try:
                        model_param = data[api_model_url[1]]
                    except:
                        model_param = ""
                    self.logging(f"###param###: {param}")
                    url = f"{self.base_url}{api_model_url[0]}"
                    url = f"{url}{param}" if param else url
                    self.logging(f"###URL###: {url}")
                    if api_model['method'] == "POST":
                        api_result = requests.post(
                            f"{url}",
                            headers = self.headers,
                            data = data
                        )
                    if api_model['method'] == "GET":
                        api_result = requests.get(
                            f"{url}",
                            headers = self.headers
                            )
                    if api_result:
                        self.logging(api_result)
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
