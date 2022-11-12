#!/usr/bin/python
"""
Importer functionality

Importing data from files to SQL database.
"""
import collections
import json
import os
import pathlib

from lokaord import logman
from lokaord.database import db
from lokaord.database.models import isl
from lokaord.exporter import hashify_ord_data
from lokaord.exporter import ord_data_to_fancy_json_str
from lokaord.exporter import get_nafnord_from_db_to_ordered_dict
from lokaord.exporter import get_lysingarord_from_db_to_ordered_dict
from lokaord.exporter import get_sagnord_from_db_to_ordered_dict


def build_db_from_datafiles():
    logman.info('Building database from datafiles ..')
    datafiles_dir_abs = os.path.abspath(
        os.path.join(os.path.dirname(os.path.realpath(__file__)), 'database', 'data')
    )
    logman.info('We import core words first, then combined (samssett).')
    # nafnorð core
    nafnord_dir = os.path.join(datafiles_dir_abs, 'nafnord')
    nafnord_files, nafnord_files_samsett = list_json_files_separate_samsett_ord(nafnord_dir)
    logman.info('Reading core "nafnorð" datafiles (%s) ..' % (len(nafnord_files), ))
    for nafnord_file in nafnord_files:
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
    # lýsingarorð core
    lysingarord_dir = os.path.join(datafiles_dir_abs, 'lysingarord')
    lysingarord_files, lysingarord_files_samsett = list_json_files_separate_samsett_ord(
        lysingarord_dir
    )
    logman.info('Reading core "lýsingarorð" datafiles (%s) ..' % (len(lysingarord_files), ))
    for lysingarord_file in lysingarord_files:
        logman.info('File lysingarord/%s ..' % (lysingarord_file.name, ))
        lysingarord_data = None
        with lysingarord_file.open(mode='r', encoding='utf-8') as fi:
            lysingarord_data = json.loads(fi.read())
        isl_ord = lookup_lysingarord(lysingarord_data)
        if isl_ord is None:
            add_lysingarord(lysingarord_data)
            logman.info('Added lýsingarorð "%s".' % (lysingarord_data['orð'], ))
        else:
            logman.warning('Lýsingarorð "%s" already exists! Skipping.' % (
                lysingarord_data['orð'],
            ))
    # sagnorð core
    sagnord_dir = os.path.join(datafiles_dir_abs, 'sagnord')
    sagnord_files, sagnord_files_samsett = list_json_files_separate_samsett_ord(sagnord_dir)
    logman.info('Reading core "sagnorð" datafiles (%s) ..' % (len(sagnord_files), ))
    for sagnord_file in sagnord_files:
        logman.info('File sagnord/%s ..' % (sagnord_file.name, ))
        sagnord_data = None
        with sagnord_file.open(mode='r', encoding='utf-8') as fi:
            sagnord_data = json.loads(fi.read())
        isl_ord = lookup_sagnord(sagnord_data)
        if isl_ord is None:
            add_sagnord(sagnord_data)
            logman.info('Added sagnorð "%s".' % (sagnord_data['orð'], ))
        else:
            logman.warning('Sagnorð "%s" already exists! Skipping.' % (
                sagnord_data['orð'],
            ))
    # TODO: add other orðflokkar
    # nafnorð samsett
    logman.info('Reading samsett "nafnorð" datafiles (%s) ..' % (len(nafnord_files_samsett), ))
    for nafnord_file in nafnord_files_samsett:
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
    # lýsingarorð samsett
    logman.info('Reading samsett "lýsingarorð" datafiles (%s) ..' % (
        len(lysingarord_files_samsett),
    ))
    for lysingarord_file in lysingarord_files_samsett:
        logman.info('File lysingarord/%s ..' % (lysingarord_file.name, ))
        lysingarord_data = None
        with lysingarord_file.open(mode='r', encoding='utf-8') as fi:
            lysingarord_data = json.loads(fi.read())
        isl_ord = lookup_lysingarord(lysingarord_data)
        if isl_ord is None:
            add_lysingarord(lysingarord_data)
            logman.info('Added lýsingarorð "%s".' % (lysingarord_data['orð'], ))
        else:
            logman.warning('Lýsingarorð "%s" already exists! Skipping.' % (
                lysingarord_data['orð'],
            ))
    # sagnorð samsett
    logman.info('Reading samsett "sagnorð" datafiles (%s) ..' % (len(sagnord_files_samsett), ))
    for sagnord_file in sagnord_files_samsett:
        logman.info('File sagnord/%s ..' % (sagnord_file.name, ))
        sagnord_data = None
        with sagnord_file.open(mode='r', encoding='utf-8') as fi:
            sagnord_data = json.loads(fi.read())
        isl_ord = lookup_sagnord(sagnord_data)
        if isl_ord is None:
            add_sagnord(sagnord_data)
            logman.info('Added sagnorð "%s".' % (sagnord_data['orð'], ))
        else:
            logman.warning('Sagnorð "%s" already exists! Skipping.' % (
                sagnord_data['orð'],
            ))
    # TODO: add other orðflokkar
    logman.info('TODO: finish implementing build_db_from_datafiles')


def list_json_files_separate_samsett_ord(file_dir):
    files_list = []
    files_list_samsett = []
    for json_file in sorted(pathlib.Path(file_dir).iterdir()):
        if not json_file.is_file():
            continue
        if not json_file.name.endswith('.json'):
            continue
        json_data = None
        with json_file.open(mode='r', encoding='utf-8') as fi:
            json_data = json.loads(fi.read())
        if 'samsett' in json_data:
            files_list_samsett.append(json_file)
            continue
        files_list.append(json_file)
    return (files_list, files_list_samsett)



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
    '''
    add nafnorð from datafile to database
    '''
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
        Ordflokkur=isl.Ordflokkar.Nafnord,
        OsjalfstaedurOrdhluti=(
            'ósjálfstætt' in nafnord_data and nafnord_data['ósjálfstætt'] is True
        )
    )
    db.Session.add(isl_ord)
    db.Session.commit()
    if 'samsett' in nafnord_data:
        add_samsett_ord(isl_ord.Ord_id, nafnord_data)
        isl_ord.Samsett = True
        db.Session.commit()
        return isl_ord
    isl_nafnord = isl.Nafnord(
        fk_Ord_id=isl_ord.Ord_id,
        Kyn=isl_ord_kyn
    )
    db.Session.add(isl_nafnord)
    db.Session.commit()
    if 'et' in nafnord_data:
        if 'ág' in nafnord_data['et']:
            isl_nafnord.fk_et_Fallbeyging_id = add_fallbeyging(nafnord_data['et']['ág'])
            db.Session.commit()
        if 'mg' in nafnord_data['et']:
            isl_nafnord.fk_et_mgr_Fallbeyging_id = add_fallbeyging(nafnord_data['et']['mg'])
            db.Session.commit()
    if 'ft' in nafnord_data:
        if 'ág' in nafnord_data['ft']:
            isl_nafnord.fk_ft_Fallbeyging_id = add_fallbeyging(nafnord_data['ft']['ág'])
            db.Session.commit()
        if 'mg' in nafnord_data['ft']:
            isl_nafnord.fk_ft_mgr_Fallbeyging_id = add_fallbeyging(nafnord_data['ft']['mg'])
            db.Session.commit()
    # TODO: add undantekning handling
    return isl_ord


