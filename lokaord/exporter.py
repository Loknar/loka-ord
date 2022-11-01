#!/usr/bin/python
"""
Exporter functionality

Exporting data from SQL database to files.
"""
import collections
import json
import os

from lokaord import logman
from lokaord.database import db
from lokaord.database.models import isl


class MyJSONEncoder(json.JSONEncoder):
    '''
    json encoder for doing a bit of custom json string indentation
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
    isl_ord_sagnord_list = db.Session.query(isl.Ord).filter_by(
        Ordflokkur=isl.Ordflokkar.Sagnord,
        Samsett=False
    ).order_by(isl.Ord.Ord, isl.Ord.Ord_id).all()
    for isl_ord_sagnord in isl_ord_sagnord_list:
        sagnord_data = get_sagnord_from_db_to_ordered_dict(isl_ord_sagnord)
        sagnord_data_hash = hashlib.sha256(
            json.dumps(
                sagnord_data, separators=(',', ':'), ensure_ascii=False, sort_keys=True
            ).encode('utf-8')
        ).hexdigest()
        # ensure unique sagnord_data_hash
        if sagnord_data_hash in hash_to_isl_ord_id:
            counter = 0
            sagnord_data_hash_incr = '%s_%s' % (sagnord_data_hash, hex(counter)[2:])
            while sagnord_data_hash_incr in hash_to_isl_ord_id:
                counter += 1
                sagnord_data_hash_incr = '%s_%s' % (sagnord_data_hash, hex(counter)[2:])
            sagnord_data_hash = sagnord_data_hash_incr
        hash_to_isl_ord_id[sagnord_data_hash] = isl_ord_sagnord.Ord_id
        isl_ord_id_to_hash[str(isl_ord_sagnord.Ord_id)] = sagnord_data_hash
        sagnord_data['hash'] = sagnord_data_hash
        sagnord_data_json_str = json.dumps(
            sagnord_data, indent='\t', ensure_ascii=False, separators=(',', ': '),
            cls=MyJSONEncoder
        )
        isl_ord_sagnord_filename = '%s.json' % (sagnord_data['orð'], )
        with open(
            os.path.join(datafiles_dir_abs, 'sagnord', isl_ord_sagnord_filename),
            mode='w',
            encoding='utf-8'
        ) as json_file:
            json_file.write(sagnord_data_json_str)
            logman.info('Wrote file "sagnord/%s' % (isl_ord_sagnord_filename, ))
    # fleiri orð
    logman.info('TODO: finish implementing write_datafiles_from_db')


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


def get_sagnord_from_db_to_ordered_dict(isl_ord):
    data = collections.OrderedDict()
    data['orð'] = isl_ord.Ord
    data['flokkur'] = 'sagnorð'
    isl_sagnord_list = db.Session.query(isl.Sagnord).filter_by(fk_Ord_id=isl_ord.Ord_id)
    assert(len(isl_sagnord_list.all()) < 2)
    isl_sagnord = isl_sagnord_list.first()
    assert(isl_sagnord is not None)
    # setup data dict
    if (
        isl_sagnord.Germynd_Nafnhattur is not None or
        isl_sagnord.Germynd_Sagnbot is not None or
        isl_sagnord.Germynd_Bodhattur_styfdur is not None or
        isl_sagnord.Germynd_Bodhattur_et is not None or
        isl_sagnord.Germynd_Bodhattur_ft is not None or
        isl_sagnord.fk_Germynd_personuleg_framsoguhattur is not None or
        isl_sagnord.fk_Germynd_personuleg_vidtengingarhattur is not None or
        isl_sagnord.Germynd_opersonuleg_frumlag is not None or
        isl_sagnord.fk_Germynd_opersonuleg_framsoguhattur is not None or
        isl_sagnord.fk_Germynd_opersonuleg_vidtengingarhattur is not None or
        isl_sagnord.Germynd_spurnarmyndir_framsoguhattur_nutid_et is not None or
        isl_sagnord.Germynd_spurnarmyndir_framsoguhattur_nutid_ft is not None or
        isl_sagnord.Germynd_spurnarmyndir_framsoguhattur_thatid_et is not None or
        isl_sagnord.Germynd_spurnarmyndir_framsoguhattur_thatid_ft is not None or
        isl_sagnord.Germynd_spurnarmyndir_vidtengingarhattur_nutid_et is not None or
        isl_sagnord.Germynd_spurnarmyndir_vidtengingarhattur_nutid_ft is not None or
        isl_sagnord.Germynd_spurnarmyndir_vidtengingarhattur_thatid_et is not None or
        isl_sagnord.Germynd_spurnarmyndir_vidtengingarhattur_thatid_ft is not None
    ):
        data['germynd'] = collections.OrderedDict()
        # germynd nafnháttur
        if isl_sagnord.Germynd_Nafnhattur is not None:
            data['germynd']['nafnháttur'] = isl_sagnord.Germynd_Nafnhattur
        # germynd sagnbót
        if isl_sagnord.Germynd_Sagnbot is not None:
            data['germynd']['sagnbót'] = isl_sagnord.Germynd_Sagnbot
        if (
            isl_sagnord.Germynd_Bodhattur_styfdur is not None or
            isl_sagnord.Germynd_Bodhattur_et is not None or
            isl_sagnord.Germynd_Bodhattur_ft is not None
        ):
            data['germynd']['boðháttur'] = collections.OrderedDict()
        if (
            isl_sagnord.fk_Germynd_personuleg_framsoguhattur is not None or
            isl_sagnord.fk_Germynd_personuleg_vidtengingarhattur is not None
        ):
            data['germynd']['persónuleg'] = collections.OrderedDict()
        if (
            isl_sagnord.Germynd_opersonuleg_frumlag is not None or
            isl_sagnord.fk_Germynd_opersonuleg_framsoguhattur is not None or
            isl_sagnord.fk_Germynd_opersonuleg_vidtengingarhattur is not None
        ):
            data['germynd']['ópersónuleg'] = collections.OrderedDict()
        if (
            isl_sagnord.Germynd_spurnarmyndir_framsoguhattur_nutid_et is not None or
            isl_sagnord.Germynd_spurnarmyndir_framsoguhattur_nutid_ft is not None or
            isl_sagnord.Germynd_spurnarmyndir_framsoguhattur_thatid_et is not None or
            isl_sagnord.Germynd_spurnarmyndir_framsoguhattur_thatid_ft is not None or
            isl_sagnord.Germynd_spurnarmyndir_vidtengingarhattur_nutid_et is not None or
            isl_sagnord.Germynd_spurnarmyndir_vidtengingarhattur_nutid_ft is not None or
            isl_sagnord.Germynd_spurnarmyndir_vidtengingarhattur_thatid_et is not None or
            isl_sagnord.Germynd_spurnarmyndir_vidtengingarhattur_thatid_ft is not None
        ):
            data['germynd']['spurnarmyndir'] = collections.OrderedDict()
            if (
                isl_sagnord.Germynd_spurnarmyndir_framsoguhattur_nutid_et is not None or
                isl_sagnord.Germynd_spurnarmyndir_framsoguhattur_nutid_ft is not None or
                isl_sagnord.Germynd_spurnarmyndir_framsoguhattur_thatid_et is not None or
                isl_sagnord.Germynd_spurnarmyndir_framsoguhattur_thatid_ft is not None
            ):
                data['germynd']['spurnarmyndir']['framsöguháttur'] = collections.OrderedDict()
                if (
                    isl_sagnord.Germynd_spurnarmyndir_framsoguhattur_nutid_et is not None or
                    isl_sagnord.Germynd_spurnarmyndir_framsoguhattur_nutid_ft is not None
                ):
                    data['germynd']['spurnarmyndir']['framsöguháttur']['nútíð'] = (
                        collections.OrderedDict()
                    )
                if (
                    isl_sagnord.Germynd_spurnarmyndir_framsoguhattur_thatid_et is not None or
                    isl_sagnord.Germynd_spurnarmyndir_framsoguhattur_thatid_ft is not None
                ):
                    data['germynd']['spurnarmyndir']['framsöguháttur']['þátíð'] = (
                        collections.OrderedDict()
                    )
            if (
                isl_sagnord.Germynd_spurnarmyndir_vidtengingarhattur_nutid_et is not None or
                isl_sagnord.Germynd_spurnarmyndir_vidtengingarhattur_nutid_ft is not None or
                isl_sagnord.Germynd_spurnarmyndir_vidtengingarhattur_thatid_et is not None or
                isl_sagnord.Germynd_spurnarmyndir_vidtengingarhattur_thatid_ft is not None
            ):
                data['germynd']['spurnarmyndir']['viðtengingarháttur'] = collections.OrderedDict()
                if (
                    isl_sagnord.Germynd_spurnarmyndir_vidtengingarhattur_nutid_et is not None or
                    isl_sagnord.Germynd_spurnarmyndir_vidtengingarhattur_nutid_ft is not None
                ):
                    data['germynd']['spurnarmyndir']['viðtengingarháttur']['nútíð'] = (
                        collections.OrderedDict()
                    )
                if (
                    isl_sagnord.Germynd_spurnarmyndir_vidtengingarhattur_thatid_et is not None or
                    isl_sagnord.Germynd_spurnarmyndir_vidtengingarhattur_thatid_ft is not None
                ):
                    data['germynd']['spurnarmyndir']['viðtengingarháttur']['þátíð'] = (
                        collections.OrderedDict()
                    )
    if (
        isl_sagnord.Midmynd_Nafnhattur is not None or
        isl_sagnord.Midmynd_Sagnbot is not None or
        isl_sagnord.Midmynd_Bodhattur_et is not None or
        isl_sagnord.Midmynd_Bodhattur_ft is not None or
        isl_sagnord.fk_Midmynd_personuleg_framsoguhattur is not None or
        isl_sagnord.fk_Midmynd_personuleg_vidtengingarhattur is not None or
        isl_sagnord.Midmynd_opersonuleg_frumlag is not None or
        isl_sagnord.fk_Midmynd_opersonuleg_framsoguhattur is not None or
        isl_sagnord.fk_Midmynd_opersonuleg_vidtengingarhattur is not None or
        isl_sagnord.Midmynd_spurnarmyndir_framsoguhattur_nutid_et is not None or
        isl_sagnord.Midmynd_spurnarmyndir_framsoguhattur_nutid_ft is not None or
        isl_sagnord.Midmynd_spurnarmyndir_framsoguhattur_thatid_et is not None or
        isl_sagnord.Midmynd_spurnarmyndir_framsoguhattur_thatid_ft is not None or
        isl_sagnord.Midmynd_spurnarmyndir_vidtengingarhattur_nutid_et is not None or
        isl_sagnord.Midmynd_spurnarmyndir_vidtengingarhattur_nutid_ft is not None or
        isl_sagnord.Midmynd_spurnarmyndir_vidtengingarhattur_thatid_et is not None or
        isl_sagnord.Midmynd_spurnarmyndir_vidtengingarhattur_thatid_ft is not None
    ):
        data['miðmynd'] = collections.OrderedDict()
        # miðmynd nafnháttur
        if isl_sagnord.Midmynd_Nafnhattur is not None:
            data['miðmynd']['nafnháttur'] = isl_sagnord.Midmynd_Nafnhattur
        # miðmynd sagnbót
        if isl_sagnord.Midmynd_Sagnbot is not None:
            data['miðmynd']['sagnbót'] = isl_sagnord.Midmynd_Sagnbot
        if (
            isl_sagnord.Midmynd_Bodhattur_et is not None or
            isl_sagnord.Midmynd_Bodhattur_ft is not None
        ):
            data['miðmynd']['boðháttur'] = collections.OrderedDict()
        if (
            isl_sagnord.fk_Midmynd_personuleg_framsoguhattur is not None or
            isl_sagnord.fk_Midmynd_personuleg_vidtengingarhattur is not None
        ):
            data['miðmynd']['persónuleg'] = collections.OrderedDict()
        if (
            isl_sagnord.Midmynd_opersonuleg_frumlag is not None or
            isl_sagnord.fk_Midmynd_opersonuleg_framsoguhattur is not None or
            isl_sagnord.fk_Midmynd_opersonuleg_vidtengingarhattur is not None
        ):
            data['miðmynd']['ópersónuleg'] = collections.OrderedDict()
        if (
            isl_sagnord.Midmynd_spurnarmyndir_framsoguhattur_nutid_et is not None or
            isl_sagnord.Midmynd_spurnarmyndir_framsoguhattur_nutid_ft is not None or
            isl_sagnord.Midmynd_spurnarmyndir_framsoguhattur_thatid_et is not None or
            isl_sagnord.Midmynd_spurnarmyndir_framsoguhattur_thatid_ft is not None or
            isl_sagnord.Midmynd_spurnarmyndir_vidtengingarhattur_nutid_et is not None or
            isl_sagnord.Midmynd_spurnarmyndir_vidtengingarhattur_nutid_ft is not None or
            isl_sagnord.Midmynd_spurnarmyndir_vidtengingarhattur_thatid_et is not None or
            isl_sagnord.Midmynd_spurnarmyndir_vidtengingarhattur_thatid_ft is not None
        ):
            data['miðmynd']['spurnarmyndir'] = collections.OrderedDict()
            if (
                isl_sagnord.Midmynd_spurnarmyndir_framsoguhattur_nutid_et is not None or
                isl_sagnord.Midmynd_spurnarmyndir_framsoguhattur_nutid_ft is not None or
                isl_sagnord.Midmynd_spurnarmyndir_framsoguhattur_thatid_et is not None or
                isl_sagnord.Midmynd_spurnarmyndir_framsoguhattur_thatid_ft is not None
            ):
                data['miðmynd']['spurnarmyndir']['framsöguháttur'] = collections.OrderedDict()
                if (
                    isl_sagnord.Midmynd_spurnarmyndir_framsoguhattur_nutid_et is not None or
                    isl_sagnord.Midmynd_spurnarmyndir_framsoguhattur_nutid_ft is not None
                ):
                    data['miðmynd']['spurnarmyndir']['framsöguháttur']['nútíð'] = (
                        collections.OrderedDict()
                    )
                if (
                    isl_sagnord.Midmynd_spurnarmyndir_framsoguhattur_thatid_et is not None or
                    isl_sagnord.Midmynd_spurnarmyndir_framsoguhattur_thatid_ft is not None
                ):
                    data['miðmynd']['spurnarmyndir']['framsöguháttur']['þátíð'] = (
                        collections.OrderedDict()
                    )
            if (
                isl_sagnord.Midmynd_spurnarmyndir_vidtengingarhattur_nutid_et is not None or
                isl_sagnord.Midmynd_spurnarmyndir_vidtengingarhattur_nutid_ft is not None or
                isl_sagnord.Midmynd_spurnarmyndir_vidtengingarhattur_thatid_et is not None or
                isl_sagnord.Midmynd_spurnarmyndir_vidtengingarhattur_thatid_ft is not None
            ):
                data['miðmynd']['spurnarmyndir']['viðtengingarháttur'] = collections.OrderedDict()
                if (
                    isl_sagnord.Midmynd_spurnarmyndir_vidtengingarhattur_nutid_et is not None or
                    isl_sagnord.Midmynd_spurnarmyndir_vidtengingarhattur_nutid_ft is not None
                ):
                    data['miðmynd']['spurnarmyndir']['viðtengingarháttur']['nútíð'] = (
                        collections.OrderedDict()
                    )
                if (
                    isl_sagnord.Midmynd_spurnarmyndir_vidtengingarhattur_thatid_et is not None or
                    isl_sagnord.Midmynd_spurnarmyndir_vidtengingarhattur_thatid_ft is not None
                ):
                    data['miðmynd']['spurnarmyndir']['viðtengingarháttur']['þátíð'] = (
                        collections.OrderedDict()
                    )
    if (
        isl_sagnord.LysingarhatturNutidar is not None or
        isl_sagnord.fk_LysingarhatturThatidar_sb_et_kk_id is not None or
        isl_sagnord.fk_LysingarhatturThatidar_sb_et_kvk_id is not None or
        isl_sagnord.fk_LysingarhatturThatidar_sb_et_hk_id is not None or
        isl_sagnord.fk_LysingarhatturThatidar_sb_ft_kk_id is not None or
        isl_sagnord.fk_LysingarhatturThatidar_sb_ft_kvk_id is not None or
        isl_sagnord.fk_LysingarhatturThatidar_sb_ft_hk_id is not None or
        isl_sagnord.fk_LysingarhatturThatidar_vb_et_kk_id is not None or
        isl_sagnord.fk_LysingarhatturThatidar_vb_et_kvk_id is not None or
        isl_sagnord.fk_LysingarhatturThatidar_vb_et_hk_id is not None or
        isl_sagnord.fk_LysingarhatturThatidar_vb_ft_kk_id is not None or
        isl_sagnord.fk_LysingarhatturThatidar_vb_ft_kvk_id is not None or
        isl_sagnord.fk_LysingarhatturThatidar_vb_ft_hk_id is not None
    ):
        data['lýsingarháttur'] = collections.OrderedDict()
        # lýsingarháttur nútíðar
        if isl_sagnord.LysingarhatturNutidar is not None:
            data['lýsingarháttur']['nútíðar'] = isl_sagnord.LysingarhatturNutidar
        if (
            isl_sagnord.fk_LysingarhatturThatidar_sb_et_kk_id is not None or
            isl_sagnord.fk_LysingarhatturThatidar_sb_et_kvk_id is not None or
            isl_sagnord.fk_LysingarhatturThatidar_sb_et_hk_id is not None or
            isl_sagnord.fk_LysingarhatturThatidar_sb_ft_kk_id is not None or
            isl_sagnord.fk_LysingarhatturThatidar_sb_ft_kvk_id is not None or
            isl_sagnord.fk_LysingarhatturThatidar_sb_ft_hk_id is not None or
            isl_sagnord.fk_LysingarhatturThatidar_vb_et_kk_id is not None or
            isl_sagnord.fk_LysingarhatturThatidar_vb_et_kvk_id is not None or
            isl_sagnord.fk_LysingarhatturThatidar_vb_et_hk_id is not None or
            isl_sagnord.fk_LysingarhatturThatidar_vb_ft_kk_id is not None or
            isl_sagnord.fk_LysingarhatturThatidar_vb_ft_kvk_id is not None or
            isl_sagnord.fk_LysingarhatturThatidar_vb_ft_hk_id is not None
        ):
            data['lýsingarháttur']['þátíðar'] = collections.OrderedDict()
            if (
                isl_sagnord.fk_LysingarhatturThatidar_sb_et_kk_id is not None or
                isl_sagnord.fk_LysingarhatturThatidar_sb_et_kvk_id is not None or
                isl_sagnord.fk_LysingarhatturThatidar_sb_et_hk_id is not None or
                isl_sagnord.fk_LysingarhatturThatidar_sb_ft_kk_id is not None or
                isl_sagnord.fk_LysingarhatturThatidar_sb_ft_kvk_id is not None or
                isl_sagnord.fk_LysingarhatturThatidar_sb_ft_hk_id is not None
            ):
                data['lýsingarháttur']['þátíðar']['sb'] = collections.OrderedDict()
                if (
                    isl_sagnord.fk_LysingarhatturThatidar_sb_et_kk_id is not None or
                    isl_sagnord.fk_LysingarhatturThatidar_sb_et_kvk_id is not None or
                    isl_sagnord.fk_LysingarhatturThatidar_sb_et_hk_id is not None
                ):
                    data['lýsingarháttur']['þátíðar']['sb']['et'] = collections.OrderedDict()
                if (
                    isl_sagnord.fk_LysingarhatturThatidar_sb_ft_kk_id is not None or
                    isl_sagnord.fk_LysingarhatturThatidar_sb_ft_kvk_id is not None or
                    isl_sagnord.fk_LysingarhatturThatidar_sb_ft_hk_id is not None
                ):
                    data['lýsingarháttur']['þátíðar']['sb']['ft'] = collections.OrderedDict()
            if (
                isl_sagnord.fk_LysingarhatturThatidar_vb_et_kk_id is not None or
                isl_sagnord.fk_LysingarhatturThatidar_vb_et_kvk_id is not None or
                isl_sagnord.fk_LysingarhatturThatidar_vb_et_hk_id is not None or
                isl_sagnord.fk_LysingarhatturThatidar_vb_ft_kk_id is not None or
                isl_sagnord.fk_LysingarhatturThatidar_vb_ft_kvk_id is not None or
                isl_sagnord.fk_LysingarhatturThatidar_vb_ft_hk_id is not None
            ):
                data['lýsingarháttur']['þátíðar']['vb'] = collections.OrderedDict()
                if (
                    isl_sagnord.fk_LysingarhatturThatidar_vb_et_kk_id is not None or
                    isl_sagnord.fk_LysingarhatturThatidar_vb_et_kvk_id is not None or
                    isl_sagnord.fk_LysingarhatturThatidar_vb_et_hk_id is not None
                ):
                    data['lýsingarháttur']['þátíðar']['vb']['et'] = collections.OrderedDict()
                if (
                    isl_sagnord.fk_LysingarhatturThatidar_vb_ft_kk_id is not None or
                    isl_sagnord.fk_LysingarhatturThatidar_vb_ft_kvk_id is not None or
                    isl_sagnord.fk_LysingarhatturThatidar_vb_ft_hk_id is not None
                ):
                    data['lýsingarháttur']['þátíðar']['vb']['ft'] = collections.OrderedDict()
    # germynd boðháttur
    if isl_sagnord.Germynd_Bodhattur_styfdur is not None:
        data['germynd']['boðháttur']['stýfður'] = isl_sagnord.Germynd_Bodhattur_styfdur
        data['germynd']['boðháttur']['et'] = isl_sagnord.Germynd_Bodhattur_et
        data['germynd']['boðháttur']['ft'] = isl_sagnord.Germynd_Bodhattur_ft
    # germynd persónuleg
    if isl_sagnord.fk_Germynd_personuleg_framsoguhattur is not None:
        data['germynd']['persónuleg']['framsöguháttur'] = get_sagnbeyging_obj_from_db(
            isl_sagnord.fk_Germynd_personuleg_framsoguhattur
        )
    if isl_sagnord.fk_Germynd_personuleg_vidtengingarhattur is not None:
        data['germynd']['persónuleg']['viðtengingarháttur'] = get_sagnbeyging_obj_from_db(
            isl_sagnord.fk_Germynd_personuleg_vidtengingarhattur
        )
    # germynd ópersónuleg
    if isl_sagnord.Germynd_opersonuleg_frumlag == isl.Fall.Tholfall:
        data['germynd']['ópersónuleg']['frumlag'] = 'þolfall'
    elif isl_sagnord.Germynd_opersonuleg_frumlag == isl.Fall.Thagufall:
        data['germynd']['ópersónuleg']['frumlag'] = 'þágufall'
    elif isl_sagnord.Germynd_opersonuleg_frumlag == isl.Fall.Eignarfall:
        data['germynd']['ópersónuleg']['frumlag'] = 'eignarfall'
    if isl_sagnord.fk_Germynd_opersonuleg_framsoguhattur is not None:
        data['germynd']['ópersónuleg']['framsöguháttur'] = get_sagnbeyging_obj_from_db(
            isl_sagnord.fk_Germynd_opersonuleg_framsoguhattur
        )
    if isl_sagnord.fk_Germynd_opersonuleg_vidtengingarhattur is not None:
        data['germynd']['ópersónuleg']['viðtengingarháttur'] = get_sagnbeyging_obj_from_db(
            isl_sagnord.fk_Germynd_opersonuleg_vidtengingarhattur
        )
    # germynd spurnarmyndir
    if isl_sagnord.Germynd_spurnarmyndir_framsoguhattur_nutid_et is not None:
        data['germynd']['spurnarmyndir']['framsöguháttur']['nútíð']['et'] = (
            isl_sagnord.Germynd_spurnarmyndir_framsoguhattur_nutid_et
        )
    if isl_sagnord.Germynd_spurnarmyndir_framsoguhattur_nutid_ft is not None:
        data['germynd']['spurnarmyndir']['framsöguháttur']['nútíð']['ft'] = (
            isl_sagnord.Germynd_spurnarmyndir_framsoguhattur_nutid_ft
        )
    if isl_sagnord.Germynd_spurnarmyndir_framsoguhattur_thatid_et is not None:
        data['germynd']['spurnarmyndir']['framsöguháttur']['þátíð']['et'] = (
            isl_sagnord.Germynd_spurnarmyndir_framsoguhattur_thatid_et
        )
    if isl_sagnord.Germynd_spurnarmyndir_framsoguhattur_thatid_ft is not None:
        data['germynd']['spurnarmyndir']['framsöguháttur']['þátíð']['ft'] = (
            isl_sagnord.Germynd_spurnarmyndir_framsoguhattur_thatid_ft
        )
    #
    if isl_sagnord.Germynd_spurnarmyndir_vidtengingarhattur_nutid_et is not None:
        data['germynd']['spurnarmyndir']['viðtengingarháttur']['nútíð']['et'] = (
            isl_sagnord.Germynd_spurnarmyndir_vidtengingarhattur_nutid_et
        )
    if isl_sagnord.Germynd_spurnarmyndir_vidtengingarhattur_nutid_ft is not None:
        data['germynd']['spurnarmyndir']['viðtengingarháttur']['nútíð']['ft'] = (
            isl_sagnord.Germynd_spurnarmyndir_vidtengingarhattur_nutid_ft
        )
    if isl_sagnord.Germynd_spurnarmyndir_vidtengingarhattur_thatid_et is not None:
        data['germynd']['spurnarmyndir']['viðtengingarháttur']['þátíð']['et'] = (
            isl_sagnord.Germynd_spurnarmyndir_vidtengingarhattur_thatid_et
        )
    if isl_sagnord.Germynd_spurnarmyndir_vidtengingarhattur_thatid_ft is not None:
        data['germynd']['spurnarmyndir']['viðtengingarháttur']['þátíð']['ft'] = (
            isl_sagnord.Germynd_spurnarmyndir_vidtengingarhattur_thatid_ft
        )
    # miðmynd boðháttur
    if isl_sagnord.Midmynd_Bodhattur_et is not None:
        data['miðmynd']['boðháttur']['et'] = isl_sagnord.Midmynd_Bodhattur_et
    if isl_sagnord.Midmynd_Bodhattur_ft is not None:
        data['miðmynd']['boðháttur']['ft'] = isl_sagnord.Midmynd_Bodhattur_ft
    # miðmynd persónuleg
    if isl_sagnord.fk_Midmynd_personuleg_framsoguhattur is not None:
        data['miðmynd']['persónuleg']['framsöguháttur'] = get_sagnbeyging_obj_from_db(
            isl_sagnord.fk_Midmynd_personuleg_framsoguhattur
        )
    if isl_sagnord.fk_Midmynd_personuleg_vidtengingarhattur is not None:
        data['miðmynd']['persónuleg']['viðtengingarháttur'] = get_sagnbeyging_obj_from_db(
            isl_sagnord.fk_Midmynd_personuleg_vidtengingarhattur
        )
    # miðmynd ópersónuleg
    elif isl_sagnord.Midmynd_opersonuleg_frumlag == isl.Fall.Tholfall:
        data['miðmynd']['ópersónuleg']['frumlag'] = 'þolfall'
    elif isl_sagnord.Midmynd_opersonuleg_frumlag == isl.Fall.Thagufall:
        data['miðmynd']['ópersónuleg']['frumlag'] = 'þágufall'
    elif isl_sagnord.Midmynd_opersonuleg_frumlag == isl.Fall.Eignarfall:
        data['miðmynd']['ópersónuleg']['frumlag'] = 'eignarfall'
    if isl_sagnord.fk_Midmynd_opersonuleg_framsoguhattur is not None:
        data['miðmynd']['ópersónuleg']['framsöguháttur'] = get_sagnbeyging_obj_from_db(
            isl_sagnord.fk_Midmynd_opersonuleg_framsoguhattur
        )
    if isl_sagnord.fk_Midmynd_opersonuleg_vidtengingarhattur is not None:
        data['miðmynd']['ópersónuleg']['viðtengingarháttur'] = get_sagnbeyging_obj_from_db(
            isl_sagnord.fk_Midmynd_opersonuleg_vidtengingarhattur
        )
    # miðmynd spurnarmyndir
    if isl_sagnord.Midmynd_spurnarmyndir_framsoguhattur_nutid_et is not None:
        data['miðmynd']['spurnarmyndir']['framsöguháttur']['nútíð']['et'] = (
            isl_sagnord.Midmynd_spurnarmyndir_framsoguhattur_nutid_et
        )
    if isl_sagnord.Midmynd_spurnarmyndir_framsoguhattur_nutid_ft is not None:
        data['miðmynd']['spurnarmyndir']['framsöguháttur']['nútíð']['ft'] = (
            isl_sagnord.Midmynd_spurnarmyndir_framsoguhattur_nutid_ft
        )
    if isl_sagnord.Midmynd_spurnarmyndir_framsoguhattur_thatid_et is not None:
        data['miðmynd']['spurnarmyndir']['framsöguháttur']['þátíð']['et'] = (
            isl_sagnord.Midmynd_spurnarmyndir_framsoguhattur_thatid_et
        )
    if isl_sagnord.Midmynd_spurnarmyndir_framsoguhattur_thatid_ft is not None:
        data['miðmynd']['spurnarmyndir']['framsöguháttur']['þátíð']['ft'] = (
            isl_sagnord.Midmynd_spurnarmyndir_framsoguhattur_thatid_ft
        )
    #
    if isl_sagnord.Midmynd_spurnarmyndir_vidtengingarhattur_nutid_et is not None:
        data['miðmynd']['spurnarmyndir']['viðtengingarháttur']['nútíð']['et'] = (
            isl_sagnord.Midmynd_spurnarmyndir_vidtengingarhattur_nutid_et
        )
    if isl_sagnord.Midmynd_spurnarmyndir_vidtengingarhattur_nutid_ft is not None:
        data['miðmynd']['spurnarmyndir']['viðtengingarháttur']['nútíð']['ft'] = (
            isl_sagnord.Midmynd_spurnarmyndir_vidtengingarhattur_nutid_ft
        )
    if isl_sagnord.Midmynd_spurnarmyndir_vidtengingarhattur_thatid_et is not None:
        data['miðmynd']['spurnarmyndir']['viðtengingarháttur']['þátíð']['et'] = (
            isl_sagnord.Midmynd_spurnarmyndir_vidtengingarhattur_thatid_et
        )
    if isl_sagnord.Midmynd_spurnarmyndir_vidtengingarhattur_thatid_ft is not None:
        data['miðmynd']['spurnarmyndir']['viðtengingarháttur']['þátíð']['ft'] = (
            isl_sagnord.Midmynd_spurnarmyndir_vidtengingarhattur_thatid_ft
        )
    # lýsingarháttur þátíðar
    if isl_sagnord.fk_LysingarhatturThatidar_sb_et_kk_id is not None:
        data['lýsingarháttur']['þátíðar']['sb']['et']['kk'] = get_fallbeyging_list_from_db(
            isl_sagnord.fk_LysingarhatturThatidar_sb_et_kk_id
        )
    if isl_sagnord.fk_LysingarhatturThatidar_sb_et_kvk_id is not None:
        data['lýsingarháttur']['þátíðar']['sb']['et']['kvk'] = get_fallbeyging_list_from_db(
            isl_sagnord.fk_LysingarhatturThatidar_sb_et_kvk_id
        )
    if isl_sagnord.fk_LysingarhatturThatidar_sb_et_hk_id is not None:
        data['lýsingarháttur']['þátíðar']['sb']['et']['hk'] = get_fallbeyging_list_from_db(
            isl_sagnord.fk_LysingarhatturThatidar_sb_et_hk_id
        )
    if isl_sagnord.fk_LysingarhatturThatidar_sb_ft_kk_id is not None:
        data['lýsingarháttur']['þátíðar']['sb']['ft']['kk'] = get_fallbeyging_list_from_db(
            isl_sagnord.fk_LysingarhatturThatidar_sb_ft_kk_id
        )
    if isl_sagnord.fk_LysingarhatturThatidar_sb_ft_kvk_id is not None:
        data['lýsingarháttur']['þátíðar']['sb']['ft']['kvk'] = get_fallbeyging_list_from_db(
            isl_sagnord.fk_LysingarhatturThatidar_sb_ft_kvk_id
        )
    if isl_sagnord.fk_LysingarhatturThatidar_sb_ft_hk_id is not None:
        data['lýsingarháttur']['þátíðar']['sb']['ft']['hk'] = get_fallbeyging_list_from_db(
            isl_sagnord.fk_LysingarhatturThatidar_sb_ft_hk_id
        )
    #
    if isl_sagnord.fk_LysingarhatturThatidar_vb_et_kk_id is not None:
        data['lýsingarháttur']['þátíðar']['vb']['et']['kk'] = get_fallbeyging_list_from_db(
            isl_sagnord.fk_LysingarhatturThatidar_vb_et_kk_id
        )
    if isl_sagnord.fk_LysingarhatturThatidar_vb_et_kvk_id is not None:
        data['lýsingarháttur']['þátíðar']['vb']['et']['kvk'] = get_fallbeyging_list_from_db(
            isl_sagnord.fk_LysingarhatturThatidar_vb_et_kvk_id
        )
    if isl_sagnord.fk_LysingarhatturThatidar_vb_et_hk_id is not None:
        data['lýsingarháttur']['þátíðar']['vb']['et']['hk'] = get_fallbeyging_list_from_db(
            isl_sagnord.fk_LysingarhatturThatidar_vb_et_hk_id
        )
    if isl_sagnord.fk_LysingarhatturThatidar_vb_ft_kk_id is not None:
        data['lýsingarháttur']['þátíðar']['vb']['ft']['kk'] = get_fallbeyging_list_from_db(
            isl_sagnord.fk_LysingarhatturThatidar_vb_ft_kk_id
        )
    if isl_sagnord.fk_LysingarhatturThatidar_vb_ft_kvk_id is not None:
        data['lýsingarháttur']['þátíðar']['vb']['ft']['kvk'] = get_fallbeyging_list_from_db(
            isl_sagnord.fk_LysingarhatturThatidar_vb_ft_kvk_id
        )
    if isl_sagnord.fk_LysingarhatturThatidar_vb_ft_hk_id is not None:
        data['lýsingarháttur']['þátíðar']['vb']['ft']['hk'] = get_fallbeyging_list_from_db(
            isl_sagnord.fk_LysingarhatturThatidar_vb_ft_hk_id
        )
    return data


def get_fallbeyging_list_from_db(fallbeyging_id):
    fb = db.Session.query(isl.Fallbeyging).filter_by(
        Fallbeyging_id=fallbeyging_id
    ).first()
    assert(fb is not None)
    return [fb.Nefnifall, fb.Tholfall, fb.Thagufall, fb.Eignarfall]


def get_sagnbeyging_obj_from_db(sagnbeyging_id):
    data = collections.OrderedDict()
    sagnbeyging = db.Session.query(isl.Sagnbeyging).filter_by(
        Sagnbeyging_id=sagnbeyging_id
    ).first()
    assert(sagnbeyging is not None)
    if (
        sagnbeyging.FyrstaPersona_eintala_nutid is not None or
        sagnbeyging.OnnurPersona_eintala_nutid is not None or
        sagnbeyging.ThridjaPersona_eintala_nutid is not None or
        sagnbeyging.FyrstaPersona_fleirtala_nutid is not None or
        sagnbeyging.OnnurPersona_fleirtala_nutid is not None or
        sagnbeyging.ThridjaPersona_fleirtala_nutid is not None
    ):
        data['nútíð'] = collections.OrderedDict()
    if (
        sagnbeyging.FyrstaPersona_eintala_thatid is not None or
        sagnbeyging.OnnurPersona_eintala_thatid is not None or
        sagnbeyging.ThridjaPersona_eintala_thatid is not None or
        sagnbeyging.FyrstaPersona_fleirtala_thatid is not None or
        sagnbeyging.OnnurPersona_fleirtala_thatid is not None or
        sagnbeyging.ThridjaPersona_fleirtala_thatid is not None
    ):
        data['þátíð'] = collections.OrderedDict()
    if (
        sagnbeyging.FyrstaPersona_eintala_nutid is not None or
        sagnbeyging.OnnurPersona_eintala_nutid is not None or
        sagnbeyging.ThridjaPersona_eintala_nutid is not None
    ):
        data['nútíð']['et'] = [
            sagnbeyging.FyrstaPersona_eintala_nutid,
            sagnbeyging.OnnurPersona_eintala_nutid,
            sagnbeyging.ThridjaPersona_eintala_nutid
        ]
    if (
        sagnbeyging.FyrstaPersona_fleirtala_nutid is not None or
        sagnbeyging.OnnurPersona_fleirtala_nutid is not None or
        sagnbeyging.ThridjaPersona_fleirtala_nutid is not None
    ):
        data['nútíð']['ft'] = [
            sagnbeyging.FyrstaPersona_fleirtala_nutid,
            sagnbeyging.OnnurPersona_fleirtala_nutid,
            sagnbeyging.ThridjaPersona_fleirtala_nutid
        ]
    if (
        sagnbeyging.FyrstaPersona_eintala_thatid is not None or
        sagnbeyging.OnnurPersona_eintala_thatid is not None or
        sagnbeyging.ThridjaPersona_eintala_thatid is not None
    ):
        data['þátíð']['et'] = [
            sagnbeyging.FyrstaPersona_eintala_thatid,
            sagnbeyging.OnnurPersona_eintala_thatid,
            sagnbeyging.ThridjaPersona_eintala_thatid
        ]
    if (
        sagnbeyging.FyrstaPersona_fleirtala_thatid is not None or
        sagnbeyging.OnnurPersona_fleirtala_thatid is not None or
        sagnbeyging.ThridjaPersona_fleirtala_thatid is not None
    ):
        data['þátíð']['ft'] = [
            sagnbeyging.FyrstaPersona_fleirtala_thatid,
            sagnbeyging.OnnurPersona_fleirtala_thatid,
            sagnbeyging.ThridjaPersona_fleirtala_thatid
        ]
    return data
