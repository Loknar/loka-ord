#!/usr/bin/python
import datetime
from enum import Enum
import json
import os
import pathlib

import git
import typer

from lokaord import exporter
from lokaord import handlers
from lokaord import importer
from lokaord import logman
from lokaord import seer
from lokaord import stats
from lokaord import tui
from lokaord.database import db
from lokaord.exc import OrdToDeleteHasDependentsError
from lokaord.version import __version__  # noqa

Name = 'lokaord'
Ts = None


class LoggerRoles(str, Enum):
	cli = 'cli'
	api = 'api'
	cron = 'cron'
	hook = 'hook'
	mod = 'mod'

	def __str__(self):
		return self.name


class LogLevel(str, Enum):
	notset = 'notset'
	debug = 'debug'
	info = 'info'
	warn = 'warn'
	error = 'error'
	critical = 'critical'

	def __str__(self):
		return self.name


class TimeOffset(str, Enum):
	last2min = 'last2min'
	last10min = 'last10min'
	last30min = 'last30min'

	def __str__(self):
		return self.name


def get_offset_time(offset: TimeOffset) -> datetime.datetime:
	match offset:
		case TimeOffset.last2min:
			return (
				datetime.datetime.utcnow() - datetime.timedelta(minutes=2)
			)
		case TimeOffset.last10min:
			return (
				datetime.datetime.utcnow() - datetime.timedelta(minutes=10)
			)
		case TimeOffset.last30min:
			return (
				datetime.datetime.utcnow() - datetime.timedelta(minutes=30)
			)
		case _:
			raise Exception('Unimplemented offset?')


def backup_db(name: str = None):
	if name is None:
		name = Name
	db.backup_sqlite_db_file(name)


def use_backup(name: str = None, filename: str = None):
	logman.info('Use backup ..')
	current_file_directory = os.path.dirname(os.path.realpath(__file__))
	backup_handling_path_str = os.path.join(
		current_file_directory, 'database', 'disk', 'db_bak_handling.json'
	)
	backup_handling_path = pathlib.Path(backup_handling_path_str)
	backup_handling = None
	try:
		with backup_handling_path.open(mode='r', encoding='utf-8') as fi:
			backup_handling = json.loads(fi.read())
	except json.decoder.JSONDecodeError:
		raise Exception(f'File "{backup_handling_path.name}" has invalid JSON format.')
	if name is None:
		name = backup_handling['default']['name']
		logman.info(f'Default backup name "{name}".')
	else:
		logman.info(f'Backup name "{name}.')
	if filename is None:
		filename = backup_handling['default']['filename']
		logman.info(f'Default backup filename "{filename}".')
	else:
		logman.info(f'Backup filename "{filename}.')
	logman.info(f'Using backup in "{name}", filename "{filename}.sqlite".')
	db.use_backup_sqlite_db_file(name, filename)
	db.init(Name)
	if (
		filename in backup_handling['handling'] and
		'ord_delete' in backup_handling['handling'][filename]
	):
		logman.info(f'Remove specified list of orð from database backup ..')
		if not isinstance(backup_handling['handling'][filename]['ord_delete'], list):
			raise Exception('"ord_delete" should be list')
		for kennistrengur in backup_handling['handling'][filename]['ord_delete']:
			if not isinstance(kennistrengur, str):
				raise Exception('contents of "ord_delete" should be strings')
			delete_ord(kennistrengur)


def build_db(rebuild: bool = False, changes_only: bool = False):
	if rebuild is True:
		db.delete_sqlite_db_file(Name)
	db.init(Name)
	if changes_only is True:
		importer.import_changed_datafiles_to_db()
	else:
		importer.import_datafiles_to_db()


def write_files(ts: datetime.datetime = None):
	db.init(Name)
	exporter.write_datafiles_from_db(ts)


def webpack(words_per_pack: int = seer.WPP):
	seer.webpack(words_per_pack)


def build_sight():
	seer.build_sight()


def search(word: str):
	seer.search_word(word)


