#!/usr/bin/python
"""
Seer of words

Scan text, attempt to identify words.
"""
import copy
import datetime
import itertools
import json
import pickle
import platform
import os
import pathlib
import sys
from typing import Callable

from lokaord import logman
from lokaord.database.models.utils import TimestampIsoformat as ts_iso
from lokaord.version import __version__ as version

if platform.system() == 'Linux':
    import pointless


def search_word(word):
    sight = load_sight()
    print('\033[36m---\033[0m\n%s\n\033[36m---\033[0m' % (word, ))
    if word in sight['orð']:
        for option in sight['orð'][word]:
            print(
                (
                    '\033[34m├\033[0m \033[36m{m}\033[0m\n'
                    '\033[34m├\033[0m \033[33m{k} ({h})\033[0m\n'
                    '\033[34m└\033[0m \033[35m{f}\033[0m'
                ).format(
                    m=option['mynd'],
                    k=sight['hash'][option['hash']]['d']['kennistrengur'],
                    h=option['hash'],
                    f=sight['hash'][option['hash']]['f']
                )
            )
    else:
        print('fannst ekki')
    print('\033[36m---\033[0m')


def word_change_possibilities(word: str) -> list[str]:
    myset = set([word])
    def uppercase(word: str):
        return '%s%s' % (word[0].upper(), word[1:])
    def lowercase(word: str):
        return word.lower()
    def ellify(word: str):
        return word.replace('ll', 'łl')
    def apply_possibility(
        word: str, possibility: list[bool], changes: list[Callable[[str], str]]
    ) -> str:
        if len(possibility) != len(changes):
            raise Exception('possibility and changes should have same length')
        e_word = word
        for i in range(len(possibility)):
            if possibility[i] is True:
                e_word = changes[i](e_word)
        return e_word
    changes = [
        uppercase,
        lowercase,
        ellify
    ]
    possibilities = sorted(
        list(set(itertools.permutations(
            [True] * len(changes) + [False] * (len(changes) - 1),
            len(changes)))), reverse=True
    )
    for possibility in possibilities:
        myset.add(apply_possibility(word, possibility, changes))
    return list(myset)


