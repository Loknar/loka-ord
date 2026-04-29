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


def setup_data_directory(folder_name: str):
	if '/' in folder_name:
		raise Exception('Bad name provided!')
	if '.' in folder_name:
		raise Exception('Bad name provided!')
	current_file_directory = os.path.dirname(os.path.realpath(__file__))
	location_directory = os.path.join(current_file_directory, 'disk')
	data_directory = os.path.realpath(os.path.join(location_directory, folder_name))
	if not data_directory.startswith(location_directory):
		raise Exception('Unexpected file directory encountered!')
	if not os.path.exists(data_directory):
		os.makedirs(data_directory)
		logman.Logger.info('Created data directory for "%s".' % (folder_name, ))


def backup_sqlite_db_file(folder_name: str):
	if '/' in folder_name:
		raise Exception('Bad name provided!')
	if '.' in folder_name:
		raise Exception('Bad name provided!')
	timestamp_str = datetime.datetime.utcnow().isoformat()[:19]
	current_file_directory = os.path.dirname(os.path.realpath(__file__))
	data_directory = os.path.join(current_file_directory, 'disk', folder_name)
	sqlite_db_file = os.path.join(data_directory, 'db.sqlite')
	sqlite_db_bak_file = os.path.join(data_directory, 'db_%s.sqlite' % (timestamp_str, ))
	if not os.path.exists(sqlite_db_file):
		raise Exception('File does not exist!')
	if os.path.islink(sqlite_db_file):
		raise Exception('Folder paths to links are not allowed!')
	if not os.path.isfile(sqlite_db_file):
		raise Exception('File to backup not found!')
	shutil.copy(sqlite_db_file, sqlite_db_bak_file)
	logman.info(f'Backed up current "db.sqlite" file to "db_{timestamp_str}.sqlite".')


def use_backup_sqlite_db_file(folder_name: str, filename: str, use_force: bool = False):
	if '/' in folder_name:
		raise Exception('Bad name provided!')
	if '.' in folder_name:
		raise Exception('Bad name provided!')
	if '/' in filename:
		raise Exception('Bad name provided!')
	if '.' in filename:
		raise Exception('Bad name provided!')
	filename_sqlite = '%s.sqlite' % (filename, )
	current_file_directory = os.path.dirname(os.path.realpath(__file__))
	data_directory = os.path.join(current_file_directory, 'disk', folder_name)
	sqlite_db_file = os.path.join(data_directory, 'db.sqlite')
	sqlite_db_file_bak = os.path.join(data_directory, filename_sqlite)
	if not os.path.exists(sqlite_db_file_bak):
		raise Exception('Backup file does not exist!')
	if os.path.islink(sqlite_db_file_bak):
		raise Exception('Paths to links are not allowed!')
	if not os.path.isfile(sqlite_db_file_bak):
		raise Exception('Backup file not found!')
	if os.path.exists(sqlite_db_file):
		if os.path.islink(sqlite_db_file):
			raise Exception('Folder paths to links are not allowed!')
		if os.path.isfile(sqlite_db_file):
			if use_force is True:
				delete_sqlite_db_file(folder_name)
			else:
				raise Exception('File "db.sqlite" already exists, delete or move it.')
	shutil.copy(sqlite_db_file_bak, sqlite_db_file)
	logman.info(f'Copied backup "{folder_name}" file "{filename_sqlite}" to "db.sqlite"')


def delete_sqlite_db_file(folder_name: str):
	if '/' in folder_name:
		raise Exception('Bad name provided!')
	if '.' in folder_name:
		raise Exception('Bad name provided!')
	current_file_directory = os.path.dirname(os.path.realpath(__file__))
	data_directory = os.path.join('disk', folder_name)
	sqlite_db_file = os.path.join(data_directory, 'db.sqlite')
	abs_sqlite_db_file = os.path.join(current_file_directory, sqlite_db_file)
	if not os.path.exists(abs_sqlite_db_file):
		logman.warning('SQLite file "%s" was not found and therefore couldn\'t be deleted.' % (
			sqlite_db_file,
		))
	else:
		if os.path.islink(abs_sqlite_db_file):
			raise Exception('Folder paths to links are not allowed!')
		if not os.path.isfile(abs_sqlite_db_file):
			raise Exception('File to delete not found!')
		os.remove(abs_sqlite_db_file)


def create_db_uri(db_name: str):
	if '/' in db_name:
		raise Exception('Bad name provided!')
	if '.' in db_name:
		raise Exception('Bad name provided!')
	db_uri = ''
	use_sqlite = True
	if use_sqlite:
		db_uri = 'sqlite:///lokaord/database/disk/{db_name}/db.sqlite'.format(db_name=db_name)
	return db_uri


def session_has_changes():
	global Session
	return bool(Session.new) or bool(Session.dirty) or bool(Session.deleted)


def setup_connection(db_uri: str, db_echo: bool = False):
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
