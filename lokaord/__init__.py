#!/usr/bin/python
import json
import os
import pathlib
import sys

from lokaord.database import db
from lokaord.database.models import isl
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
    logman.info('Building database from datafiles ..')
    # nafnorð
    logman.info('Reading "nafnorð" datafiles ..')
    nafnord_dir_abs = os.path.abspath(
        os.path.join(os.path.dirname(os.path.realpath(__file__)), 'database', 'data', 'nafnord')
    )
    for nafnord_file in sorted(pathlib.Path(nafnord_dir_abs).iterdir()):
        assert(nafnord_file.is_file())
        assert(nafnord_file.name.endswith('.json'))
        logman.info('File nafnord/%s ..' % (nafnord_file.name, ))
        nafnord_data = None
        with nafnord_file.open(mode='r', encoding='utf-8') as fi:
            nafnord_data = json.loads(fi.read())
        isl_ord = lookup_nafnord(nafnord_data)
        if isl_ord is None:
            add_nafnord(nafnord_data)
            logman.info('Added nafnorð "%s" (%s).' % (nafnord_data['orð'], nafnord_data['kyn']))
        else:
            logman.warning('Nafnorð "%s" (%s) already exists! Skipping.' % (
                nafnord_data['orð'], nafnord_data['kyn']
            ))
    import pdb; pdb.set_trace()
    # lýsningarorð
    # sagnorð
    logman.info('TODO: finish implementing build_db_from_datafiles')
    return


def lookup_nafnord(nafnord_data):
    '''
    Assume icelandic nafnorð are genderly unique, until we have counter-example.
    '''
    isl_ord = None
    isl_ord_kyn = None
    if nafnord_data['kyn'] == 'kk':
        isl_ord_kyn = isl.Kyn.Karlkyn
    elif nafnord_data['kyn'] == 'kvk':
        isl_ord_kyn = isl.Kyn.Kvenkyn
    elif nafnord_data['kyn'] == 'hk':
        isl_ord_kyn = isl.Kyn.Hvorugkyn
    assert(isl_ord_kyn is not None)
    isl_ord_list = db.Session.query(isl.Ord).filter_by(
        Ord=nafnord_data['orð'],
        Ordflokkur=isl.Ordflokkar.Nafnord
    ).all()
    for potential_isl_ord in isl_ord_list:
        isl_nafnord = db.Session.query(isl.Nafnord).filter_by(
            fk_Ord_id=potential_isl_ord.Ord_id
        ).first()
        if isl_nafnord.Kyn == isl_ord_kyn:
            assert(isl_ord is None)  # if/when this fails it means we have counter-example
            isl_ord = potential_isl_ord
    return isl_ord


def add_nafnord(nafnord_data):
    assert('flokkur' in nafnord_data and nafnord_data['flokkur'] == 'nafnorð')
    isl_ord_kyn = None
    if nafnord_data['kyn'] == 'kk':
        isl_ord_kyn = isl.Kyn.Karlkyn
    elif nafnord_data['kyn'] == 'kvk':
        isl_ord_kyn = isl.Kyn.Kvenkyn
    elif nafnord_data['kyn'] == 'hk':
        isl_ord_kyn = isl.Kyn.Hvorugkyn
    assert(isl_ord_kyn is not None)
    isl_ord = isl.Ord(
        Ord=nafnord_data['orð'],
        Ordflokkur=isl.Ordflokkar.Nafnord
    )
    db.Session.add(isl_ord)
    db.Session.commit()
    isl_nafnord = isl.Nafnord(
        fk_Ord_id=isl_ord.Ord_id,
        Kyn=isl_ord_kyn
    )
    db.Session.add(isl_nafnord)
    db.Session.commit()
    if 'et' in nafnord_data:
        if 'ág' in nafnord_data['et']:
            assert_fallbeyging_list(nafnord_data['et']['ág'])
            isl_nafnord_fallbeyging_et_ag = isl.Fallbeyging(
                Nefnifall=nafnord_data['et']['ág'][0],
                Tholfall=nafnord_data['et']['ág'][1],
                Thagufall=nafnord_data['et']['ág'][2],
                Eignarfall=nafnord_data['et']['ág'][3]
            )
            db.Session.add(isl_nafnord_fallbeyging_et_ag)
            db.Session.commit()
            isl_nafnord.fk_et_Fallbeyging_id = isl_nafnord_fallbeyging_et_ag.Fallbeyging_id
            db.Session.commit()
        if 'mg' in nafnord_data['et']:
            assert_fallbeyging_list(nafnord_data['et']['mg'])
            isl_nafnord_fallbeyging_et_mg = isl.Fallbeyging(
                Nefnifall=nafnord_data['et']['mg'][0],
                Tholfall=nafnord_data['et']['mg'][1],
                Thagufall=nafnord_data['et']['mg'][2],
                Eignarfall=nafnord_data['et']['mg'][3]
            )
            db.Session.add(isl_nafnord_fallbeyging_et_mg)
            db.Session.commit()
            isl_nafnord.fk_et_mgr_Fallbeyging_id = isl_nafnord_fallbeyging_et_mg.Fallbeyging_id
            db.Session.commit()
    if 'ft' in nafnord_data:
        if 'ág' in nafnord_data['ft']:
            assert_fallbeyging_list(nafnord_data['ft']['ág'])
            isl_nafnord_fallbeyging_ft_ag = isl.Fallbeyging(
                Nefnifall=nafnord_data['ft']['ág'][0],
                Tholfall=nafnord_data['ft']['ág'][1],
                Thagufall=nafnord_data['ft']['ág'][2],
                Eignarfall=nafnord_data['ft']['ág'][3]
            )
            db.Session.add(isl_nafnord_fallbeyging_ft_ag)
            db.Session.commit()
            isl_nafnord.fk_ft_Fallbeyging_id = isl_nafnord_fallbeyging_ft_ag.Fallbeyging_id
            db.Session.commit()
        if 'mg' in nafnord_data['ft']:
            assert_fallbeyging_list(nafnord_data['ft']['mg'])
            isl_nafnord_fallbeyging_ft_mg = isl.Fallbeyging(
                Nefnifall=nafnord_data['ft']['mg'][0],
                Tholfall=nafnord_data['ft']['mg'][1],
                Thagufall=nafnord_data['ft']['mg'][2],
                Eignarfall=nafnord_data['ft']['mg'][3]
            )
            db.Session.add(isl_nafnord_fallbeyging_ft_mg)
            db.Session.commit()
            isl_nafnord.fk_ft_mgr_Fallbeyging_id = isl_nafnord_fallbeyging_ft_mg.Fallbeyging_id
            db.Session.commit()
    # TODO: add samsett/undantekning handling


def assert_fallbeyging_list(fallbeyging_list):
    '''
    assert object structure of [str/None, str/None, str/None, str/None]
    '''
    assert(type(fallbeyging_list) is list)
    assert(len(fallbeyging_list) == 4)
    for fallbeyging in fallbeyging_list:
        if fallbeyging is not None:
            assert(type(fallbeyging) is str)


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
