#!/usr/bin/python
"""
Importer functionality

Importing data from files to SQL database.
"""
import collections
import json
import os
import pathlib
import re

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
    import_tasks = [
        {
            'name': 'nafnorð',
            'root': datafiles_dir_abs,
            'dir': 'nafnord',
            'f_lookup': lookup_nafnord,
            'f_add': add_nafnord,
            'has_samsett': True
        },
        {
            'name': 'lýsingarorð',
            'root': datafiles_dir_abs,
            'dir': 'lysingarord',
            'f_lookup': lookup_lysingarord,
            'f_add': add_lysingarord,
            'has_samsett': True
        },
        {
            'name': 'sagnorð',
            'root': datafiles_dir_abs,
            'dir': 'sagnord',
            'f_lookup': lookup_sagnord,
            'f_add': add_sagnord,
            'has_samsett': True
        },
        {
            'name': 'greinir',
            'root': datafiles_dir_abs,
            'dir': 'greinir',
            'f_lookup': lookup_greinir,
            'f_add': add_greinir,
            'has_samsett': False
        },
        {
            'name': 'frumtölur',
            'root': datafiles_dir_abs,
            'dir': os.path.join('toluord', 'frumtolur'),
            'f_lookup': lookup_frumtala,
            'f_add': add_frumtala,
            'has_samsett': True
        },
        {
            'name': 'raðtölur',
            'root': datafiles_dir_abs,
            'dir': os.path.join('toluord', 'radtolur'),
            'f_lookup': lookup_radtala,
            'f_add': add_radtala,
            'has_samsett': True
        },
        {
            'name': 'ábendingarfornöfn',
            'root': datafiles_dir_abs,
            'dir': os.path.join('fornofn', 'abendingar'),
            'f_lookup': lookup_fornafn,
            'f_add': add_fornafn,
            'has_samsett': True
        },
        {
            'name': 'afturbeygt fornafn',
            'root': datafiles_dir_abs,
            'dir': os.path.join('fornofn', 'afturbeygt'),
            'f_lookup': lookup_fornafn,
            'f_add': add_fornafn,
            'has_samsett': False
        },
        {
            'name': 'eignarfornöfn',
            'root': datafiles_dir_abs,
            'dir': os.path.join('fornofn', 'eignar'),
            'f_lookup': lookup_fornafn,
            'f_add': add_fornafn,
            'has_samsett': True
        },
        {
            'name': 'óákveðin fornöfn',
            'root': datafiles_dir_abs,
            'dir': os.path.join('fornofn', 'oakvedin'),
            'f_lookup': lookup_fornafn,
            'f_add': add_fornafn,
            'has_samsett': True
        },
        {
            'name': 'persónufornöfn',
            'root': datafiles_dir_abs,
            'dir': os.path.join('fornofn', 'personu'),
            'f_lookup': lookup_fornafn,
            'f_add': add_fornafn,
            'has_samsett': True
        },
        {
            'name': 'spurnarfornöfn',
            'root': datafiles_dir_abs,
            'dir': os.path.join('fornofn', 'spurnar'),
            'f_lookup': lookup_fornafn,
            'f_add': add_fornafn,
            'has_samsett': True
        },
        {
            'name': 'smáorð, forsetning',
            'root': datafiles_dir_abs,
            'dir': os.path.join('smaord', 'forsetning'),
            'f_lookup': lookup_forsetning,
            'f_add': add_forsetning,
            'has_samsett': False
        },
        {
            'name': 'smáorð, atviksorð',
            'root': datafiles_dir_abs,
            'dir': os.path.join('smaord', 'atviksord'),
            'f_lookup': lookup_atviksord,
            'f_add': add_atviksord,
            'has_samsett': False
        },
        {
            'name': 'smáorð, nafnháttarmerki',
            'root': datafiles_dir_abs,
            'dir': os.path.join('smaord', 'nafnhattarmerki'),
            'f_lookup': lookup_nafnhattarmerki,
            'f_add': add_nafnhattarmerki,
            'has_samsett': False
        },
        {
            'name': 'smáorð, samtenging',
            'root': datafiles_dir_abs,
            'dir': os.path.join('smaord', 'samtenging'),
            'f_lookup': lookup_samtenging,
            'f_add': add_samtenging,
            'has_samsett': False
        },
        {
            'name': 'smáorð, upphrópun',
            'root': datafiles_dir_abs,
            'dir': os.path.join('smaord', 'upphropun'),
            'f_lookup': lookup_upphropun,
            'f_add': add_upphropun,
            'has_samsett': False
        },
        {
            'name': 'sérnafn, eiginnöfn (kk)',
            'root': datafiles_dir_abs,
            'dir': os.path.join('sernofn', 'mannanofn', 'islensk-karlmannsnofn', 'eigin'),
            'f_lookup': lookup_sernafn,
            'f_add': add_sernafn,
            'has_samsett': True
        },
        {
            'name': 'sérnafn, gælunöfn (kk)',
            'root': datafiles_dir_abs,
            'dir': os.path.join('sernofn', 'mannanofn', 'islensk-karlmannsnofn', 'gaelu'),
            'f_lookup': lookup_sernafn,
            'f_add': add_sernafn,
            'has_samsett': True
        },
        {
            'name': 'sérnafn, kenninöfn (kk)',
            'root': datafiles_dir_abs,
            'dir': os.path.join('sernofn', 'mannanofn', 'islensk-karlmannsnofn', 'kenni'),
            'f_lookup': lookup_sernafn,
            'f_add': add_sernafn,
            'has_samsett': True
        },
        {
            'name': 'sérnafn, eiginnöfn (kvk)',
            'root': datafiles_dir_abs,
            'dir': os.path.join('sernofn', 'mannanofn', 'islensk-kvenmannsnofn', 'eigin'),
            'f_lookup': lookup_sernafn,
            'f_add': add_sernafn,
            'has_samsett': True
        },
        {
            'name': 'sérnafn, gælunöfn (kvk)',
            'root': datafiles_dir_abs,
            'dir': os.path.join('sernofn', 'mannanofn', 'islensk-kvenmannsnofn', 'gaelu'),
            'f_lookup': lookup_sernafn,
            'f_add': add_sernafn,
            'has_samsett': True
        },
        {
            'name': 'sérnafn, kenninöfn (kvk)',
            'root': datafiles_dir_abs,
            'dir': os.path.join('sernofn', 'mannanofn', 'islensk-kvenmannsnofn', 'kenni'),
            'f_lookup': lookup_sernafn,
            'f_add': add_sernafn,
            'has_samsett': True
        },
        {
            'name': 'sérnafn, íslensk millinöfn (ættarnöfn)',
            'root': datafiles_dir_abs,
            'dir': os.path.join('sernofn', 'mannanofn', 'islensk-millinofn'),
            'f_lookup': lookup_sernafn,
            'f_add': add_sernafn,
            'has_samsett': False
        },
        {
            'name': 'sérnafn, örnefni',
            'root': datafiles_dir_abs,
            'dir': os.path.join('sernofn', 'ornefni'),
            'f_lookup': lookup_sernafn,
            'f_add': add_sernafn,
            'has_samsett': True
        }
    ]
    logman.info('We import core words first, then combined (samssett).')
    for task in import_tasks:
        do_import_task(task, do_samsett=False)
    logman.info('Now importing combined words (samsett).')
    for task in import_tasks:
        do_import_task(task, do_samsett=True)
    #
    logman.info('TODO: finish implementing build_db_from_datafiles')


