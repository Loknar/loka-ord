#!/usr/bin/python
"""
Seer of words

Scan text, attempt to identify words.
"""
import copy
import datetime
import json
import pickle
import platform
import os
import pathlib
import sys

from lokaord import logman
from lokaord.database.models.utils import TimestampIsoformat as ts_iso
from lokaord.version import __version__ as version

if platform.system() == 'Linux':
    import pointless


def search_word(word):
    sight = load_sight()
    print('---\n%s\n---' % (word, ))
    if word in sight['orð']:
        for option in sight['orð'][word]:
            print(option['mynd'])
            print(option['hash'])
    else:
        print('fann ekki')
    print('---')


def scan_sentence(sentence):
    sight = load_sight()
    print('---\n%s\n---' % (sentence, ))
    for word in sentence.split(' '):
        if word not in sight['orð']:
            msg = ''
            e_word = word.strip()
            if e_word[-1] in ('.', ','):
                e_word = e_word[:-1]
            if 'll' in e_word:
                e_word = e_word.replace('ll', 'łl')
            if e_word in sight['orð']:
                msg = ' en fann "%s"' % (e_word, )
            print('vantar "%s"%s' % (word, msg))
            if e_word in sight['orð']:
                for option in sight['orð'][e_word]:
                    print(option['mynd'])
                    print(option['hash'])
            print('---')
        else:
            print('fann "%s"' % (word, ))
            for option in sight['orð'][word]:
                print(option['mynd'])
                print(option['hash'])
            print('---')
    # import pdb; pdb.set_trace()


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
            'name': 'frumtölur',
            'root': datafiles_dir_abs,
            'dir': os.path.join('toluord', 'frumtolur'),
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
            if (
                ord_mynd.startswith('smáorð') or
                ('óbeygjanlegt' in ord_data and ord_data['óbeygjanlegt'] is True)
            ):
                if ord_data['orð'] not in sight['orð']:
                    sight['orð'][ord_data['orð']] = []
                sight['orð'][ord_data['orð']].append({'mynd': ord_mynd, 'hash': ord_data['hash']})
            sight['hash'][ord_data['hash']] = {
                'f': os.path.join(task['dir'], ord_file.name),
                'd': copy.deepcopy(ord_data)
            }
            if 'ósjálfstætt' not in ord_data or ord_data['ósjálfstætt'] is False:
                add_myndir(ord_data, sight, ord_mynd, ord_data['hash'])
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
        'fleiryrt', 'óbeygjanlegt', 'gildi', 'stýrir'
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
                if len(ord_data[key]) == 4:
                    add_myndir(ord_data[key][0], sight, '%s-%s' % (curr_ord_mynd, 'nf'), ord_hash)
                    add_myndir(ord_data[key][1], sight, '%s-%s' % (curr_ord_mynd, 'þf'), ord_hash)
                    add_myndir(ord_data[key][2], sight, '%s-%s' % (curr_ord_mynd, 'þgf'), ord_hash)
                    add_myndir(ord_data[key][3], sight, '%s-%s' % (curr_ord_mynd, 'ef'), ord_hash)
                elif len(ord_data[key]) == 3:
                    add_myndir(ord_data[key][0], sight, '%s-%s' % (curr_ord_mynd, '1p'), ord_hash)
                    add_myndir(ord_data[key][1], sight, '%s-%s' % (curr_ord_mynd, '2p'), ord_hash)
                    add_myndir(ord_data[key][2], sight, '%s-%s' % (curr_ord_mynd, '3p'), ord_hash)
                else:
                    raise Exception('Peculiar list length.')
            else:
                raise Exception('Peculiar key-value type.')
    else:
        raise Exception('Peculiar ord_data type.')
