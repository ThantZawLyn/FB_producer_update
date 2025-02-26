import enum

from sqlalchemy import VARCHAR, Boolean, Column, DateTime, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import ENUM
from sqlalchemy.orm import relationship

from ..database import db


class TaskStatus(str, enum.Enum):
    in_queue: str = "in_queue"
    in_progress: str = "in_progress"
    success: str = "success"
    retry: str = "retry"
    failed: str = "failed"


class SubtaskType(str, enum.Enum):
    like: str = "like"
    comment: str = "comment"
    share: str = "share"
    personal_page: str = "personal_page"


class Post(db.Model):
    __tablename__ = 'posts'
    id = Column('id', Integer, primary_key=True)
    date = Column('date', DateTime)
    last_time_updated = Column('last_time_updated', DateTime)
    content_id = Column(Integer, ForeignKey('content.id'))
    task_id = Column(Integer, ForeignKey('tasks.id'))
    user_id = Column(Integer, ForeignKey('users.id'))
    stat_id = Column(Integer, ForeignKey('post_stat.id'))

    fb_post_id = Column('fb_post_id', VARCHAR(1024))
    fb_post_id_new = Column('fb_post_id_new', VARCHAR(1024))
    fb_repost_id = Column('fb_repost_id', VARCHAR(128))
    fb_repost_link = Column('fb_repost_link', VARCHAR(2048))
    fb_post_link = Column('fb_post_link', VARCHAR(1024))

    content = relationship("Content")
    task = relationship("Task")
    user = relationship("User")
    stat = relationship("PostStat")


class PostStat(db.Model):
    __tablename__ = 'post_stat'
    id = Column('id', Integer, primary_key=True)
    likes = Column('likes', VARCHAR(32))
    comments = Column('comments', VARCHAR(32))
    shares = Column('shares', VARCHAR(32))


class Photo(db.Model):
    __tablename__ = 'photos'
    id = Column('id', Integer, primary_key=True)
    content_id = Column(Integer, ForeignKey('content.id'))
    photo_link = Column('photo_link', VARCHAR(1024))

    content = relationship("Content", back_populates="photos")


class Video(db.Model):
    __tablename__ = 'videos'
    id = Column('id', Integer, primary_key=True)
    content_id = Column(Integer, ForeignKey('content.id'))
    video_link = Column('video_link', VARCHAR(1024))

    content = relationship("Content", back_populates="videos")


class Content(db.Model):
    __tablename__ = 'content'
    id = Column('id', Integer, primary_key=True)
    text = Column('text', VARCHAR(1024))

    post = relationship("Post", back_populates="content", uselist=False)
    comment = relationship("Comment", back_populates="content", uselist=False)
    photos = relationship("Photo", back_populates="content", uselist=True)
    videos = relationship("Video", back_populates="content", uselist=True)


class Subtask(db.Model):
    __tablename__ = 'subtasks'
    id = Column('id', Integer, primary_key=True)
    post_id = Column(Integer, ForeignKey('posts.id'))
    subtask_type = Column(ENUM(SubtaskType))
    start_time = Column('start_time', DateTime)
    end_time = Column('end_time', DateTime)
    status = Column(ENUM(TaskStatus))


class Task(db.Model):
    __tablename__ = 'tasks'
    id = Column('id', Integer, primary_key=True)
    interval = Column('interval', Integer)
    retro = Column('retro', DateTime)
    until = Column('until', DateTime)
    sent_time = Column('sent_time', DateTime)
    received_time = Column('received_time', DateTime)
    finish_time = Column('finish_time', DateTime)
    status = Column('status', ENUM(TaskStatus))
    enabled = Column('enabled', Boolean)
    priority = Column('priority', Integer)


class Comment(db.Model):
    __tablename__ = 'comments'
    id = Column('id', Integer, primary_key=True)
    date = Column('date', DateTime)
    fb_comment_id = Column('fb_comment_id', VARCHAR(255))
    parent_comment_id = Column('parent_comment_id', Integer)
    content_id = Column(Integer, ForeignKey('content.id'))
    likes_count = Column('likes_count', Integer)
    user_id = Column(Integer, ForeignKey('users.id'))
    post_id = Column(Integer, ForeignKey('posts.id'))
    content = relationship("Content")
    user = relationship("User")
    post = relationship("Post")


