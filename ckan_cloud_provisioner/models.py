import os
import json
import datetime

from contextlib import contextmanager

from sqlalchemy import types
from sqlalchemy import inspect
from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy import Column, Unicode, String, create_engine
from sqlalchemy.orm import sessionmaker

# ## SQL DB
Base = declarative_base()

_sql_engine = None
_sql_session = None


def setup_engine(connection_string):
    global _sql_engine
    _sql_engine = create_engine(connection_string)
    Base.metadata.create_all(_sql_engine)


# ## Json as string Type
class JsonType(types.TypeDecorator):
    impl = types.Unicode

    def process_bind_param(self, value, dialect):
        return json.dumps(value)

    def process_result_value(self, value, dialect):
        if value:
            return json.loads(value)
        else:
            return None

    def copy(self, **kw):
        return JsonType(self.impl.length)


@contextmanager
def session_scope():
    """Provide a transactional scope around a series of operations."""
    global _sql_session
    if _sql_session is None:
        assert _sql_engine is not None, "No database defined, please set your DATABASE_URL environment variable"
        _sql_session = sessionmaker(bind=_sql_engine)
    session = _sql_session()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.expunge_all()
        session.close()


def object_as_dict(obj):
    return {c.key: getattr(obj, c.key)
            for c in inspect(obj).mapper.column_attrs}

# ## USERS
class Common():
    key = Column(String(128), primary_key=True)
    value = Column(JsonType)

class User(Base, Common):
    __tablename__ = 'mcp_users'

class Instance(Base, Common):
    __tablename__ = 'mcp_instance'


def create_or_edit(kind, key, value):
    ret = dict(created=False)
    with session_scope() as session:
        document = session.query(kind).filter(kind.key==key).first()
        if document is None:
            document = kind(key=key, value=value)
            ret['created'] = True
        else:
            document.value = value
        session.add(document)
    return ret


def query(kind):
    ret = dict(results=[])
    with session_scope() as session:
        documents = session.query(kind)
        for doc in documents:
            ret['results'].append(object_as_dict(doc))
    return ret


def query_one(kind, key):
    with session_scope() as session:
        document = session.query(kind).filter(kind.key==key).first()
        if document is not None:
            return document.value


def delete(kind, key):
    ret = dict(deleted=False)
    with session_scope() as session:
        document = session.query(kind).filter(kind.key==key).first()
        if document is not None:
            ret['deleted'] = True
            session.delete(document)
    return ret
