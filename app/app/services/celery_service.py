from celery import Celery

from ..database.models import SubtaskType
from ..database.tasks_dao import change_subtask_status, change_task_status
from ..main import app, logger

TASK_KEYWORD_ID = "task_keyword_id"
TASK_SOURCE_ID = "task_source_id"
TASK_WARM_ACCOUNT = "task_warm_account"
TASK_RE_LOGIN_ALL_DISABLED_ACCOUNTS = "task_re_login_all_disabled_accounts"
TASK_RE_ENABLE_ALL_DISABLED_PROXY = "task_re_enable_all_disabled_proxy"
SUB_TASK_POST_LIKES = "sub_task_post_likes"
SUB_TASK_POST_COMMENTS = "sub_task_post_comments"
SUB_TASK_POST_SHARES = "sub_task_post_shares"
SUB_TASK_PERSONAL_PAGE = "sub_task_personal_page"

celery = Celery(
    app.config['CELERY_QUEUE_NAME'],
    broker=app.config['CELERY_BROKER_URL'],
    backend=app.config['CELERY_BACKEND']
)
celery.conf.update(app.config)
celery.conf.task_routes = (
    [('task.*', {'queue': 'tasks'}), ('sub_task.*', {'queue': 'sub_tasks'})],)


def send(task_limit, get_function, send_function):
    """???"""
    if task_limit > 0:
        tasks = get_function().limit(task_limit).all()

        tasks_count = len(tasks)
        for t in tasks:
            send_function(t)
        return tasks_count
    return 0


def send_keyword(task_id):
    """Отправление задачи по ключевому слову."""
    logger.log("send keyword with task_id: {}".format(task_id))
    change_task_status(task_id)
    celery.send_task(TASK_KEYWORD_ID, args=(task_id,))


def send_source(task_id):
    """Отправление задачи по указанному источнику."""
    logger.log("send source with task_id: {}".format(task_id))
    change_task_status(task_id)
    celery.send_task(TASK_SOURCE_ID, args=(task_id,))


def send_keyword_by_task(task):
    """Отправление ключевого слова по номеру задачи."""
    send_keyword(task.task_id)


def send_source_by_task(task):
    """Отправление источника по номеру задачи."""
    send_source(task.task_id)


def send_accounts_warming():
    """Отправление задачи по прогреву аккаунтов."""
    logger.log("send account warming")
    celery.send_task(TASK_WARM_ACCOUNT)


def send_re_login_disabled_accounts():
    """Отправление аккаунтов на перезапуск."""
    logger.log("send re login disabled accounts")
    celery.send_task(TASK_RE_LOGIN_ALL_DISABLED_ACCOUNTS)


def send_re_enable_disabled_proxy(proxy_id):
    """Отправление прокси на перезапуск."""
    logger.log("send re enabled disabled proxy id: {}".format(proxy_id))
    celery.send_task(TASK_RE_ENABLE_ALL_DISABLED_PROXY, args=(proxy_id,))


def send_subtask_like(subtask_id, countdown=None):
    """Отправление позадачи лайк."""
    logger.log("send like subtask_id: {}".format(subtask_id))
    celery.send_task(SUB_TASK_POST_LIKES, args=(subtask_id,), countdown=countdown)


def send_subtask_comment(subtask_id, countdown=None):
    """Отправление позадачи коммент."""
    logger.log("send comment subtask_id: {}".format(subtask_id))
    celery.send_task(SUB_TASK_POST_COMMENTS, args=(subtask_id,), countdown=countdown)


def send_subtask_share(subtask_id, countdown=None):
    """Отправление позадачи шэринга."""
    logger.log("send shares subtask_id: {}".format(subtask_id))
    celery.send_task(SUB_TASK_POST_SHARES, args=(subtask_id,), countdown=countdown)


def send_subtask_personal_page(subtask_id, countdown=None):
    """Отправление позадачи по извлечению личной страницы."""
    logger.log("send personal page subtask_id: {}".format(subtask_id))
    celery.send_task(SUB_TASK_PERSONAL_PAGE, args=(subtask_id,), countdown=countdown)


def send_subtask(subtask):
    """Отправление подзадачи."""
    change_subtask_status(subtask)

    if subtask.subtask_type == SubtaskType.like:
        send_subtask_like(subtask.id)

    if subtask.subtask_type == SubtaskType.comment:
        send_subtask_comment(subtask.id)

    if subtask.subtask_type == SubtaskType.share:
        send_subtask_share(subtask.id)

    if subtask.subtask_type == SubtaskType.personal_page:
        send_subtask_personal_page(subtask.id)
