# YouVersion app key is never be hardcoded or logged
# it only ever lives in an env var and is read here once at startup

import os

class ConfigError(Exception):
    pass

#this is where env vars are read
class Config:
    def __init__(self, app_key=None, base_url=None):
        #gets the api key and url from env var or what's provided
        self.app_key = app_key or os.environ.get("YOUVERSION_APP_KEY") #only place the key is read
        self.base_url = base_url or os.environ.get(
            "YOUVERSION_BASE_URL", "https://api.youversion.com"
        )
        if not self.app_key: #just for safety
            raise ConfigError(
                "YOUVERSION_APP_KEY is not set. Copy .env.example to .env and fill it in."
            )