class Like(db.Model):
    __tablename__ = 'likes'
    id = Column('id', Integer, primary_key=True)
    like_type = Column('like_type', VARCHAR(255))
    post_id = Column(Integer, ForeignKey('posts.id'))
    comment_id = Column(Integer, ForeignKey('comments.id'))
    user_id = Column(Integer, ForeignKey('users.id'))
    post = relationship("Post")
    comment = relationship("Comment")
    user = relationship("User")


class TaskKeyword(db.Model):
    __tablename__ = 'tasks_keyword'
    id = Column('id', Integer, primary_key=True)
    keyword = Column('keyword', VARCHAR(255))
    task_id = Column(Integer, ForeignKey('tasks.id'))
    task = relationship("Task")


class TaskSource(db.Model):
    __tablename__ = 'tasks_source'
    id = Column('id', Integer, primary_key=True)
    source_id = Column('source_id', VARCHAR(1024))
    task_id = Column(Integer, ForeignKey('tasks.id'))
    task = relationship("Task")


class UserUniversity(db.Model):
    __tablename__ = 'user_university'
    id = Column(Integer, primary_key=True)
    name = Column('name', VARCHAR(1024))
    info = Column('info', VARCHAR(1024))
    link = Column('link', VARCHAR(1024))

    user_id = Column(Integer, ForeignKey('users.id'))
    user = relationship("User", back_populates="universities")


class UserJob(db.Model):
    __tablename__ = 'user_job'
    id = Column(Integer, primary_key=True)
    name = Column('name', VARCHAR(1024))
    info = Column('info', VARCHAR(1024))
    link = Column('link', VARCHAR(1024))

    user_id = Column(Integer, ForeignKey('users.id'))
    user = relationship("User", back_populates="jobs")


class User(db.Model):
    __tablename__ = 'users'
    id = Column('id', Integer, primary_key=True)
    name = Column('name', VARCHAR(255))
    link = Column('link', VARCHAR(255))

    sex = Column("sex", VARCHAR(8))
    city_of_birth = Column("city_of_birth", VARCHAR(128))
    current_city = Column("current_city", VARCHAR(128))
    birthday = Column("birthday", VARCHAR(128))
    fb_id = Column("fb_id", VARCHAR(32))

    universities = relationship("UserUniversity", back_populates="user")
    jobs = relationship("UserJob", back_populates="user")


class WorkerCredential(db.Model):
    __tablename__ = 'worker_credentials'
    id = Column('id', Integer, primary_key=True)
    account_id = Column('account_id', Integer)
    proxy_id = Column('proxy_id', Integer)
    user_agent_id = Column('user_agent_id', Integer)
    inProgress = Column('inProgress', Boolean)
    inProgressTimeStamp = Column('in_progress_timestamp', DateTime)
    locked = Column('locked', Boolean)
    last_time_finished = Column('last_time_finished', DateTime)
    alive_timestamp = Column('alive_timestamp', DateTime)
    attemp = Column('attemp', Integer)


class Share(db.Model):
    __tablename__ = 'shares'
    id = Column('id', Integer, primary_key=True)
    post_id = Column(Integer, ForeignKey('posts.id'))
    user_id = Column(Integer, ForeignKey('users.id'))
    post = relationship("Post")
    user = relationship("User")


class FBAccount(db.Model):
    __tablename__ = 'accounts'
    id = Column('id', Integer, primary_key=True)
    login = Column('login', VARCHAR(255))
    password = Column('password', VARCHAR(255))
    available = Column('available', Boolean, nullable=False)


class Proxy(db.Model):
    __tablename__ = 'proxy'
    id = Column('id', Integer, primary_key=True)
    host = Column('host', VARCHAR(255))
    port = Column('port', Integer)
    login = Column('login', VARCHAR(255))
    password = Column('password', VARCHAR(255))
    available = Column('available', Boolean)
    last_time_checked = Column('last_time_checked', DateTime)
    expirationDate = Column('expirationDate', DateTime)
    attempts = Column('attempts', Integer)


class UserAgent(db.Model):
    __tablename__ = 'user_agent'
    id = Column('id', Integer, primary_key=True)
    userAgentData = Column('userAgentData', VARCHAR(2048))
    window_size_id = Column(Integer, ForeignKey('window_size.id'))
    window_size = relationship("WindowSize")


class WindowSize(db.Model):
    __tablename__ = 'window_size'
    id = Column('id', Integer, primary_key=True)
    width = Column('width', Integer)
    height = Column('height', Integer)