def lookup_lysingarord(lysingarord_data):
    '''
    Assume icelandic lýsingarorð are unique, until we have counter-example.
    '''
    isl_ord = None
    isl_ord_query = db.Session.query(isl.Ord).filter_by(
        Ord=lysingarord_data['orð'],
        Ordflokkur=isl.Ordflokkar.Lysingarord
    )
    assert(len(isl_ord_query.all()) < 2)  # if/when this fails it means we have counter-example
    potential_isl_ord = isl_ord_query.first()
    if potential_isl_ord is not None:
        isl_lysingarord = db.Session.query(isl.Lysingarord).filter_by(
            fk_Ord_id=potential_isl_ord.Ord_id
        ).first()
        assert(isl_lysingarord is not None)
        isl_ord = potential_isl_ord
    return isl_ord


def add_lysingarord(lysingarord_data):
    '''
    add lýsingarorð from datafile to database
    '''
    assert('flokkur' in lysingarord_data and lysingarord_data['flokkur'] == 'lýsingarorð')
    isl_ord = isl.Ord(
        Ord=lysingarord_data['orð'],
        Ordflokkur=isl.Ordflokkar.Lysingarord
    )
    db.Session.add(isl_ord)
    db.Session.commit()
    isl_lysingarord = isl.Lysingarord(
        fk_Ord_id=isl_ord.Ord_id
    )
    db.Session.add(isl_lysingarord)
    db.Session.commit()
    if 'samsett' in lysingarord_data:
        add_samsett_ord(isl_ord.Ord_id, lysingarord_data)
        isl_ord.Samsett = True
        db.Session.commit()
        return isl_ord
    if 'frumstig' in lysingarord_data:
        if 'sb' in lysingarord_data['frumstig']:
            if 'et' in lysingarord_data['frumstig']['sb']:
                if 'kk' in lysingarord_data['frumstig']['sb']['et']:
                    isl_lysingarord.fk_Frumstig_sb_et_kk_Fallbeyging_id = (
                        add_fallbeyging(lysingarord_data['frumstig']['sb']['et']['kk'])
                    )
                    db.Session.commit()
                if 'kvk' in lysingarord_data['frumstig']['sb']['et']:
                    isl_lysingarord.fk_Frumstig_sb_et_kvk_Fallbeyging_id = (
                        add_fallbeyging(lysingarord_data['frumstig']['sb']['et']['kvk'])
                    )
                    db.Session.commit()
                if 'hk' in lysingarord_data['frumstig']['sb']['et']:
                    isl_lysingarord.fk_Frumstig_sb_et_hk_Fallbeyging_id = (
                        add_fallbeyging(lysingarord_data['frumstig']['sb']['et']['hk'])
                    )
                    db.Session.commit()
            if 'ft' in lysingarord_data['frumstig']['sb']:
                if 'kk' in lysingarord_data['frumstig']['sb']['ft']:
                    isl_lysingarord.fk_Frumstig_sb_ft_kk_Fallbeyging_id = (
                        add_fallbeyging(lysingarord_data['frumstig']['sb']['ft']['kk'])
                    )
                    db.Session.commit()
                if 'kvk' in lysingarord_data['frumstig']['sb']['ft']:
                    isl_lysingarord.fk_Frumstig_sb_ft_kvk_Fallbeyging_id = (
                        add_fallbeyging(lysingarord_data['frumstig']['sb']['ft']['kvk'])
                    )
                    db.Session.commit()
                if 'hk' in lysingarord_data['frumstig']['sb']['ft']:
                    isl_lysingarord.fk_Frumstig_sb_ft_hk_Fallbeyging_id = (
                        add_fallbeyging(lysingarord_data['frumstig']['sb']['ft']['hk'])
                    )
                    db.Session.commit()
        if 'vb' in lysingarord_data['frumstig']:
            if 'et' in lysingarord_data['frumstig']['vb']:
                if 'kk' in lysingarord_data['frumstig']['vb']['et']:
                    isl_lysingarord.fk_Frumstig_vb_et_kk_Fallbeyging_id = (
                        add_fallbeyging(lysingarord_data['frumstig']['vb']['et']['kk'])
                    )
                    db.Session.commit()
                if 'kvk' in lysingarord_data['frumstig']['vb']['et']:
                    isl_lysingarord.fk_Frumstig_vb_et_kvk_Fallbeyging_id = (
                        add_fallbeyging(lysingarord_data['frumstig']['vb']['et']['kvk'])
                    )
                    db.Session.commit()
                if 'hk' in lysingarord_data['frumstig']['vb']['et']:
                    isl_lysingarord.fk_Frumstig_vb_et_hk_Fallbeyging_id = (
                        add_fallbeyging(lysingarord_data['frumstig']['vb']['et']['hk'])
                    )
                    db.Session.commit()
            if 'ft' in lysingarord_data['frumstig']['vb']:
                if 'kk' in lysingarord_data['frumstig']['vb']['ft']:
                    isl_lysingarord.fk_Frumstig_vb_ft_kk_Fallbeyging_id = (
                        add_fallbeyging(lysingarord_data['frumstig']['vb']['ft']['kk'])
                    )
                    db.Session.commit()
                if 'kvk' in lysingarord_data['frumstig']['vb']['ft']:
                    isl_lysingarord.fk_Frumstig_vb_ft_kvk_Fallbeyging_id = (
                        add_fallbeyging(lysingarord_data['frumstig']['vb']['ft']['kvk'])
                    )
                    db.Session.commit()
                if 'hk' in lysingarord_data['frumstig']['vb']['ft']:
                    isl_lysingarord.fk_Frumstig_vb_ft_hk_Fallbeyging_id = (
                        add_fallbeyging(lysingarord_data['frumstig']['vb']['ft']['hk'])
                    )
                    db.Session.commit()
    if 'miðstig' in lysingarord_data:
        if 'vb' in lysingarord_data['miðstig']:
            if 'et' in lysingarord_data['miðstig']['vb']:
                if 'kk' in lysingarord_data['miðstig']['vb']['et']:
                    isl_lysingarord.fk_Midstig_vb_et_kk_Fallbeyging_id = (
                        add_fallbeyging(lysingarord_data['miðstig']['vb']['et']['kk'])
                    )
                    db.Session.commit()
                if 'kvk' in lysingarord_data['miðstig']['vb']['et']:
                    isl_lysingarord.fk_Midstig_vb_et_kvk_Fallbeyging_id = (
                        add_fallbeyging(lysingarord_data['miðstig']['vb']['et']['kvk'])
                    )
                    db.Session.commit()
                if 'hk' in lysingarord_data['miðstig']['vb']['et']:
                    isl_lysingarord.fk_Midstig_vb_et_hk_Fallbeyging_id = (
                        add_fallbeyging(lysingarord_data['miðstig']['vb']['et']['hk'])
                    )
                    db.Session.commit()
            if 'ft' in lysingarord_data['miðstig']['vb']:
                if 'kk' in lysingarord_data['miðstig']['vb']['ft']:
                    isl_lysingarord.fk_Midstig_vb_ft_kk_Fallbeyging_id = (
                        add_fallbeyging(lysingarord_data['miðstig']['vb']['ft']['kk'])
                    )
                    db.Session.commit()
                if 'kvk' in lysingarord_data['miðstig']['vb']['ft']:
                    isl_lysingarord.fk_Midstig_vb_ft_kvk_Fallbeyging_id = (
                        add_fallbeyging(lysingarord_data['miðstig']['vb']['ft']['kvk'])
                    )
                    db.Session.commit()
                if 'hk' in lysingarord_data['miðstig']['vb']['ft']:
                    isl_lysingarord.fk_Midstig_vb_ft_hk_Fallbeyging_id = (
                        add_fallbeyging(lysingarord_data['miðstig']['vb']['ft']['hk'])
                    )
                    db.Session.commit()
    if 'efstastig' in lysingarord_data:
        if 'sb' in lysingarord_data['efstastig']:
            if 'et' in lysingarord_data['efstastig']['sb']:
                if 'kk' in lysingarord_data['efstastig']['sb']['et']:
                    isl_lysingarord.fk_Efstastig_sb_et_kk_Fallbeyging_id = (
                        add_fallbeyging(lysingarord_data['efstastig']['sb']['et']['kk'])
                    )
                    db.Session.commit()
                if 'kvk' in lysingarord_data['efstastig']['sb']['et']:
                    isl_lysingarord.fk_Efstastig_sb_et_kvk_Fallbeyging_id = (
                        add_fallbeyging(lysingarord_data['efstastig']['sb']['et']['kvk'])
                    )
                    db.Session.commit()
                if 'hk' in lysingarord_data['efstastig']['sb']['et']:
                    isl_lysingarord.fk_Efstastig_sb_et_hk_Fallbeyging_id = (
                        add_fallbeyging(lysingarord_data['efstastig']['sb']['et']['hk'])
                    )
                    db.Session.commit()
            if 'ft' in lysingarord_data['efstastig']['sb']:
                if 'kk' in lysingarord_data['efstastig']['sb']['ft']:
                    isl_lysingarord.fk_Efstastig_sb_ft_kk_Fallbeyging_id = (
                        add_fallbeyging(lysingarord_data['efstastig']['sb']['ft']['kk'])
                    )
                    db.Session.commit()
                if 'kvk' in lysingarord_data['efstastig']['sb']['ft']:
                    isl_lysingarord.fk_Efstastig_sb_ft_kvk_Fallbeyging_id = (
                        add_fallbeyging(lysingarord_data['efstastig']['sb']['ft']['kvk'])
                    )
                    db.Session.commit()
                if 'hk' in lysingarord_data['efstastig']['sb']['ft']:
                    isl_lysingarord.fk_Efstastig_sb_ft_hk_Fallbeyging_id = (
                        add_fallbeyging(lysingarord_data['efstastig']['sb']['ft']['hk'])
                    )
                    db.Session.commit()
        if 'vb' in lysingarord_data['efstastig']:
            if 'et' in lysingarord_data['efstastig']['vb']:
                if 'kk' in lysingarord_data['efstastig']['vb']['et']:
                    isl_lysingarord.fk_Efstastig_vb_et_kk_Fallbeyging_id = (
                        add_fallbeyging(lysingarord_data['efstastig']['vb']['et']['kk'])
                    )
                    db.Session.commit()
                if 'kvk' in lysingarord_data['efstastig']['vb']['et']:
                    isl_lysingarord.fk_Efstastig_vb_et_kvk_Fallbeyging_id = (
                        add_fallbeyging(lysingarord_data['efstastig']['vb']['et']['kvk'])
                    )
                    db.Session.commit()
                if 'hk' in lysingarord_data['efstastig']['vb']['et']:
                    isl_lysingarord.fk_Efstastig_vb_et_hk_Fallbeyging_id = (
                        add_fallbeyging(lysingarord_data['efstastig']['vb']['et']['hk'])
                    )
                    db.Session.commit()
            if 'ft' in lysingarord_data['efstastig']['vb']:
                if 'kk' in lysingarord_data['efstastig']['vb']['ft']:
                    isl_lysingarord.fk_Efstastig_vb_ft_kk_Fallbeyging_id = (
                        add_fallbeyging(lysingarord_data['efstastig']['vb']['ft']['kk'])
                    )
                    db.Session.commit()
                if 'kvk' in lysingarord_data['efstastig']['vb']['ft']:
                    isl_lysingarord.fk_Efstastig_vb_ft_kvk_Fallbeyging_id = (
                        add_fallbeyging(lysingarord_data['efstastig']['vb']['ft']['kvk'])
                    )
                    db.Session.commit()
                if 'hk' in lysingarord_data['efstastig']['vb']['ft']:
                    isl_lysingarord.fk_Efstastig_vb_ft_hk_Fallbeyging_id = (
                        add_fallbeyging(lysingarord_data['efstastig']['vb']['ft']['hk'])
                    )
                    db.Session.commit()
    # TODO: add samsett/undantekning handling
    return isl_ord


