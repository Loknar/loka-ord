#!/usr/bin/python
"""
Importer functionality

Importing data from files to SQL database.
"""
import os

import git

from lokaord import logman
from lokaord.database import db
from lokaord.database.models import isl
from lokaord.exc import VoidKennistrengurError
from lokaord import handlers


def import_datafiles_to_db():
    """
    Go through every file within "lokaord/database/data" directory and import to database.
    """
    logman.info('Running import for all datafiles to database ..')
    tasks = []
    task_retries = []
    for handler in handlers.list_handlers():
        kjarna_ord, samsett_ord = handler.get_files_list_sorted()
        tasks.append({
            'handler': handler,
            'kjarna-orð': kjarna_ord,
            'samsett-orð': samsett_ord
        })
    # kjarna-orð
    logman.info('Importing kjarna orð.')
    for task in tasks:
        handler = task['handler']
        logman.info('Doing kjarna-orð files for %s ..' % (handler.group.value, ))
        wordCount = len(task['kjarna-orð'])
        for index, ord_file in enumerate(task['kjarna-orð']):
            if index % 100 == 0:
                logman.info('Orð %s of %s, file "%s"' % (index + 1, wordCount, ord_file, ))
            else:
                logman.debug('Orð %s of %s, file "%s"' % (index + 1, wordCount, ord_file, ))
            isl_ord = handler()
            isl_ord.load_from_file(ord_file)
            _, changes_made = isl_ord.write_to_db()
            if changes_made is True:
                logman.debug('Orð %s in file "%s" was changed.' % (
                    isl_ord.data.kennistrengur, ord_file
                ))
    # samsett-orð
    logman.info('Importing samsett orð.')
    for task in tasks:
        handler = task['handler']
        logman.info('Doing samsett-orð files for %s ..' % (handler.group.value, ))
        wordCount = len(task['samsett-orð'])
        for index, ord_file in enumerate(task['samsett-orð']):
            try:
                if index % 100 == 0:
                    logman.info('Orð %s of %s, file "%s"' % (index + 1, wordCount, ord_file, ))
                else:
                    logman.debug('Orð %s of %s, file "%s"' % (index + 1, wordCount, ord_file, ))
                isl_ord = handler()
                isl_ord.load_from_file(ord_file)
                _, changes_made = isl_ord.write_to_db()
                if changes_made is True:
                    logman.debug('Orð %s in file "%s" was changed.' % (
                        isl_ord.data.kennistrengur, ord_file
                    ))
            except VoidKennistrengurError:
                logman.debug('Encountered void kennistrengur for orð %s in file "%s", skipping.' % (
                    isl_ord.data.kennistrengur, ord_file
                ))
                task_retries.append({
                    'handler': handler,
                    'file': ord_file,
                })
    # samsett-orð with void kennistrengur
    # these are usually words samsett/combined from other samsett-orð
    logman.info('Retrying importing samsett orð encountering void kennistrengur.')
    for task in task_retries:
        handler = task['handler']
        ord_file = task['file']
        logman.debug('Orð file "%s"' % (ord_file, ))
        isl_ord = handler()
        isl_ord.load_from_file(ord_file)
        _, changes_made = isl_ord.write_to_db()
        if changes_made is True:
            logman.debug('Orð %s in file "%s" was changed.' % (
                isl_ord.data.kennistrengur, ord_file
            ))
    # skammstafanir
    logman.info('Importing skammstafanir.')
    for skammstofun_file in handlers.Skammstofun.get_files_list_sorted():
        logman.debug('Skammstöfun file "%s"' % (skammstofun_file, ))
        skammstofun = handlers.Skammstofun()
        skammstofun.load_from_file(skammstofun_file)
        _, changes_made = skammstofun.write_to_db()
        if changes_made is True:
            logman.debug('Skammstöfun %s in file "%s" was changed.' % (
                skammstofun.data.kennistrengur, skammstofun_file
            ))
    logman.info('Done importing data from datafiles to database.')


def import_changed_datafiles_to_db():
    """
    Go through datafiles in "lokaord/database/data" directory that have changed according to git
    or are currently not tracked by git.
    """
    logman.info('Doing import for changed or new datafiles to database ..')
    handlers_map = handlers.get_handlers_map()
    files = get_changed_and_untracked_data_files()
    ord_files, skammstofun_files = handlers.Ord.sort_files_skammstafanir_from_ord(files)
    kjarna_ord, samsett_ord = handlers.Ord.sort_files_to_kjarna_and_samsett_ord(ord_files)
    # kjarna-orð
    logman.info('Importing changed or new kjarna orð.')
    for kjarna_ord_file in kjarna_ord:
        logman.info('Orð file "%s"' % (kjarna_ord_file, ))
        handler = handlers_map[handlers.Ord.load_json(kjarna_ord_file)['flokkur']]
        isl_ord = handler()
        isl_ord.load_from_file(kjarna_ord_file)
        _, changes_made = isl_ord.write_to_db()
        if changes_made is True:
            logman.info('Orð %s in file "%s" was changed.' % (
                isl_ord.data.kennistrengur, kjarna_ord_file
            ))
    # samsett-orð
    logman.info('Importing changed or new samsett orð.')
    for samsett_ord_file in samsett_ord:
        logman.info('Orð file "%s"' % (samsett_ord_file, ))
        handler = handlers_map[handlers.Ord.load_json(samsett_ord_file)['flokkur']]
        isl_ord = handler()
        isl_ord.load_from_file(samsett_ord_file)
        _, changes_made = isl_ord.write_to_db()
        if changes_made is True:
            logman.info('Orð %s in file "%s" was changed.' % (
                isl_ord.data.kennistrengur, samsett_ord_file
            ))
    # skammstafanir
    logman.info('Importing changed or new skammstafanir.')
    for skammstofun_file in skammstofun_files:
        logman.info('Skammstöfun file "%s"' % (skammstofun_file, ))
        skammstofun = handlers.Skammstofun()
        skammstofun.load_from_file(skammstofun_file)
        _, changes_made = skammstofun.write_to_db()
        if changes_made is True:
            logman.info('Skammstöfun %s in file "%s" was changed.' % (
                skammstofun.data.kennistrengur, skammstofun_file
            ))
    logman.info('Done importing data from datafiles to database.')


def get_changed_and_untracked_data_files():
    """
    list orð files with changes according to git
    """
    repo_dir_abs = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '..'))
    repo = git.Repo(repo_dir_abs)
    datafiles_dir_rel = 'lokaord/database/data/'
    dfdr_len = len(datafiles_dir_rel)
    files = []
    for local_changed_file in repo.index.diff(None):
        ch_fname = local_changed_file.a_path
        if ch_fname.startswith(datafiles_dir_rel):
            files.append(ch_fname[dfdr_len:])
    for untracked_file in repo.untracked_files:
        if untracked_file.startswith(datafiles_dir_rel):
            files.append(untracked_file[dfdr_len:])
    return files
