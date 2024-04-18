import traceback
from datetime import timedelta
from random import randint

from timeloop import Timeloop

from ..database.tasks_dao import (get_available_wc, get_comments_to_sent,
                                  get_keywords_ready_to_sent,
                                  get_like_ready_to_sent,
                                  get_personal_data_to_sent,
                                  get_share_ready_to_sent,
                                  get_sources_ready_to_sent)
from ..database.worker_credentials_dao import free_frozen_credentials
from ..main import logger
from .celery_service import (send, send_keyword_by_task, send_source_by_task,
                             send_subtask)
from .credentials_management import accounts_warming, proxy_re_enable

TASK_PERCENTAGE = 100
SUBTASK_LIKE_PERCENTAGE = 0
SUBTASK_COMMENT_PERCENTAGE = 0
SUBTASK_SHARE_PERCENTAGE = 0
SUBTASK_PERSONAL_DATA_PERCENTAGE = 0
tl = Timeloop()


@tl.job(interval=timedelta(seconds=30))
def check_tasks():
    """Задача проверки количества аккаунтов и распределения работы между ними."""
    available_wc = get_available_wc()
    logger.log("available_wc: {}".format(available_wc))
    # TODO: Refactor this
    if available_wc <= 3:
        return

    try:
        logger.log("start send schedule tasks")
        task_count, like_count, share_count, personal_data_count, comment_count = split_wc_between_tasks(
            get_available_wc())
        logger.log(
            "free wc for tasks: {}, like: {}, share: {}, personal_data: {}, comments: {}".format(
                task_count,
                like_count,
                share_count,
                personal_data_count,
                comment_count,
            )
        )
#        keywords_count = 0
        keywords_count = send(
            task_count,
            get_keywords_ready_to_sent,
            send_keyword_by_task
        )
        source_count = send(
            task_count - keywords_count,
            get_sources_ready_to_sent,
            send_source_by_task
        )

        subtasks_like_count = send(like_count, get_like_ready_to_sent, send_subtask)
        subtasks_share_count = send(share_count, get_share_ready_to_sent, send_subtask)
        subtasks_personal_data_count = send(
            personal_data_count,
            get_personal_data_to_sent,
            send_subtask
        )
        subtasks_comment_count = send(comment_count, get_comments_to_sent, send_subtask)

        logger.log("{} keyword, "
                   "{} source, "
                   "{} like, "
                   "{} share, "
                   "{} personal data, "
                   "{} comments, "
                   .format(keywords_count,
                           source_count,
                           subtasks_like_count,
                           subtasks_share_count,
                           subtasks_personal_data_count,
                           subtasks_comment_count))
    except:
        logger.log("Error appeared. Continue scheduling")
        traceback.print_exc()


@tl.job(interval=timedelta(minutes=5))
def unlock_frozen_credentials():
    """Задача разблокировки замороженных аккаунтов."""
    print("unlock_frozen_credentials task starts")
    free_frozen_credentials()


@tl.job(interval=timedelta(minutes=3))
def warming_accounts():
    """Задача прогрева аккаунтов"""
    print("warming accounts")
    accounts_warming()


def split_wc_between_tasks(count):
    """Вычисление процентного соотношения веса всех типов задач."""
#    task_count = round((count / 100) * TASK_PERCENTAGE)
#    subtask_count = count - task_count

#    like_count = round((count / 100) * SUBTASK_LIKE_PERCENTAGE)
#    share_count = round((count / 100) * SUBTASK_SHARE_PERCENTAGE)
#    personal_data_count = round((count / 100) * SUBTASK_PERSONAL_DATA_PERCENTAGE)

#   comment_count = subtask_count - like_count - share_count - personal_data_count
 
    task_count = count
    #task_count = round((count / 100) * TASK_PERCENTAGE)
    subtask_count = count - task_count

    like_count = 0
    share_count = 0
    personal_data_count = 0
    #personal_data_count = count - task_count
    #personal_data_count = round((count / 100) * SUBTASK_PERSONAL_DATA_PERCENTAGE)
    comment_count = 0
    #comment_count = subtask_count - personal_data_count

#    comment_count = subtask_count - like_count - share_count - personal_data_count

    return task_count, like_count, share_count, personal_data_count, comment_count


tl.start()
