#!/usr/bin/python
import datetime
from enum import Enum
import json
import sys

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


def backup_db():
    db.backup_sqlite_db_file(Name)


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
    print(stats.get_words_count_markdown_table())


def add_word():
    db.init(Name)
    cli.add_word_cli()


def run_fiddle():
    db.init(Name)
    logman.info('Running fiddle!')