def scan_sentence(sentence: str, show_kennistrengir: bool = False, show_matches: bool = False):
	seer.scan_sentence(sentence, show_kennistrengir=show_kennistrengir, show_matches=show_matches)


def get_stats():
	db.init(Name)
	print(json.dumps(
		stats.get_words_count(), separators=(',', ':'), ensure_ascii=False, sort_keys=True
	))


def get_md_stats(update_readme_table: bool = False) -> str:
	pre_str = 'Gagnasafnið telur eftirfarandi fjölda orða:\n\n'
	post_str = '\n\n## Forkröfur (Requirements)'
	db.init(Name)
	md_stats_str = stats.get_words_count_markdown_table()
	if update_readme_table is True:
		readme_file = os.path.realpath(
			os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', 'README.md')
		)
		readme_file_contents = None
		with open(readme_file, 'r') as rfi:
			readme_file_contents = rfi.read()
		if readme_file_contents.find(pre_str) == -1:
			raise Exception('Failed to find pre-string.')
		if readme_file_contents.find(post_str) == -1:
			raise Exception('Failed to find post-string.')
		readme_file_index_a = readme_file_contents.find(pre_str) + len(pre_str)
		readme_file_index_b = readme_file_contents.find(post_str)
		updated_readme_file_contents = '{pre}{table}{post}'.format(
			pre=readme_file_contents[:readme_file_index_a],
			table=md_stats_str,
			post=readme_file_contents[readme_file_index_b:]
		)
		with open(readme_file, 'w') as wfi:
			wfi.write(updated_readme_file_contents)
	return '\nMarkdown Table Stats:\n\n%s' % (md_stats_str, )


def get_runtime():
	print('\nRuntime: %s' % (stats.calc_runtime(), ))


def add_word():
	db.init(Name)
	tui.add_word_tui()


def assert_clean_git():
	repo_dir_abs = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '..'))
	repo = git.Repo(repo_dir_abs)
	if repo.is_dirty():
		changed_files = repo.index.diff(None)
		untracked_files = repo.untracked_files
		feedback = '\n\n'
		if len(changed_files) != 0:
			feedback += 'Changes:\n'
			for changed_file in changed_files:
				feedback += '    %s\n' % (changed_file.a_path, )
		if len(untracked_files) != 0:
			feedback += 'Untracked:\n'
			for untracked_file in untracked_files:
				feedback += '    %s\n' % (untracked_file, )
		raise Exception(feedback)
	print('\nThe git repo is all clean!')


def check_samsett_circular_definitions():
	db.init(Name)
	exporter.check_samsett_circular_definitions()


def check_ord_dependents(kennistrengur: str):
	db.init(Name)
	isl_ord = handlers.get_ord_by_kennistrengur(kennistrengur)
	if isl_ord is None:
		logman.error(f'Orð with kennistrengur "{kennistrengur}" not found.')
		raise typer.Exit(code=1)
	dependents = handlers.get_dependents_of_ord(isl_ord)
	if len(dependents) > 0:
		logman.info('Orð "%s" has the following dependent orð: %s' % (
			kennistrengur, ', '.join(dependents))
		)
	else:
		logman.info('Orð "%s" has no dependent orð.' % (kennistrengur, ))
	skammstafanir = handlers.get_skammstafanir_with_ord(isl_ord)
	if len(skammstafanir) > 0:
		logman.info('Orð "%s" in the following skammstafanir: %s' % (
			kennistrengur, ', '.join(skammstafanir))
		)
	else:
		logman.info('Orð "%s" not in any skammstöfun.' % (kennistrengur, ))


def delete_ord(kennistrengur: str):
	db.init(Name)
	isl_ord = handlers.get_ord_by_kennistrengur(kennistrengur)
	if isl_ord is None:
		logman.error(f'Orð with kennistrengur "{kennistrengur}" not found.')
		raise typer.Exit(code=1)
	try:
		handlers.delete_ord_from_db(isl_ord)
	except OrdToDeleteHasDependentsError as err:
		logman.error(err.msg)
		raise typer.Exit(code=1)


def run_fiddle():
	db.init(Name)
	logman.info('Running fiddle!')
