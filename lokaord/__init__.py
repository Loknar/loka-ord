#!/usr/bin/python
import collections
import hashlib
import json
import os
import pathlib
import sys

from lokaord.database import db
from lokaord.database.models import isl
from lokaord import logman

__version__ = "0.0.1"

ArgParser = None


class MyJSONEncoder(json.JSONEncoder):
    '''
    custom hacky json encoder for doing some custom json indentation
    '''
    def iterencode(self, o, _one_shot=False):
        list_lvl = 0
        for s in super(MyJSONEncoder, self).iterencode(o, _one_shot=_one_shot):
            if s.startswith('['):
                list_lvl += 1
                s = ''.join([x.strip() for x in s.split('\n')])
            elif 0 < list_lvl:
                s = ''.join([x.strip() for x in s.split('\n')])
                if s and s.startswith(','):
                    s = ', ' + s[1:]
            if s.endswith(']'):
                list_lvl -= 1
            yield s


def print_help_and_exit():
    if ArgParser is not None:
        ArgParser.print_help(sys.stderr)
    else:
        logman.error('Exiting ..')
    sys.exit(1)


def build_db_from_datafiles():
    logman.info('Building database from datafiles ..')
    datafiles_dir_abs = os.path.abspath(
        os.path.join(os.path.dirname(os.path.realpath(__file__)), 'database', 'data')
    )
    # nafnorð
    logman.info('Reading "nafnorð" datafiles ..')
    nafnord_dir = os.path.join(datafiles_dir_abs, 'nafnord')
    for nafnord_file in sorted(pathlib.Path(nafnord_dir).iterdir()):
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
    # lýsingarorð
    logman.info('Reading "lýsingarorð" datafiles ..')
    lysingarord_dir = os.path.join(datafiles_dir_abs, 'lysingarord')
    for lysingarord_file in sorted(pathlib.Path(lysingarord_dir).iterdir()):
        assert(lysingarord_file.is_file())
        assert(lysingarord_file.name.endswith('.json'))
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
    # sagnorð
    # fleiri orð
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
    # TODO: add samsett/undantekning handling


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


