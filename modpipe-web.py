import os
import config
from app import app
from app import logs
logs.info(config.Config)
app.config.from_object(os.environ['APP_SETTINGS'])