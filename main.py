#!/usr/bin/python
import argparse
import sys

import lokaord


if __name__ == '__main__':
    lokaord.ArgParser = argparse.ArgumentParser(
        description='Loka-Orð', formatter_class=argparse.RawTextHelpFormatter
    )
    lokaord.ArgParser.prog = 'lokaord'
    lokaord.ArgParser._actions[0].help = 'Show this help message and exit.'
    lokaord.ArgParser.add_argument('-v', '--version', action='store_true', help=(
        'Print version and exit.'
    ))
    lokaord.ArgParser.add_argument('-ln', '--logger-name', default='lokaord', help=(
        'Define logger name (Default: "lokaord").'
    ))
    lokaord.ArgParser.add_argument('-ldir', '--log-directory', default='./logs/', help=(
        'Directory to write logs in. Default: "./logs/".'
    ))
    lokaord.ArgParser.add_argument('-r', '--role', default='cli', help=(
        'Define runner role.\n'
        'Available options: "cli", "api", "cron", "hook", "mod" (Default: "cli").'
    ))
    lokaord.ArgParser.add_argument('-bdb', '--build-db', action='store_true', help=(
        'Build database from datafiles.'
    ))
    lokaord.ArgParser.add_argument('-wf', '--write-files', action='store_true', help=(
        'Write datafiles from database.'
    ))
    lokaord.ArgParser.add_argument('-aw', '--add-word', action='store_true', help=(
        'Add word CLI.'
    ))
    lokaord.ArgParser.add_argument('-s', '--search', metavar=('WORD', ), help=(
        'Search for word in database.'
    ))
    lokaord.ArgParser.add_argument('-st', '--stats', action='store_true', help=(
        'Print database word count.'
    ))
    pargs = lokaord.ArgParser.parse_args()
    if len(sys.argv) == 1:
        lokaord.print_help_and_exit()
    if pargs.version is True:
        print(lokaord.__version__)
    arguments = {
        'logger_name': pargs.logger_name,
        'log_directory': pargs.log_directory,
        'role': pargs.role,
        'build_db': pargs.build_db,
        'write_files': pargs.write_files,
        'add_word': None,
        'add_word_cli': pargs.add_word,
        'search': pargs.search,
        'stats': pargs.stats,
    }
    lokaord.main(arguments)
