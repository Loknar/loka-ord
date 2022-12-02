#!/usr/bin/python
"""
CLI functionality

CLI for adding words to SQL database that are in turn written to files.
"""
import collections
import json
import os

from lokaord.version import __version__
from lokaord import logman
from lokaord.importer import add_word, lookup_nafnord, lookup_lysingarord, lookup_sagnord
from lokaord.exporter import hashify_ord_data, ord_data_to_fancy_json_str


def add_word_cli():
    header = '''lokaorð (%s)
    \033[33m___       __    __                           __   ________    ____
   /   | ____/ /___/ /  _      ______  _________/ /  / ____/ /   /  _/
  / /| |/ __  / __  /  | | /| / / __ \\/ ___/ __  /  / /   / /    / /
 / ___ / /_/ / /_/ /   | |/ |/ / /_/ / /  / /_/ /  / /___/ /____/ /
/_/  |_\\__,_/\\__,_/    |__/|__/\\____/_/   \\__,_/   \\____/_____/___/\033[0m

   Orðflokkar
      1) Nafnorð      (dæmi: "hestur", "kýr", "lamb")
      2) Lýsingarorð  (dæmi: "sterkur", "veikur", "lipur")
      3) Sagnorð      (dæmi: "gefa", "hjálpa", "kenna")

    (Einungis stuðningur fyrir ofangreinda orðflokka eins og er.)
    ''' % (__version__, )
    print(header)
    ordflokkur = None
    while ordflokkur not in ('1', '2', '3'):
        if ordflokkur is not None:
            print('Sláðu inn tölustaf (1, 2 eða 3).')
        ordflokkur = input('Veldu orðflokk (1/2/3): ')
    word_data = None
    if ordflokkur == '1':
        word_data = input_nafnord_cli()
    elif ordflokkur == '2':
        word_data = input_lysingarord_cli()
    elif ordflokkur == '3':
        word_data = input_sagnord_cli()
    assert(word_data is not None)
    word_data_json_str = json.dumps(word_data, separators=(',', ':'), ensure_ascii=False)
    logman.info('Add-Word-CLI: orð json: %s' % (word_data_json_str, ))
    add_word(word_data)

def fix_word_cli():
    header = f'''lokaorð ({__version__})
    ███████╗██╗██╗░░██╗  ░██╗░░░░░░░██╗░█████╗░██████╗░██████╗░
    ██╔════╝██║╚██╗██╔╝  ░██║░░██╗░░██║██╔══██╗██╔══██╗██╔══██╗
    █████╗░░██║░╚███╔╝░  ░╚██╗████╗██╔╝██║░░██║██████╔╝██║░░██║
    ██╔══╝░░██║░██╔██╗░  ░░████╔═████║░██║░░██║██╔══██╗██║░░██║
    ██║░░░░░██║██╔╝╚██╗  ░░╚██╔╝░╚██╔╝░╚█████╔╝██║░░██║██████╔╝
    ╚═╝░░░░░╚═╝╚═╝░░╚═╝  ░░░╚═╝░░░╚═╝░░░╚════╝░╚═╝░░╚═╝╚═════╝░\033[0m

   Orðflokkar
      1) Nafnorð      (dæmi: "hestur", "kýr", "lamb")

    (Einungis stuðningur fyrir ofangreinda orðflokka eins og er.)
    '''
    print(header)

    # Biðja um orð í nefnifalli án greinis
    ord = input('Skrifaðu orðið sem þú vilt leiðrétta í nefnifalli, eintölu og án greinis: ')
    kyn = input('Kyn (kk/kvk/hk): ')

    # Sækja json yfir í dict er hún er til, annars segja orð sé ekki til
    path = f'./lokaord/database/data/nafnord/{ord}-{kyn}.json'
    if os.path.exists(path):
        with open(path, 'r', encoding="utf-8") as f:
            old_ord = json.load(f)
            new_ord = old_ord
        instructions = '''

    Ef ekki þarf að leiðrétta orð, ýttu þá á enter til að hunsa.
    Ef orðið er vitlaust, leiðréttu það og ýttu á enter.
        '''
        # print('\nEf ekki þarf að leiðrétta orð, ýttu þá á enter til að hunsa. \nEf orðið er vitlaust, leiðréttu það og ýttu á enter.')
        print(instructions)
    else:
        print('Þetta orð finnst ekki.')
        return
    if 'et' in old_ord:

        print('\nEintala án greinis')
        et_nf_ag = input(f'Hér er {old_ord["et"]["ág"][0]}: ')
        if et_nf_ag != '':
            new_ord["et"]["ág"][0] = et_nf_ag
        et_tf_ag = input(f'Um {old_ord["et"]["ág"][1]}: ')
        if et_tf_ag != '':
            new_ord["et"]["ág"][1] = et_tf_ag
        et_thf_ag = input(f'Frá {old_ord["et"]["ág"][2]}: ')
        if et_thf_ag != '':
            new_ord["et"]["ág"][2] = et_thf_ag
        et_ef_ag = input(f'Til {old_ord["et"]["ág"][3]}: ')
        if et_ef_ag != '':
            new_ord["et"]["ág"][3] = et_ef_ag

        print('\nEintala með greinis')
        et_nf_mg = input(f'Hér er {old_ord["et"]["mg"][0]}: ')
        if et_nf_mg != '':
            new_ord["et"]["mg"][0] = et_nf_mg
        et_tf_mg = input(f'Um {old_ord["et"]["mg"][1]}: ')
        if et_tf_mg != '':
            new_ord["et"]["mg"][1] = et_tf_mg
        et_thf_mg = input(f'Frá {old_ord["et"]["mg"][2]}: ')
        if et_thf_mg != '':
            new_ord["et"]["mg"][2] = et_thf_mg
        et_ef_mg = input(f'Til {old_ord["et"]["mg"][3]}: ')
        if et_ef_mg != '':
            new_ord["et"]["mg"][3] = et_ef_mg

    if 'ft' in old_ord:
        print('\nFleirtala án greinis')
        ft_nf_ag = input(f'Hér eru {old_ord["ft"]["ág"][0]}: ')
        if ft_nf_ag != '':
            new_ord["ft"]["ág"][0] = ft_nf_ag
        ft_tf_ag = input(f'Um {old_ord["ft"]["ág"][1]}: ')
        if ft_tf_ag != '':
            new_ord["ft"]["ág"][1] = ft_tf_ag
        ft_thf_ag = input(f'Frá {old_ord["ft"]["ág"][2]}: ')
        if ft_thf_ag != '':
            new_ord["ft"]["ág"][2] = ft_thf_ag
        ft_ef_ag = input(f'Til {old_ord["ft"]["ág"][3]}: ')
        if ft_ef_ag != '':
            new_ord["ft"]["ág"][3] = ft_ef_ag

        print('\nFleirtala með greinis')
        ft_nf_mg = input(f'Hér eru {old_ord["ft"]["mg"][0]}: ')
        if ft_nf_mg != '':
            new_ord["ft"]["mg"][0] = ft_nf_mg
        ft_tf_mg = input(f'Um {old_ord["ft"]["mg"][1]}: ')
        if ft_tf_mg != '':
            new_ord["ft"]["mg"][1] = ft_tf_mg
        ft_thf_mg = input(f'Frá {old_ord["ft"]["mg"][2]}: ')
        if ft_thf_mg != '':
            new_ord["ft"]["mg"][2] = ft_thf_mg
        ft_ef_mg = input(f'Til {old_ord["ft"]["mg"][3]}: ')
        if ft_ef_mg != '':
            new_ord["ft"]["mg"][3] = ft_ef_mg
    
    new_ord['hash'] = hashify_ord_data(new_ord)

    with open(path, 'w', encoding="utf-8") as f:
        f.write(ord_data_to_fancy_json_str(new_ord))

    print('Þér hefur tekist að leiðrétta orðið, en til að uppfæra gagnagrunnin þarftu að keyra main.py -rbdb')


def input_ja_nei_cli(fyrirspurn):
    svar = None
    ja = ['já', 'ja', 'j', 'yes', 'y']
    nei = ['nei', 'n', 'no']
    svor = ja + nei
    while svar not in svor:
        if svar is not None:
            print('Vinsamlegast svaraðu "já" (já/ja/j/yes/y) eða "nei" (nei/n/no).')
        svar = input('%s (já/nei): ' % (fyrirspurn, ))
    return (svar in ja)