def scan_sentence(sentence: str, clean_str: bool = True):
    if clean_str is True:
        sentence = clean_string(sentence)
    sight = load_sight()
    print('\033[36m---\033[0m\n%s\n\033[36m---\033[0m' % (sentence, ))
    scanned_sentence = []
    found = 0
    maybe = 0
    missing = 0
    for word in sentence.split(' '):
        if word == '':
            continue
        scanned_word = {
            'orð': word,
            'orð-hreinsað': None,
            'leiðir': None,
            'fylgir': None,
            'staða': None,
            'möguleikar': []
        }
        if word in sight['orð']:
            scanned_word['staða'] = 'fannst'
            for option in sight['orð'][word]:
                scanned_word['möguleikar'].append({
                    'm': option['mynd'],
                    'k': sight['hash'][option['hash']]['d']['kennistrengur'],
                    'h': option['hash'],
                    'f': sight['hash'][option['hash']]['f']
                })
            found += 1
            scanned_sentence.append(scanned_word)
            continue
        onhanging_chars = set([
            '.', ',', ':', ';', '(', ')', '[', ']', '-', '/', '„', '“', '?', '!', '´', '%'
        ])
        msg = ''
        e_word = word.strip()
        while e_word[-1] in onhanging_chars:
            if scanned_word['fylgir'] is None:
                scanned_word['fylgir'] = ''
            scanned_word['fylgir'] = '%s%s' % (e_word[-1], scanned_word['fylgir'])
            e_word = e_word[:-1]
        while e_word[0] in onhanging_chars:
            if scanned_word['leiðir'] is None:
                scanned_word['leiðir'] = ''
            scanned_word['leiðir'] += e_word[0]
            e_word = e_word[1:]
        if word in sight['skammstafanir']:
            myndir = ' / '.join(['"%s"' % x for x in sight['skammstafanir'][word]['myndir']])
            scanned_word['staða'] = 'skammstöfun'
            scanned_word['möguleikar'].append({
                'm': myndir,
                'k': sight['skammstafanir'][word]['kennistrengur'],
                'h': sight['skammstafanir'][word]['hash'],
                'f': sight['hash'][sight['skammstafanir'][word]['hash']]['f']
            })
            found += 1
            scanned_sentence.append(scanned_word)
            continue
        elif e_word in sight['skammstafanir']:
            myndir = ' / '.join(['"%s"' % x for x in sight['skammstafanir'][e_word]['myndir']])
            scanned_word['staða'] = 'skammstöfun'
            scanned_word['möguleikar'].append({
                'm': myndir,
                'k': sight['skammstafanir'][e_word]['kennistrengur'],
                'h': sight['skammstafanir'][e_word]['hash'],
                'f': sight['hash'][sight['skammstafanir'][e_word]['hash']]['f']
            })
            found += 1
            scanned_sentence.append(scanned_word)
            continue
        e_word_possibilities = word_change_possibilities(e_word)
        for e_word_p in e_word_possibilities:
            if e_word_p in sight['orð']:
                scanned_word['orð-hreinsað'] = e_word
                scanned_word['staða'] = 'mögulega'
                for option in sight['orð'][e_word_p]:
                    scanned_word['möguleikar'].append({
                        'm': option['mynd'],
                        'k': sight['hash'][option['hash']]['d']['kennistrengur'],
                        'h': option['hash'],
                        'f': sight['hash'][option['hash']]['f']
                    })
                maybe += 1
                break
            elif e_word_p.isdigit():
                scanned_word['orð-hreinsað'] = e_word_p
                scanned_word['staða'] = 'tala'
                break
            else:
                scanned_word['staða'] = 'vantar'
        if scanned_word['staða'] == 'vantar':
            missing += 1
        scanned_sentence.append(scanned_word)
    highlighted_sentence_list = []
    for scanned_word in scanned_sentence:
        if scanned_word['staða'] == 'fannst':
            print('"%s" \033[42m\033[30m FANNST \033[0m' % (scanned_word['orð'], ))
            highlighted_sentence_list.append(
                '\033[42m\033[30m%s\033[0m' % (scanned_word['orð'], )
            )
        elif scanned_word['staða'] == 'mögulega':
            print('"%s" \033[43m\033[30m MÖGULEGA \033[0m "%s"' % (
                scanned_word['orð'],
                scanned_word['orð-hreinsað']
            ))
            highlighted_sentence_list.append(
                '%s%s%s' % (
                    '' if scanned_word['leiðir'] is None else scanned_word['leiðir'],
                    '\033[43m\033[30m%s\033[0m' % (scanned_word['orð-hreinsað'], ),
                    '' if scanned_word['fylgir'] is None else scanned_word['fylgir']
                )
            )
        elif scanned_word['staða'] == 'tala':
            print('"%s" \033[46m\033[30m TALA \033[0m' % (
                scanned_word['orð-hreinsað'],
            ))
            highlighted_sentence_list.append(
                '%s%s%s' % (
                    '' if scanned_word['leiðir'] is None else scanned_word['leiðir'],
                    '\033[46m\033[30m%s\033[0m' % (scanned_word['orð-hreinsað'], ),
                    '' if scanned_word['fylgir'] is None else scanned_word['fylgir']
                )
            )
        elif scanned_word['staða'] == 'skammstöfun':
            print('"%s" \033[44m\033[37m SKAMMSTÖFUN \033[0m' % (scanned_word['orð'], ))
            highlighted_sentence_list.append(
                '\033[44m\033[37m%s\033[0m' % (scanned_word['orð'], )
            )
        elif scanned_word['staða'] == 'vantar':
            print('"%s" \033[41m\033[37m VANTAR \033[0m' % (scanned_word['orð'], ))
            highlighted_sentence_list.append(
                '\033[41m\033[37m%s\033[0m' % (scanned_word['orð'], )
            )
        for option in scanned_word['möguleikar']:
            print(
                (
                    '\033[34m├\033[0m \033[36m{m}\033[0m\n'
                    '\033[34m├\033[0m \033[33m{k} ({h})\033[0m\n'
                    '\033[34m└\033[0m \033[35m{f}\033[0m'
                ).format(**option)
            )
    highlighted_sentence = ' '.join(highlighted_sentence_list)
    print('\033[36m---\033[0m\n%s\n\033[36m---\033[0m' % (highlighted_sentence, ))
    print('Fannst: %s/%s, %s %%' % (
        found, len(scanned_sentence), format(100 * found/len(scanned_sentence), '.3g'))
    )
    print('Kannski: %s/%s, %s %%' % (
        maybe, len(scanned_sentence), format(100 * maybe/len(scanned_sentence), '.3g'))
    )
    print('Vantar: %s/%s, %s %%' % (
        missing, len(scanned_sentence), format(100 * missing/len(scanned_sentence), '.3g'))
    )