def lookup_sagnord(sagnord_data):
    '''
    Assume icelandic sagnorð are unique, until we have counter-example.
    '''
    isl_ord = None
    isl_ord_query = db.Session.query(isl.Ord).filter_by(
        Ord=sagnord_data['orð'],
        Ordflokkur=isl.Ordflokkar.Sagnord
    )
    assert(len(isl_ord_query.all()) < 2)  # if/when this fails it means we have counter-example
    potential_isl_ord = isl_ord_query.first()
    if potential_isl_ord is not None:
        isl_sagnord = db.Session.query(isl.Sagnord).filter_by(
            fk_Ord_id=potential_isl_ord.Ord_id
        ).first()
        assert(isl_sagnord is not None)
        isl_ord = potential_isl_ord
    return isl_ord


def add_sagnord(sagnord_data):
    '''
    add sagnorð from datafile to database
    '''
    assert('flokkur' in sagnord_data and sagnord_data['flokkur'] == 'sagnorð')
    isl_ord = isl.Ord(
        Ord=sagnord_data['orð'],
        Ordflokkur=isl.Ordflokkar.Sagnord
    )
    db.Session.add(isl_ord)
    db.Session.commit()
    isl_sagnord = isl.Sagnord(
        fk_Ord_id=isl_ord.Ord_id
    )
    db.Session.add(isl_sagnord)
    db.Session.commit()
    if 'samsett' in sagnord_data:
        add_samsett_ord(isl_ord.Ord_id, sagnord_data)
        isl_ord.Samsett = True
        db.Session.commit()
        return isl_ord
    if 'germynd' in sagnord_data:
        if 'nafnháttur' in sagnord_data['germynd']:
            isl_sagnord.Germynd_Nafnhattur = sagnord_data['germynd']['nafnháttur']
            db.Session.commit()
        if 'sagnbót' in sagnord_data['germynd']:
            isl_sagnord.Germynd_Sagnbot = sagnord_data['germynd']['sagnbót']
            db.Session.commit()
        if 'boðháttur' in sagnord_data['germynd']:
            if 'stýfður' in sagnord_data['germynd']['boðháttur']:
                isl_sagnord.Germynd_Bodhattur_styfdur = (
                    sagnord_data['germynd']['boðháttur']['stýfður']
                )
                db.Session.commit()
            if 'et' in sagnord_data['germynd']['boðháttur']:
                isl_sagnord.Germynd_Bodhattur_et = (
                    sagnord_data['germynd']['boðháttur']['et']
                )
                db.Session.commit()
            if 'ft' in sagnord_data['germynd']['boðháttur']:
                isl_sagnord.Germynd_Bodhattur_ft = (
                    sagnord_data['germynd']['boðháttur']['ft']
                )
                db.Session.commit()
        if 'persónuleg' in sagnord_data['germynd']:
            if 'framsöguháttur' in sagnord_data['germynd']['persónuleg']:
                isl_sagnord.fk_Germynd_personuleg_framsoguhattur = (
                    add_sagnbeyging(sagnord_data['germynd']['persónuleg']['framsöguháttur'])
                )
                db.Session.commit()
            if 'viðtengingarháttur' in sagnord_data['germynd']['persónuleg']:
                isl_sagnord.fk_Germynd_personuleg_vidtengingarhattur = (
                    add_sagnbeyging(sagnord_data['germynd']['persónuleg']['viðtengingarháttur'])
                )
                db.Session.commit()
        if 'ópersónuleg' in sagnord_data['germynd']:
            if 'frumlag' in sagnord_data['germynd']['ópersónuleg']:
                if sagnord_data['germynd']['ópersónuleg']['frumlag'] == 'þolfall':
                    isl_sagnord.Germynd_opersonuleg_frumlag = isl.Fall.Tholfall  # type: ignore
                elif sagnord_data['germynd']['ópersónuleg']['frumlag'] == 'þágufall':
                    isl_sagnord.Germynd_opersonuleg_frumlag = isl.Fall.Thagufall  # type: ignore
                elif sagnord_data['germynd']['ópersónuleg']['frumlag'] == 'eignarfall':
                    isl_sagnord.Germynd_opersonuleg_frumlag = isl.Fall.Eignarfall  # type: ignore
                else:
                    assert(False)  # invalid fall?
                db.Session.commit()
            if 'framsöguháttur' in sagnord_data['germynd']['ópersónuleg']:
                isl_sagnord.fk_Germynd_opersonuleg_framsoguhattur = (
                    add_sagnbeyging(sagnord_data['germynd']['ópersónuleg']['framsöguháttur'])
                )
                db.Session.commit()
            if 'viðtengingarháttur' in sagnord_data['germynd']['ópersónuleg']:
                isl_sagnord.fk_Germynd_opersonuleg_vidtengingarhattur = (
                    add_sagnbeyging(sagnord_data['germynd']['ópersónuleg']['viðtengingarháttur'])
                )
                db.Session.commit()
        if 'spurnarmyndir' in sagnord_data['germynd']:
            if 'framsöguháttur' in sagnord_data['germynd']['spurnarmyndir']:
                spm_frsh = sagnord_data['germynd']['spurnarmyndir']['framsöguháttur']
                if 'nútíð' in spm_frsh:
                    if 'et' in spm_frsh['nútíð']:
                        isl_sagnord.Germynd_spurnarmyndir_framsoguhattur_nutid_et = (
                            spm_frsh['nútíð']['et']
                        )
                        db.Session.commit()
                    if 'ft' in spm_frsh['nútíð']:
                        isl_sagnord.Germynd_spurnarmyndir_framsoguhattur_nutid_ft = (
                            spm_frsh['nútíð']['ft']
                        )
                        db.Session.commit()
                if 'þátíð' in spm_frsh:
                    if 'et' in spm_frsh['þátíð']:
                        isl_sagnord.Germynd_spurnarmyndir_framsoguhattur_thatid_et = (
                            spm_frsh['þátíð']['et']
                        )
                        db.Session.commit()
                    if 'ft' in spm_frsh['þátíð']:
                        isl_sagnord.Germynd_spurnarmyndir_framsoguhattur_thatid_ft = (
                            spm_frsh['þátíð']['ft']
                        )
                        db.Session.commit()
            if 'viðtengingarháttur' in sagnord_data['germynd']['spurnarmyndir']:
                spm_vth = sagnord_data['germynd']['spurnarmyndir']['viðtengingarháttur']
                if 'nútíð' in spm_vth:
                    if 'et' in spm_vth['nútíð']:
                        isl_sagnord.Germynd_spurnarmyndir_vidtengingarhattur_nutid_et = (
                            spm_vth['nútíð']['et']
                        )
                        db.Session.commit()
                    if 'ft' in spm_vth['nútíð']:
                        isl_sagnord.Germynd_spurnarmyndir_vidtengingarhattur_nutid_ft = (
                            spm_vth['nútíð']['ft']
                        )
                        db.Session.commit()
                if 'þátíð' in spm_vth:
                    if 'et' in spm_vth['þátíð']:
                        isl_sagnord.Germynd_spurnarmyndir_vidtengingarhattur_thatid_et = (
                            spm_vth['þátíð']['et']
                        )
                        db.Session.commit()
                    if 'ft' in spm_vth['þátíð']:
                        isl_sagnord.Germynd_spurnarmyndir_vidtengingarhattur_thatid_ft = (
                            spm_vth['þátíð']['ft']
                        )
                        db.Session.commit()
    if 'miðmynd' in sagnord_data:
        if 'nafnháttur' in sagnord_data['miðmynd']:
            isl_sagnord.Midmynd_Nafnhattur = sagnord_data['miðmynd']['nafnháttur']
            db.Session.commit()
        if 'sagnbót' in sagnord_data['miðmynd']:
            isl_sagnord.Midmynd_Sagnbot = sagnord_data['miðmynd']['sagnbót']
            db.Session.commit()
        if 'boðháttur' in sagnord_data['miðmynd']:
            if 'et' in sagnord_data['miðmynd']['boðháttur']:
                isl_sagnord.Midmynd_Bodhattur_et = (
                    sagnord_data['miðmynd']['boðháttur']['et']
                )
                db.Session.commit()
            if 'ft' in sagnord_data['miðmynd']['boðháttur']:
                isl_sagnord.Midmynd_Bodhattur_ft = (
                    sagnord_data['miðmynd']['boðháttur']['ft']
                )
                db.Session.commit()
        if 'persónuleg' in sagnord_data['miðmynd']:
            if 'framsöguháttur' in sagnord_data['miðmynd']['persónuleg']:
                isl_sagnord.fk_Midmynd_personuleg_framsoguhattur = (
                    add_sagnbeyging(sagnord_data['miðmynd']['persónuleg']['framsöguháttur'])
                )
                db.Session.commit()
            if 'viðtengingarháttur' in sagnord_data['miðmynd']['persónuleg']:
                isl_sagnord.fk_Midmynd_personuleg_vidtengingarhattur = (
                    add_sagnbeyging(sagnord_data['miðmynd']['persónuleg']['viðtengingarháttur'])
                )
                db.Session.commit()
        if 'ópersónuleg' in sagnord_data['miðmynd']:
            if 'frumlag' in sagnord_data['miðmynd']['ópersónuleg']:
                if sagnord_data['miðmynd']['ópersónuleg']['frumlag'] == 'þolfall':
                    isl_sagnord.Midmynd_opersonuleg_frumlag = isl.Fall.Tholfall  # type: ignore
                elif sagnord_data['miðmynd']['ópersónuleg']['frumlag'] == 'þágufall':
                    isl_sagnord.Midmynd_opersonuleg_frumlag = isl.Fall.Thagufall  # type: ignore
                elif sagnord_data['miðmynd']['ópersónuleg']['frumlag'] == 'eignarfall':
                    isl_sagnord.Midmynd_opersonuleg_frumlag = isl.Fall.Eignarfall  # type: ignore
                else:
                    assert(False)  # invalid fall or None? should not happen here
                db.Session.commit()
            if 'framsöguháttur' in sagnord_data['miðmynd']['ópersónuleg']:
                isl_sagnord.fk_Midmynd_opersonuleg_framsoguhattur = (
                    add_sagnbeyging(sagnord_data['miðmynd']['ópersónuleg']['framsöguháttur'])
                )
                db.Session.commit()
            if 'viðtengingarháttur' in sagnord_data['miðmynd']['ópersónuleg']:
                isl_sagnord.fk_Midmynd_opersonuleg_vidtengingarhattur = (
                    add_sagnbeyging(sagnord_data['miðmynd']['ópersónuleg']['viðtengingarháttur'])
                )
                db.Session.commit()
        if 'spurnarmyndir' in sagnord_data['miðmynd']:
            if 'framsöguháttur' in sagnord_data['miðmynd']['spurnarmyndir']:
                spm_frsh = sagnord_data['miðmynd']['spurnarmyndir']['framsöguháttur']
                if 'nútíð' in spm_frsh:
                    if 'et' in spm_frsh['nútíð']:
                        isl_sagnord.Midmynd_spurnarmyndir_framsoguhattur_nutid_et = (
                            spm_frsh['nútíð']['et']
                        )
                        db.Session.commit()
                    if 'ft' in spm_frsh['nútíð']:
                        isl_sagnord.Midmynd_spurnarmyndir_framsoguhattur_nutid_ft = (
                            spm_frsh['nútíð']['ft']
                        )
                        db.Session.commit()
                if 'þátíð' in spm_frsh:
                    if 'et' in spm_frsh['þátíð']:
                        isl_sagnord.Midmynd_spurnarmyndir_framsoguhattur_thatid_et = (
                            spm_frsh['þátíð']['et']
                        )
                        db.Session.commit()
                    if 'ft' in spm_frsh['þátíð']:
                        isl_sagnord.Midmynd_spurnarmyndir_framsoguhattur_thatid_ft = (
                            spm_frsh['þátíð']['ft']
                        )
                        db.Session.commit()
            if 'viðtengingarháttur' in sagnord_data['miðmynd']['spurnarmyndir']:
                spm_vth = sagnord_data['miðmynd']['spurnarmyndir']['viðtengingarháttur']
                if 'nútíð' in spm_vth:
                    if 'et' in spm_vth['nútíð']:
                        isl_sagnord.Midmynd_spurnarmyndir_vidtengingarhattur_nutid_et = (
                            spm_vth['nútíð']['et']
                        )
                        db.Session.commit()
                    if 'ft' in spm_vth['nútíð']:
                        isl_sagnord.Midmynd_spurnarmyndir_vidtengingarhattur_nutid_ft = (
                            spm_vth['nútíð']['ft']
                        )
                        db.Session.commit()
                if 'þátíð' in spm_vth:
                    if 'et' in spm_vth['þátíð']:
                        isl_sagnord.Midmynd_spurnarmyndir_vidtengingarhattur_thatid_et = (
                            spm_vth['þátíð']['et']
                        )
                        db.Session.commit()
                    if 'ft' in spm_vth['þátíð']:
                        isl_sagnord.Midmynd_spurnarmyndir_vidtengingarhattur_thatid_ft = (
                            spm_vth['þátíð']['ft']
                        )
                        db.Session.commit()
    if 'lýsingarháttur' in sagnord_data:
        if 'nútíðar' in sagnord_data['lýsingarháttur']:
            isl_sagnord.LysingarhatturNutidar = sagnord_data['lýsingarháttur']['nútíðar']
            db.Session.commit()
        if 'þátíðar' in sagnord_data['lýsingarháttur']:
            if 'sb' in sagnord_data['lýsingarháttur']['þátíðar']:
                if 'et' in sagnord_data['lýsingarháttur']['þátíðar']['sb']:
                    if 'kk' in sagnord_data['lýsingarháttur']['þátíðar']['sb']['et']:
                        isl_sagnord.fk_LysingarhatturThatidar_sb_et_kk_id = (
                            add_fallbeyging(
                                sagnord_data['lýsingarháttur']['þátíðar']['sb']['et']['kk']
                            )
                        )
                        db.Session.commit()
                    if 'kvk' in sagnord_data['lýsingarháttur']['þátíðar']['sb']['et']:
                        isl_sagnord.fk_LysingarhatturThatidar_sb_et_kvk_id = (
                            add_fallbeyging(
                                sagnord_data['lýsingarháttur']['þátíðar']['sb']['et']['kvk']
                            )
                        )
                        db.Session.commit()
                    if 'hk' in sagnord_data['lýsingarháttur']['þátíðar']['sb']['et']:
                        isl_sagnord.fk_LysingarhatturThatidar_sb_et_hk_id = (
                            add_fallbeyging(
                                sagnord_data['lýsingarháttur']['þátíðar']['sb']['et']['hk']
                            )
                        )
                        db.Session.commit()
                if 'ft' in sagnord_data['lýsingarháttur']['þátíðar']['sb']:
                    if 'kk' in sagnord_data['lýsingarháttur']['þátíðar']['sb']['ft']:
                        isl_sagnord.fk_LysingarhatturThatidar_sb_ft_kk_id = (
                            add_fallbeyging(
                                sagnord_data['lýsingarháttur']['þátíðar']['sb']['ft']['kk']
                            )
                        )
                        db.Session.commit()
                    if 'kvk' in sagnord_data['lýsingarháttur']['þátíðar']['sb']['ft']:
                        isl_sagnord.fk_LysingarhatturThatidar_sb_ft_kvk_id = (
                            add_fallbeyging(
                                sagnord_data['lýsingarháttur']['þátíðar']['sb']['ft']['kvk']
                            )
                        )
                        db.Session.commit()
                    if 'hk' in sagnord_data['lýsingarháttur']['þátíðar']['sb']['ft']:
                        isl_sagnord.fk_LysingarhatturThatidar_sb_ft_hk_id = (
                            add_fallbeyging(
                                sagnord_data['lýsingarháttur']['þátíðar']['sb']['ft']['hk']
                            )
                        )
                        db.Session.commit()
            if 'vb' in sagnord_data['lýsingarháttur']['þátíðar']:
                if 'et' in sagnord_data['lýsingarháttur']['þátíðar']['vb']:
                    if 'kk' in sagnord_data['lýsingarháttur']['þátíðar']['vb']['et']:
                        isl_sagnord.fk_LysingarhatturThatidar_vb_et_kk_id = (
                            add_fallbeyging(
                                sagnord_data['lýsingarháttur']['þátíðar']['vb']['et']['kk']
                            )
                        )
                        db.Session.commit()
                    if 'kvk' in sagnord_data['lýsingarháttur']['þátíðar']['vb']['et']:
                        isl_sagnord.fk_LysingarhatturThatidar_vb_et_kvk_id = (
                            add_fallbeyging(
                                sagnord_data['lýsingarháttur']['þátíðar']['vb']['et']['kvk']
                            )
                        )
                        db.Session.commit()
                    if 'hk' in sagnord_data['lýsingarháttur']['þátíðar']['vb']['et']:
                        isl_sagnord.fk_LysingarhatturThatidar_vb_et_hk_id = (
                            add_fallbeyging(
                                sagnord_data['lýsingarháttur']['þátíðar']['vb']['et']['hk']
                            )
                        )
                        db.Session.commit()
                if 'ft' in sagnord_data['lýsingarháttur']['þátíðar']['vb']:
                    if 'kk' in sagnord_data['lýsingarháttur']['þátíðar']['vb']['ft']:
                        isl_sagnord.fk_LysingarhatturThatidar_vb_ft_kk_id = (
                            add_fallbeyging(
                                sagnord_data['lýsingarháttur']['þátíðar']['vb']['ft']['kk']
                            )
                        )
                        db.Session.commit()
                    if 'kvk' in sagnord_data['lýsingarháttur']['þátíðar']['vb']['ft']:
                        isl_sagnord.fk_LysingarhatturThatidar_vb_ft_kvk_id = (
                            add_fallbeyging(
                                sagnord_data['lýsingarháttur']['þátíðar']['vb']['ft']['kvk']
                            )
                        )
                        db.Session.commit()
                    if 'hk' in sagnord_data['lýsingarháttur']['þátíðar']['vb']['ft']:
                        isl_sagnord.fk_LysingarhatturThatidar_vb_ft_hk_id = (
                            add_fallbeyging(
                                sagnord_data['lýsingarháttur']['þátíðar']['vb']['ft']['hk']
                            )
                        )
                        db.Session.commit()
    # TODO: add samsett/undantekning handling
    return isl_ord


