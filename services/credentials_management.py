from ..database.worker_credentials_dao import (get_disabled_proxies,
                                               get_potential_new_wc_count)
from ..main import logger
from .celery_service import (send_accounts_warming,
                             send_re_enable_disabled_proxy)
from datetime import datetime, timedelta, time

def accounts_warming():
    """Прогрев аккаунтов."""
    logger.log("{} Datetime Now".format(datetime.now()))
    logger.log("Start accounts warming loop")
    account_count, proxy_count, user_agent_count = get_potential_new_wc_count()
    if account_count == 0:
        logger.log("Accounts are empty")
    if proxy_count == 0:
        logger.log("Proxy are empty")
    if user_agent_count == 0:
        logger.log("User agents are empty")

    if account_count == 0 or proxy_count == 0 or user_agent_count == 0:
        logger.log("Warming canceled")
        return 0

    wc_count = min(account_count, proxy_count, user_agent_count)
    logger.log("{} wc to warm found".format(str(wc_count)))
    for i in range(0, wc_count):
        send_accounts_warming()


def proxy_re_enable(limit):
    """Перезапуск прокси."""
    logger.log("Start proxies re enable")

    wcs = get_disabled_proxies(limit)
    logger.log("Proxies count: {}".format(str(len(wcs))))
    for wc in wcs:
        send_re_enable_disabled_proxy(wc.proxy_id)
