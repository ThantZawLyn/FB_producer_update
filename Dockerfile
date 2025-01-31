FROM tiangolo/uwsgi-nginx-flask:python3.8

WORKDIR /pysetup
#COPY requirements.txt . /pysetup/
COPY ./requirements.txt /pysetup/

RUN pip install --no-cache-dir -r requirements.txt
RUN ln -sf /usr/share/zoneinfo/Asia/Yangon /etc/localtime

WORKDIR /app

#COPY . /app/ /app/
COPY ./app/ /app/