def add_fallbeyging(fallbeyging_list):
    '''
    add fallbeyging to database, return Fallbeyging_id
    '''
    assert_fallbeyging_list(fallbeyging_list)
    isl_ord_fallbeyging = isl.Fallbeyging(
        Nefnifall=fallbeyging_list[0],
        Tholfall=fallbeyging_list[1],
        Thagufall=fallbeyging_list[2],
        Eignarfall=fallbeyging_list[3]
    )
    db.Session.add(isl_ord_fallbeyging)
    db.Session.commit()
    return isl_ord_fallbeyging.Fallbeyging_id


def assert_fallbeyging_list(fallbeyging_list):
    '''
    assert object structure of [str/None, str/None, str/None, str/None]
    '''
    assert(type(fallbeyging_list) is list)
    assert(len(fallbeyging_list) == 4)
    for fallbeyging in fallbeyging_list:
        if fallbeyging is not None:
            assert(type(fallbeyging) is str)


def add_sagnbeyging(sagnbeyging_obj):
    '''
    add fallbeyging to database, return Fallbeyging_id
    '''
    assert_sagnbeyging_obj(sagnbeyging_obj)
    kwargs = {}
    if 'nútíð' in sagnbeyging_obj:
        if 'et' in sagnbeyging_obj['nútíð']:
            kwargs['FyrstaPersona_eintala_nutid'] = sagnbeyging_obj['nútíð']['et'][0]
            kwargs['OnnurPersona_eintala_nutid'] = sagnbeyging_obj['nútíð']['et'][1]
            kwargs['ThridjaPersona_eintala_nutid'] = sagnbeyging_obj['nútíð']['et'][2]
        if 'ft' in sagnbeyging_obj['nútíð']:
            kwargs['FyrstaPersona_fleirtala_nutid'] = sagnbeyging_obj['nútíð']['ft'][0]
            kwargs['OnnurPersona_fleirtala_nutid'] = sagnbeyging_obj['nútíð']['ft'][1]
            kwargs['ThridjaPersona_fleirtala_nutid'] = sagnbeyging_obj['nútíð']['ft'][2]
    if 'þátíð' in sagnbeyging_obj:
        if 'et' in sagnbeyging_obj['þátíð']:
            kwargs['FyrstaPersona_eintala_thatid'] = sagnbeyging_obj['þátíð']['et'][0]
            kwargs['OnnurPersona_eintala_thatid'] = sagnbeyging_obj['þátíð']['et'][1]
            kwargs['ThridjaPersona_eintala_thatid'] = sagnbeyging_obj['þátíð']['et'][2]
        if 'ft' in sagnbeyging_obj['þátíð']:
            kwargs['FyrstaPersona_fleirtala_thatid'] = sagnbeyging_obj['þátíð']['ft'][0]
            kwargs['OnnurPersona_fleirtala_thatid'] = sagnbeyging_obj['þátíð']['ft'][1]
            kwargs['ThridjaPersona_fleirtala_thatid'] = sagnbeyging_obj['þátíð']['ft'][2]
    isl_ord_sagnbeyging = isl.Sagnbeyging(**kwargs)
    db.Session.add(isl_ord_sagnbeyging)
    db.Session.commit()
    return isl_ord_sagnbeyging.Sagnbeyging_id