def input_nafnord_cli():
    data = collections.OrderedDict()
    logman.info('Add-Word-CLI: nafnorð')
    kyn = None
    while kyn not in ('kk', 'kvk', 'hk'):
        if kyn is not None:
            print('Reyndu aftur. \033[90m[Karlkyn (kk), Kvenkyn (kvk), Hvorugkyn (hk)]\033[0m')
        kyn = input('Kyn (kk/kvk/hk): ')
    data['orð'] = None
    data['flokkur'] = 'nafnorð'
    data['kyn'] = kyn
    sla_inn_eintolu = input_ja_nei_cli('Slá inn eintölu?')
    if sla_inn_eintolu is True:
        # et.ág
        fallbeyging_et_ag = input_fallbeyging_cli(
            msg_mynd='Eintala án greinis',
            msg_mynd_s='et.ág',
            msg_daemi=[
                '\033[90mhér er\033[0m \033[32mhestur\033[0m',
                '\033[90mum\033[0m \033[32mhest\033[0m',
                '\033[90mfrá\033[0m \033[32mhesti\033[0m',
                '\033[90mtil\033[0m \033[32mhests\033[0m'
            ]
        )
        data['orð'] = fallbeyging_et_ag[0]
        isl_ord_lookup = lookup_nafnord({'orð': data['orð'], 'kyn': kyn})
        if isl_ord_lookup is not None:
            raise Exception('Þetta orð er nú þegar í grunninum?')
        logman.info('kyn: %s' % (kyn, ))
        data['et'] = collections.OrderedDict()
        data['et']['ág'] = fallbeyging_et_ag
        # et.mg
        data['et']['mg'] = input_fallbeyging_cli(
            msg_mynd='Eintala með greini',
            msg_mynd_s='et.mg',
            msg_daemi=[
                '\033[90mhér er\033[0m \033[32mhesturinn\033[0m',
                '\033[90mum\033[0m \033[32mhestinn\033[0m',
                '\033[90mfrá\033[0m \033[32mhestinum\033[0m',
                '\033[90mtil\033[0m \033[32mhestsins\033[0m'
            ]
        )
    if not sla_inn_eintolu or input_ja_nei_cli('Slá inn fleirtölu?'):
        # ft.ág
        data['ft'] = collections.OrderedDict()
        data['ft']['ág'] = input_fallbeyging_cli(
            msg_mynd='Fleirtala án greinis',
            msg_mynd_s='ft.ág',
            msg_daemi=[
                '\033[90mhér eru\033[0m \033[32mhestar\033[0m',
                '\033[90mum\033[0m \033[32mhesta\033[0m',
                '\033[90mfrá\033[0m \033[32mhestum\033[0m',
                '\033[90mtil\033[0m \033[32mhesta\033[0m'
            ]
        )
        if data['orð'] is None:
            data['orð'] = data['ft']['ág'][0]
            isl_ord_lookup = lookup_nafnord({'orð': data['orð'], 'kyn': kyn})
            if isl_ord_lookup is not None:
                raise Exception('Þetta orð er nú þegar í grunninum?')
        # ft.mg
        data['ft']['mg'] = input_fallbeyging_cli(
            msg_mynd='Fleirtala með greini',
            msg_mynd_s='ft.mg',
            msg_daemi=[
                '\033[90mhér eru\033[0m \033[32mhestarnir\033[0m',
                '\033[90mum\033[0m \033[32mhestana\033[0m',
                '\033[90mfrá\033[0m \033[32mhestunum\033[0m',
                '\033[90mtil\033[0m \033[32mhestanna\033[0m'
            ]
        )
    return data


