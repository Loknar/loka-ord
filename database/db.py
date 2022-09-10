#!/usr/bin/python
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, scoped_session, sessionmaker

import logman

# SQLAlchemy - Declarative method
# https://docs.sqlalchemy.org/en/latest/orm/extensions/declarative/basic_use.html

Engine = None
Session = None
Base = declarative_base()
Base.query = None


def setup_data_directory(folder_name, root_file):
    # TODO: don't know best practices for preventing directory traversal attack, needs reviewing
    assert('/' not in folder_name)
    assert('.' not in folder_name)
    root_directory = os.path.dirname(os.path.realpath(root_file))
    location_directory = os.path.join(root_directory, 'database/disk')
    data_directory = os.path.realpath(os.path.join(location_directory, folder_name))
    assert(data_directory.startswith(location_directory))
    if not os.path.exists(data_directory):
        os.makedirs(data_directory)
        logman.Logger.info('Created data directory for "%s".' % (folder_name, ))


def create_db_uri(db_name):
    # TODO: don't know best practices for preventing directory traversal attack, needs reviewing
    assert('/' not in db_name)
    assert('.' not in db_name)
    db_uri = ''
    use_sqlite = True
    if use_sqlite:
        db_uri = 'sqlite:///database/disk/{db_name}/db.sqlite'.format(db_name=db_name)
    return db_uri


def setup_connection(db_uri, db_echo=False):
    global Engine, Session, Base
    Engine = create_engine(db_uri, convert_unicode=True, echo=db_echo)
    Session = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=Engine))
    Base.query = Session.query_property()


def init_db():
    global Base
    # Import all modules here that define models so that they are registered on the metadata.
    # Or import them first before calling init_db()
    #
    from database import models
    Base.metadata.create_all(bind=Engine)