def assert_sagnbeyging_obj(sagnbeyging_obj):
    '''
    assert object structure of {
        "nútíð": {
            "et": [str/None, str/None, str/None]
            "ft": [str/None, str/None, str/None]
        }
        "þátíð": {
            "et": [str/None, str/None, str/None]
            "ft": [str/None, str/None, str/None]
        }
    } where object root has at least one suggested key
    '''
    dictorinos = (dict, collections.OrderedDict)
    assert(type(sagnbeyging_obj) in dictorinos)
    assert('nútíð' in sagnbeyging_obj or 'þátíð' in sagnbeyging_obj)
    if 'nútíð' in sagnbeyging_obj:
        assert(type(sagnbeyging_obj['nútíð']) in dictorinos)
        assert('et' in sagnbeyging_obj['nútíð'] or 'ft' in sagnbeyging_obj['nútíð'])
        if 'et' in sagnbeyging_obj['nútíð']:
            assert(type(sagnbeyging_obj['nútíð']['et']) is list)
            assert(len(sagnbeyging_obj['nútíð']['et']) == 3)
            for sagnbeyging in sagnbeyging_obj['nútíð']['et']:
                if sagnbeyging is not None:
                    assert(type(sagnbeyging) is str)
        if 'ft' in sagnbeyging_obj['nútíð']:
            assert(type(sagnbeyging_obj['nútíð']['ft']) is list)
            assert(len(sagnbeyging_obj['nútíð']['ft']) == 3)
            for sagnbeyging in sagnbeyging_obj['nútíð']['ft']:
                if sagnbeyging is not None:
                    assert(type(sagnbeyging) is str)
    if 'þátíð' in sagnbeyging_obj:
        assert(type(sagnbeyging_obj['þátíð']) in dictorinos)
        assert('et' in sagnbeyging_obj['þátíð'] or 'ft' in sagnbeyging_obj['þátíð'])
        if 'et' in sagnbeyging_obj['þátíð']:
            assert(type(sagnbeyging_obj['þátíð']['et']) is list)
            assert(len(sagnbeyging_obj['þátíð']['et']) == 3)
            for sagnbeyging in sagnbeyging_obj['þátíð']['et']:
                if sagnbeyging is not None:
                    assert(type(sagnbeyging) is str)
        if 'ft' in sagnbeyging_obj['þátíð']:
            assert(type(sagnbeyging_obj['þátíð']['ft']) is list)
            assert(len(sagnbeyging_obj['þátíð']['ft']) == 3)
            for sagnbeyging in sagnbeyging_obj['þátíð']['ft']:
                if sagnbeyging is not None:
                    assert(type(sagnbeyging) is str)