def input_lysingarord_cli():
    data = collections.OrderedDict()
    logman.info('Add-Word-CLI: lýsingarorð')
    # frumstig sb et kk
    frumstig_sb_et_kk = input_fallbeyging_cli(
        msg_mynd='Frumstig sterk beyging eintala karlkyn',
        msg_mynd_s='frumstig.sb.et.kk',
        msg_daemi=[
            '\033[90mhér er\033[0m \033[32msterkur\033[0m \033[90mhestur\033[0m',
            '\033[90mum\033[0m \033[32msterkan\033[0m \033[90mhest\033[0m',
            '\033[90mfrá\033[0m \033[32msterkum\033[0m \033[90mhesti\033[0m',
            '\033[90mtil\033[0m \033[32msterks\033[0m \033[90mhests\033[0m'
        ]
    )
    data['orð'] = frumstig_sb_et_kk[0]
    isl_ord_lookup = lookup_lysingarord({'orð': data['orð']})
    if isl_ord_lookup is not None:
        raise Exception('Þetta orð er nú þegar í grunninum?')
    data['flokkur'] = 'lýsingarorð'
    data['frumstig'] = collections.OrderedDict()
    data['frumstig']['sb'] = collections.OrderedDict()
    data['frumstig']['sb']['et'] = collections.OrderedDict()
    data['frumstig']['sb']['et']['kk'] = frumstig_sb_et_kk
    # frumstig sb et kvk
    data['frumstig']['sb']['et']['kvk'] = input_fallbeyging_cli(
        msg_mynd='Frumstig sterk beyging eintala kvenkyn',
        msg_mynd_s='frumstig.sb.et.kvk',
        msg_daemi=[
            '\033[90mhér er\033[0m \033[32msterk\033[0m \033[90mkýr\033[0m',
            '\033[90mum\033[0m \033[32msterka\033[0m \033[90mkú\033[0m',
            '\033[90mfrá\033[0m \033[32msterkri\033[0m \033[90mkú\033[0m',
            '\033[90mtil\033[0m \033[32msterkrar\033[0m \033[90mkýr\033[0m'
        ]
    )
    # frumstig sb et hk
    data['frumstig']['sb']['et']['hk'] = input_fallbeyging_cli(
        msg_mynd='Frumstig sterk beyging eintala hvorugkyn',
        msg_mynd_s='frumstig.sb.et.hk',
        msg_daemi=[
            '\033[90mhér er\033[0m \033[32msterkt\033[0m \033[90mlamb\033[0m',
            '\033[90mum\033[0m \033[32msterkt\033[0m \033[90mlamb\033[0m',
            '\033[90mfrá\033[0m \033[32msterku\033[0m \033[90mlambi\033[0m',
            '\033[90mtil\033[0m \033[32msterks\033[0m \033[90mlambs\033[0m'
        ]
    )
    # frumstig sb ft kk
    data['frumstig']['sb']['ft'] = collections.OrderedDict()
    data['frumstig']['sb']['ft']['kk'] = input_fallbeyging_cli(
        msg_mynd='Frumstig sterk beyging fleirtala karlkyn',
        msg_mynd_s='frumstig.sb.ft.kk',
        msg_daemi=[
            '\033[90mhér eru\033[0m \033[32msterkir\033[0m \033[90mhestar\033[0m',
            '\033[90mum\033[0m \033[32msterka\033[0m \033[90mhesta\033[0m',
            '\033[90mfrá\033[0m \033[32msterkum\033[0m \033[90mhestum\033[0m',
            '\033[90mtil\033[0m \033[32msterkra\033[0m \033[90mhesta\033[0m'
        ]
    )
    # frumstig sb ft kvk
    data['frumstig']['sb']['ft']['kvk'] = input_fallbeyging_cli(
        msg_mynd='Frumstig sterk beyging fleirtala kvenkyn',
        msg_mynd_s='frumstig.sb.ft.kvk',
        msg_daemi=[
            '\033[90mhér eru\033[0m \033[32msterkar\033[0m \033[90mkýr\033[0m',
            '\033[90mum\033[0m \033[32msterkar\033[0m \033[90mkýr\033[0m',
            '\033[90mfrá\033[0m \033[32msterkum\033[0m \033[90mkúm\033[0m',
            '\033[90mtil\033[0m \033[32msterkra\033[0m \033[90mkúa\033[0m'
        ]
    )
    # frumstig sb ft hk
    data['frumstig']['sb']['ft']['hk'] = input_fallbeyging_cli(
        msg_mynd='Frumstig sterk beyging fleirtala hvorugkyn',
        msg_mynd_s='frumstig.sb.ft.hk',
        msg_daemi=[
            '\033[90mhér eru\033[0m \033[32msterk\033[0m \033[90mlömb\033[0m',
            '\033[90mum\033[0m \033[32msterk\033[0m \033[90mlömb\033[0m',
            '\033[90mfrá\033[0m \033[32msterkum\033[0m \033[90mlömbum\033[0m',
            '\033[90mtil\033[0m \033[32msterkra\033[0m \033[90mlamba\033[0m'
        ]
    )
    # frumstig vb et kk
    data['frumstig']['vb'] = collections.OrderedDict()
    data['frumstig']['vb']['et'] = collections.OrderedDict()
    data['frumstig']['vb']['et']['kk'] = input_fallbeyging_cli(
        msg_mynd='Frumstig veik beyging eintala karlkyn',
        msg_mynd_s='frumstig.vb.et.kk',
        msg_daemi=[
            '\033[90mhér er\033[0m \033[32msterki\033[0m \033[90mhesturinn\033[0m',
            '\033[90mum\033[0m \033[32msterka\033[0m \033[90mhestinn\033[0m',
            '\033[90mfrá\033[0m \033[32msterka\033[0m \033[90mhestinum\033[0m',
            '\033[90mtil\033[0m \033[32msterka\033[0m \033[90mhestsins\033[0m'
        ]
    )
    # frumstig vb et kvk
    data['frumstig']['vb']['et']['kvk'] = input_fallbeyging_cli(
        msg_mynd='Frumstig veik beyging eintala kvenkyn',
        msg_mynd_s='frumstig.vb.et.kvk',
        msg_daemi=[
            '\033[90mhér er\033[0m \033[32msterka\033[0m \033[90mkýrin\033[0m',
            '\033[90mum\033[0m \033[32msterku\033[0m \033[90mkúna\033[0m',
            '\033[90mfrá\033[0m \033[32msterku\033[0m \033[90mkúnni\033[0m',
            '\033[90mtil\033[0m \033[32msterku\033[0m \033[90mkýrinnar\033[0m'
        ]
    )
    # frumstig vb et hk
    data['frumstig']['vb']['et']['hk'] = input_fallbeyging_cli(
        msg_mynd='Frumstig veik beyging eintala hvorugkyn',
        msg_mynd_s='frumstig.vb.et.hk',
        msg_daemi=[
            '\033[90mhér er\033[0m \033[32msterka\033[0m \033[90mlambið\033[0m',
            '\033[90mum\033[0m \033[32msterka\033[0m \033[90mlambið\033[0m',
            '\033[90mfrá\033[0m \033[32msterka\033[0m \033[90mlambinu\033[0m',
            '\033[90mtil\033[0m \033[32msterka\033[0m \033[90mlambsins\033[0m'
        ]
    )
    # frumstig vb ft kk
    data['frumstig']['vb']['ft'] = collections.OrderedDict()
    data['frumstig']['vb']['ft']['kk'] = input_fallbeyging_cli(
        msg_mynd='Frumstig veik beyging fleirtala karlkyn',
        msg_mynd_s='frumstig.vb.ft.kk',
        msg_daemi=[
            '\033[90mhér eru\033[0m \033[32msterku\033[0m \033[90mhestarnir\033[0m',
            '\033[90mum\033[0m \033[32msterku\033[0m \033[90mhestana\033[0m',
            '\033[90mfrá\033[0m \033[32msterku\033[0m \033[90mhestunum\033[0m',
            '\033[90mtil\033[0m \033[32msterku\033[0m \033[90mhestanna\033[0m'
        ]
    )
    # frumstig vb ft kvk
    data['frumstig']['vb']['ft']['kvk'] = input_fallbeyging_cli(
        msg_mynd='Frumstig veik beyging fleirtala kvenkyn',
        msg_mynd_s='frumstig.vb.ft.kvk',
        msg_daemi=[
            '\033[90mhér eru\033[0m \033[32msterku\033[0m \033[90mkýrnar\033[0m',
            '\033[90mum\033[0m \033[32msterku\033[0m \033[90mkýrnar\033[0m',
            '\033[90mfrá\033[0m \033[32msterku\033[0m \033[90mkúnum\033[0m',
            '\033[90mtil\033[0m \033[32msterku\033[0m \033[90mkúnna\033[0m'
        ]
    )
    # frumstig vb ft hk
    data['frumstig']['vb']['ft']['hk'] = input_fallbeyging_cli(
        msg_mynd='Frumstig veik beyging fleirtala hvorugkyn',
        msg_mynd_s='frumstig.vb.ft.hk',
        msg_daemi=[
            '\033[90mhér eru\033[0m \033[32msterku\033[0m \033[90mlömbin\033[0m',
            '\033[90mum\033[0m \033[32msterku\033[0m \033[90mlömbin\033[0m',
            '\033[90mfrá\033[0m \033[32msterku\033[0m \033[90mlömbunum\033[0m',
            '\033[90mtil\033[0m \033[32msterku\033[0m \033[90mlambanna\033[0m'
        ]
    )
    # miðstig vb et kk
    data['miðstig'] = collections.OrderedDict()
    data['miðstig']['vb'] = collections.OrderedDict()
    data['miðstig']['vb']['et'] = collections.OrderedDict()
    data['miðstig']['vb']['et']['kk'] = input_fallbeyging_cli(
        msg_mynd='Miðstig veik beyging eintala karlkyn',
        msg_mynd_s='midstig.vb.et.kk',
        msg_daemi=[
            '\033[90mhér er\033[0m \033[32msterkari\033[0m \033[90mhestur\033[0m',
            '\033[90mum\033[0m \033[32msterkari\033[0m \033[90mhest\033[0m',
            '\033[90mfrá\033[0m \033[32msterkari\033[0m \033[90mhesti\033[0m',
            '\033[90mtil\033[0m \033[32msterkari\033[0m \033[90mhests\033[0m'
        ]
    )
    # miðstig vb et kvk
    data['miðstig']['vb']['et']['kvk'] = input_fallbeyging_cli(
        msg_mynd='Miðstig veik beyging eintala kvenkyn',
        msg_mynd_s='midstig.vb.et.kvk',
        msg_daemi=[
            '\033[90mhér er\033[0m \033[32msterkari\033[0m \033[90mkýr\033[0m',
            '\033[90mum\033[0m \033[32msterkari\033[0m \033[90mkú\033[0m',
            '\033[90mfrá\033[0m \033[32msterkari\033[0m \033[90mkú\033[0m',
            '\033[90mtil\033[0m \033[32msterkari\033[0m \033[90mkýr\033[0m'
        ]
    )
    # miðstig vb et hk
    data['miðstig']['vb']['et']['hk'] = input_fallbeyging_cli(
        msg_mynd='Miðstig veik beyging eintala hvorugkyn',
        msg_mynd_s='midstig.vb.et.hk',
        msg_daemi=[
            '\033[90mhér er\033[0m \033[32msterkara\033[0m \033[90mlamb\033[0m',
            '\033[90mum\033[0m \033[32msterkara\033[0m \033[90mlamb\033[0m',
            '\033[90mfrá\033[0m \033[32msterkara\033[0m \033[90mlambi\033[0m',
            '\033[90mtil\033[0m \033[32msterkara\033[0m \033[90mlambs\033[0m'
        ]
    )
    # miðstig vb ft kk
    data['miðstig']['vb']['ft'] = collections.OrderedDict()
    data['miðstig']['vb']['ft']['kk'] = input_fallbeyging_cli(
        msg_mynd='Miðstig veik beyging fleirtala karlkyn',
        msg_mynd_s='midstig.vb.ft.kk',
        msg_daemi=[
            '\033[90mhér eru\033[0m \033[32msterkari\033[0m \033[90mhestar\033[0m',
            '\033[90mum\033[0m \033[32msterkari\033[0m \033[90mhesta\033[0m',
            '\033[90mfrá\033[0m \033[32msterkari\033[0m \033[90mhestum\033[0m',
            '\033[90mtil\033[0m \033[32msterkari\033[0m \033[90mhesta\033[0m'
        ]
    )
    # miðstig vb ft kvk
    data['miðstig']['vb']['ft']['kvk'] = input_fallbeyging_cli(
        msg_mynd='Miðstig veik beyging fleirtala kvenkyn',
        msg_mynd_s='midstig.vb.ft.kvk',
        msg_daemi=[
            '\033[90mhér eru\033[0m \033[32msterkari\033[0m \033[90mkýr\033[0m',
            '\033[90mum\033[0m \033[32msterkari\033[0m \033[90mkýr\033[0m',
            '\033[90mfrá\033[0m \033[32msterkari\033[0m \033[90mkúm\033[0m',
            '\033[90mtil\033[0m \033[32msterkari\033[0m \033[90mkúa\033[0m'
        ]
    )
    # miðstig vb ft hk
    data['miðstig']['vb']['ft']['hk'] = input_fallbeyging_cli(
        msg_mynd='Miðstig veik beyging fleirtala hvorugkyn',
        msg_mynd_s='midstig.vb.ft.hk',
        msg_daemi=[
            '\033[90mhér eru\033[0m \033[32msterkari\033[0m \033[90mlömb\033[0m',
            '\033[90mum\033[0m \033[32msterkari\033[0m \033[90mlömb\033[0m',
            '\033[90mfrá\033[0m \033[32msterkari\033[0m \033[90mlömbum\033[0m',
            '\033[90mtil\033[0m \033[32msterkari\033[0m \033[90mlamba\033[0m'
        ]
    )
    # efstastig sb et kk
    data['efstastig'] = collections.OrderedDict()
    data['efstastig']['sb'] = collections.OrderedDict()
    data['efstastig']['sb']['et'] = collections.OrderedDict()
    data['efstastig']['sb']['et']['kk'] = input_fallbeyging_cli(
        msg_mynd='Efstastig sterk beyging eintala karlkyn',
        msg_mynd_s='efstastig.sb.et.kk',
        msg_daemi=[
            '\033[90mhér er hestur\033[0m \033[32msterkastur\033[0m',
            '\033[90mum hest\033[0m \033[32msterkastan\033[0m',
            '\033[90mfrá hesti\033[0m \033[32msterkustum\033[0m',
            '\033[90mtil hests\033[0m \033[32msterkasts\033[0m'
        ]
    )
    # efstastig sb et kvk
    data['efstastig']['sb']['et']['kvk'] = input_fallbeyging_cli(
        msg_mynd='Efstastig sterk beyging eintala kvenkyn',
        msg_mynd_s='efstastig.sb.et.kvk',
        msg_daemi=[
            '\033[90mhér er kýr\033[0m \033[32msterkust\033[0m',
            '\033[90mum kú\033[0m \033[32msterkasta\033[0m',
            '\033[90mfrá kú\033[0m \033[32msterkastri\033[0m',
            '\033[90mtil kýr\033[0m \033[32msterkastrar\033[0m'
        ]
    )
    # efstastig sb et hk
    data['efstastig']['sb']['et']['hk'] = input_fallbeyging_cli(
        msg_mynd='Efstastig sterk beyging eintala hvorugkyn',
        msg_mynd_s='efstastig.sb.et.hk',
        msg_daemi=[
            '\033[90mhér er lamb\033[0m \033[32msterkast\033[0m',
            '\033[90mum lamb\033[0m \033[32msterkast\033[0m',
            '\033[90mfrá lambi\033[0m \033[32msterkustu\033[0m',
            '\033[90mtil lambs\033[0m \033[32msterkasts\033[0m'
        ]
    )
    # efstastig sb ft kk
    data['efstastig']['sb']['ft'] = collections.OrderedDict()
    data['efstastig']['sb']['ft']['kk'] = input_fallbeyging_cli(
        msg_mynd='Efstastig sterk beyging fleirtala karlkyn',
        msg_mynd_s='efstastig.sb.ft.kk',
        msg_daemi=[
            '\033[90mhér eru hestar\033[0m \033[32msterkastir\033[0m',
            '\033[90mum hesta\033[0m \033[32msterkasta\033[0m',
            '\033[90mfrá hestum\033[0m \033[32msterkustum\033[0m',
            '\033[90mtil hesta\033[0m \033[32msterkastra\033[0m'
        ]
    )
    # efstastig sb ft kvk
    data['efstastig']['sb']['ft']['kvk'] = input_fallbeyging_cli(
        msg_mynd='Efstastig sterk beyging fleirtala kvenkyn',
        msg_mynd_s='efstastig.sb.ft.kvk',
        msg_daemi=[
            '\033[90mhér eru kýr\033[0m \033[32msterkastar\033[0m',
            '\033[90mum kýr\033[0m \033[32msterkastar\033[0m',
            '\033[90mfrá kúm\033[0m \033[32msterkustum\033[0m',
            '\033[90mtil kúa\033[0m \033[32msterkastra\033[0m'
        ]
    )
    # efstastig sb ft hk
    data['efstastig']['sb']['ft']['hk'] = input_fallbeyging_cli(
        msg_mynd='Efstastig sterk beyging fleirtala hvorugkyn',
        msg_mynd_s='efstastig.sb.ft.hk',
        msg_daemi=[
            '\033[90mhér eru lömb\033[0m \033[32msterkust\033[0m',
            '\033[90mum lömb\033[0m \033[32msterkust\033[0m',
            '\033[90mfrá lömbum\033[0m \033[32msterkustum\033[0m',
            '\033[90mtil lamba\033[0m \033[32msterkastra\033[0m'
        ]
    )
    # efstastig vb et kk
    data['efstastig']['vb'] = collections.OrderedDict()
    data['efstastig']['vb']['et'] = collections.OrderedDict()
    data['efstastig']['vb']['et']['kk'] = input_fallbeyging_cli(
        msg_mynd='Efstastig veik beyging eintala karlkyn',
        msg_mynd_s='miðstig.vb.et.kk',
        msg_daemi=[
            '\033[90mhér er\033[0m \033[32msterkasti\033[0m \033[90mhesturinn\033[0m',
            '\033[90mum\033[0m \033[32msterkasta\033[0m \033[90mhestinn\033[0m',
            '\033[90mfrá\033[0m \033[32msterkasta\033[0m \033[90mhestinum\033[0m',
            '\033[90mtil\033[0m \033[32msterkasta\033[0m \033[90mhestsins\033[0m'
        ]
    )
    # efstastig vb et kvk
    data['efstastig']['vb']['et']['kvk'] = input_fallbeyging_cli(
        msg_mynd='Efstastig veik beyging eintala kvenkyn',
        msg_mynd_s='miðstig.vb.et.kvk',
        msg_daemi=[
            '\033[90mhér er\033[0m \033[32msterkasta\033[0m \033[90mkýrin\033[0m',
            '\033[90mum\033[0m \033[32msterkustu\033[0m \033[90mkúna\033[0m',
            '\033[90mfrá\033[0m \033[32msterkustu\033[0m \033[90mkúnni\033[0m',
            '\033[90mtil\033[0m \033[32msterkustu\033[0m \033[90mkýrinnar\033[0m'
        ]
    )
    # efstastig vb et hk
    data['efstastig']['vb']['et']['hk'] = input_fallbeyging_cli(
        msg_mynd='Efstastig veik beyging eintala hvorugkyn',
        msg_mynd_s='miðstig.vb.et.hk',
        msg_daemi=[
            '\033[90mhér er\033[0m \033[32msterkasta\033[0m \033[90mlambið\033[0m',
            '\033[90mum\033[0m \033[32msterkasta\033[0m \033[90mlambið\033[0m',
            '\033[90mfrá\033[0m \033[32msterkasta\033[0m \033[90mlambinu\033[0m',
            '\033[90mtil\033[0m \033[32msterkasta\033[0m \033[90mlambsins\033[0m'
        ]
    )
    # efstastig vb ft kk
    data['efstastig']['vb']['ft'] = collections.OrderedDict()
    data['efstastig']['vb']['ft']['kk'] = input_fallbeyging_cli(
        msg_mynd='Efstastig veik beyging fleirtala karlkyn',
        msg_mynd_s='miðstig.vb.ft.kk',
        msg_daemi=[
            '\033[90mhér eru\033[0m \033[32msterkustu\033[0m \033[90mhestarnir\033[0m',
            '\033[90mum\033[0m \033[32msterkustu\033[0m \033[90mhestana\033[0m',
            '\033[90mfrá\033[0m \033[32msterkustu\033[0m \033[90mhestunum\033[0m',
            '\033[90mtil\033[0m \033[32msterkustu\033[0m \033[90mhestanna\033[0m'
        ]
    )
    # efstastig vb ft kvk
    data['efstastig']['vb']['ft']['kvk'] = input_fallbeyging_cli(
        msg_mynd='Efstastig veik beyging fleirtala kvenkyn',
        msg_mynd_s='miðstig.vb.ft.kk',
        msg_daemi=[
            '\033[90mhér eru\033[0m \033[32msterkustu\033[0m \033[90mkýrnar\033[0m',
            '\033[90mum\033[0m \033[32msterkustu\033[0m \033[90mkýrnar\033[0m',
            '\033[90mfrá\033[0m \033[32msterkustu\033[0m \033[90mkúnum\033[0m',
            '\033[90mtil\033[0m \033[32msterkustu\033[0m \033[90mkúnna\033[0m'
        ]
    )
    # efstastig vb ft hk
    data['efstastig']['vb']['ft']['hk'] = input_fallbeyging_cli(
        msg_mynd='Efstastig veik beyging fleirtala hvorugkyn',
        msg_mynd_s='miðstig.vb.ft.hk',
        msg_daemi=[
            '\033[90mhér eru\033[0m \033[32msterkustu\033[0m \033[90mlömbin\033[0m',
            '\033[90mum\033[0m \033[32msterkustu\033[0m \033[90mlömbin\033[0m',
            '\033[90mfrá\033[0m \033[32msterkustu\033[0m \033[90mlömbunum\033[0m',
            '\033[90mtil\033[0m \033[32msterkustu\033[0m \033[90mlambanna\033[0m'
        ]
    )
    return data