def write_datafiles_from_db():
    logman.info('Writing datafiles from database ..')
    datafiles_dir_abs = os.path.abspath(
        os.path.join(os.path.dirname(os.path.realpath(__file__)), 'database', 'data')
    )
    isl_ord_id_to_hash = {}
    hash_to_isl_ord_id = {}
    # nafnorð
    isl_ord_nafnord_list = db.Session.query(isl.Ord).filter_by(
        Ordflokkur=isl.Ordflokkar.Nafnord,
        Samsett=False
    ).order_by(isl.Ord.Ord, isl.Ord.Ord_id).all()
    for isl_ord_nafnord in isl_ord_nafnord_list:
        nafnord_data = get_nafnord_from_db_to_ordered_dict(isl_ord_nafnord)
        nafnord_data_hash = hashlib.sha256(
            json.dumps(
                nafnord_data, separators=(',', ':'), ensure_ascii=False, sort_keys=True
            ).encode('utf-8')
        ).hexdigest()
        # ensure unique nafnord_data_hash
        if nafnord_data_hash in hash_to_isl_ord_id:
            counter = 0
            nafnord_data_hash_incr = '%s_%s' % (nafnord_data_hash, hex(counter)[2:])
            while nafnord_data_hash_incr in hash_to_isl_ord_id:
                counter += 1
                nafnord_data_hash_incr = '%s_%s' % (nafnord_data_hash, hex(counter)[2:])
            nafnord_data_hash = nafnord_data_hash_incr
        hash_to_isl_ord_id[nafnord_data_hash] = isl_ord_nafnord.Ord_id
        isl_ord_id_to_hash[str(isl_ord_nafnord.Ord_id)] = nafnord_data_hash
        nafnord_data['hash'] = nafnord_data_hash
        nafnord_data_json_str = json.dumps(
            nafnord_data, indent='\t', ensure_ascii=False, separators=(',', ': '),
            cls=MyJSONEncoder
        )
        isl_ord_nafnord_filename = '%s-%s.json' % (nafnord_data['orð'], nafnord_data['kyn'])
        with open(
            os.path.join(datafiles_dir_abs, 'nafnord', isl_ord_nafnord_filename),
            mode='w',
            encoding='utf-8'
        ) as json_file:
            json_file.write(nafnord_data_json_str)
            logman.info('Wrote file "nafnord/%s' % (isl_ord_nafnord_filename, ))
    # lýsingarorð
    isl_ord_lysingarord_list = db.Session.query(isl.Ord).filter_by(
        Ordflokkur=isl.Ordflokkar.Lysingarord,
        Samsett=False
    ).order_by(isl.Ord.Ord, isl.Ord.Ord_id).all()
    for isl_ord_lysingarord in isl_ord_lysingarord_list:
        lysingarord_data = get_lysingarord_from_db_to_ordered_dict(isl_ord_lysingarord)
        lysingarord_data_hash = hashlib.sha256(
            json.dumps(
                lysingarord_data, separators=(',', ':'), ensure_ascii=False, sort_keys=True
            ).encode('utf-8')
        ).hexdigest()
        # ensure unique lysingarord_data_hash
        if lysingarord_data_hash in hash_to_isl_ord_id:
            counter = 0
            lysingarord_data_hash_incr = '%s_%s' % (lysingarord_data_hash, hex(counter)[2:])
            while lysingarord_data_hash_incr in hash_to_isl_ord_id:
                counter += 1
                lysingarord_data_hash_incr = '%s_%s' % (lysingarord_data_hash, hex(counter)[2:])
            lysingarord_data_hash = lysingarord_data_hash_incr
        hash_to_isl_ord_id[lysingarord_data_hash] = isl_ord_lysingarord.Ord_id
        isl_ord_id_to_hash[str(isl_ord_lysingarord.Ord_id)] = lysingarord_data_hash
        lysingarord_data['hash'] = lysingarord_data_hash
        lysingarord_data_json_str = json.dumps(
            lysingarord_data, indent='\t', ensure_ascii=False, separators=(',', ': '),
            cls=MyJSONEncoder
        )
        isl_ord_lysingarord_filename = '%s.json' % (lysingarord_data['orð'], )
        with open(
            os.path.join(datafiles_dir_abs, 'lysingarord', isl_ord_lysingarord_filename),
            mode='w',
            encoding='utf-8'
        ) as json_file:
            json_file.write(lysingarord_data_json_str)
            logman.info('Wrote file "lysingarord/%s' % (isl_ord_lysingarord_filename, ))

    # sagnorð
    # fleiri orð
    logman.info('TODO: finish implementing write_datafiles_from_db')
    return


def get_nafnord_from_db_to_ordered_dict(isl_ord):
    data = collections.OrderedDict()
    data['orð'] = isl_ord.Ord
    data['flokkur'] = 'nafnorð'
    isl_nafnord_list = db.Session.query(isl.Nafnord).filter_by(
        fk_Ord_id=isl_ord.Ord_id
    )
    assert(len(isl_nafnord_list.all()) < 2)
    isl_nafnord = isl_nafnord_list.first()
    assert(isl_nafnord is not None)
    data['kyn'] = None
    if isl_nafnord.Kyn is isl.Kyn.Karlkyn:
        data['kyn'] = 'kk'
    elif isl_nafnord.Kyn is isl.Kyn.Kvenkyn:
        data['kyn'] = 'kvk'
    elif isl_nafnord.Kyn is isl.Kyn.Hvorugkyn:
        data['kyn'] = 'hk'
    if (
        isl_nafnord.fk_et_Fallbeyging_id is not None or
        isl_nafnord.fk_et_mgr_Fallbeyging_id
    ):
        data['et'] = collections.OrderedDict()
    if isl_nafnord.fk_et_Fallbeyging_id is not None:
        data['et']['ág'] = get_fallbeyging_list_from_db(
            isl_nafnord.fk_et_Fallbeyging_id
        )
    if isl_nafnord.fk_et_mgr_Fallbeyging_id is not None:
        data['et']['mg'] = get_fallbeyging_list_from_db(
            isl_nafnord.fk_et_mgr_Fallbeyging_id
        )
    if (
        isl_nafnord.fk_ft_Fallbeyging_id is not None or
        isl_nafnord.fk_ft_mgr_Fallbeyging_id is not None
    ):
        data['ft'] = collections.OrderedDict()
    if isl_nafnord.fk_ft_Fallbeyging_id is not None:
        data['ft']['ág'] = get_fallbeyging_list_from_db(
            isl_nafnord.fk_ft_Fallbeyging_id
        )
    if isl_nafnord.fk_ft_mgr_Fallbeyging_id is not None:
        data['ft']['mg'] = get_fallbeyging_list_from_db(
            isl_nafnord.fk_ft_mgr_Fallbeyging_id
        )
    return data