def assert_ordhluti_obj(ordhluti_obj, ordflokkur, last_obj=False):
    '''
    assert object structure of {
        ["mynd": str,]
        ["samsetning": "stofn"/"eignarfalls"/"bandsstafs",]
        "orð": str,
        "flokkur": {str defning orðflokkur},
        ["kyn": "kvk"/"kk"/"hk",]
        "hash": str
    }
    with some additional rules/caveats
    '''
    dictorinos = (dict, collections.OrderedDict)
    samsetningar = ['stofn', 'eignarfalls', 'bandstafs']
    ordflokkar = [
        'nafnorð',
        'lýsingarorð',
        'greinir',
        'frumtala',
        'raðtala',
        'fornafn',
        'sagnorð',
        'forsetning',
        'atviksorð',
        'nafnháttarmerki',
        'samtenging',
        'upphrópun'
    ]
    kyn = ['kk', 'kvk', 'hk']
    assert(type(ordhluti_obj) in dictorinos)
    if last_obj is False or 'mynd' in ordhluti_obj:
        assert('mynd' in ordhluti_obj)
        assert(type(ordhluti_obj['mynd']) is str)
        assert(len(ordhluti_obj['mynd']) > 0)
        assert('samsetning' in ordhluti_obj)
        assert(ordhluti_obj['samsetning'] in samsetningar)
    assert('orð' in ordhluti_obj)
    assert(type(ordhluti_obj['orð']) is str)
    assert(len(ordhluti_obj['orð']) > 0)
    assert('flokkur' in ordhluti_obj)
    assert(ordhluti_obj['flokkur'] in ordflokkar)
    if ordhluti_obj['flokkur'] == 'nafnorð':
        assert('kyn' in ordhluti_obj)
        assert(ordhluti_obj['kyn'] in kyn)
    assert('hash' in ordhluti_obj)
    assert(type(ordhluti_obj['hash']) is str)
    assert(len(ordhluti_obj['hash']) > 0)
    if last_obj is True and 'mynd' not in ordhluti_obj:
        assert(ordhluti_obj['flokkur'] == ordflokkur)


