#!/usr/bin/python
import sys

from lokaord.database import db
from lokaord import logman

__version__ = "0.0.1"

ArgParser = None


def print_help_and_exit():
    if ArgParser is not None:
        ArgParser.print_help(sys.stderr)
    else:
        logman.error('Exiting ..')
    sys.exit(1)


def main(arguments):
    # logman.init(role='cli')
    # logman.info('Loka-Orð initialized')
    # db_name = 'lokaord'
    # database.db.setup_data_directory(db_name, __file__)
    # db_uri = database.db.create_db_uri(db_name)
    # database.db.setup_connection(db_uri, db_echo=False)
    # database.db.init_db()
    if 'build-db' in arguments and arguments['build-db'] is True:
        return True
    return False
