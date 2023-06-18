#!/usr/bin/python
import datetime
import os
import shutil

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, scoped_session, sessionmaker

from lokaord import logman

# SQLAlchemy - Declare models
# https://docs.sqlalchemy.org/en/20/orm/quickstart.html#declare-models

Engine = None
Session = None


class Base(DeclarativeBase):
    pass


def setup_data_directory(folder_name):
    # TODO: do we need beeter practices here for preventing directory traversal attack?
    assert('/' not in folder_name)
    assert('.' not in folder_name)
    current_file_directory = os.path.dirname(os.path.realpath(__file__))
    location_directory = os.path.join(current_file_directory, 'disk')
    data_directory = os.path.realpath(os.path.join(location_directory, folder_name))
    assert(data_directory.startswith(location_directory))
    if not os.path.exists(data_directory):
        os.makedirs(data_directory)
        logman.Logger.info('Created data directory for "%s".' % (folder_name, ))


def backup_sqlite_db_file(folder_name):
    timestamp_str = datetime.datetime.utcnow().isoformat()[:19]
    assert('/' not in folder_name)
    assert('.' not in folder_name)
    current_file_directory = os.path.dirname(os.path.realpath(__file__))
    data_directory = os.path.join(current_file_directory, 'disk', folder_name)
    sqlite_db_file = os.path.join(data_directory, 'db.sqlite')
    sqlite_db_bak_file = os.path.join(data_directory, 'db_%s.sqlite' % (timestamp_str, ))
    assert(os.path.exists(sqlite_db_file))
    assert(not os.path.islink(sqlite_db_file))
    assert(os.path.isfile(sqlite_db_file))
    shutil.copy(sqlite_db_file, sqlite_db_bak_file)
    logman.info(f'Backed up current "db.sqlite" file to "db_{timestamp_str}.sqlite".')


def delete_sqlite_db_file(folder_name):
    assert('/' not in folder_name)
    assert('.' not in folder_name)
    current_file_directory = os.path.dirname(os.path.realpath(__file__))
    data_directory = os.path.join('disk', folder_name)
    sqlite_db_file = os.path.join(data_directory, 'db.sqlite')
    abs_sqlite_db_file = os.path.join(current_file_directory, sqlite_db_file)
    if not os.path.exists(abs_sqlite_db_file):
        logman.warning('SQLite file "%s" was not found and therefore couldn\'t be deleted.' % (
            sqlite_db_file,
        ))
    else:
        assert(not os.path.islink(abs_sqlite_db_file))
        assert(os.path.isfile(abs_sqlite_db_file))
        os.remove(abs_sqlite_db_file)


def create_db_uri(db_name):
    assert('/' not in db_name)
    assert('.' not in db_name)
    db_uri = ''
    use_sqlite = True
    if use_sqlite:
        db_uri = 'sqlite:///lokaord/database/disk/{db_name}/db.sqlite'.format(db_name=db_name)
    return db_uri


def session_has_changes():
    global Session
    return bool(Session.new) or bool(Session.dirty) or bool(Session.deleted)


def setup_connection(db_uri, db_echo=False):
    global Engine, Session, Base
    Engine = create_engine(db_uri, echo=db_echo)
    Session = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=Engine))
    Base.query = Session.query_property()


def init_db():
    global Base
    # Import all modules here that define models so that they are registered on the metadata.
    # Or import them first before calling init_db()
    #
    from lokaord.database import models
    Base.metadata.create_all(bind=Engine)


def init(name: str):
    global Session
    if Session is None:
        setup_data_directory(name)
        db_uri = create_db_uri(name)
        setup_connection(db_uri, db_echo=False)
        init_db()
        logman.info('Database connection initialized.')
