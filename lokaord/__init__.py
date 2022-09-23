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
    logman.info('Reading "sagnorð" datafiles ..')
    sagnord_dir = os.path.join(datafiles_dir_abs, 'sagnord')
    for sagnord_file in sorted(pathlib.Path(sagnord_dir).iterdir()):
        assert(sagnord_file.is_file())
        assert(sagnord_file.name.endswith('.json'))
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
    # fleiri orð
    logman.info('TODO: finish implementing build_db_from_datafiles')


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
                    isl_sagnord.Germynd_opersonuleg_frumlag = isl.Fall.Tholfall
                elif sagnord_data['germynd']['ópersónuleg']['frumlag'] == 'þágufall':
                    isl_sagnord.Germynd_opersonuleg_frumlag = isl.Fall.Thagufall
                elif sagnord_data['germynd']['ópersónuleg']['frumlag'] == 'eignarfall':
                    isl_sagnord.Germynd_opersonuleg_frumlag = isl.Fall.Eignarfall
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
                    isl_sagnord.Midmynd_opersonuleg_frumlag = isl.Fall.Tholfall
                elif sagnord_data['miðmynd']['ópersónuleg']['frumlag'] == 'þágufall':
                    isl_sagnord.Midmynd_opersonuleg_frumlag = isl.Fall.Thagufall
                elif sagnord_data['miðmynd']['ópersónuleg']['frumlag'] == 'eignarfall':
                    isl_sagnord.Midmynd_opersonuleg_frumlag = isl.Fall.Eignarfall
                else:
                    assert(False)  # invalid fall?
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


def add_word(word_data):
    return


def add_word_cli():
    header = '''loka-orð (%s)
    ___       __    __                           __   ________    ____
   /   | ____/ /___/ /  _      ______  _________/ /  / ____/ /   /  _/
  / /| |/ __  / __  /  | | /| / / __ \\/ ___/ __  /  / /   / /    / /
 / ___ / /_/ / /_/ /   | |/ |/ / /_/ / /  / /_/ /  / /___/ /____/ /
/_/  |_\\__,_/\\__,_/    |__/|__/\\____/_/   \\__,_/   \\____/_____/___/

   Orðflokkar
      1) Nafnorð      (dæmi: "hestur", "kýr", "lamb")
      2) Lýsingarorð  (dæmi: "sterkur", "veikur", "lipur")
      3) Sagnorð      (dæmi: "gefa", "hjálpa", "kenna")
    ''' % (__version__, )
    print(header)
    ordflokkur = None
    while ordflokkur not in ('1', '2', '3'):
        if ordflokkur is not None:
            print('Sláðu inn tölustaf (1, 2 eða 3).')
        ordflokkur = input('Veldu orðflokk (1/2/3): ')
    print(ordflokkur)
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
    if 'add_word_cli' in arguments and arguments['add_word_cli'] is True:
        add_word_cli()
    if 'build_db' in arguments and arguments['build_db'] is True:
        build_db_from_datafiles()
    if 'write_files' in arguments and arguments['write_files'] is True:
        write_datafiles_from_db()