def load_sight(filename='sight', use_pointless=None):
    if use_pointless is None:
        use_pointless = (platform.system() == 'Linux')
    if use_pointless is True and platform.system() != 'Linux':
        logman.warning('Using pointless only available on Linux.')
    assert('/' not in filename)
    assert('.' not in filename)
    root_storage_dir_abs = os.path.abspath(os.path.dirname(os.path.realpath(__file__)))
    sight_storage_dir_rel = os.path.join('database', 'disk', 'lokaord')
    sight_filepath_rel = os.path.join(sight_storage_dir_rel, '%s.%s' % (
        filename, 'pointless' if use_pointless is True else 'pickle'
    ))
    sight_filepath_abs = os.path.join(root_storage_dir_abs, sight_filepath_rel)
    if not os.path.isfile(sight_filepath_abs):
        logman.error('No file "%s", try building sight.' % (sight_filepath_rel, ))
        logman.error('Exiting ..')
        sys.exit(1)
    sight = None
    if use_pointless is True:
        sight = pointless.Pointless(sight_filepath_abs).GetRoot()
    else:
        with open(sight_filepath_abs, 'rb') as file:
            sight = pickle.load(file)
    assert(sight is not None)
    logman.info('Loaded sight file "%s", ts: %s, v: %s' % (
        sight_filepath_rel, sight['ts'], sight['v']
    ))
    return sight


