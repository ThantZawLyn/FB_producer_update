from flask_sqlalchemy import SQLAlchemy

from ..main import app
from ..utils.logging import Log

db = SQLAlchemy(app)
logger = Log()
logger.log("PRODUCER DB {0}".format(db))
from . import models
from . import tasks_dao
