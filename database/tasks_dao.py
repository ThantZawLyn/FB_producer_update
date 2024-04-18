from datetime import datetime

from dateutil import parser

from sqlalchemy import false, or_, text, true

from ..database import db
from ..database.models import (Post, Subtask, SubtaskType, Task, TaskKeyword,
                               TaskSource, TaskStatus, User, WorkerCredential)
from ..main import (TIMEOUT_BETWEEN_ACCOUNTS_WORK,
                    TIMEOUT_BETWEEN_RETRY_SEND,
                    logger)


def create_task(data):
    """Создание задачи в БД."""
    task = Task(interval=data['interval'],
                retro=parser.parse(data['retro']),
                enabled=data['enabled'])
    if 'until' in data:
        task.until = data['until']

    db.session.add(task)
    db.session.commit()
    return task


def patch_task(task, data):
    """Обновление задачи в БД."""
    if 'interval' in data:
        task.interval = data['interval']
    if 'retro' in data:
        task.retro = data['retro']
    if 'until' in data:
        task.until = data['until']
    if 'enabled' in data:
        task.enabled = data['enabled']


def create_keyword(data):
    """Добавление ключевого слова в БД."""
    if has_task_keyword_by_keyword(data['keyword']):
        return False

    task = create_task(data)
    keyword = TaskKeyword(keyword=data['keyword'], task_id=task.id)
    db.session.add(keyword)
    db.session.commit()
    return keyword


def patch_keyword(task_type, data):
    """Обновление ключевого слова в БД."""
    if 'keyword' in data:
        task_type.keyword = data['keyword']
    patch_task(task_type.task, data)
    db.session.commit()
    return task_type


def create_source(data):
    """."""
    if has_task_source_by_source_id(data['source_id']):
        return False

    task = create_task(data)
    source = TaskSource(source_id=data['source_id'], task_id=task.id)
    db.session.add(source)
    db.session.commit()
    return source


def patch_source(task_type, data):
    if 'source_id' in data:
        task_type.source_id = data['source_id']
    patch_task(task_type.task, data)
    db.session.commit()
    return task_type


def get_tasks():
    return Task.query.all()


def get_task_sources():
    return TaskSource.query.all()


def get_task_keywords():
    return TaskKeyword.query.all()


def has_task_source_by_source_id(source_id):
    if db.session.query(TaskSource).filter(TaskSource.source_id == source_id).first():
        return True
    return False


def get_task_source(task_id):
    task_query = TaskSource.query.filter(TaskSource.id == task_id)
    return task_query.first()


def has_task_keyword_by_keyword(keyword):
    if db.session.query(TaskKeyword).filter(TaskKeyword.keyword == keyword).first():
        return True
    return False


def get_task_keyword(task_id):
    task_query = TaskKeyword.query.filter(TaskKeyword.id == task_id)
    return task_query.first()


def get_task(task_id):
    task_query = Task.query.filter(Task.id == task_id)
    return task_query.first()


def get_subtasks(task_id):
    subtasks = db.session.query(Subtask).join(
        Post,
        Post.id == Subtask.post_id
    ).join(
        Task,
        Task.id == Post.task_id
    ).filter(Task.id == task_id).all()

    return subtasks


def get_subtasks_statistics(task_id):
    def get_base_query():
        return db.session.query(Subtask).join(
            Post,
            Post.id == Subtask.post_id
        ).filter(Post.task_id == task_id)

    all = get_base_query().count()
    in_progress = get_base_query().filter(
        Subtask.status == TaskStatus.in_progress
    ).count()
    failed = get_base_query().filter(Subtask.status == TaskStatus.failed).count()
    success = get_base_query().filter(Subtask.status == TaskStatus.success).count()

    comments = get_base_query().filter(
        Subtask.subtask_type == SubtaskType.comment
    ).count()
    shares = get_base_query().filter(
        Subtask.subtask_type == SubtaskType.share
    ).count()
    likes = get_base_query().filter(
        Subtask.subtask_type == SubtaskType.like
    ).count()
    users = get_base_query().filter(
        Subtask.subtask_type == SubtaskType.personal_page
    ).count()

    return all, in_progress, failed, success, comments, shares, likes, users


def change_task_status(task_id):
    task = db.session.query(Task).filter(Task.id == task_id).first()
    task.sent_time = datetime.now().isoformat()
    task.status = TaskStatus.in_queue
    db.session.commit()


def change_subtask_status(subtask):
    subtask.status = TaskStatus.in_queue
    db.session.commit()


def get_keywords_ready_to_sent():
    return db.session.query(TaskKeyword). \
        join(Task, TaskKeyword.task_id == Task.id).filter(Task.id.in_(get_tasks_query()))


def get_sources_ready_to_sent():
    return db.session.query(TaskSource). \
        join(Task, TaskSource.task_id == Task.id).filter(Task.id.in_(get_tasks_query()))


def get_tasks_query():
    none_count = db.session.query(Task).filter(Task.status.is_(None)).count()
    print("New tasks with null count: {}".format(none_count))

    if none_count > 0:
        return db.session.query(Task.id).filter(
            Task.status.is_(None)
        ).order_by(Task.id)

    retry_new_task_count = db.session.query(Task).filter(
        Task.status == TaskStatus.retry
    ).filter(text('((tasks.finish_time + \'' + str(3) +
                    ' minute\'::interval) < \'' + str(datetime.now()) +
                    "\' or tasks.finish_time is Null)")).count()    
    

    print("Retry new task with finish time count: {}".format(retry_new_task_count))

    if retry_new_task_count > 0:
        return db.session.query(Task.id).filter(
            Task.status == TaskStatus.retry
        ).filter(
            text('((tasks.finish_time + \'' + str(3) +
                    ' minute\'::interval) < \'' + str(datetime.now()) +
                    "\' or tasks.finish_time is Null)")
        ).order_by(Task.received_time)

    return db.session.query(Task.id).filter(
        task_ready_to_send_condition_repeat_send()
    ).order_by(
        text('(tasks.received_time + (tasks.interval || \' minute\')::interval)')
    )


def get_like_ready_to_sent():
    return subtasks_query(SubtaskType.like)


def get_share_ready_to_sent():
    return subtasks_query(SubtaskType.share)


def get_personal_data_to_sent():
    return subtasks_query(SubtaskType.personal_page)


def get_comments_to_sent():
    return subtasks_query(SubtaskType.comment)


def subtasks_query(subtask_type):
    return db.session.query(Subtask).filter(
        Subtask.subtask_type == subtask_type
    ).filter(
        text('subtasks.status is Null or subtasks.status = \'retry\'')
    ).order_by(Subtask.id.desc())


def task_ready_to_send_condition_repeat_send():
    return text(
        '(tasks.received_time is not Null) and (tasks.received_time + (tasks.interval || \' minute\')::interval) < \'' + str(
            datetime.now()) + '\'' +
        ' and tasks.enabled = true'
        ' and (tasks.status = \'success\' or tasks.status = \'retry\' or tasks.status = \'in_queue\'or tasks.status is Null)')


def get_available_wc():
    available_wc_count = db.session.query(WorkerCredential).filter(
        WorkerCredential.attemp <= 10
    ).filter(
        WorkerCredential.inProgress == false()
    ).filter(
        text('((worker_credentials.last_time_finished + \'' +
             str(TIMEOUT_BETWEEN_ACCOUNTS_WORK) +
             ' minute\'::interval) < \'' + str(datetime.now()) +
             "\' or worker_credentials.last_time_finished is Null)")
    ).count()

    logger.log("Available wc count to send: {}".format(str(available_wc_count)))

    return available_wc_count