def do_import_task(task, do_samsett=False):
    f_lookup = task['f_lookup']
    f_add = task['f_add']
    files = None
    if task['has_samsett'] is True:
        if 'samsett_split' not in task:
            task['samsett_split'] = list_json_files_separate_samsett_ord(
                os.path.join(task['root'], task['dir'])
            )
        if do_samsett is False:
            files = task['samsett_split'][0]
        else:
            files = task['samsett_split'][1]
    else:
        if do_samsett is True:
            # nothing to do here
            return
        files = sorted(pathlib.Path(os.path.join(task['root'], task['dir'])).iterdir())
    assert(files is not None)
    logman.info('Task %s "%s" %s..' % (
        'kjarna' if do_samsett is False else 'samsett',
        task['name'],
        'filecount=%s' % (len(files), )
    ))
    for ord_file in files:
        logman.info('File %s/%s ..' % (task['dir'], ord_file.name))
        ord_data = None
        with ord_file.open(mode='r', encoding='utf-8') as fi:
            ord_data = json.loads(fi.read())
        merking = detect_merking_in_filename(ord_file.name)
        isl_ord = f_lookup(ord_data, merking)
        hr_ord = '"%s"' % (ord_data['orð'], )
        if ord_data['flokkur'] == 'nafnorð':
            hr_ord = '"%s" (%s)' % (ord_data['orð'], ord_data['kyn'])
        if isl_ord is None:
            f_add(ord_data, merking)
            logman.info('Added to %s, %s%s.' % (
                task['name'],
                hr_ord,
                ' [ó]' if 'ósjálfstætt' in ord_data and ord_data['ósjálfstætt'] is True else ''
            ))
        else:
            logman.warning('%s task, %s already exists! Skipping.' % (
                '%s%s' % (task['name'][0].upper(), task['name'][1:]),
                hr_ord
            ))


def detect_merking_in_filename(filename):
    '''
    look for "merking" in filename, for example "lofa" in filename "heita-_lofa_.json"
    if no "merking" then return None
    '''
    match = re.search(r'_([a-zA-ZáÁðÐéÉíÍłŁóÓúÚýÝæÆöÖ]*)_', filename)
    if match is not None:
        return match.group()[1:-1]
    return None



def list_json_files_separate_samsett_ord(file_dir):
    '''
    returns two lists in a tuple, first list contains json files without "samsett" root key,
    second list contains json files with "samsett" root key

    files not with .json ending are ignored
    '''
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



def lookup_nafnord(nafnord_data, merking=None):
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
    osjalfstaett_ord = (
        'ósjálfstætt' in nafnord_data and nafnord_data['ósjálfstætt'] is True
    )
    isl_ord_list = db.Session.query(isl.Ord).filter_by(
        Ord=nafnord_data['orð'],
        Ordflokkur=isl.Ordflokkar.Nafnord,
        OsjalfstaedurOrdhluti=osjalfstaett_ord,
        Merking=merking
    ).all()
    for potential_isl_ord in isl_ord_list:
        isl_nafnord = db.Session.query(isl.Nafnord).filter_by(
            fk_Ord_id=potential_isl_ord.Ord_id
        ).first()
        if isl_nafnord.Kyn == isl_ord_kyn:
            assert(isl_ord is None)  # if/when this fails it means we have counter-example
            isl_ord = potential_isl_ord
    return isl_ord


def add_nafnord(nafnord_data, merking=None):
    '''
    add nafnorð from datafile to database
    '''
    assert('flokkur' in nafnord_data and nafnord_data['flokkur'] == 'nafnorð')
    isl_ord_kyn = string_to_kyn(nafnord_data['kyn'])
    isl_ord = isl.Ord(
        Ord=nafnord_data['orð'],
        Ordflokkur=isl.Ordflokkar.Nafnord,
        OsjalfstaedurOrdhluti=(
            'ósjálfstætt' in nafnord_data and nafnord_data['ósjálfstætt'] is True
        ),
        Merking=merking
    )
    db.Session.add(isl_ord)
    db.Session.commit()
    isl_nafnord = isl.Nafnord(fk_Ord_id=isl_ord.Ord_id, Kyn=isl_ord_kyn)
    db.Session.add(isl_nafnord)
    db.Session.commit()
    if 'samsett' in nafnord_data:
        add_samsett_ord(isl_ord.Ord_id, nafnord_data)
        isl_ord.Samsett = True
        db.Session.commit()
        return isl_ord
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