def get_lysingarord_from_db_to_ordered_dict(isl_ord):
    data = collections.OrderedDict()
    data['orð'] = isl_ord.Ord
    data['flokkur'] = 'lýsingarorð'
    isl_lysingarord_list = db.Session.query(isl.Lysingarord).filter_by(
        fk_Ord_id=isl_ord.Ord_id
    )
    assert(len(isl_lysingarord_list.all()) < 2)
    isl_lysingarord = isl_lysingarord_list.first()
    assert(isl_lysingarord is not None)
    # setup data dict
    if (
        isl_lysingarord.fk_Frumstig_sb_et_kk_Fallbeyging_id is not None or
        isl_lysingarord.fk_Frumstig_sb_et_kvk_Fallbeyging_id is not None or
        isl_lysingarord.fk_Frumstig_sb_et_hk_Fallbeyging_id is not None or
        isl_lysingarord.fk_Frumstig_sb_ft_kk_Fallbeyging_id is not None or
        isl_lysingarord.fk_Frumstig_sb_ft_kvk_Fallbeyging_id is not None or
        isl_lysingarord.fk_Frumstig_sb_ft_hk_Fallbeyging_id is not None or
        isl_lysingarord.fk_Frumstig_vb_et_kk_Fallbeyging_id is not None or
        isl_lysingarord.fk_Frumstig_vb_et_kvk_Fallbeyging_id is not None or
        isl_lysingarord.fk_Frumstig_vb_et_hk_Fallbeyging_id is not None or
        isl_lysingarord.fk_Frumstig_vb_ft_kk_Fallbeyging_id is not None or
        isl_lysingarord.fk_Frumstig_vb_ft_kvk_Fallbeyging_id is not None or
        isl_lysingarord.fk_Frumstig_vb_ft_hk_Fallbeyging_id is not None
    ):
        data['frumstig'] = collections.OrderedDict()
    if (
        isl_lysingarord.fk_Frumstig_sb_et_kk_Fallbeyging_id is not None or
        isl_lysingarord.fk_Frumstig_sb_et_kvk_Fallbeyging_id is not None or
        isl_lysingarord.fk_Frumstig_sb_et_hk_Fallbeyging_id is not None or
        isl_lysingarord.fk_Frumstig_sb_ft_kk_Fallbeyging_id is not None or
        isl_lysingarord.fk_Frumstig_sb_ft_kvk_Fallbeyging_id is not None or
        isl_lysingarord.fk_Frumstig_sb_ft_hk_Fallbeyging_id is not None
    ):
        data['frumstig']['sb'] = collections.OrderedDict()
    if (
        isl_lysingarord.fk_Frumstig_sb_et_kk_Fallbeyging_id is not None or
        isl_lysingarord.fk_Frumstig_sb_et_kvk_Fallbeyging_id is not None or
        isl_lysingarord.fk_Frumstig_sb_et_hk_Fallbeyging_id is not None
    ):
        data['frumstig']['sb']['et'] = collections.OrderedDict()
    if (
        isl_lysingarord.fk_Frumstig_sb_ft_kk_Fallbeyging_id is not None or
        isl_lysingarord.fk_Frumstig_sb_ft_kvk_Fallbeyging_id is not None or
        isl_lysingarord.fk_Frumstig_sb_ft_hk_Fallbeyging_id is not None
    ):
        data['frumstig']['sb']['ft'] = collections.OrderedDict()
    if (
        isl_lysingarord.fk_Frumstig_vb_et_kk_Fallbeyging_id is not None or
        isl_lysingarord.fk_Frumstig_vb_et_kvk_Fallbeyging_id is not None or
        isl_lysingarord.fk_Frumstig_vb_et_hk_Fallbeyging_id is not None or
        isl_lysingarord.fk_Frumstig_vb_ft_kk_Fallbeyging_id is not None or
        isl_lysingarord.fk_Frumstig_vb_ft_kvk_Fallbeyging_id is not None or
        isl_lysingarord.fk_Frumstig_vb_ft_hk_Fallbeyging_id is not None
    ):
        data['frumstig']['vb'] = collections.OrderedDict()
    if (
        isl_lysingarord.fk_Frumstig_vb_et_kk_Fallbeyging_id is not None or
        isl_lysingarord.fk_Frumstig_vb_et_kvk_Fallbeyging_id is not None or
        isl_lysingarord.fk_Frumstig_vb_et_hk_Fallbeyging_id is not None
    ):
        data['frumstig']['vb']['et'] = collections.OrderedDict()
    if (
        isl_lysingarord.fk_Frumstig_vb_ft_kk_Fallbeyging_id is not None or
        isl_lysingarord.fk_Frumstig_vb_ft_kvk_Fallbeyging_id is not None or
        isl_lysingarord.fk_Frumstig_vb_ft_hk_Fallbeyging_id is not None
    ):
        data['frumstig']['vb']['ft'] = collections.OrderedDict()
    if (
        isl_lysingarord.fk_Midstig_vb_et_kk_Fallbeyging_id is not None or
        isl_lysingarord.fk_Midstig_vb_et_kvk_Fallbeyging_id is not None or
        isl_lysingarord.fk_Midstig_vb_et_hk_Fallbeyging_id is not None or
        isl_lysingarord.fk_Midstig_vb_ft_kk_Fallbeyging_id is not None or
        isl_lysingarord.fk_Midstig_vb_ft_kvk_Fallbeyging_id is not None or
        isl_lysingarord.fk_Midstig_vb_ft_hk_Fallbeyging_id is not None
    ):
        data['miðstig'] = collections.OrderedDict()
        data['miðstig']['vb'] = collections.OrderedDict()
    if (
        isl_lysingarord.fk_Midstig_vb_et_kk_Fallbeyging_id is not None or
        isl_lysingarord.fk_Midstig_vb_et_kvk_Fallbeyging_id is not None or
        isl_lysingarord.fk_Midstig_vb_et_hk_Fallbeyging_id is not None
    ):
        data['miðstig']['vb']['et'] = collections.OrderedDict()
    if (
        isl_lysingarord.fk_Midstig_vb_ft_kk_Fallbeyging_id is not None or
        isl_lysingarord.fk_Midstig_vb_ft_kvk_Fallbeyging_id is not None or
        isl_lysingarord.fk_Midstig_vb_ft_hk_Fallbeyging_id is not None
    ):
        data['miðstig']['vb']['ft'] = collections.OrderedDict()
    if (
        isl_lysingarord.fk_Efstastig_sb_et_kk_Fallbeyging_id is not None or
        isl_lysingarord.fk_Efstastig_sb_et_kvk_Fallbeyging_id is not None or
        isl_lysingarord.fk_Efstastig_sb_et_hk_Fallbeyging_id is not None or
        isl_lysingarord.fk_Efstastig_sb_ft_kk_Fallbeyging_id is not None or
        isl_lysingarord.fk_Efstastig_sb_ft_kvk_Fallbeyging_id is not None or
        isl_lysingarord.fk_Efstastig_sb_ft_hk_Fallbeyging_id is not None or
        isl_lysingarord.fk_Efstastig_vb_et_kk_Fallbeyging_id is not None or
        isl_lysingarord.fk_Efstastig_vb_et_kvk_Fallbeyging_id is not None or
        isl_lysingarord.fk_Efstastig_vb_et_hk_Fallbeyging_id is not None or
        isl_lysingarord.fk_Efstastig_vb_ft_kk_Fallbeyging_id is not None or
        isl_lysingarord.fk_Efstastig_vb_ft_kvk_Fallbeyging_id is not None or
        isl_lysingarord.fk_Efstastig_vb_ft_hk_Fallbeyging_id is not None
    ):
        data['efstastig'] = collections.OrderedDict()
    if (
        isl_lysingarord.fk_Efstastig_sb_et_kk_Fallbeyging_id is not None or
        isl_lysingarord.fk_Efstastig_sb_et_kvk_Fallbeyging_id is not None or
        isl_lysingarord.fk_Efstastig_sb_et_hk_Fallbeyging_id is not None or
        isl_lysingarord.fk_Efstastig_sb_ft_kk_Fallbeyging_id is not None or
        isl_lysingarord.fk_Efstastig_sb_ft_kvk_Fallbeyging_id is not None or
        isl_lysingarord.fk_Efstastig_sb_ft_hk_Fallbeyging_id is not None
    ):
        data['efstastig']['sb'] = collections.OrderedDict()
    if (
        isl_lysingarord.fk_Efstastig_sb_et_kk_Fallbeyging_id is not None or
        isl_lysingarord.fk_Efstastig_sb_et_kvk_Fallbeyging_id is not None or
        isl_lysingarord.fk_Efstastig_sb_et_hk_Fallbeyging_id is not None
    ):
        data['efstastig']['sb']['et'] = collections.OrderedDict()
    if (
        isl_lysingarord.fk_Efstastig_sb_ft_kk_Fallbeyging_id is not None or
        isl_lysingarord.fk_Efstastig_sb_ft_kvk_Fallbeyging_id is not None or
        isl_lysingarord.fk_Efstastig_sb_ft_hk_Fallbeyging_id is not None
    ):
        data['efstastig']['sb']['ft'] = collections.OrderedDict()
    if (
        isl_lysingarord.fk_Efstastig_vb_et_kk_Fallbeyging_id is not None or
        isl_lysingarord.fk_Efstastig_vb_et_kvk_Fallbeyging_id is not None or
        isl_lysingarord.fk_Efstastig_vb_et_hk_Fallbeyging_id is not None or
        isl_lysingarord.fk_Efstastig_vb_ft_kk_Fallbeyging_id is not None or
        isl_lysingarord.fk_Efstastig_vb_ft_kvk_Fallbeyging_id is not None or
        isl_lysingarord.fk_Efstastig_vb_ft_hk_Fallbeyging_id is not None
    ):
        data['efstastig']['vb'] = collections.OrderedDict()
    if (
        isl_lysingarord.fk_Efstastig_vb_et_kk_Fallbeyging_id is not None or
        isl_lysingarord.fk_Efstastig_vb_et_kvk_Fallbeyging_id is not None or
        isl_lysingarord.fk_Efstastig_vb_et_hk_Fallbeyging_id is not None
    ):
        data['efstastig']['vb']['et'] = collections.OrderedDict()
    if (
        isl_lysingarord.fk_Efstastig_vb_ft_kk_Fallbeyging_id is not None or
        isl_lysingarord.fk_Efstastig_vb_ft_kvk_Fallbeyging_id is not None or
        isl_lysingarord.fk_Efstastig_vb_ft_hk_Fallbeyging_id is not None
    ):
        data['efstastig']['vb']['ft'] = collections.OrderedDict()
    # Frumstig, sterk beyging
    if isl_lysingarord.fk_Frumstig_sb_et_kk_Fallbeyging_id is not None:
        data['frumstig']['sb']['et']['kk'] = get_fallbeyging_list_from_db(
            isl_lysingarord.fk_Frumstig_sb_et_kk_Fallbeyging_id
        )
    if isl_lysingarord.fk_Frumstig_sb_et_kvk_Fallbeyging_id is not None:
        data['frumstig']['sb']['et']['kvk'] = get_fallbeyging_list_from_db(
            isl_lysingarord.fk_Frumstig_sb_et_kvk_Fallbeyging_id
        )
    if isl_lysingarord.fk_Frumstig_sb_et_hk_Fallbeyging_id is not None:
        data['frumstig']['sb']['et']['hk'] = get_fallbeyging_list_from_db(
            isl_lysingarord.fk_Frumstig_sb_et_hk_Fallbeyging_id
        )
    if isl_lysingarord.fk_Frumstig_sb_ft_kk_Fallbeyging_id is not None:
        data['frumstig']['sb']['ft']['kk'] = get_fallbeyging_list_from_db(
            isl_lysingarord.fk_Frumstig_sb_ft_kk_Fallbeyging_id
        )
    if isl_lysingarord.fk_Frumstig_sb_ft_kvk_Fallbeyging_id is not None:
        data['frumstig']['sb']['ft']['kvk'] = get_fallbeyging_list_from_db(
            isl_lysingarord.fk_Frumstig_sb_ft_kvk_Fallbeyging_id
        )
    if isl_lysingarord.fk_Frumstig_sb_ft_hk_Fallbeyging_id is not None:
        data['frumstig']['sb']['ft']['hk'] = get_fallbeyging_list_from_db(
            isl_lysingarord.fk_Frumstig_sb_ft_hk_Fallbeyging_id
        )
    # Frumstig, veik beyging
    if isl_lysingarord.fk_Frumstig_vb_et_kk_Fallbeyging_id is not None:
        data['frumstig']['vb']['et']['kk'] = get_fallbeyging_list_from_db(
            isl_lysingarord.fk_Frumstig_vb_et_kk_Fallbeyging_id
        )
    if isl_lysingarord.fk_Frumstig_vb_et_kvk_Fallbeyging_id is not None:
        data['frumstig']['vb']['et']['kvk'] = get_fallbeyging_list_from_db(
            isl_lysingarord.fk_Frumstig_vb_et_kvk_Fallbeyging_id
        )
    if isl_lysingarord.fk_Frumstig_vb_et_hk_Fallbeyging_id is not None:
        data['frumstig']['vb']['et']['hk'] = get_fallbeyging_list_from_db(
            isl_lysingarord.fk_Frumstig_vb_et_hk_Fallbeyging_id
        )
    if isl_lysingarord.fk_Frumstig_vb_ft_kk_Fallbeyging_id is not None:
        data['frumstig']['vb']['ft']['kk'] = get_fallbeyging_list_from_db(
            isl_lysingarord.fk_Frumstig_vb_ft_kk_Fallbeyging_id
        )
    if isl_lysingarord.fk_Frumstig_vb_ft_kvk_Fallbeyging_id is not None:
        data['frumstig']['vb']['ft']['kvk'] = get_fallbeyging_list_from_db(
            isl_lysingarord.fk_Frumstig_vb_ft_kvk_Fallbeyging_id
        )
    if isl_lysingarord.fk_Frumstig_vb_ft_hk_Fallbeyging_id is not None:
        data['frumstig']['vb']['ft']['hk'] = get_fallbeyging_list_from_db(
            isl_lysingarord.fk_Frumstig_vb_ft_hk_Fallbeyging_id
        )
    # Miðstig, veik beyging (miðstig hafa enga sterka beygingu)
    if isl_lysingarord.fk_Midstig_vb_et_kk_Fallbeyging_id is not None:
        data['miðstig']['vb']['et']['kk'] = get_fallbeyging_list_from_db(
            isl_lysingarord.fk_Midstig_vb_et_kk_Fallbeyging_id
        )
    if isl_lysingarord.fk_Midstig_vb_et_kvk_Fallbeyging_id is not None:
        data['miðstig']['vb']['et']['kvk'] = get_fallbeyging_list_from_db(
            isl_lysingarord.fk_Midstig_vb_et_kvk_Fallbeyging_id
        )
    if isl_lysingarord.fk_Midstig_vb_et_hk_Fallbeyging_id is not None:
        data['miðstig']['vb']['et']['hk'] = get_fallbeyging_list_from_db(
            isl_lysingarord.fk_Midstig_vb_et_hk_Fallbeyging_id
        )
    if isl_lysingarord.fk_Midstig_vb_ft_kk_Fallbeyging_id is not None:
        data['miðstig']['vb']['ft']['kk'] = get_fallbeyging_list_from_db(
            isl_lysingarord.fk_Midstig_vb_ft_kk_Fallbeyging_id
        )
    if isl_lysingarord.fk_Midstig_vb_ft_kvk_Fallbeyging_id is not None:
        data['miðstig']['vb']['ft']['kvk'] = get_fallbeyging_list_from_db(
            isl_lysingarord.fk_Midstig_vb_ft_kvk_Fallbeyging_id
        )
    if isl_lysingarord.fk_Midstig_vb_ft_hk_Fallbeyging_id is not None:
        data['miðstig']['vb']['ft']['hk'] = get_fallbeyging_list_from_db(
            isl_lysingarord.fk_Midstig_vb_ft_hk_Fallbeyging_id
        )
    # Efsta stig, sterk beyging
    if isl_lysingarord.fk_Efstastig_sb_et_kk_Fallbeyging_id is not None:
        data['efstastig']['sb']['et']['kk'] = get_fallbeyging_list_from_db(
            isl_lysingarord.fk_Efstastig_sb_et_kk_Fallbeyging_id
        )
    if isl_lysingarord.fk_Efstastig_sb_et_kvk_Fallbeyging_id is not None:
        data['efstastig']['sb']['et']['kvk'] = get_fallbeyging_list_from_db(
            isl_lysingarord.fk_Efstastig_sb_et_kvk_Fallbeyging_id
        )
    if isl_lysingarord.fk_Efstastig_sb_et_hk_Fallbeyging_id is not None:
        data['efstastig']['sb']['et']['hk'] = get_fallbeyging_list_from_db(
            isl_lysingarord.fk_Efstastig_sb_et_hk_Fallbeyging_id
        )
    if isl_lysingarord.fk_Efstastig_sb_ft_kk_Fallbeyging_id is not None:
        data['efstastig']['sb']['ft']['kk'] = get_fallbeyging_list_from_db(
            isl_lysingarord.fk_Efstastig_sb_ft_kk_Fallbeyging_id
        )
    if isl_lysingarord.fk_Efstastig_sb_ft_kvk_Fallbeyging_id is not None:
        data['efstastig']['sb']['ft']['kvk'] = get_fallbeyging_list_from_db(
            isl_lysingarord.fk_Efstastig_sb_ft_kvk_Fallbeyging_id
        )
    if isl_lysingarord.fk_Efstastig_sb_ft_hk_Fallbeyging_id is not None:
        data['efstastig']['sb']['ft']['hk'] = get_fallbeyging_list_from_db(
            isl_lysingarord.fk_Efstastig_sb_ft_hk_Fallbeyging_id
        )
    # Efsta stig, veik beyging
    if isl_lysingarord.fk_Efstastig_vb_et_kk_Fallbeyging_id is not None:
        data['efstastig']['vb']['et']['kk'] = get_fallbeyging_list_from_db(
            isl_lysingarord.fk_Efstastig_vb_et_kk_Fallbeyging_id
        )
    if isl_lysingarord.fk_Efstastig_vb_et_kvk_Fallbeyging_id is not None:
        data['efstastig']['vb']['et']['kvk'] = get_fallbeyging_list_from_db(
            isl_lysingarord.fk_Efstastig_vb_et_kvk_Fallbeyging_id
        )
    if isl_lysingarord.fk_Efstastig_vb_et_hk_Fallbeyging_id is not None:
        data['efstastig']['vb']['et']['hk'] = get_fallbeyging_list_from_db(
            isl_lysingarord.fk_Efstastig_vb_et_hk_Fallbeyging_id
        )
    if isl_lysingarord.fk_Efstastig_vb_ft_kk_Fallbeyging_id is not None:
        data['efstastig']['vb']['ft']['kk'] = get_fallbeyging_list_from_db(
            isl_lysingarord.fk_Efstastig_vb_ft_kk_Fallbeyging_id
        )
    if isl_lysingarord.fk_Efstastig_vb_ft_kvk_Fallbeyging_id is not None:
        data['efstastig']['vb']['ft']['kvk'] = get_fallbeyging_list_from_db(
            isl_lysingarord.fk_Efstastig_vb_ft_kvk_Fallbeyging_id
        )
    if isl_lysingarord.fk_Efstastig_vb_ft_hk_Fallbeyging_id is not None:
        data['efstastig']['vb']['ft']['hk'] = get_fallbeyging_list_from_db(
            isl_lysingarord.fk_Efstastig_vb_ft_hk_Fallbeyging_id
        )
    return data


def get_fallbeyging_list_from_db(fallbeyging_id):
    fb = db.Session.query(isl.Fallbeyging).filter_by(
        Fallbeyging_id=fallbeyging_id
    ).first()
    assert(fb is not None)
    return [fb.Nefnifall, fb.Tholfall, fb.Thagufall, fb.Eignarfall]


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