def build_sight(filename='sight', use_pointless=None):
    if use_pointless is None:
        use_pointless = (platform.system() == 'Linux')
    logman.info('Building sight ..')
    if use_pointless is True and platform.system() != 'Linux':
        logman.warning('Using pointless only available on Linux.')
    ts = datetime.datetime.utcnow().strftime(ts_iso)
    root_storage_dir_abs = os.path.abspath(os.path.dirname(os.path.realpath(__file__)))
    datafiles_dir_abs = os.path.join(root_storage_dir_abs, 'database', 'data')
    sight_storage_dir_rel = os.path.join('database', 'disk', 'lokaord')
    sight_storage_dir_abs = os.path.join(root_storage_dir_abs, sight_storage_dir_rel)
    if not os.path.exists(sight_storage_dir_abs):
        os.makedirs(sight_storage_dir_abs)
        logman.Logger.info('Created data directory "%s" for "%s.%s".' % (
            filename, sight_storage_dir_abs, 'pointless' if use_pointless is True else 'pickle'
        ))
    sight_filepath_rel = os.path.join(sight_storage_dir_rel, '%s.%s' % (
        filename, 'pointless' if use_pointless is True else 'pickle'
    ))
    sight_filepath_abs = os.path.join(root_storage_dir_abs, sight_filepath_rel)
    sight = {
        'orð': {},
        'hash': {},
        'kennistrengur': {},
        'skammstafanir': {},
        'ts': ts,
        'v': version
    }
    knowledge_tasks = [
        {
            'name': 'nafnorð',
            'root': datafiles_dir_abs,
            'dir': 'nafnord',
        },
        {
            'name': 'lýsingarorð',
            'root': datafiles_dir_abs,
            'dir': 'lysingarord',
        },
        {
            'name': 'sagnorð',
            'root': datafiles_dir_abs,
            'dir': 'sagnord',
        },
        {
            'name': 'greinir',
            'root': datafiles_dir_abs,
            'dir': 'greinir',
        },
        {
            'name': 'fjöldatölur',
            'root': datafiles_dir_abs,
            'dir': os.path.join('toluord', 'fjoldatolur'),
        },
        {
            'name': 'raðtölur',
            'root': datafiles_dir_abs,
            'dir': os.path.join('toluord', 'radtolur'),
        },
        {
            'name': 'ábendingarfornöfn',
            'root': datafiles_dir_abs,
            'dir': os.path.join('fornofn', 'abendingar'),
        },
        {
            'name': 'afturbeygt fornafn',
            'root': datafiles_dir_abs,
            'dir': os.path.join('fornofn', 'afturbeygt'),
        },
        {
            'name': 'eignarfornöfn',
            'root': datafiles_dir_abs,
            'dir': os.path.join('fornofn', 'eignar'),
        },
        {
            'name': 'óákveðin fornöfn',
            'root': datafiles_dir_abs,
            'dir': os.path.join('fornofn', 'oakvedin'),
        },
        {
            'name': 'persónufornöfn',
            'root': datafiles_dir_abs,
            'dir': os.path.join('fornofn', 'personu'),
        },
        {
            'name': 'spurnarfornöfn',
            'root': datafiles_dir_abs,
            'dir': os.path.join('fornofn', 'spurnar'),
        },
        {
            'name': 'smáorð, forsetning',
            'root': datafiles_dir_abs,
            'dir': os.path.join('smaord', 'forsetning'),
        },
        {
            'name': 'smáorð, atviksorð',
            'root': datafiles_dir_abs,
            'dir': os.path.join('smaord', 'atviksord'),
        },
        {
            'name': 'smáorð, nafnháttarmerki',
            'root': datafiles_dir_abs,
            'dir': os.path.join('smaord', 'nafnhattarmerki'),
        },
        {
            'name': 'smáorð, samtenging',
            'root': datafiles_dir_abs,
            'dir': os.path.join('smaord', 'samtenging'),
        },
        {
            'name': 'smáorð, upphrópun',
            'root': datafiles_dir_abs,
            'dir': os.path.join('smaord', 'upphropun'),
        },
        {
            'name': 'sérnöfn, eiginnafn (kk)',
            'root': datafiles_dir_abs,
            'dir': os.path.join('sernofn', 'mannanofn', 'islensk-karlmannsnofn', 'eigin'),
        },
        {
            'name': 'sérnöfn, kenninafn (kk)',
            'root': datafiles_dir_abs,
            'dir': os.path.join('sernofn', 'mannanofn', 'islensk-karlmannsnofn', 'kenni'),
        },
        {
            'name': 'sérnöfn, eiginnafn (kvk)',
            'root': datafiles_dir_abs,
            'dir': os.path.join('sernofn', 'mannanofn', 'islensk-kvenmannsnofn', 'eigin'),
        },
        {
            'name': 'sérnöfn, kenninafn (kvk)',
            'root': datafiles_dir_abs,
            'dir': os.path.join('sernofn', 'mannanofn', 'islensk-kvenmannsnofn', 'kenni'),
        },
        {
            'name': 'sérnöfn, miłlinafn',
            'root': datafiles_dir_abs,
            'dir': os.path.join('sernofn', 'mannanofn', 'islensk-millinofn'),
        },
        {
            'name': 'sérnöfn, gælunafn (kk)',
            'root': datafiles_dir_abs,
            'dir': os.path.join('sernofn', 'gaelunofn', 'kk'),
        },
        {
            'name': 'sérnöfn, gælunafn (kvk)',
            'root': datafiles_dir_abs,
            'dir': os.path.join('sernofn', 'gaelunofn', 'kvk'),
        },
        {
            'name': 'sérnöfn, gælunafn (hk)',
            'root': datafiles_dir_abs,
            'dir': os.path.join('sernofn', 'gaelunofn', 'hk'),
        },
        {
            'name': 'sérnöfn, örnefni',
            'root': datafiles_dir_abs,
            'dir': os.path.join('sernofn', 'ornefni'),
        }
    ]
    for task in knowledge_tasks:
        logman.info('Accumulating "%s" knowledge ..' % (task['name'], ))
        for ord_file in sorted(pathlib.Path(os.path.join(task['root'], task['dir'])).iterdir()):
            logman.info('File %s ..' % (os.path.join(task['dir'], ord_file.name), ))
            ord_data = None
            with ord_file.open(mode='r', encoding='utf-8') as fi:
                ord_data = json.loads(fi.read())
            ord_mynd = ord_data['flokkur']
            if 'undirflokkur' in ord_data:
                ord_mynd += '.%s' % (ord_data['undirflokkur'], )
            if 'kyn' in ord_data:
                ord_mynd += '.%s' % (ord_data['kyn'], )
            if 'tölugildi' in ord_data and ord_data['tölugildi'] > 4294967295:
                # pointless styður ekki of stórar tölur (max 0xffffffff)
                # long too large for mere 32 bits
                ord_data['tölugildi'] = str(ord_data['tölugildi'])
            if (
                ord_mynd.startswith('smáorð') or
                ord_mynd == 'sérnafn.millinafn' or
                ('óbeygjanlegt' in ord_data and ord_data['óbeygjanlegt'] is True)
            ):
                if ord_data['orð'] not in sight['orð']:
                    sight['orð'][ord_data['orð']] = []
                sight['orð'][ord_data['orð']].append({'mynd': ord_mynd, 'hash': ord_data['hash']})
            sight['hash'][ord_data['hash']] = {
                'f': os.path.join(task['dir'], ord_file.name),
                'd': copy.deepcopy(ord_data)
            }
            sight['kennistrengur'][ord_data['kennistrengur']] = ord_data['hash']
            if 'ósjálfstætt' not in ord_data or ord_data['ósjálfstætt'] is False:
                add_myndir(ord_data, sight, ord_mynd, ord_data['hash'])
    for sk_file in sorted(pathlib.Path(os.path.join(task['root'], 'skammstafanir')).iterdir()):
        logman.info('File %s ..' % (os.path.join('skammstafanir', sk_file.name), ))
        sk_data = None
        with sk_file.open(mode='r', encoding='utf-8') as fi:
            sk_data = json.loads(fi.read())
        sight['skammstafanir'][sk_data['skammstöfun']] = sk_data
        sight['hash'][sk_data['hash']] = {
            'f': os.path.join('skammstafanir', sk_file.name),
            'd': copy.deepcopy(sk_data)
        }
    logman.info('Writing sight to "%s" ..' % (sight_filepath_rel, ))
    if use_pointless is True:
        pointless.serialize(sight, sight_filepath_abs)
    else:
        with open(sight_filepath_abs, 'wb') as file:
            pickle.dump(sight, file, protocol=pickle.HIGHEST_PROTOCOL)
    logman.info('Sight has been written.')


