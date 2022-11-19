#!/usr/bin/python
import json
import sys

from lokaord import cli
from lokaord import exporter
from lokaord import importer
from lokaord import logman
from lokaord.version import __version__
from lokaord.database import db
from lokaord.database.models import isl

ArgParser = None


def get_words_count():
    '''
    collect some basic word count stats
    '''
    return {
        'no': db.Session.query(isl.Ord).filter_by(Ordflokkur=isl.Ordflokkar.Nafnord).count(),
        'lo': db.Session.query(isl.Ord).filter_by(Ordflokkur=isl.Ordflokkar.Lysingarord).count(),
        'so': db.Session.query(isl.Ord).filter_by(Ordflokkur=isl.Ordflokkar.Sagnord).count(),
        'to': (  # töluorð (frumtölur + raðtölur)
            db.Session.query(isl.Ord).filter_by(Ordflokkur=isl.Ordflokkar.Frumtala).count() +
            db.Session.query(isl.Ord).filter_by(Ordflokkur=isl.Ordflokkar.Radtala).count()
        ),
        'fn': db.Session.query(isl.Ord).filter_by(Ordflokkur=isl.Ordflokkar.Fornafn).count()
    }


def main(arguments):
    logman.init(
        arguments['logger_name'], role=arguments['role'], output_dir=arguments['log_directory']
    )
    db_name = 'lokaord'
    if 'backup_db' in arguments and arguments['backup_db'] is True:
        db.backup_sqlite_db_file(db_name)
    if 'rebuild_db' in arguments and arguments['rebuild_db'] is True:
        db.delete_sqlite_db_file(db_name)
    if db.Session is None:
        db.setup_data_directory(db_name)
        db_uri = db.create_db_uri(db_name)
        db.setup_connection(db_uri, db_echo=False)
        db.init_db()
    if 'stats' in arguments and arguments['stats'] is True:
        print(json.dumps(
            get_words_count(), separators=(',', ':'), ensure_ascii=False, sort_keys=True
        ))
    if 'add_word_cli' in arguments and arguments['add_word_cli'] is True:
        cli.add_word_cli()
    if (
        'build_db' in arguments and arguments['build_db'] is True or
        'rebuild_db' in arguments and arguments['rebuild_db'] is True
    ):
        importer.build_db_from_datafiles()
    if 'write_files' in arguments and arguments['write_files'] is True:
        exporter.write_datafiles_from_db()