def input_sagnord_cli():
    data = collections.OrderedDict()
    logman.info('Add-Word-CLI: sagnorð')
    germynd_nafnhattur = input(
        'Germynd nafnháttur (dæmi: \033[90mað\033[0m \033[32mgefa\033[0m): '
    )
    data['orð'] = germynd_nafnhattur
    isl_ord_lookup = lookup_sagnord({'orð': data['orð']})
    if isl_ord_lookup is not None:
        raise Exception('Þetta orð er nú þegar í grunninum?')
    data['flokkur'] = 'sagnorð'
    data['germynd'] = collections.OrderedDict()
    data['germynd']['nafnháttur'] = germynd_nafnhattur
    logman.info('germynd.nafnhattur: %s' % (germynd_nafnhattur, ))
    germynd_sagnbot = input(
        'Germynd sagnbót (dæmi: \033[90még hef\033[0m \033[32mgefið\033[0m): '
    )
    data['germynd']['sagnbót'] = germynd_sagnbot
    logman.info('germynd.sagnbot: %s' % (germynd_sagnbot, ))
    germynd_bodhattur_styfdur = input(
        'Germynd boðháttur stýfður (dæmi: \033[32mgef\033[0m \033[90mþú\033[0m): '
    )
    data['germynd']['boðháttur'] = collections.OrderedDict()
    data['germynd']['boðháttur']['stýfður'] = germynd_bodhattur_styfdur
    logman.info('germynd.boðháttur.stýfður: %s' % (germynd_bodhattur_styfdur, ))
    germynd_bodhattur_et = input(
        'Germynd boðháttur eintala (dæmi: \033[32mgefðu\033[0m): '
    )
    data['germynd']['boðháttur']['et'] = germynd_bodhattur_et
    logman.info('germynd.boðháttur.et: %s' % (germynd_bodhattur_et, ))
    germynd_bodhattur_ft = input(
        'Germynd boðháttur fleirtala (dæmi: \033[32mgefið\033[0m \033[90mþið\033[0m): '
    )
    data['germynd']['boðháttur']['ft'] = germynd_bodhattur_ft
    logman.info('germynd.boðháttur.ft: %s' % (germynd_bodhattur_ft, ))
    # germynd persónuleg framsöguháttur nútíð et
    data['germynd']['persónuleg'] = collections.OrderedDict()
    data['germynd']['persónuleg']['framsöguháttur'] = collections.OrderedDict()
    data['germynd']['persónuleg']['framsöguháttur']['nútíð'] = collections.OrderedDict()
    data['germynd']['persónuleg']['framsöguháttur']['nútíð']['et'] = input_personubeyging_cli(
        msg_mynd='Germynd persónuleg framsöguháttur nútíð eintala',
        msg_mynd_s='germynd.personuleg.framsoguhattur.nutid.et',
        msg_daemi=[
            '\033[90még\033[0m \033[32mgef\033[0m',
            '\033[90mþú\033[0m \033[32mgefur\033[0m',
            '\033[90mhann/hún/það\033[0m \033[32mgefur\033[0m'
        ]
    )
    # germynd persónuleg framsöguháttur nútíð ft
    data['germynd']['persónuleg']['framsöguháttur']['nútíð']['ft'] = input_personubeyging_cli(
        msg_mynd='Germynd persónuleg framsöguháttur nútíð fleirtala',
        msg_mynd_s='germynd.personuleg.framsoguhattur.nutid.ft',
        msg_daemi=[
            '\033[90mvið\033[0m \033[32mgefum\033[0m',
            '\033[90mþið\033[0m \033[32mgefið\033[0m',
            '\033[90mþeir/þær/þau\033[0m \033[32mgefa\033[0m'
        ]
    )
    # germynd persónuleg framsöguháttur þátíð et
    data['germynd']['persónuleg']['framsöguháttur']['þátíð'] = collections.OrderedDict()
    data['germynd']['persónuleg']['framsöguháttur']['þátíð']['et'] = input_personubeyging_cli(
        msg_mynd='Germynd persónuleg framsöguháttur þátíð eintala',
        msg_mynd_s='germynd.personuleg.framsoguhattur.thatid.et',
        msg_daemi=[
            '\033[90még\033[0m \033[32mgaf\033[0m',
            '\033[90mþú\033[0m \033[32mgafst\033[0m',
            '\033[90mhann/hún/það\033[0m \033[32mgaf\033[0m'
        ]
    )
    # germynd persónuleg framsöguháttur þátíð ft
    data['germynd']['persónuleg']['framsöguháttur']['þátíð']['ft'] = input_personubeyging_cli(
        msg_mynd='Germynd persónuleg framsöguháttur þátíð fleirtala',
        msg_mynd_s='germynd.personuleg.framsoguhattur.thatid.ft',
        msg_daemi=[
            '\033[90mvið\033[0m \033[32mgáfum\033[0m',
            '\033[90mþið\033[0m \033[32mgáfuð\033[0m',
            '\033[90mþeir/þær/þau\033[0m \033[32mgáfu\033[0m'
        ]
    )
    # germynd persónuleg viðtengingarháttur nútíð et
    data['germynd']['persónuleg']['viðtengingarháttur'] = collections.OrderedDict()
    data['germynd']['persónuleg']['viðtengingarháttur']['nútíð'] = collections.OrderedDict()
    data['germynd']['persónuleg']['viðtengingarháttur']['nútíð']['et'] = input_personubeyging_cli(
        msg_mynd='Germynd persónuleg viðtengingarháttur nútíð eintala',
        msg_mynd_s='germynd.personuleg.vidtengingarhattur.nutid.et',
        msg_daemi=[
            '\033[90mþótt ég\033[0m \033[32mgefi\033[0m',
            '\033[90mþótt þú\033[0m \033[32mgefir\033[0m',
            '\033[90mþótt hann/hún/það\033[0m \033[32mgefi\033[0m'
        ]
    )
    # germynd persónuleg viðtengingarháttur nútíð ft
    data['germynd']['persónuleg']['viðtengingarháttur']['nútíð']['ft'] = input_personubeyging_cli(
        msg_mynd='Germynd persónuleg viðtengingarháttur nútíð fleirtala',
        msg_mynd_s='germynd.personuleg.vidtengingarhattur.nutid.et',
        msg_daemi=[
            '\033[90mþótt við\033[0m \033[32mgefum\033[0m',
            '\033[90mþótt þið\033[0m \033[32mgefið\033[0m',
            '\033[90mþótt þeir/þær/þau\033[0m \033[32mgefi\033[0m'
        ]
    )
    # germynd persónuleg viðtengingarháttur þátíð et
    data['germynd']['persónuleg']['viðtengingarháttur']['þátíð'] = collections.OrderedDict()
    data['germynd']['persónuleg']['viðtengingarháttur']['þátíð']['et'] = input_personubeyging_cli(
        msg_mynd='Germynd persónuleg viðtengingarháttur þátíð eintala',
        msg_mynd_s='germynd.personuleg.vidtengingarhattur.thatid.et',
        msg_daemi=[
            '\033[90mþótt ég\033[0m \033[32mgæfi\033[0m',
            '\033[90mþótt þú\033[0m \033[32mgæfir\033[0m',
            '\033[90mþótt hann/hún/það\033[0m \033[32mgæfi\033[0m'
        ]
    )
    # germynd persónuleg viðtengingarháttur þátíð ft
    data['germynd']['persónuleg']['viðtengingarháttur']['þátíð']['ft'] = input_personubeyging_cli(
        msg_mynd='Germynd persónuleg viðtengingarháttur þátíð fleirtala',
        msg_mynd_s='germynd.personuleg.vidtengingarhattur.thatid.ft',
        msg_daemi=[
            '\033[90mþótt við\033[0m \033[32mgæfum\033[0m',
            '\033[90mþótt þið\033[0m \033[32mgæfuð\033[0m',
            '\033[90mþótt þeir/þær/þau\033[0m \033[32mgæfu\033[0m'
        ]
    )
    # germynd spurnarmyndir framsöguháttur nútíð et
    data['germynd']['spurnarmyndir'] = collections.OrderedDict()
    data['germynd']['spurnarmyndir']['framsöguháttur'] = collections.OrderedDict()
    data['germynd']['spurnarmyndir']['framsöguháttur']['nútíð'] = collections.OrderedDict()
    germynd_spurnarmyndir_framsoguhattur_nutid_et = input((
        'Germynd spurnarmynd framsöguháttur nútíð eintala '
        '(dæmi: \033[32mgefurðu\033[0m): '
    ))
    data['germynd']['spurnarmyndir']['framsöguháttur']['nútíð']['et'] = (
        germynd_spurnarmyndir_framsoguhattur_nutid_et
    )
    logman.info('germynd.spurnarmynd.framsoguhattur.nutid.et: %s' % (
        germynd_spurnarmyndir_framsoguhattur_nutid_et,
    ))
    # germynd spurnarmyndir framsöguháttur nútíð ft
    germynd_spurnarmyndir_framsoguhattur_nutid_ft = input((
        'Germynd spurnarmynd framsöguháttur nútíð fleirtala '
        '(dæmi: \033[32mgefiði\033[0m \033[90mykkar orð til Loka\033[0m): '
    ))
    data['germynd']['spurnarmyndir']['framsöguháttur']['nútíð']['ft'] = (
        germynd_spurnarmyndir_framsoguhattur_nutid_ft
    )
    logman.info('germynd.spurnarmynd.framsoguhattur.nutid.ft: %s' % (
        germynd_spurnarmyndir_framsoguhattur_nutid_ft,
    ))
    # germynd spurnarmyndir framsöguháttur þátíð et
    data['germynd']['spurnarmyndir']['framsöguháttur']['þátíð'] = collections.OrderedDict()
    germynd_spurnarmyndir_framsoguhattur_thatid_et = input((
        'Germynd spurnarmynd framsöguháttur þátíð eintala '
        '(dæmi: \033[32mgafstu\033[0m): '
    ))
    data['germynd']['spurnarmyndir']['framsöguháttur']['þátíð']['et'] = (
        germynd_spurnarmyndir_framsoguhattur_thatid_et
    )
    logman.info('germynd.spurnarmynd.framsoguhattur.thatid.et: %s' % (
        germynd_spurnarmyndir_framsoguhattur_thatid_et,
    ))
    # germynd spurnarmyndir framsöguháttur þátíð ft
    germynd_spurnarmyndir_framsoguhattur_thatid_ft = input((
        'Germynd spurnarmynd framsöguháttur þátíð fleirtala '
        '(dæmi: \033[32mgáfuði\033[0m): '
    ))
    data['germynd']['spurnarmyndir']['framsöguháttur']['þátíð']['ft'] = (
        germynd_spurnarmyndir_framsoguhattur_thatid_ft
    )
    logman.info('germynd.spurnarmynd.framsoguhattur.thatid.ft: %s' % (
        germynd_spurnarmyndir_framsoguhattur_thatid_ft,
    ))
    # germynd spurnarmyndir viðtengingarháttur nútíð et
    data['germynd']['spurnarmyndir']['viðtengingarháttur'] = collections.OrderedDict()
    data['germynd']['spurnarmyndir']['viðtengingarháttur']['nútíð'] = collections.OrderedDict()
    germynd_spurnarmyndir_vidteningarhattur_nutid_et = input((
        'Germynd spurnarmynd viðtengingarháttur nútíð eintala '
        '(dæmi: \033[32mgefirðu\033[0m): '
    ))
    data['germynd']['spurnarmyndir']['viðtengingarháttur']['nútíð']['et'] = (
        germynd_spurnarmyndir_vidteningarhattur_nutid_et
    )
    logman.info('germynd.spurnarmynd.vidtengingarhattur.nutid.et: %s' % (
        germynd_spurnarmyndir_vidteningarhattur_nutid_et,
    ))
    # germynd spurnarmyndir viðtengingarháttur nútíð ft
    germynd_spurnarmyndir_vidteningarhattur_nutid_ft = input((
        'Germynd spurnarmynd viðtengingarháttur nútíð fleirtala '
        '(dæmi: \033[32mgefiði\033[0m \033[90morð þá gleður það Loka\033[0m): '
    ))
    data['germynd']['spurnarmyndir']['viðtengingarháttur']['nútíð']['ft'] = (
        germynd_spurnarmyndir_vidteningarhattur_nutid_ft
    )
    logman.info('germynd.spurnarmynd.vidtengingarhattur.nutid.ft: %s' % (
        germynd_spurnarmyndir_vidteningarhattur_nutid_ft,
    ))
    # germynd spurnarmyndir viðtengingarháttur þátíð et
    data['germynd']['spurnarmyndir']['viðtengingarháttur']['þátíð'] = collections.OrderedDict()
    germynd_spurnarmyndir_vidteningarhattur_thatid_et = input((
        'Germynd spurnarmynd viðtengingarháttur þátíð eintala '
        '(dæmi: \033[32mgæfirðu\033[0m): '
    ))
    data['germynd']['spurnarmyndir']['viðtengingarháttur']['þátíð']['et'] = (
        germynd_spurnarmyndir_vidteningarhattur_thatid_et
    )
    logman.info('germynd.spurnarmynd.vidtengingarhattur.thatid.et: %s' % (
        germynd_spurnarmyndir_vidteningarhattur_thatid_et,
    ))
    # germynd spurnarmyndir viðtengingarháttur þátíð ft
    germynd_spurnarmyndir_vidteningarhattur_thatid_ft = input((
        'Germynd spurnarmynd viðtengingarháttur þátíð fleirtala '
        '(dæmi: \033[32mgæfuði\033[0m): '
    ))
    data['germynd']['spurnarmyndir']['viðtengingarháttur']['þátíð']['ft'] = (
        germynd_spurnarmyndir_vidteningarhattur_thatid_ft
    )
    logman.info('germynd.spurnarmynd.vidtengingarhattur.thatid.ft: %s' % (
        germynd_spurnarmyndir_vidteningarhattur_thatid_ft,
    ))
    # miðmynd nafnháttur
    data['miðmynd'] = collections.OrderedDict()
    midmynd_nafnhattur = input(
        'Miðmynd nafnháttur (dæmi: \033[90mað\033[0m \033[32mgefast\033[0m): '
    )
    data['miðmynd']['nafnháttur'] = midmynd_nafnhattur
    logman.info('midmynd.nafnhattur: %s' % (midmynd_nafnhattur, ))
    # miðmynd sagnbót
    midmynd_sagnbot = input(
        'Miðmynd sagnbót (dæmi: \033[90még hef\033[0m \033[32mgefist\033[0m): '
    )
    data['miðmynd']['sagnbót'] = midmynd_nafnhattur
    logman.info('midmynd.sagnbot: %s' % (midmynd_nafnhattur, ))
    # miðmynd boðháttur eintala
    midmynd_bodhattur_et = input(
        'Miðmynd boðháttur eintala (dæmi: \033[32mgefstu\033[0m \033[90mupp\033[0m): '
    )
    if midmynd_bodhattur_et.strip() != '':
        data['miðmynd']['boðháttur'] = collections.OrderedDict()
        data['miðmynd']['boðháttur']['et'] = midmynd_bodhattur_et
        logman.info('midmynd.boðháttur.et: %s' % (midmynd_bodhattur_et, ))
    # miðmynd boðháttur fleirtala
    midmynd_bodhattur_ft = input(
        'Miðmynd boðháttur fleirtala (dæmi: \033[32mgefist\033[0m \033[90mupp\033[0m): '
    )
    if midmynd_bodhattur_ft.strip() != '':
        if 'boðháttur' not in data['miðmynd']:
            data['miðmynd']['boðháttur'] = collections.OrderedDict()
        data['miðmynd']['boðháttur']['ft'] = midmynd_bodhattur_et
        logman.info('midmynd.boðháttur.ft: %s' % (midmynd_bodhattur_et, ))
    # miðmynd persónuleg framsöguháttur nútíð eintala
    data['miðmynd']['persónuleg'] = collections.OrderedDict()
    data['miðmynd']['persónuleg']['framsöguháttur'] = collections.OrderedDict()
    data['miðmynd']['persónuleg']['framsöguháttur']['nútíð'] = collections.OrderedDict()
    data['miðmynd']['persónuleg']['framsöguháttur']['nútíð']['et'] = input_personubeyging_cli(
        msg_mynd='Miðmynd persónuleg framsöguháttur nútíð eintala',
        msg_mynd_s='midmynd.personuleg.framsoguhattur.nutid.et',
        msg_daemi=[
            '\033[90még\033[0m \033[32mgefst\033[0m',
            '\033[90mþú\033[0m \033[32mgefst\033[0m',
            '\033[90mhann/hún/það\033[0m \033[32mgefst\033[0m'
        ]
    )
    # miðmynd persónuleg framsöguháttur nútíð fleirtala
    data['miðmynd']['persónuleg']['framsöguháttur']['nútíð']['ft'] = input_personubeyging_cli(
        msg_mynd='Miðmynd persónuleg framsöguháttur nútíð fleirtala',
        msg_mynd_s='midmynd.personuleg.framsoguhattur.nutid.ft',
        msg_daemi=[
            '\033[90mvið\033[0m \033[32mgefumst\033[0m',
            '\033[90mþið\033[0m \033[32mgefist\033[0m',
            '\033[90mþeir/þær/þau\033[0m \033[32mgefsast\033[0m'
        ]
    )
    # miðmynd persónuleg framsöguháttur þátíð eintala
    data['miðmynd']['persónuleg']['framsöguháttur']['þátíð'] = collections.OrderedDict()
    data['miðmynd']['persónuleg']['framsöguháttur']['þátíð']['et'] = input_personubeyging_cli(
        msg_mynd='Miðmynd persónuleg framsöguháttur þátíð eintala',
        msg_mynd_s='midmynd.personuleg.framsoguhattur.thatid.et',
        msg_daemi=[
            '\033[90még\033[0m \033[32mgafst\033[0m',
            '\033[90mþú\033[0m \033[32mgafst\033[0m',
            '\033[90mhann/hún/það\033[0m \033[32mgafst\033[0m'
        ]
    )
    # miðmynd persónuleg framsöguháttur þátíð fleirtala
    data['miðmynd']['persónuleg']['framsöguháttur']['þátíð']['ft'] = input_personubeyging_cli(
        msg_mynd='Miðmynd persónuleg framsöguháttur þátíð fleirtala',
        msg_mynd_s='midmynd.personuleg.framsoguhattur.thatid.ft',
        msg_daemi=[
            '\033[90mvið\033[0m \033[32mgáfumst\033[0m',
            '\033[90mþið\033[0m \033[32mgáfust\033[0m',
            '\033[90mþeir/þær/þau\033[0m \033[32mgáfust\033[0m'
        ]
    )
    # miðmynd persónuleg viðtengingarháttur nútíð eintala
    data['miðmynd']['persónuleg']['viðtengingarháttur'] = collections.OrderedDict()
    data['miðmynd']['persónuleg']['viðtengingarháttur']['nútíð'] = collections.OrderedDict()
    data['miðmynd']['persónuleg']['viðtengingarháttur']['nútíð']['et'] = input_personubeyging_cli(
        msg_mynd='Miðmynd persónuleg viðtengingarháttur nútíð eintala',
        msg_mynd_s='midmynd.personuleg.vidtengingarhattur.nutid.et',
        msg_daemi=[
            '\033[90mþó ég\033[0m \033[32mgefist\033[0m',
            '\033[90mþó þú\033[0m \033[32mgefist\033[0m',
            '\033[90mþó hann/hún/það\033[0m \033[32mgefist\033[0m'
        ]
    )
    # miðmynd persónuleg viðtengingarháttur nútíð fleirtala
    data['miðmynd']['persónuleg']['viðtengingarháttur']['nútíð']['ft'] = input_personubeyging_cli(
        msg_mynd='Miðmynd persónuleg viðtengingarháttur nútíð fleirtala',
        msg_mynd_s='midmynd.personuleg.vidtengingarhattur.nutid.ft',
        msg_daemi=[
            '\033[90mþó við\033[0m \033[32mgefumst\033[0m',
            '\033[90mþó þið\033[0m \033[32mgefist\033[0m',
            '\033[90mþó þeir/þær/þau\033[0m \033[32mgefist\033[0m'
        ]
    )
    # miðmynd persónuleg viðtengingarháttur þátíð eintala
    data['miðmynd']['persónuleg']['viðtengingarháttur']['þátíð'] = collections.OrderedDict()
    data['miðmynd']['persónuleg']['viðtengingarháttur']['þátíð']['et'] = input_personubeyging_cli(
        msg_mynd='Miðmynd persónuleg viðtengingarháttur þátíð eintala',
        msg_mynd_s='midmynd.personuleg.vidtengingarhattur.thatid.et',
        msg_daemi=[
            '\033[90mþó ég\033[0m \033[32mgæfist\033[0m',
            '\033[90mþó þú\033[0m \033[32mgæfist\033[0m',
            '\033[90mþó hann/hún/það\033[0m \033[32mgæfist\033[0m'
        ]
    )
    # miðmynd persónuleg viðtengingarháttur þátíð fleirtala
    data['miðmynd']['persónuleg']['viðtengingarháttur']['þátíð']['ft'] = input_personubeyging_cli(
        msg_mynd='Miðmynd persónuleg viðtengingarháttur þátíð fleirtala',
        msg_mynd_s='midmynd.personuleg.vidtengingarhattur.thatid.ft',
        msg_daemi=[
            '\033[90mþó við\033[0m \033[32mgæfumst\033[0m',
            '\033[90mþó þið\033[0m \033[32mgæfust\033[0m',
            '\033[90mþó þeir/þær/þau\033[0m \033[32mgæfust\033[0m'
        ]
    )
    # miðmynd spurnarmyndir framsöguháttur nútíð eintala
    data['miðmynd']['spurnarmyndir'] = collections.OrderedDict()
    data['miðmynd']['spurnarmyndir']['framsöguháttur'] = collections.OrderedDict()
    data['miðmynd']['spurnarmyndir']['framsöguháttur']['nútíð'] = collections.OrderedDict()
    midmynd_spurnarmyndir_framsoguhattur_nutid_et = input((
        'Miðmynd spurnarmyndir framsöguháttur nútíð eintala '
        '(dæmi: \033[32mgefstu\033[0m): '
    ))
    data['miðmynd']['spurnarmyndir']['framsöguháttur']['nútíð']['et'] = (
        midmynd_spurnarmyndir_framsoguhattur_nutid_et
    )
    logman.info('midmynd.spurnarmynd.framsoguhattur.nutid.et: %s' % (
        midmynd_spurnarmyndir_framsoguhattur_nutid_et,
    ))
    # miðmynd spurnarmyndir framsöguháttur þátíð eintala
    data['miðmynd']['spurnarmyndir']['framsöguháttur']['þátíð'] = collections.OrderedDict()
    midmynd_spurnarmyndir_framsoguhattur_thatid_et = input((
        'Miðmynd spurnarmyndir framsöguháttur þátíð eintala '
        '(dæmi: \033[32mgafstu\033[0m): '
    ))
    data['miðmynd']['spurnarmyndir']['framsöguháttur']['þátíð']['et'] = (
        midmynd_spurnarmyndir_framsoguhattur_thatid_et
    )
    logman.info('midmynd.spurnarmynd.framsoguhattur.thatid.et: %s' % (
        midmynd_spurnarmyndir_framsoguhattur_thatid_et,
    ))
    # miðmynd spurnarmyndir viðtengingarháttur nútíð eintala
    data['miðmynd']['spurnarmyndir']['viðtengingarháttur'] = collections.OrderedDict()
    data['miðmynd']['spurnarmyndir']['viðtengingarháttur']['nútíð'] = collections.OrderedDict()
    midmynd_spurnarmyndir_vidtengingarhattur_nutid_et = input((
        'Miðmynd spurnarmyndir viðtengingarháttur nútíð eintala '
        '(dæmi: \033[32mgefistu\033[0m): '
    ))
    data['miðmynd']['spurnarmyndir']['viðtengingarháttur']['nútíð']['et'] = (
        midmynd_spurnarmyndir_vidtengingarhattur_nutid_et
    )
    logman.info('midmynd.spurnarmynd.vidtengingarhattur.nutid.et: %s' % (
        midmynd_spurnarmyndir_vidtengingarhattur_nutid_et,
    ))
    # miðmynd spurnarmyndir viðtengingarháttur þátíð eintala
    data['miðmynd']['spurnarmyndir']['viðtengingarháttur']['þátíð'] = collections.OrderedDict()
    midmynd_spurnarmyndir_vidtengingarhattur_thatid_et = input((
        'Miðmynd spurnarmyndir viðtengingarháttur þátið eintala '
        '(dæmi: \033[32mgæfistu\033[0m): '
    ))
    data['miðmynd']['spurnarmyndir']['viðtengingarháttur']['þátíð']['et'] = (
        midmynd_spurnarmyndir_vidtengingarhattur_thatid_et
    )
    logman.info('midmynd.spurnarmynd.vidtengingarhattur.thatid.et: %s' % (
        midmynd_spurnarmyndir_vidtengingarhattur_thatid_et,
    ))
    # lýsingarháttur nútíðar
    data['lýsingarháttur'] = collections.OrderedDict()
    lysingarhattur_nutidar = input(
        'Lýsingarháttur nútíðar (dæmi: einhver er \033[32mgefandi\033[0m): '
    )
    data['lýsingarháttur']['nútíðar'] = lysingarhattur_nutidar
    logman.info('lysingarhattur.nutidar: %s' % (lysingarhattur_nutidar, ))
    # lýsingarháttur þátíðar sterk beyging eintala kk
    data['lýsingarháttur']['þátíðar'] = collections.OrderedDict()
    data['lýsingarháttur']['þátíðar']['sb'] = collections.OrderedDict()
    data['lýsingarháttur']['þátíðar']['sb']['et'] = collections.OrderedDict()
    data['lýsingarháttur']['þátíðar']['sb']['et']['kk'] = input_fallbeyging_cli(
        msg_mynd='Lýsingarháttur þátíðar sterk beyging eintala karlkyn',
        msg_mynd_s='lysingarhattur.þatid.sb.et.kk',
        msg_daemi=[
            '\033[90mhér er\033[0m \033[32mgefinn\033[0m \033[90mhestur\033[0m',
            '\033[90mum\033[0m \033[32mgefinn\033[0m \033[90mhest\033[0m',
            '\033[90mfrá\033[0m \033[32mgefnum\033[0m \033[90mhesti\033[0m',
            '\033[90mtil\033[0m \033[32mgefins\033[0m \033[90mhests\033[0m'
        ]
    )
    # lýsingarháttur þátíðar sterk beyging eintala kvk
    data['lýsingarháttur']['þátíðar']['sb']['et']['kvk'] = input_fallbeyging_cli(
        msg_mynd='Lýsingarháttur þátíðar sterk beyging eintala kvenkyn',
        msg_mynd_s='lysingarhattur.þatid.sb.et.kvk',
        msg_daemi=[
            '\033[90mhér er\033[0m \033[32mgefin\033[0m \033[90mkýr\033[0m',
            '\033[90mum\033[0m \033[32mgefna\033[0m \033[90mkú\033[0m',
            '\033[90mfrá\033[0m \033[32mgefinni\033[0m \033[90mkú\033[0m',
            '\033[90mtil\033[0m \033[32mgefinnar\033[0m \033[90mkýr\033[0m'
        ]
    )
    # lýsingarháttur þátíðar sterk beyging eintala hk
    data['lýsingarháttur']['þátíðar']['sb']['et']['hk'] = input_fallbeyging_cli(
        msg_mynd='Lýsingarháttur þátíðar sterk beyging eintala hvorugkyn',
        msg_mynd_s='lysingarhattur.þatid.sb.et.hk',
        msg_daemi=[
            '\033[90mhér er\033[0m \033[32mgefið\033[0m \033[90mlamb\033[0m',
            '\033[90mum\033[0m \033[32mgefið\033[0m \033[90mlamb\033[0m',
            '\033[90mfrá\033[0m \033[32mgefnu\033[0m \033[90mlambi\033[0m',
            '\033[90mtil\033[0m \033[32mgefins\033[0m \033[90mlambs\033[0m'
        ]
    )
    # lýsingarháttur þátíðar sterk beyging fleirtala kk
    data['lýsingarháttur']['þátíðar']['sb']['ft'] = collections.OrderedDict()
    data['lýsingarháttur']['þátíðar']['sb']['ft']['kk'] = input_fallbeyging_cli(
        msg_mynd='Lýsingarháttur þátíðar sterk beyging fleirtala karlkyn',
        msg_mynd_s='lysingarhattur.þatid.sb.ft.kk',
        msg_daemi=[
            '\033[90mhér eru\033[0m \033[32mgefnir\033[0m \033[90mhestar\033[0m',
            '\033[90mum\033[0m \033[32mgefna\033[0m \033[90mhesta\033[0m',
            '\033[90mfrá\033[0m \033[32mgefnum\033[0m \033[90mhestum\033[0m',
            '\033[90mtil\033[0m \033[32mgefinna\033[0m \033[90mhesta\033[0m'
        ]
    )
    # lýsingarháttur þátíðar sterk beyging fleirtala kvk
    data['lýsingarháttur']['þátíðar']['sb']['ft']['kvk'] = input_fallbeyging_cli(
        msg_mynd='Lýsingarháttur þátíðar sterk beyging fleirtala kvenkyn',
        msg_mynd_s='lysingarhattur.þatid.sb.ft.kvk',
        msg_daemi=[
            '\033[90mhér eru\033[0m \033[32mgefnar\033[0m \033[90mkýr\033[0m',
            '\033[90mum\033[0m \033[32mgefnar\033[0m \033[90mkýr\033[0m',
            '\033[90mfrá\033[0m \033[32mgefnum\033[0m \033[90mkúm\033[0m',
            '\033[90mtil\033[0m \033[32mgefinna\033[0m \033[90mkúa\033[0m'
        ]
    )
    # lýsingarháttur þátíðar sterk beyging fleirtala hk
    data['lýsingarháttur']['þátíðar']['sb']['ft']['hk'] = input_fallbeyging_cli(
        msg_mynd='Lýsingarháttur þátíðar sterk beyging fleirtala hvorugkyn',
        msg_mynd_s='lysingarhattur.þatid.sb.ft.hk',
        msg_daemi=[
            '\033[90mhér eru\033[0m \033[32mgefin\033[0m \033[90mlömb\033[0m',
            '\033[90mum\033[0m \033[32mgefin\033[0m \033[90mlömb\033[0m',
            '\033[90mfrá\033[0m \033[32mgefnum\033[0m \033[90mlömbum\033[0m',
            '\033[90mtil\033[0m \033[32mgefinna\033[0m \033[90mlamba\033[0m'
        ]
    )
    # lýsingarháttur þátíðar veik beyging eintala kk
    data['lýsingarháttur']['þátíðar']['vb'] = collections.OrderedDict()
    data['lýsingarháttur']['þátíðar']['vb']['et'] = collections.OrderedDict()
    data['lýsingarháttur']['þátíðar']['vb']['et']['kk'] = input_fallbeyging_cli(
        msg_mynd='Lýsingarháttur þátíðar veik beyging eintala karlkyn',
        msg_mynd_s='lysingarhattur.þatid.vb.et.kk',
        msg_daemi=[
            '\033[90mhér er\033[0m \033[32mgefni\033[0m \033[90mhesturinn\033[0m',
            '\033[90mum\033[0m \033[32mgefna\033[0m \033[90mhestinn\033[0m',
            '\033[90mfrá\033[0m \033[32mgefna\033[0m \033[90mhestinum\033[0m',
            '\033[90mtil\033[0m \033[32mgefna\033[0m \033[90mhestsins\033[0m'
        ]
    )
    # lýsingarháttur þátíðar veik beyging eintala kvk
    data['lýsingarháttur']['þátíðar']['vb']['et']['kvk'] = input_fallbeyging_cli(
        msg_mynd='Lýsingarháttur þátíðar veik beyging eintala kvenkyn',
        msg_mynd_s='lysingarhattur.þatid.vb.et.kvk',
        msg_daemi=[
            '\033[90mhér er\033[0m \033[32mgefna\033[0m \033[90mkýrin\033[0m',
            '\033[90mum\033[0m \033[32mgefnu\033[0m \033[90mkúna\033[0m',
            '\033[90mfrá\033[0m \033[32mgefnu\033[0m \033[90mkúnni\033[0m',
            '\033[90mtil\033[0m \033[32mgefnu\033[0m \033[90mkýrinnar\033[0m'
        ]
    )
    # lýsingarháttur þátíðar veik beyging eintala hk
    data['lýsingarháttur']['þátíðar']['vb']['et']['hk'] = input_fallbeyging_cli(
        msg_mynd='Lýsingarháttur þátíðar veik beyging eintala hvorugkyn',
        msg_mynd_s='lysingarhattur.þatid.vb.et.hk',
        msg_daemi=[
            '\033[90mhér er\033[0m \033[32mgefna\033[0m \033[90mlambið\033[0m',
            '\033[90mum\033[0m \033[32mgefna\033[0m \033[90mlambið\033[0m',
            '\033[90mfrá\033[0m \033[32mgefna\033[0m \033[90mlambinu\033[0m',
            '\033[90mtil\033[0m \033[32mgefna\033[0m \033[90mlambsins\033[0m'
        ]
    )
    # lýsingarháttur þátíðar veik beyging fleirtala kk
    data['lýsingarháttur']['þátíðar']['vb']['ft'] = collections.OrderedDict()
    data['lýsingarháttur']['þátíðar']['vb']['ft']['kk'] = input_fallbeyging_cli(
        msg_mynd='Lýsingarháttur þátíðar veik beyging fleirtala karlkyn',
        msg_mynd_s='lysingarhattur.þatid.vb.ft.kk',
        msg_daemi=[
            '\033[90mhér eru\033[0m \033[32mgefnu\033[0m \033[90mhestarnir\033[0m',
            '\033[90mum\033[0m \033[32mgefnu\033[0m \033[90mhestana\033[0m',
            '\033[90mfrá\033[0m \033[32mgefnu\033[0m \033[90mhestunum\033[0m',
            '\033[90mtil\033[0m \033[32mgefnu\033[0m \033[90mhestanna\033[0m'
        ]
    )
    # lýsingarháttur þátíðar veik beyging fleirtala kvk
    data['lýsingarháttur']['þátíðar']['vb']['ft']['kvk'] = input_fallbeyging_cli(
        msg_mynd='Lýsingarháttur þátíðar veik beyging fleirtala kvenkyn',
        msg_mynd_s='lysingarhattur.þatid.vb.ft.kvk',
        msg_daemi=[
            '\033[90mhér eru\033[0m \033[32mgefnu\033[0m \033[90mkýrnar\033[0m',
            '\033[90mum\033[0m \033[32mgefnu\033[0m \033[90mkýrnar\033[0m',
            '\033[90mfrá\033[0m \033[32mgefnu\033[0m \033[90mkúnum\033[0m',
            '\033[90mtil\033[0m \033[32mgefnu\033[0m \033[90mkúnna\033[0m'
        ]
    )
    # lýsingarháttur þátíðar veik beyging fleirtala hk
    data['lýsingarháttur']['þátíðar']['vb']['ft']['hk'] = input_fallbeyging_cli(
        msg_mynd='Lýsingarháttur þátíðar veik beyging fleirtala hvorugkyn',
        msg_mynd_s='lysingarhattur.þatid.vb.ft.hk',
        msg_daemi=[
            '\033[90mhér eru\033[0m \033[32mgefnu\033[0m \033[90mlömbin\033[0m',
            '\033[90mum\033[0m \033[32mgefnu\033[0m \033[90mlömbin\033[0m',
            '\033[90mfrá\033[0m \033[32mgefnu\033[0m \033[90mlömbunum\033[0m',
            '\033[90mtil\033[0m \033[32mgefnu\033[0m \033[90mlambanna\033[0m'
        ]
    )
    return data


