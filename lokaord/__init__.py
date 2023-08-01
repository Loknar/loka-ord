#!/usr/bin/python
import datetime
from enum import Enum
import json
import os
import sys

import git

from lokaord import cli
from lokaord import exporter
from lokaord import importer
from lokaord import logman
from lokaord import seer
from lokaord import stats
from lokaord.database import db
from lokaord.database.models import isl
from lokaord.version import __version__

Name = 'lokaord'
Ts = None


class LoggerRoles(str, Enum):
    cli = 'cli'
    api = 'api'
    cron = 'cron'
    hook = 'hook'
    mod = 'mod'


class LogLevel(str, Enum):
    notset = 'notset'
    debug = 'debug'
    info = 'info'
    warn = 'warn'
    error = 'error'
    critical = 'critical'


class TimeOffset(str, Enum):
    last2min = 'last2min'
    last10min = 'last10min'
    last30min = 'last30min'


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


def webpack(words_per_pack: int = 3000):
    seer.webpack(words_per_pack)


def build_sight():
    seer.build_sight()


def search(word: str):
    seer.search_word(word)


def scan_sentence(sentence: str):
    seer.scan_sentence(sentence)


def get_stats():
    db.init(Name)
    print(json.dumps(
        stats.get_words_count(), separators=(',', ':'), ensure_ascii=False, sort_keys=True
    ))


def get_md_stats():
    db.init(Name)
    print('\nMarkdown Table Stats:\n\n%s' % (stats.get_words_count_markdown_table(), ))


def get_runtime():
    print('\nRuntime: %s' % (stats.calc_runtime(), ))


def add_word():
    db.init(Name)
    cli.add_word_cli()


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


def run_fiddle():
    db.init(Name)
    logman.info('Running fiddle!')
