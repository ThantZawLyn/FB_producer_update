import os

from flask import Flask

from .utils.logging import Log

app = Flask(__name__)
logger = Log()

CURRENT_PROFILE = 'prod'

app.config['CELERY_QUEUE_NAME'] = 'tasks'
app.config['CELERY_BROKER_URL'] = 'amqp://guest@{0}//'.format(
    os.environ.get('RABBITMQ_SERVICE_SERVICE_HOST')
)
app.config['CELERY_BACKEND'] = 'amqp'
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('FBS_DATABASE_POSTGRESQL_SERVICE_HOST')

logger.log("PRODUCER LINK " + app.config['SQLALCHEMY_DATABASE_URI'])

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

TIMEOUT_BETWEEN_ACCOUNTS_WORK = 3
TIMEOUT_BETWEEN_RETRY_SEND = 5