def lookup_lysingarord(lysingarord_data, merking=None):
    '''
    Assume icelandic lýsingarorð are unique, until we have counter-example.
    '''
    isl_ord = None
    osjalfstaett_ord = (
        'ósjálfstætt' in lysingarord_data and lysingarord_data['ósjálfstætt'] is True
    )
    isl_ord_query = db.Session.query(isl.Ord).filter_by(
        Ord=lysingarord_data['orð'],
        Ordflokkur=isl.Ordflokkar.Lysingarord,
        OsjalfstaedurOrdhluti=osjalfstaett_ord,
        Merking=merking
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


def add_lysingarord(lysingarord_data, merking=None):
    '''
    add lýsingarorð from datafile to database
    '''
    assert('flokkur' in lysingarord_data and lysingarord_data['flokkur'] == 'lýsingarorð')
    isl_ord = isl.Ord(
        Ord=lysingarord_data['orð'],
        Ordflokkur=isl.Ordflokkar.Lysingarord,
        OsjalfstaedurOrdhluti=(
            'ósjálfstætt' in lysingarord_data and lysingarord_data['ósjálfstætt'] is True
        ),
        Merking=merking
    )
    db.Session.add(isl_ord)
    db.Session.commit()
    isl_lysingarord = isl.Lysingarord(fk_Ord_id=isl_ord.Ord_id)
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


def lookup_sagnord(sagnord_data, merking=None):
    '''
    Assume icelandic sagnorð are unique, until we have counter-example.
    '''
    isl_ord = None
    osjalfstaett_ord = (
        'ósjálfstætt' in sagnord_data and sagnord_data['ósjálfstætt'] is True
    )
    isl_ord_query = db.Session.query(isl.Ord).filter_by(
        Ord=sagnord_data['orð'],
        Ordflokkur=isl.Ordflokkar.Sagnord,
        OsjalfstaedurOrdhluti=osjalfstaett_ord,
        Merking=merking
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


def add_sagnord(sagnord_data, merking=None):
    '''
    add sagnorð from datafile to database
    '''
    assert('flokkur' in sagnord_data and sagnord_data['flokkur'] == 'sagnorð')
    isl_ord = isl.Ord(Ord=sagnord_data['orð'], Ordflokkur=isl.Ordflokkar.Sagnord, Merking=merking)
    db.Session.add(isl_ord)
    db.Session.commit()
    isl_sagnord = isl.Sagnord(fk_Ord_id=isl_ord.Ord_id)
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
    if 'óskháttur_1p_ft' in sagnord_data:
        assert(type(sagnord_data['óskháttur_1p_ft']) is str)
        isl_sagnord.Oskhattur_1p_ft = sagnord_data['óskháttur_1p_ft']
        db.Session.commit()
    if 'óskháttur_3p' in sagnord_data:
        assert(type(sagnord_data['óskháttur_3p']) is str)
        isl_sagnord.Oskhattur_3p = sagnord_data['óskháttur_3p']
        db.Session.commit()
    # TODO: add undantekning handling
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
        ["lágstafa": True,]
        "hash": str
    }
    with some additional rules/caveats
    '''
    dictorinos = (dict, collections.OrderedDict)
    samsetningar = ['stofn', 'eignarfalls', 'bandstafs']
    ordflokkar = set([
        'nafnorð',
        'lýsingarorð',
        'greinir',
        'töluorð',
        'fornafn',
        'sagnorð',
        'smáorð',
        'sérnafn'
    ])
    toluord_undirflokkar = set([
        'frumtala',
        'raðtala'
    ])
    fornofn_undirflokkar = set([
        'ábendingar',
        'afturbeygt',
        'eignar',
        'óákveðið',
        'persónu',
        'spurnar'
    ])
    smaord_undirflokkar = set([
        'forsetning',
        'atviksorð',
        'nafnháttarmerki',
        'samtenging',
        'upphrópun'
    ])
    sernofn_undirflokkar = set([
        'eiginnafn',
        'gælunafn',
        'kenninafn',
        'millinafn',
        'örnefni'
    ])
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
    elif ordhluti_obj['flokkur'] == 'töluorð':
        assert('undirflokkur' in ordhluti_obj)
        assert(ordhluti_obj['undirflokkur'] in toluord_undirflokkar)
    elif ordhluti_obj['flokkur'] == 'fornafn':
        assert('undirflokkur' in ordhluti_obj)
        assert(ordhluti_obj['undirflokkur'] in fornofn_undirflokkar)
    elif ordhluti_obj['flokkur'] == 'smáorð':
        assert('undirflokkur' in ordhluti_obj)
        assert(ordhluti_obj['undirflokkur'] in smaord_undirflokkar)
    elif ordhluti_obj['flokkur'] == 'sérnafn':
        assert('undirflokkur' in ordhluti_obj)
        assert(ordhluti_obj['undirflokkur'] in sernofn_undirflokkar)
    assert('hash' in ordhluti_obj)
    assert(type(ordhluti_obj['hash']) is str)
    assert(len(ordhluti_obj['hash']) > 0)
    if last_obj is True and 'mynd' not in ordhluti_obj:
        if ordhluti_obj['flokkur'] != 'sérnafn' and ordflokkur != 'sérnafn':
            assert(ordhluti_obj['flokkur'] == ordflokkur)
    if 'lágstafa' in ordhluti_obj:
        assert(type(ordhluti_obj['lágstafa']) is bool)


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
        ordhluti_osjalfstaett = (
            'ósjálfstætt' in ordhluti_obj and ordhluti_obj['ósjálfstætt'] is True
        )
        ordhluti_lagstafa = (
            'lágstafa' in ordhluti_obj and ordhluti_obj['lágstafa'] is True
        )
        ordhluti_hastafa = (
            'hástafa' in ordhluti_obj and ordhluti_obj['hástafa'] is True
        )
        ordhluti_exclude_et_ag = False
        ordhluti_exclude_et_mg = False
        ordhluti_exclude_ft_ag = False
        ordhluti_exclude_ft_mg = False
        if 'beygingar' in ordhluti_obj:
            ordhluti_exclude_et_ag = True
            ordhluti_exclude_et_mg = True
            ordhluti_exclude_ft_ag = True
            ordhluti_exclude_ft_mg = True
            for beyging_key in ordhluti_obj['beygingar']:
                if beyging_key == 'et-ág':
                    ordhluti_exclude_et_ag = False
                elif beyging_key == 'et-mg':
                    ordhluti_exclude_et_mg = False
                elif beyging_key == 'ft-ág':
                    ordhluti_exclude_ft_ag = False
                elif beyging_key == 'ft-mg':
                    ordhluti_exclude_ft_mg = False
                else:
                    raise Exception('Unexpected beyging key.')
        if 'mynd' in ordhluti_obj:
            if last_ordhluti_obj_id is None and ord_data['flokkur'] == 'lýsingarorð':
                isl_ord = db.Session.query(isl.Ord).filter_by(Ord_id=isl_ord_id).first()
                isl_ord.Obeygjanlegt = True
                db.Session.commit()
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
                'orð': ordhluti_obj['orð'],
                'kyn': ordhluti_obj['kyn'],
                'ósjálfstætt': ordhluti_osjalfstaett
            }, merking=ordhluti_obj['merking'] if 'merking' in ordhluti_obj else None)
        elif ordhluti_obj['flokkur'] == 'lýsingarorð':
            ordhluti_isl_ord = lookup_lysingarord({
                'orð': ordhluti_obj['orð'],
                'ósjálfstætt': ordhluti_osjalfstaett
            }, merking=ordhluti_obj['merking'] if 'merking' in ordhluti_obj else None)
        elif ordhluti_obj['flokkur'] == 'sagnorð':
            ordhluti_isl_ord = lookup_sagnord({
                'orð': ordhluti_obj['orð'],
                'ósjálfstætt': ordhluti_osjalfstaett
            }, merking=ordhluti_obj['merking'] if 'merking' in ordhluti_obj else None)
        elif ordhluti_obj['flokkur'] == 'greinir':
            ordhluti_isl_ord = lookup_greinir({'orð': ordhluti_obj['orð']})
        elif ordhluti_obj['flokkur'] == 'töluorð':
            if ordhluti_obj['undirflokkur'] == 'frumtala':
                ordhluti_isl_ord = lookup_frumtala({'orð': ordhluti_obj['orð']})
            elif ordhluti_obj['undirflokkur'] == 'raðtala':
                ordhluti_isl_ord = lookup_radtala({'orð': ordhluti_obj['orð']})
        elif ordhluti_obj['flokkur'] == 'fornafn':
            ordhluti_isl_ord = lookup_fornafn({
                'orð': ordhluti_obj['orð'],
                'undirflokkur': ordhluti_obj['undirflokkur']
            })
        elif ordhluti_obj['flokkur'] == 'smáorð':
            if ordhluti_obj['undirflokkur'] == 'forsetning':
                ordhluti_isl_ord = lookup_forsetning({
                    'orð': ordhluti_obj['orð'],
                    'undirflokkur': ordhluti_obj['undirflokkur']
                })
            elif ordhluti_obj['undirflokkur'] == 'atviksorð':
                ordhluti_isl_ord = lookup_atviksord({
                    'orð': ordhluti_obj['orð'],
                    'undirflokkur': ordhluti_obj['undirflokkur']
                })
            elif ordhluti_obj['undirflokkur'] == 'nafnháttarmerki':
                ordhluti_isl_ord = lookup_nafnhattarmerki({
                    'orð': ordhluti_obj['orð'],
                    'undirflokkur': ordhluti_obj['undirflokkur']
                })
            elif ordhluti_obj['undirflokkur'] == 'samtenging':
                ordhluti_isl_ord = lookup_samtenging({
                    'orð': ordhluti_obj['orð'],
                    'undirflokkur': ordhluti_obj['undirflokkur']
                })
            elif ordhluti_obj['undirflokkur'] == 'upphrópun':
                ordhluti_isl_ord = lookup_upphropun({
                    'orð': ordhluti_obj['orð'],
                    'undirflokkur': ordhluti_obj['undirflokkur']
                })
        elif ordhluti_obj['flokkur'] == 'sérnafn':
            ordhluti_isl_ord = lookup_sernafn({
                'orð': ordhluti_obj['orð'],
                'undirflokkur': ordhluti_obj['undirflokkur'],
                'kyn': None if 'kyn' not in ordhluti_obj else ordhluti_obj['kyn'],
                'ósjálfstætt': (
                    False if 'ósjálfstætt' not in ordhluti_obj else ordhluti_obj['ósjálfstætt']
                )
            })
        assert(ordhluti_isl_ord is not None)
        isl_ordhluti = db.Session.query(isl.SamsettOrdhlutar).filter_by(
            fk_Ord_id=ordhluti_isl_ord.Ord_id,
            Ordmynd=ordhluti_mynd,
            Gerd=ordhluti_gerd,
            fk_NaestiOrdhluti_id=last_ordhluti_obj_id,
            Lagstafa=ordhluti_lagstafa,
            Hastafa=ordhluti_hastafa,
            Exclude_et_ag=ordhluti_exclude_et_ag,
            Exclude_et_mg=ordhluti_exclude_et_mg,
            Exclude_ft_ag=ordhluti_exclude_ft_ag,
            Exclude_ft_mg=ordhluti_exclude_ft_mg
        ).first()
        # if identical orðhluti doesn't exist then create it
        if isl_ordhluti is None:
            isl_ordhluti = isl.SamsettOrdhlutar(
                fk_Ord_id=ordhluti_isl_ord.Ord_id,
                Ordmynd=ordhluti_mynd,
                Gerd=ordhluti_gerd,
                fk_NaestiOrdhluti_id=last_ordhluti_obj_id,
                Lagstafa=ordhluti_lagstafa,
                Hastafa=ordhluti_hastafa,
                Exclude_et_ag=ordhluti_exclude_et_ag,
                Exclude_et_mg=ordhluti_exclude_et_mg,
                Exclude_ft_ag=ordhluti_exclude_ft_ag,
                Exclude_ft_mg=ordhluti_exclude_ft_mg
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


def lookup_greinir(greinir_data, merking=None):
    isl_ord = None
    isl_ord_query = db.Session.query(isl.Ord).filter_by(
        Ord=greinir_data['orð'],
        Ordflokkur=isl.Ordflokkar.Greinir,
        Merking=merking
    )
    assert(len(isl_ord_query.all()) < 2)
    isl_ord = isl_ord_query.first()
    return isl_ord


def add_greinir(greinir_data, merking=None):
    '''
    add greinir from datafile to database
    '''
    assert('flokkur' in greinir_data and greinir_data['flokkur'] == 'greinir')
    isl_ord = isl.Ord(Ord=greinir_data['orð'], Ordflokkur=isl.Ordflokkar.Greinir, Merking=merking)
    db.Session.add(isl_ord)
    db.Session.commit()
    isl_greinir = isl.Greinir(fk_Ord_id=isl_ord.Ord_id)
    db.Session.add(isl_greinir)
    db.Session.commit()
    if 'et' in greinir_data:
        if 'kk' in greinir_data['et']:
            isl_greinir.fk_et_kk_Fallbeyging_id = add_fallbeyging(greinir_data['et']['kk'])
            db.Session.commit()
        if 'kvk' in greinir_data['et']:
            isl_greinir.fk_et_kvk_Fallbeyging_id = add_fallbeyging(greinir_data['et']['kvk'])
            db.Session.commit()
        if 'hk' in greinir_data['et']:
            isl_greinir.fk_et_hk_Fallbeyging_id = add_fallbeyging(greinir_data['et']['hk'])
            db.Session.commit()
    if 'ft' in greinir_data:
        if 'kk' in greinir_data['et']:
            isl_greinir.fk_ft_kk_Fallbeyging_id = add_fallbeyging(greinir_data['ft']['kk'])
            db.Session.commit()
        if 'kvk' in greinir_data['et']:
            isl_greinir.fk_ft_kvk_Fallbeyging_id = add_fallbeyging(greinir_data['ft']['kvk'])
            db.Session.commit()
        if 'hk' in greinir_data['et']:
            isl_greinir.fk_ft_hk_Fallbeyging_id = add_fallbeyging(greinir_data['ft']['hk'])
            db.Session.commit()
    return isl_ord


def lookup_frumtala(frumtala_data, merking=None):
    isl_ord = None
    isl_ord_query = db.Session.query(isl.Ord).filter_by(
        Ord=frumtala_data['orð'],
        Ordflokkur=isl.Ordflokkar.Frumtala,
        Merking=merking
    )
    assert(len(isl_ord_query.all()) < 2)
    isl_ord = isl_ord_query.first()
    return isl_ord


def add_frumtala(frumtala_data, merking=None):
    '''
    add frumtala from datafile to database
    '''
    assert('flokkur' in frumtala_data and frumtala_data['flokkur'] == 'töluorð')
    assert('undirflokkur' in frumtala_data and frumtala_data['undirflokkur'] == 'frumtala')
    if 'gildi' in frumtala_data:
        assert(type(frumtala_data['gildi']) is int)
    isl_ord = isl.Ord(
        Ord=frumtala_data['orð'],
        Ordflokkur=isl.Ordflokkar.Frumtala,
        Merking=merking
    )
    db.Session.add(isl_ord)
    db.Session.commit()
    isl_frumtala = isl.Frumtala(fk_Ord_id=isl_ord.Ord_id)
    db.Session.add(isl_frumtala)
    db.Session.commit()
    if 'gildi' in frumtala_data:
        isl_frumtala.Gildi = frumtala_data['gildi']
        db.Session.commit()
    if 'samsett' in frumtala_data:
        add_samsett_ord(isl_ord.Ord_id, frumtala_data)
        isl_ord.Samsett = True
        db.Session.commit()
        return isl_ord
    if 'et' in frumtala_data:
        if 'kk' in frumtala_data['et']:
            isl_frumtala.fk_et_kk_Fallbeyging_id = add_fallbeyging(frumtala_data['et']['kk'])
            db.Session.commit()
        if 'kvk' in frumtala_data['et']:
            isl_frumtala.fk_et_kvk_Fallbeyging_id = add_fallbeyging(frumtala_data['et']['kvk'])
            db.Session.commit()
        if 'hk' in frumtala_data['et']:
            isl_frumtala.fk_et_hk_Fallbeyging_id = add_fallbeyging(frumtala_data['et']['hk'])
            db.Session.commit()
    if 'ft' in frumtala_data:
        if 'kk' in frumtala_data['ft']:
            isl_frumtala.fk_ft_kk_Fallbeyging_id = add_fallbeyging(frumtala_data['ft']['kk'])
            db.Session.commit()
        if 'kvk' in frumtala_data['ft']:
            isl_frumtala.fk_ft_kvk_Fallbeyging_id = add_fallbeyging(frumtala_data['ft']['kvk'])
            db.Session.commit()
        if 'hk' in frumtala_data['ft']:
            isl_frumtala.fk_ft_hk_Fallbeyging_id = add_fallbeyging(frumtala_data['ft']['hk'])
            db.Session.commit()
    return isl_ord


def lookup_radtala(radtala_data, merking=None):
    isl_ord = None
    isl_ord_query = db.Session.query(isl.Ord).filter_by(
        Ord=radtala_data['orð'],
        Ordflokkur=isl.Ordflokkar.Radtala,
        Merking=merking
    )
    assert(len(isl_ord_query.all()) < 2)
    isl_ord = isl_ord_query.first()
    return isl_ord


def add_radtala(radtala_data, merking=None):
    '''
    add raðtala from datafile to database
    '''
    assert('flokkur' in radtala_data and radtala_data['flokkur'] == 'töluorð')
    assert('undirflokkur' in radtala_data and radtala_data['undirflokkur'] == 'raðtala')
    if 'gildi' in radtala_data:
        assert(type(radtala_data['gildi']) is int)
    isl_ord = isl.Ord(Ord=radtala_data['orð'], Ordflokkur=isl.Ordflokkar.Radtala, Merking=merking)
    db.Session.add(isl_ord)
    db.Session.commit()
    isl_radtala = isl.Radtala(fk_Ord_id=isl_ord.Ord_id)
    db.Session.add(isl_radtala)
    db.Session.commit()
    if 'gildi' in radtala_data:
        isl_radtala.Gildi = radtala_data['gildi']
        db.Session.commit()
    if 'samsett' in radtala_data:
        add_samsett_ord(isl_ord.Ord_id, radtala_data)
        isl_ord.Samsett = True
        db.Session.commit()
        return isl_ord
    if 'sb' in radtala_data:
        if 'et' in radtala_data['sb']:
            if 'kk' in radtala_data['sb']['et']:
                isl_radtala.fk_sb_et_kk_Fallbeyging_id = add_fallbeyging(
                    radtala_data['sb']['et']['kk']
                )
                db.Session.commit()
            if 'kvk' in radtala_data['sb']['et']:
                isl_radtala.fk_sb_et_kvk_Fallbeyging_id = add_fallbeyging(
                    radtala_data['sb']['et']['kvk']
                )
                db.Session.commit()
            if 'hk' in radtala_data['sb']['et']:
                isl_radtala.fk_sb_et_hk_Fallbeyging_id = add_fallbeyging(
                    radtala_data['sb']['et']['hk']
                )
                db.Session.commit()
        if 'ft' in radtala_data['sb']:
            if 'kk' in radtala_data['sb']['ft']:
                isl_radtala.fk_sb_ft_kk_Fallbeyging_id = add_fallbeyging(
                    radtala_data['sb']['ft']['kk']
                )
                db.Session.commit()
            if 'kvk' in radtala_data['sb']['ft']:
                isl_radtala.fk_sb_ft_kvk_Fallbeyging_id = add_fallbeyging(
                    radtala_data['sb']['ft']['kvk']
                )
                db.Session.commit()
            if 'hk' in radtala_data['sb']['ft']:
                isl_radtala.fk_sb_ft_hk_Fallbeyging_id = add_fallbeyging(
                    radtala_data['sb']['ft']['hk']
                )
                db.Session.commit()
    if 'vb' in radtala_data:
        if 'et' in radtala_data['vb']:
            if 'kk' in radtala_data['vb']['et']:
                isl_radtala.fk_vb_et_kk_Fallbeyging_id = add_fallbeyging(
                    radtala_data['vb']['et']['kk']
                )
                db.Session.commit()
            if 'kvk' in radtala_data['vb']['et']:
                isl_radtala.fk_vb_et_kvk_Fallbeyging_id = add_fallbeyging(
                    radtala_data['vb']['et']['kvk']
                )
                db.Session.commit()
            if 'hk' in radtala_data['vb']['et']:
                isl_radtala.fk_vb_et_hk_Fallbeyging_id = add_fallbeyging(
                    radtala_data['vb']['et']['hk']
                )
                db.Session.commit()
        if 'ft' in radtala_data['vb']:
            if 'kk' in radtala_data['vb']['ft']:
                isl_radtala.fk_vb_ft_kk_Fallbeyging_id = add_fallbeyging(
                    radtala_data['vb']['ft']['kk']
                )
                db.Session.commit()
            if 'kvk' in radtala_data['vb']['ft']:
                isl_radtala.fk_vb_ft_kvk_Fallbeyging_id = add_fallbeyging(
                    radtala_data['vb']['ft']['kvk']
                )
                db.Session.commit()
            if 'hk' in radtala_data['vb']['ft']:
                isl_radtala.fk_vb_ft_hk_Fallbeyging_id = add_fallbeyging(
                    radtala_data['vb']['ft']['hk']
                )
                db.Session.commit()
    return isl_ord


def lookup_fornafn(fornafn_data, merking=None):
    isl_ord = None
    isl_fornafn_undirflokkur = string_to_fornafn_undirordflokkur(fornafn_data['undirflokkur'])
    isl_ord_list = db.Session.query(isl.Ord).filter_by(
        Ord=fornafn_data['orð'],
        Ordflokkur=isl.Ordflokkar.Fornafn,
        Merking=merking
    ).all()
    for potential_isl_ord in isl_ord_list:
        isl_fornafn = db.Session.query(isl.Fornafn).filter_by(
            fk_Ord_id=potential_isl_ord.Ord_id
        ).first()
        if isl_fornafn.Undirflokkur == isl_fornafn_undirflokkur:
            assert(isl_ord is None)  # check for duplicate word
            isl_ord = potential_isl_ord
    return isl_ord


def add_fornafn(fornafn_data, merking=None):
    '''
    add fornafn from datafile to database
    '''
    dictorinos = (dict, collections.OrderedDict)
    assert('flokkur' in fornafn_data and fornafn_data['flokkur'] == 'fornafn')
    undirflokkur = string_to_fornafn_undirordflokkur(fornafn_data['undirflokkur'])
    isl_ord = isl.Ord(Ord=fornafn_data['orð'], Ordflokkur=isl.Ordflokkar.Fornafn, Merking=merking)
    db.Session.add(isl_ord)
    db.Session.commit()
    isl_fornafn = isl.Fornafn(fk_Ord_id=isl_ord.Ord_id, Undirflokkur=undirflokkur)
    db.Session.add(isl_fornafn)
    db.Session.commit()
    if 'persóna' in fornafn_data:
        isl_fornafn.Persona = string_to_persona(fornafn_data['persóna'])
        db.Session.commit()
    if 'kyn' in fornafn_data:
        isl_fornafn.Kyn = string_to_kyn(fornafn_data['kyn'])
        db.Session.commit()
    if 'samsett' in fornafn_data:
        add_samsett_ord(isl_ord.Ord_id, fornafn_data)
        isl_ord.Samsett = True
        db.Session.commit()
        return isl_ord
    if 'et' in fornafn_data:
        if type(fornafn_data['et']) is list:
            isl_fornafn.fk_et_Fallbeyging_id = add_fallbeyging(
                fornafn_data['et']
            )
            db.Session.commit()
        elif type(fornafn_data['et']) in dictorinos:
            if 'kk' in fornafn_data['et']:
                isl_fornafn.fk_et_kk_Fallbeyging_id = add_fallbeyging(
                    fornafn_data['et']['kk']
                )
                db.Session.commit()
            if 'kvk' in fornafn_data['et']:
                isl_fornafn.fk_et_kvk_Fallbeyging_id = add_fallbeyging(
                    fornafn_data['et']['kvk']
                )
                db.Session.commit()
            if 'hk' in fornafn_data['et']:
                isl_fornafn.fk_et_hk_Fallbeyging_id = add_fallbeyging(
                    fornafn_data['et']['hk']
                )
                db.Session.commit()
    if 'ft' in fornafn_data:
        if type(fornafn_data['ft']) is list:
            isl_fornafn.fk_ft_Fallbeyging_id = add_fallbeyging(
                fornafn_data['ft']
            )
            db.Session.commit()
        elif type(fornafn_data['ft']) in dictorinos:
            if 'kk' in fornafn_data['ft']:
                isl_fornafn.fk_ft_kk_Fallbeyging_id = add_fallbeyging(
                    fornafn_data['ft']['kk']
                )
                db.Session.commit()
            if 'kvk' in fornafn_data['ft']:
                isl_fornafn.fk_ft_kvk_Fallbeyging_id = add_fallbeyging(
                    fornafn_data['ft']['kvk']
                )
                db.Session.commit()
            if 'hk' in fornafn_data['ft']:
                isl_fornafn.fk_ft_hk_Fallbeyging_id = add_fallbeyging(
                    fornafn_data['ft']['hk']
                )
                db.Session.commit()
    return isl_ord


def string_to_fornafn_undirordflokkur(mystr):
    if mystr == 'ábendingar':
        return isl.Fornafnaflokkar.Abendingarfornafn
    elif mystr == 'afturbeygt':
        return isl.Fornafnaflokkar.AfturbeygtFornafn
    elif mystr == 'eignar':
        return isl.Fornafnaflokkar.Eignarfornafn
    elif mystr == 'óákveðið':
        return isl.Fornafnaflokkar.OakvedidFornafn
    elif mystr == 'persónu':
        return isl.Fornafnaflokkar.Personufornafn
    elif mystr == 'spurnar':
        return isl.Fornafnaflokkar.Spurnarfornafn
    raise Exception('Unknown undirorðflokkur.')


def string_to_persona(mystr):
    if mystr == 'fyrsta':
        return isl.Persona.Fyrsta
    elif mystr == 'önnur':
        return isl.Persona.Onnur
    elif mystr == 'þriðja':
        return isl.Persona.Thridja
    raise Exception('Unknown persóna.')


def string_to_kyn(mystr):
    if mystr == 'kk':
        return isl.Kyn.Karlkyn
    elif mystr == 'kvk':
        return isl.Kyn.Kvenkyn
    elif mystr == 'hk':
        return isl.Kyn.Hvorugkyn
    raise Exception('Unknown kyn.')


def lookup_forsetning(forsetning_data, merking=None):
    isl_ord = None
    isl_ord_query = db.Session.query(isl.Ord).filter_by(
        Ord=forsetning_data['orð'],
        Ordflokkur=isl.Ordflokkar.Forsetning,
        Merking=merking
    )
    assert(len(isl_ord_query.all()) < 2)
    isl_ord = isl_ord_query.first()
    return isl_ord


def add_forsetning(forsetning_data, merking=None):
    assert('flokkur' in forsetning_data and forsetning_data['flokkur'] == 'smáorð')
    assert('undirflokkur' in forsetning_data and forsetning_data['undirflokkur'] == 'forsetning')
    assert('stýrir' in forsetning_data and type(forsetning_data['stýrir']) is list)
    assert(len(forsetning_data['stýrir']) > 0)
    isl_ord = isl.Ord(
        Ord=forsetning_data['orð'],
        Ordflokkur=isl.Ordflokkar.Forsetning,
        Merking=merking
    )
    db.Session.add(isl_ord)
    db.Session.commit()
    isl_forsetning = isl.Forsetning(fk_Ord_id=isl_ord.Ord_id)
    db.Session.add(isl_forsetning)
    db.Session.commit()
    for fall in forsetning_data['stýrir']:
        if fall == 'þolfall':
            isl_forsetning.StyrirTholfalli = True
        elif fall == 'þágufall':
            isl_forsetning.StyrirThagufalli = True
        elif fall == 'eignarfall':
            isl_forsetning.StyrirEignarfalli = True
        else:
            raise Exception('Unknown aukafall.')
    db.Session.commit()
    return isl_ord


def lookup_atviksord(atviksord_data, merking=None):
    isl_ord = None
    isl_ord_query = db.Session.query(isl.Ord).filter_by(
        Ord=atviksord_data['orð'],
        Ordflokkur=isl.Ordflokkar.Atviksord,
        Merking=merking
    )
    assert(len(isl_ord_query.all()) < 2)
    isl_ord = isl_ord_query.first()
    return isl_ord


def add_atviksord(atviksord_data, merking=None):
    assert('flokkur' in atviksord_data and atviksord_data['flokkur'] == 'smáorð')
    assert('undirflokkur' in atviksord_data and atviksord_data['undirflokkur'] == 'atviksorð')
    isl_ord = isl.Ord(
        Ord=atviksord_data['orð'],
        Ordflokkur=isl.Ordflokkar.Atviksord,
        Merking=merking
    )
    db.Session.add(isl_ord)
    db.Session.commit()
    if 'miðstig' in atviksord_data or 'efstastig' in atviksord_data:
        assert('miðstig' in atviksord_data)
        assert('efstastig' in atviksord_data)
        isl_atviksord = isl.Atviksord(fk_Ord_id=isl_ord.Ord_id)
        db.Session.add(isl_atviksord)
        db.Session.commit()
        isl_atviksord.Midstig = atviksord_data['miðstig']
        isl_atviksord.Efstastig = atviksord_data['efstastig']
        db.Session.commit()
    return isl_ord


def lookup_nafnhattarmerki(nafnhattarmerki_data, merking=None):
    isl_ord = None
    isl_ord_query = db.Session.query(isl.Ord).filter_by(
        Ord=nafnhattarmerki_data['orð'],
        Ordflokkur=isl.Ordflokkar.Nafnhattarmerki,
        Merking=merking
    )
    assert(len(isl_ord_query.all()) < 2)
    isl_ord = isl_ord_query.first()
    return isl_ord


def add_nafnhattarmerki(nafnhattarmerki_data, merking=None):
    assert('flokkur' in nafnhattarmerki_data and nafnhattarmerki_data['flokkur'] == 'smáorð')
    assert(
        'undirflokkur' in nafnhattarmerki_data and
        nafnhattarmerki_data['undirflokkur'] == 'nafnháttarmerki'
    )
    isl_ord = isl.Ord(
        Ord=nafnhattarmerki_data['orð'],
        Ordflokkur=isl.Ordflokkar.Nafnhattarmerki,
        Merking=merking
    )
    db.Session.add(isl_ord)
    db.Session.commit()
    return isl_ord


def lookup_samtenging(samtenging_data, merking=None):
    isl_ord = None
    isl_ord_query = db.Session.query(isl.Ord).filter_by(
        Ord=samtenging_data['orð'],
        Ordflokkur=isl.Ordflokkar.Samtenging,
        Merking=merking
    )
    assert(len(isl_ord_query.all()) < 2)
    isl_ord = isl_ord_query.first()
    return isl_ord


def add_samtenging(samtenging_data, merking=None):
    assert('flokkur' in samtenging_data and samtenging_data['flokkur'] == 'smáorð')
    assert('undirflokkur' in samtenging_data and samtenging_data['undirflokkur'] == 'samtenging')
    isl_ord = isl.Ord(
        Ord=samtenging_data['orð'],
        Ordflokkur=isl.Ordflokkar.Samtenging,
        Merking=merking
    )
    db.Session.add(isl_ord)
    db.Session.commit()
    if 'fleiryrt' in samtenging_data:
        assert(type(samtenging_data['fleiryrt']) is list)
        for fleiryrt_option in samtenging_data['fleiryrt']:
            first_word = True
            assert('týpa' in fleiryrt_option)
            assert('fylgiorð' in fleiryrt_option and type(fleiryrt_option['fylgiorð']) is list)
            last_samtenging_fleiryrt_id = None
            for fylgiord in fleiryrt_option['fylgiorð']:
                assert(type(fylgiord) is str and len(fylgiord) > 0)
                isl_ord_id = None
                fleiryrt_typa = None
                if first_word is True:
                    isl_ord_id = isl_ord.Ord_id
                    fleiryrt_typa = string_to_samtenging_fleiryrt_typa(fleiryrt_option['týpa'])
                isl_samtenging_fleiryrt = isl.SamtengingFleiryrt(
                    fk_Ord_id=isl_ord_id,
                    Ord=fylgiord,
                    fk_SamtengingFleiryrt_id=last_samtenging_fleiryrt_id,
                    Typa=fleiryrt_typa
                )
                db.Session.add(isl_samtenging_fleiryrt)
                db.Session.commit()
                first_word = False
                last_samtenging_fleiryrt_id = isl_samtenging_fleiryrt.SamtengingFleiryrt_id
    return isl_ord


def string_to_samtenging_fleiryrt_typa(mystr):
    if mystr == 'hlekkjuð':
        return isl.FleiryrtTypa.Hlekkjud
    elif mystr == 'laus':
        return isl.FleiryrtTypa.Laus
    else:
        raise Exception('Unknown SamtengingFleiryrtTypa.')


def lookup_upphropun(upphropun_data, merking=None):
    isl_ord = None
    isl_ord_query = db.Session.query(isl.Ord).filter_by(
        Ord=upphropun_data['orð'],
        Ordflokkur=isl.Ordflokkar.Upphropun,
        Merking=merking
    )
    assert(len(isl_ord_query.all()) < 2)
    isl_ord = isl_ord_query.first()
    return isl_ord


def add_upphropun(upphropun_data, merking=None):
    assert('flokkur' in upphropun_data and upphropun_data['flokkur'] == 'smáorð')
    assert('undirflokkur' in upphropun_data and upphropun_data['undirflokkur'] == 'upphrópun')
    isl_ord = isl.Ord(
        Ord=upphropun_data['orð'],
        Ordflokkur=isl.Ordflokkar.Upphropun,
        Merking=merking
    )
    db.Session.add(isl_ord)
    db.Session.commit()
    return isl_ord


def lookup_sernafn(sernafn_data, merking=None):
    '''
    Assume icelandic sérnafn normal form plus sérnafn undirflokkur plus gender are unique, until we
    have counter-example.
    '''
    isl_ord = None
    sernafn_kyn = None
    if 'kyn' in sernafn_data and sernafn_data['kyn'] is not None:
        sernafn_kyn = string_to_kyn(sernafn_data['kyn'])
    sernafn_flokkur = string_to_sernafn_undirflokkur(sernafn_data['undirflokkur'])
    osjalfstaett_ord = (
        'ósjálfstætt' in sernafn_data and sernafn_data['ósjálfstætt'] is True
    )
    isl_ord_list = db.Session.query(isl.Ord).filter_by(
        Ord=sernafn_data['orð'],
        Ordflokkur=isl.Ordflokkar.Sernafn,
        OsjalfstaedurOrdhluti=osjalfstaett_ord,
        Merking=merking
    ).all()
    for potential_isl_ord in isl_ord_list:
        isl_sernafn = db.Session.query(isl.Sernafn).filter_by(
            fk_Ord_id=potential_isl_ord.Ord_id
        ).first()
        if isl_sernafn.Undirflokkur == sernafn_flokkur and isl_sernafn.Kyn == sernafn_kyn:
            assert(isl_ord is None)  # if/when this fails it means we have counter-example
            isl_ord = potential_isl_ord
    return isl_ord


def add_sernafn(sernafn_data, merking=None):
    assert('flokkur' in sernafn_data and sernafn_data['flokkur'] == 'sérnafn')
    sernafn_kyn = None
    if 'kyn' in sernafn_data and sernafn_data['kyn'] is not None:
        sernafn_kyn = string_to_kyn(sernafn_data['kyn'])
    sernafn_flokkur = string_to_sernafn_undirflokkur(sernafn_data['undirflokkur'])
    isl_ord = isl.Ord(
        Ord=sernafn_data['orð'],
        Ordflokkur=isl.Ordflokkar.Sernafn,
        OsjalfstaedurOrdhluti=(
            'ósjálfstætt' in sernafn_data and sernafn_data['ósjálfstætt'] is True
        ),
        Merking=merking
    )
    db.Session.add(isl_ord)
    db.Session.commit()
    isl_sernafn = isl.Sernafn(
        fk_Ord_id=isl_ord.Ord_id, Undirflokkur=sernafn_flokkur, Kyn=sernafn_kyn
    )
    db.Session.add(isl_sernafn)
    db.Session.commit()
    if 'samsett' in sernafn_data:
        add_samsett_ord(isl_ord.Ord_id, sernafn_data)
        isl_ord.Samsett = True
        db.Session.commit()
        return isl_ord
    if 'et' in sernafn_data:
        if 'ág' in sernafn_data['et']:
            isl_sernafn.fk_et_Fallbeyging_id = add_fallbeyging(sernafn_data['et']['ág'])
            db.Session.commit()
        if 'mg' in sernafn_data['et']:
            isl_sernafn.fk_et_mgr_Fallbeyging_id = add_fallbeyging(sernafn_data['et']['mg'])
            db.Session.commit()
    if 'ft' in sernafn_data:
        if 'ág' in sernafn_data['ft']:
            isl_sernafn.fk_ft_Fallbeyging_id = add_fallbeyging(sernafn_data['ft']['ág'])
            db.Session.commit()
        if 'mg' in sernafn_data['ft']:
            isl_sernafn.fk_ft_mgr_Fallbeyging_id = add_fallbeyging(sernafn_data['ft']['mg'])
            db.Session.commit()
    return isl_ord


def string_to_sernafn_undirflokkur(mystr):
    if mystr == 'eiginnafn':
        return isl.Sernafnaflokkar.Eiginnafn
    elif mystr == 'gælunafn':
        return isl.Sernafnaflokkar.Gaelunafn
    elif mystr == 'kenninafn':
        return isl.Sernafnaflokkar.Kenninafn
    elif mystr == 'millinafn':
        return isl.Sernafnaflokkar.Millinafn
    elif mystr == 'örnefni':
        return isl.Sernafnaflokkar.Ornefni
    else:
        raise Exception('Unknown Sérnafn Undirflokkur.')