def add_samsett_ord(isl_ord_id, ord_data):
    assert(type(ord_data['samsett']) is list)
    assert(len(ord_data['samsett']) > 0)
    last_idx = len(ord_data['samsett']) - 1
    for idx, ordhluti_obj in enumerate(ord_data['samsett']):
        flokkur = ord_data['flokkur']
        last_obj = (idx == last_idx)
        assert_ordhluti_obj(ordhluti_obj, ordflokkur=flokkur, last_obj=last_obj)
    # handle samsett orð
    isl_samsett_ord = isl.SamsettOrd(fk_Ord_id=isl_ord_id)
    db.Session.add(isl_samsett_ord)
    db.Session.commit()
    last_ordhluti_obj_id = None
    # iterate through and ensure orðhlutar in reverse because it simplifies lots of things
    for idx, ordhluti_obj in enumerate(reversed(ord_data['samsett'])):
        # check if orðhluti with identical values already exists
        ordhluti_mynd = None
        ordhluti_gerd = None
        if 'mynd' in ordhluti_obj:
            ordhluti_mynd = ordhluti_obj['mynd']
            if ordhluti_obj['samsetning'] == 'stofn':
                ordhluti_gerd = isl.Ordasamsetningar.Stofnsamsetning
            elif ordhluti_obj['samsetning'] == 'eignarfalls':
                ordhluti_gerd = isl.Ordasamsetningar.Eignarfallssamsetning
            elif ordhluti_obj['samsetning'] == 'bandstafs':
                ordhluti_gerd = isl.Ordasamsetningar.Bandstafssamsetning
        ordhluti_isl_ord = None
        if ordhluti_obj['flokkur'] == 'nafnorð':
            ordhluti_isl_ord = lookup_nafnord({
                'orð': ordhluti_obj['orð'], 'kyn': ordhluti_obj['kyn']
            })
        elif ordhluti_obj['flokkur'] == 'lýsingarorð':
            ordhluti_isl_ord = lookup_lysingarord({'orð': ordhluti_obj['orð']})
        elif ordhluti_obj['flokkur'] == 'sagnorð':
            ordhluti_isl_ord = lookup_sagnord({'orð': ordhluti_obj['orð']})
        # TODO: add handling for the other orðflokkar here
        assert(ordhluti_isl_ord is not None)
        isl_ordhluti = db.Session.query(isl.SamsettOrdhlutar).filter_by(
            fk_Ord_id=ordhluti_isl_ord.Ord_id,
            Ordmynd=ordhluti_mynd,
            Gerd=ordhluti_gerd,
            fk_NaestiOrdhluti_id=last_ordhluti_obj_id
        ).first()
        # if identical orðhluti doesn't exist then create it
        if isl_ordhluti is None:
            isl_ordhluti = isl.SamsettOrdhlutar(
                fk_Ord_id=ordhluti_isl_ord.Ord_id,
                Ordmynd=ordhluti_mynd,
                Gerd=ordhluti_gerd,
                fk_NaestiOrdhluti_id=last_ordhluti_obj_id
            )
            db.Session.add(isl_ordhluti)
            db.Session.commit()
        last_ordhluti_obj_id = isl_ordhluti.SamsettOrdhlutar_id
        # when on the last (first) orðhluti then link it to the SamsettOrd record
        if idx == last_idx:
            isl_samsett_ord.fk_FyrstiOrdHluti_id = isl_ordhluti.SamsettOrdhlutar_id
            db.Session.commit()