def add_myndir(ord_data, sight, curr_ord_mynd, ord_hash):
    ignore_keys = set([
        'orð', 'flokkur', 'undirflokkur', 'kyn', 'hash', 'samsett', 'persóna', 'frumlag',
        'fleiryrt', 'óbeygjanlegt', 'tölugildi', 'stýrir'
    ])
    if ord_data is None:
        return
    elif type(ord_data) is str:
        if ord_data not in sight['orð']:
            sight['orð'][ord_data] = []
        sight['orð'][ord_data].append({'mynd': curr_ord_mynd, 'hash': ord_hash})
    elif type(ord_data) is dict:
        for key in ord_data:
            if key in ignore_keys:
                continue
            if type(ord_data[key]) in (dict, str):
                add_myndir(ord_data[key], sight, '%s-%s' % (curr_ord_mynd, key), ord_hash)
            elif type(ord_data[key]) is list:
                temp_ord_mynd = '%s-%s' % (curr_ord_mynd, key)
                if len(ord_data[key]) == 4:
                    add_myndir(ord_data[key][0], sight, '%s-%s' % (temp_ord_mynd, 'nf'), ord_hash)
                    add_myndir(ord_data[key][1], sight, '%s-%s' % (temp_ord_mynd, 'þf'), ord_hash)
                    add_myndir(ord_data[key][2], sight, '%s-%s' % (temp_ord_mynd, 'þgf'), ord_hash)
                    add_myndir(ord_data[key][3], sight, '%s-%s' % (temp_ord_mynd, 'ef'), ord_hash)
                elif len(ord_data[key]) == 3:
                    add_myndir(ord_data[key][0], sight, '%s-%s' % (temp_ord_mynd, '1p'), ord_hash)
                    add_myndir(ord_data[key][1], sight, '%s-%s' % (temp_ord_mynd, '2p'), ord_hash)
                    add_myndir(ord_data[key][2], sight, '%s-%s' % (temp_ord_mynd, '3p'), ord_hash)
                else:
                    raise Exception('Peculiar list length.')
            else:
                raise Exception('Peculiar key-value type.')
    else:
        raise Exception('Peculiar ord_data type.')


def clean_string(mystr: str) -> str:
    cleaned_str = mystr
    remove_strings = [
        '\xad',  # stundum notað til að tilgreina skiptingu orða á vefsíðum
    ]
    for remove_string in remove_strings:
        cleaned_str = cleaned_str.replace(remove_string, '')
    return cleaned_str
