class API:

    # ME
    def __init__(self):
        self.me = {
            "method" : "GET",
            "url" : "/1/me",
            "result" :{
                "status" : int,
                "authorization":{
                    "userLevel" : str,
                    "authType" : str,
                    "credentials" : {
                        "expires" : str,
                        "client" : str
                    }
                }
            }
        }


        # CHANNEL
        self.channel = {
            "method": "GET",
            "url": "/1/channel",
            "result":{
                "status" : int,
                "channel" : {
                    "_id": str,
                    "name": str,
                    "displayName": str,
                    "joined": bool,
                    "plan": str
                }
            }
        }

        self.channel_join = {
            "method": "POST",
            "url": "/1/channel/join",
            "data": None,
            "result": {
                "status": int
            }
        }

        self.channel_part = {
            "method": "POST",
            "url": "/1/channel/part",
            "data": None,
            "result": {
                "status": int
            }
        }


        # CHANNEL SEND
        self.channel_send = {
            "method": "POST",
            "url": "/1/channel/send",
            "data": {
                "message": str
            },
            "result": {
                "status": int
            }
        }


        # COMMANDS

        # CUSTOM COMMANDS
        self.custom_commands_get_all = {
            "method": "GET",
            "url": "/1/commands",
            "result": {
                "commands": [
                    {
                        "_id": str,
                        "createdAt": str,
                        "updatedAt": str,
                        "name": str,
                        "message": str,
                        "coolDown": int,
                        "count": int,
                        "userLevel": str
                    }
                ]
            }
        }

        self.custom_command_add = {
            "method": "POST",
            "url": "/1/commands",
            "data": {
                "message": str,
                "userLevel": str,
                "coolDown": int,
                "name": str
            },
            "result": {
                "createdAt": str,
                "updatedAt": str,
                "name": str,
                "message": str,
                "id": str,
                "cooldown": int,
                "count": int,
                "userLevel": str
            }
        }
        
        self.custom_command_get = {
            "method": "GET",
            "url": "/1/commands/:id",
            "id": str,
            "result": {
                "_id": str,
                "createdAt": str,
                "updatedAt": str,
                "name": str,
                "message": str,
                "coolDown": int,
                "count": int,
                "userLevel": str
            }
        }

        self.custom_command_edit = {
            "method": "PUT",
            "url": "/1/commands/:id",
            "id": str,
            "data": {
                "cooldown": int,
                "count": int,
                "message": str,
                "name": str,
                "userLevel": str
            },
            "result": {
                "status": int,
                "createdAt": str,
                "updatedAt": str,
                "name": str,
                "message": str,
                "_id": str,
                "coolDown": int,
                "count": int,
                "userLevel": str
            }
        }

        self.custom_command_delete = {
            "method": "DELTE",
            "url": "/1/commands/:id",
            "id": str,
            "result": {
                "status": int
            }
        }


        # DEFAULT COMMANDS
        self.default_commands_get_all = {
            "method": "GET",
            "url": "/1/commands/default",
            "result": {
                "_total": int,
                "status": int,
                "commands": [
                    {
                        "name": str,
                        "coolDown": int,
                        "enabled": bool,
                        "userLevel": str,
                        "_name": str,
                        "_description": str,
                        "_docs": str
                    },
                    {...}
                ]
            }
        }

        self.default_command_get = {
            "method": "GET",
            "url": "/1/commands/default/:name",
            "name": str,
            "result": {
                "name": str,
                "coolDown": int,
                "enabled": bool,
                "userLevel": str,
                "_name": str,
                "_description": str,
                "_docs": str
            }
        }

        self.default_command_edit = {
            "method": "PUT",
            "url": "/1/commands/default/:name",
            "name": str,
            "data": {
                "coolDown": int,
                "enabled": bool,
                "userLevel": str
            },
            "result": {
                "name": "!commands",
                "coolDown": 6,
                "enabled": bool,
                "userLevel": "everyone",
                "_name": "commands",
                "_description": "Allows users to get a list of commands and moderators to manage commands",
                "_docs": "https://docs.nightbot.tv/commands/commands"
            }
        }