#!/usr/bin/python
import json
import os
import pathlib
import sys

from lokaord.database import db
from lokaord.database.models import ord
from lokaord import logman

__version__ = "0.0.1"

ArgParser = None


def print_help_and_exit():
    if ArgParser is not None:
        ArgParser.print_help(sys.stderr)
    else:
        logman.error('Exiting ..')
    sys.exit(1)


def build_db_from_datafiles():
    # nafnorð
    logman.info('Reading "nafnorð" datafiles ..')
    nafnord_dir_abs = os.path.abspath(
        os.path.join(os.path.dirname(os.path.realpath(__file__)), 'database', 'data', 'nafnord')
    )
    for nafnord_file in sorted(pathlib.Path(nafnord_dir_abs).iterdir()):
        assert(nafnord_file.is_file())
        assert(nafnord_file.name.endswith('.json'))
        logman.info('File %s' % (nafnord_file.name, ))
        nafnord_data = None
        with nafnord_file.open(mode='r', encoding='utf-8') as fi:
            nafnord_data = json.loads(fi.read())
        import pdb; pdb.set_trace()
    logman.info('TODO: implement build_db_from_datafiles')
    return


def write_datafiles_from_db():
    logman.info('TODO: implement write_datafiles_from_db')
    return


def add_word(word_data):
    return


def add_word_cli():
    word_data = {}
    add_word(word_data)


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
    if 'build_db' in arguments and arguments['build_db'] is True:
        build_db_from_datafiles()
    if 'write_files' in arguments and arguments['write_files'] is True:
        write_datafiles_from_db()
    if 'add_word_cli' in arguments and arguments['add_word_cli'] is not None:
        add_word_cli()
