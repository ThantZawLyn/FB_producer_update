from datetime import datetime

from sqlalchemy import false, func, text, true

from ..database import db
from ..database.models import (FBAccount, Proxy, UserAgent, WindowSize,
                               WorkerCredential)
from ..main import logger


def update_worker_credential(data):
    """Обновление рабочего аккаунта."""
    worker_credential = db.session.query(WorkerCredential).filter(
        (WorkerCredential.account_id == data['account_id']) &
        (WorkerCredential.proxy_id == data['proxy_id']) &
        (WorkerCredential.user_agent_id == data['user_agent_id'])
    ).with_for_update().first()

    worker_credential.locked = True

    db.session.commit()
    return worker_credential


def get_accounts():
    """Получение полного списка аккаунтов."""
    return db.session.query(FBAccount).all()


def get_accounts_stat():
    """Получение статистики по аккаунтам."""
    all = db.session.query(FBAccount).count()
    available = db.session.query(FBAccount).filter(FBAccount.available == true()).count()
    return all, available


def create_account(login, password):
    """Создать аккаунт."""
    account = db.session.query(FBAccount).filter(FBAccount.login == login).first()
    if not account:
        fb_account = FBAccount(login=login, password=password, available=True)
        db.session.add(fb_account)
        db.session.commit()
        return True
    return False


def get_proxy():
    """Получение полного списка прокси."""
    return db.session.query(Proxy).all()


def get_user_agent():
    """Получение полного списка user-agent."""
    return db.session.query(UserAgent).all()


def get_proxy_stat():
    """Получение всех прокси и количества доступных среди них."""
    available = db.session.query(Proxy).filter(Proxy.available == true()).count()
    return get_proxy(), available


def create_user_agent(user_agent_string):
    """Создание user-agent."""
    user_agent = db.session.query(UserAgent).filter(
        UserAgent.userAgentData == user_agent_string).first()

    if not user_agent:
        window_size = db.session.query(WindowSize).order_by(func.random()).first()
        db.session.add(
            UserAgent(userAgentData=user_agent_string, window_size=window_size))
        db.session.commit()
        return True
    return False


def create_proxy(ip, port, login, password, expiration_date):
    """Создание прокси."""
    proxy = db.session.query(Proxy).filter(
        (Proxy.host == ip) &
        (Proxy.port == port) &
        (Proxy.login == login) &
        (Proxy.password == password)
    ).first()
    if not proxy:
        db.session.add(
            Proxy(
                host=ip,
                port=port,
                login=login,
                password=password,
                available=True,
                expirationDate=expiration_date)
        )
        db.session.commit()
        return True
    return False


def free_frozen_credentials():
    """Освобождение замороженных в in_progress аккаунтов от этого статуса."""
    credentials = db.session.query(WorkerCredential).filter(
        WorkerCredential.inProgress == true()
    ).filter(
        text(
            '(worker_credentials.alive_timestamp is not Null) and (worker_credentials.alive_timestamp + \'5 minute\'::interval) < \'' +
            str(datetime.now()) + "\'")
    ).with_for_update().all()

    for c in credentials:
        print("working_credentials with id={} set inProgress=false".format(c.id))
        c.inProgress = False
        db.session.commit()


def get_disabled_proxies(limit):
    """Получение списка отключенных прокси."""
    query = db.session.query(WorkerCredential).join(
        Proxy,
        Proxy.id == WorkerCredential.proxy_id
    ).filter(
        WorkerCredential.locked == true()
    ).filter(
        Proxy.available == false()
    ).filter(
        text('((proxy.last_time_checked + \'20 minute\'::interval) < \'' +
             str(datetime.now()) + "\' or proxy.last_time_checked is Null)")
    )
    if limit:
        return query.limit(limit).all()
    else:
        return query.all()


def get_potential_new_wc_count():
    """Получение количества потенциальных рабочих аккаунтов."""
    working_credentials_accounts = db.session.query(WorkerCredential.account_id)
    account_count = db.session.query(FBAccount).filter(
        (~FBAccount.id.in_(working_credentials_accounts)) &
        (FBAccount.available == true())
    ).count()

    working_credentials_proxy = db.session.query(WorkerCredential.proxy_id)
    proxy_count = db.session.query(Proxy).filter(
        (~Proxy.id.in_(working_credentials_proxy)) &
        (Proxy.available == true())).count()

    working_credentials_user_agent = db.session.query(WorkerCredential.user_agent_id)
    user_agent = db.session.query(UserAgent).filter(
        ~UserAgent.id.in_(working_credentials_user_agent)
    ).count()

    return account_count, proxy_count, user_agent