def add_word(word_data, write_to_file=True):
    datafiles_dir_abs = os.path.abspath(
        os.path.join(os.path.dirname(os.path.realpath(__file__)), 'database', 'data')
    )
    isl_ord = None
    isl_ord_data = None
    isl_ord_directory = None
    isl_ord_filename = None
    if word_data['flokkur'] == 'nafnorð':
        isl_ord_directory = 'nafnord'
        assert(lookup_nafnord(word_data) is None)
        isl_ord = add_nafnord(word_data)
        isl_ord_data = get_nafnord_from_db_to_ordered_dict(isl_ord)
        isl_ord_filename = '%s-%s.json' % (isl_ord_data['orð'], isl_ord_data['kyn'])
    elif word_data['flokkur'] == 'lýsingarorð':
        isl_ord_directory = 'lysingarord'
        assert(lookup_lysingarord(word_data) is None)
        isl_ord = add_lysingarord(word_data)
        isl_ord_data = get_lysingarord_from_db_to_ordered_dict(isl_ord)
        isl_ord_filename = '%s.json' % (isl_ord_data['orð'], )
    elif word_data['flokkur'] == 'sagnorð':
        isl_ord_directory = 'sagnord'
        assert(lookup_sagnord(word_data) is None)
        isl_ord = add_sagnord(word_data)
        isl_ord_data = get_sagnord_from_db_to_ordered_dict(isl_ord)
        isl_ord_filename = '%s.json' % (isl_ord_data['orð'], )
    assert(isl_ord is not None)
    assert(isl_ord_data is not None)
    assert(isl_ord_directory is not None)
    assert(isl_ord_filename is not None)
    if write_to_file is True:
    	# note: here we don't ensure unique hash, should we?
    	isl_ord_data_hash = hashify_ord_data(isl_ord_data)
    	isl_ord_data['hash'] = isl_ord_data_hash
    	isl_ord_data_json_str = ord_data_to_fancy_json_str(isl_ord_data)
    	with open(
    	    os.path.join(datafiles_dir_abs, isl_ord_directory, isl_ord_filename),
    	    mode='w',
    	    encoding='utf-8'
    	) as json_file:
    	    json_file.write(isl_ord_data_json_str)
    	    logman.info('Wrote file "%s/%s' % (isl_ord_directory, isl_ord_filename, ))