def input_fallbeyging_cli(msg_mynd, msg_mynd_s, msg_daemi):
    '''
    @msg_mynd: orðmynd info
    @msg_mynd_s: orðmynd info stutt
    @msg_daemi: fjögurra strengja listi með orðmyndardæmum
    '''
    fallbeyging = []
    nefnifall = input('%s nefnifall (dæmi: %s): ' % (msg_mynd, msg_daemi[0]))
    fallbeyging.append(nefnifall)
    logman.info('%s.nf: %s' % (msg_mynd_s, nefnifall, ))
    tholfall = input('%s þolfall (dæmi: %s): ' % (msg_mynd, msg_daemi[1]))
    fallbeyging.append(tholfall)
    logman.info('%s.þf: %s' % (msg_mynd_s, tholfall, ))
    thagufall = input('%s þágufall (dæmi: %s): ' % (msg_mynd, msg_daemi[2]))
    fallbeyging.append(thagufall)
    logman.info('%s.þgf: %s' % (msg_mynd_s, thagufall, ))
    eignarfall = input('%s eignarfall (dæmi: %s): ' % (msg_mynd, msg_daemi[3]))
    fallbeyging.append(eignarfall)
    logman.info('%s.ef: %s' % (msg_mynd_s, eignarfall, ))
    return fallbeyging


def input_personubeyging_cli(msg_mynd, msg_mynd_s, msg_daemi):
    '''
    @msg_mynd: orðmynd info
    @msg_mynd_s: orðmynd info stutt
    @msg_daemi: þriggja strengja listi með orðmyndardæmum
    '''
    personubeyging = []
    fyrsta_persona = input('%s fyrsta persóna (dæmi: %s): ' % (msg_mynd, msg_daemi[0]))
    personubeyging.append(fyrsta_persona)
    logman.info('%s.1p: %s' % (msg_mynd_s, fyrsta_persona, ))
    onnur_persona = input('%s önnur persóna (dæmi: %s): ' % (msg_mynd, msg_daemi[1]))
    personubeyging.append(onnur_persona)
    logman.info('%s.2p: %s' % (msg_mynd_s, onnur_persona, ))
    thridja_persona = input('%s þriðja persóna (dæmi: %s): ' % (msg_mynd, msg_daemi[2]))
    personubeyging.append(thridja_persona)
    logman.info('%s.3p: %s' % (msg_mynd_s, thridja_persona, ))
    return personubeyging