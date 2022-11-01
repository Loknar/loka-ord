#!/usr/bin/python
import json
import sys

from lokaord import cli
from lokaord import exporter
from lokaord import importer
from lokaord import logman
from lokaord.database import db
from lokaord.database.models import isl

__version__ = "0.0.1"

ArgParser = None


def print_help_and_exit():
    if ArgParser is not None:
        ArgParser.print_help(sys.stderr)
    else:
        logman.error('Exiting ..')
    sys.exit(1)


def get_words_count():
    return {
        'no': db.Session.query(isl.Ord).filter_by(Ordflokkur=isl.Ordflokkar.Nafnord).count(),
        'lo': db.Session.query(isl.Ord).filter_by(Ordflokkur=isl.Ordflokkar.Lysingarord).count(),
        'so': db.Session.query(isl.Ord).filter_by(Ordflokkur=isl.Ordflokkar.Sagnord).count()
    }


def main(arguments):
    logman.init(
        arguments['logger_name'], role=arguments['role'], output_dir=arguments['log_directory']
    )
    if db.Session is None:
        db_name = 'lokaord'
        db.setup_data_directory(db_name, __file__)
        db_uri = db.create_db_uri(db_name)
        db.setup_connection(db_uri, db_echo=False)
        db.init_db()
    if 'stats' in arguments and arguments['stats'] is True:
        print(json.dumps(
            get_words_count(), separators=(',', ':'), ensure_ascii=False, sort_keys=True
        ))
    if 'add_word_cli' in arguments and arguments['add_word_cli'] is True:
        cli.add_word_cli(version=__version__)
    if 'build_db' in arguments and arguments['build_db'] is True:
        importer.build_db_from_datafiles()
    if 'write_files' in arguments and arguments['write_files'] is True:
        exporter.write_datafiles_from_db()
