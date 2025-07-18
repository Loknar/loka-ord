#!/usr/bin/python
"""
Seer of words

Scan text, attempt to identify words.
"""
import copy
from collections import deque
from collections.abc import Iterable
import datetime
import itertools
import json
import math
import pickle
import platform
import os
import pathlib
import re
import sys
from typing import Callable

import git

from lokaord import logman
from lokaord.database.models.utils import TimestampIsoformat as ts_iso
from lokaord.handlers import DecimalJSONEncoder, MyIndentJSONEncoder
from lokaord.version import __version__ as version

if platform.system() == 'Linux':
	import pointless

WPP = 2500  # default words per page in webpack


def search_word(word):
	sight = load_sight()
	print('\033[36m---\033[0m\n%s\n\033[36m---\033[0m' % (word, ))
	if word in sight['orð']:
		for option in sight['orð'][word]:
			print(
				(
					'\033[34m├\033[0m \033[33m{k}\033[0m\n'
					'\033[34m└\033[0m \033[36m{m}\033[0m'
				).format(k=option[0], m=option[1])
			)
	else:
		print('fannst ekki')
	print('\033[36m---\033[0m')


def word_change_possibilities(word: str) -> Iterable[str]:
	"""
	provide possible word adjustments for identification attempt purposes
	"""

	def deep_replace(word: str, sub_a: str, sub_b: str) -> Iterable[str]:
		"""
		provide all possibilities of sub_a -> sub_b replacements
		"""
		occurances = []
		for loc in range(len(word)):
			if word[loc:loc + len(sub_a)] == sub_a:
				occurances.append(loc)
		len_occ = len(occurances)
		if len_occ == 0:
			return [word]
		combinations = [x for x in itertools.product([False, True], repeat=len_occ)]
		possibilities = []
		for i in range(len(combinations)):
			option = word
			for j in range(len_occ):
				if combinations[i][j] is True:
					option = option[:occurances[j]] + sub_b + option[occurances[j] + len(sub_a):]
			possibilities.append(option)
		return possibilities

	def ellify(word: str) -> Iterable[str]:
		"""
		provide all possibilities of ll -> łl and LL -> ŁL replacements
		"""
		return (deep_replace(word, 'll', 'łl') + deep_replace(word, 'LL', 'ŁL'))

	def uppercase(word: str) -> str:
		return '%s%s' % (word[0].upper(), word[1:])

	def lowercase(word: str) -> str:
		return word.lower()

	def lower_then_uppercase(word: str) -> str:
		return uppercase(lowercase(word))

	def apply_possibility(
		word: str, applier: list[bool], change_functions: list[Callable[[str], str]]
	) -> str:
		if len(applier) != len(change_functions):
			raise Exception('applier and change_functions lists should have same length')
		e_word = word
		for i in range(len(applier)):
			if applier[i] is True:
				e_word = change_functions[i](e_word)
		return e_word

	def move_uppercase_to_front(mylist: Iterable[str]) -> Iterable[str]:
		upper = []
		lower = []
		for entry in mylist:
			if entry == uppercase(entry):
				upper.append(entry)
			else:
				lower.append(entry)
		return (upper + lower)

	change_functions = [
		uppercase,
		lowercase,
		lower_then_uppercase,
	]
	len_change_functions = len(change_functions)
	appliers = sorted(
		list(set(itertools.permutations(
			[True] * len_change_functions + [False] * (len_change_functions - 1),
			len_change_functions))
		),
		reverse=True
	)
	myset = set([word])
	for ellified in ellify(word):
		for applier in appliers:
			myset.add(apply_possibility(ellified, applier, change_functions))
	possibilities = sorted(list(myset), reverse=True)
	if word == uppercase(word):
		return move_uppercase_to_front(possibilities)
	return possibilities


def scan_sentence(sentence: str, hide_matches: bool = False, clean_str: bool = True):
	"""
	identify known whole words from a sentence string
	"""
	if clean_str is True:
		sentence = clean_string(sentence)
	sight = load_sight()
	if hide_matches is False:
		print('\033[36m---\033[0m\n%s\n\033[36m---\033[0m' % (sentence, ))
	scanned_sentence = []
	found = 0
	maybe = 0
	missing = 0
	onhanging_chars = set('.,:;()[]-/„“”?!´%°%#–‐…·—‘"*\'‚’|•')
	onhanging_chars_with_dot = onhanging_chars.copy()
	onhanging_chars_with_dot.remove('.')
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
				scanned_word['möguleikar'].append({'k': option[0], 'm': option[1]})
			found += 1
			scanned_sentence.append(scanned_word)
			continue
		e_word = word.strip()
		e_word_with_dot = word.strip()
		scanned_word_alt = copy.deepcopy(scanned_word)
		while e_word[-1] in onhanging_chars:
			if scanned_word['fylgir'] is None:
				scanned_word['fylgir'] = ''
			scanned_word['fylgir'] = '%s%s' % (e_word[-1], scanned_word['fylgir'])
			e_word = e_word[:-1]
			if e_word == '':
				break
		if e_word == '':
			continue
		while e_word[0] in onhanging_chars:
			if scanned_word['leiðir'] is None:
				scanned_word['leiðir'] = ''
			scanned_word['leiðir'] += e_word[0]
			e_word = e_word[1:]
		while e_word_with_dot[-1] in onhanging_chars_with_dot:
			if scanned_word_alt['fylgir'] is None:
				scanned_word_alt['fylgir'] = ''
			scanned_word_alt['fylgir'] = '%s%s' % (e_word_with_dot[-1], scanned_word_alt['fylgir'])
			e_word_with_dot = e_word_with_dot[:-1]
			if e_word_with_dot == '':
				break
		while e_word_with_dot[0] in onhanging_chars_with_dot:
			if scanned_word_alt['leiðir'] is None:
				scanned_word_alt['leiðir'] = ''
			scanned_word_alt['leiðir'] += e_word_with_dot[0]
			e_word_with_dot = e_word_with_dot[1:]
		if word in sight['skammstafanir']:
			myndir = ' / '.join(['"%s"' % x for x in sight['skammstafanir'][word]['myndir']])
			scanned_word['staða'] = 'skammstöfun'
			scanned_word['möguleikar'].append({
				'k': sight['skammstafanir'][word]['kennistrengur'],
				'm': myndir
			})
			found += 1
			scanned_sentence.append(scanned_word)
			continue
		elif word[-1] in onhanging_chars and word[:-1] in sight['skammstafanir']:
			myndir = ' / '.join(['"%s"' % x for x in sight['skammstafanir'][word[:-1]]['myndir']])
			scanned_word['staða'] = 'skammstöfun'
			scanned_word['orð-hreinsað'] = word[:-1]
			scanned_word['fylgir'] = word[-1]
			scanned_word['möguleikar'].append({
				'k': sight['skammstafanir'][word[:-1]]['kennistrengur'],
				'm': myndir
			})
			found += 1
			scanned_sentence.append(scanned_word)
			continue
		elif e_word_with_dot in sight['skammstafanir']:
			myndir = (
				' / '.join(['"%s"' % x for x in sight['skammstafanir'][e_word_with_dot]['myndir']])
			)
			scanned_word_alt['orð-hreinsað'] = e_word_with_dot
			scanned_word_alt['staða'] = 'skammstöfun'
			scanned_word_alt['möguleikar'].append({
				'k': sight['skammstafanir'][e_word_with_dot]['kennistrengur'],
				'm': myndir
			})
			found += 1
			scanned_sentence.append(scanned_word_alt)
			continue
		elif e_word in sight['skammstafanir']:
			myndir = ' / '.join(['"%s"' % x for x in sight['skammstafanir'][e_word]['myndir']])
			scanned_word['orð-hreinsað'] = e_word
			scanned_word['staða'] = 'skammstöfun'
			scanned_word['möguleikar'].append({
				'k': sight['skammstafanir'][e_word]['kennistrengur'],
				'm': myndir
			})
			found += 1
			scanned_sentence.append(scanned_word)
			continue
		e_word_possibilities = word_change_possibilities(e_word)
		for e_word_p in e_word_possibilities:
			if e_word_p in sight['orð']:
				scanned_word['orð-hreinsað'] = e_word_p
				scanned_word['staða'] = 'mögulega'
				for option in sight['orð'][e_word_p]:
					scanned_word['möguleikar'].append({
						'k': option[0],
						'm': option[1]
					})
				maybe += 1
				break
			elif check_if_string_is_number(e_word_p):
				scanned_word['orð-hreinsað'] = e_word_p
				scanned_word['staða'] = 'tala'
				break
			elif re.fullmatch(r"(?:2[0-3]|[01]\d|\d):[0-5]\d$", e_word_p) is not None:
				scanned_word['orð-hreinsað'] = e_word_p
				scanned_word['staða'] = 'tími'
				break
			else:
				scanned_word['staða'] = 'vantar'
		if scanned_word['staða'] == 'vantar':
			missing += 1
		scanned_sentence.append(scanned_word)
	highlighted_sentence_list = []
	for scanned_word in scanned_sentence:
		if scanned_word['staða'] == 'fannst':
			if hide_matches is False:
				print('"%s" \033[42m\033[30m FANNST \033[0m' % (scanned_word['orð'], ))
			highlighted_sentence_list.append(
				'\033[42m\033[30m%s\033[0m' % (scanned_word['orð'], )
			)
		elif scanned_word['staða'] == 'mögulega':
			if hide_matches is False:
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
			if hide_matches is False:
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
		elif scanned_word['staða'] == 'tími':
			if hide_matches is False:
				print('"%s" \033[46m\033[30m TÍMI \033[0m' % (
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
			if hide_matches is False:
				print('"%s" \033[44m\033[37m SKAMMSTÖFUN \033[0m' % (scanned_word['orð'], ))
			if scanned_word['orð-hreinsað'] is None:
				highlighted_sentence_list.append(
					'\033[44m\033[37m%s\033[0m' % (scanned_word['orð'], )
				)
			else:
				highlighted_sentence_list.append(
					'%s%s%s' % (
						'' if scanned_word['leiðir'] is None else scanned_word['leiðir'],
						'\033[44m\033[37m%s\033[0m' % (scanned_word['orð-hreinsað'], ),
						'' if scanned_word['fylgir'] is None else scanned_word['fylgir']
					)
				)
		elif scanned_word['staða'] == 'vantar':
			if hide_matches is False:
				print('"%s" \033[41m\033[37m VANTAR \033[0m' % (scanned_word['orð'], ))
			highlighted_sentence_list.append(
				'\033[41m\033[37m%s\033[0m' % (scanned_word['orð'], )
			)
		if hide_matches is False:
			for option in scanned_word['möguleikar']:
				print(
					(
						'\033[34m├\033[0m \033[33m{k}\033[0m\n'
						'\033[34m└\033[0m \033[36m{m}\033[0m'
					).format(**option)
				)
	if hide_matches is False:
		print('\033[36m---\033[0m\n')
	highlighted_sentence = ' '.join(highlighted_sentence_list)
	print('%s\n\033[36m---\033[0m' % (highlighted_sentence, ))
	print('Fannst: %s/%s, %s %%' % (
		found, len(scanned_sentence), format(100 * found / len(scanned_sentence), '.3g'))
	)
	print('Kannski: %s/%s, %s %%' % (
		maybe, len(scanned_sentence), format(100 * maybe / len(scanned_sentence), '.3g'))
	)
	print('Vantar: %s/%s, %s %%' % (
		missing, len(scanned_sentence), format(100 * missing / len(scanned_sentence), '.3g'))
	)


def load_sight(filename='sight', use_pointless=None):
	"""
	load data to identify whole words
	"""
	if use_pointless is None:
		use_pointless = (platform.system() == 'Linux')
	if use_pointless is True and platform.system() != 'Linux':
		logman.warning('Using pointless only supported on Linux.')
	if '/' in filename or '.' in filename:
		raise Exception('Bad filename.')
	root_storage_dir_abs = os.path.abspath(os.path.dirname(os.path.realpath(__file__)))
	sight_storage_dir_rel = os.path.join('database', 'disk', 'lokaord')
	sight_filepath_rel = os.path.join(sight_storage_dir_rel, '%s.%s' % (
		filename, 'pointless' if use_pointless is True else 'pickle'
	))
	logman.info('Loading sight file "%s" ..' % (sight_filepath_rel, ))
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
	if sight is None:
		raise Exception('No filename?')
	logman.info('Loaded sight file "%s", ts: %s, v: %s' % (
		sight_filepath_rel, sight['ts'], sight['v']
	))
	return sight


def build_sight(filename='sight', use_pointless=None):
	"""
	collect and construct data to identify whole words
	"""
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
			sight_storage_dir_abs, filename, 'pointless' if use_pointless is True else 'pickle'
		))
	sight_filepath_rel = os.path.join(sight_storage_dir_rel, '%s.%s' % (
		filename, 'pointless' if use_pointless is True else 'pickle'
	))
	sight_filepath_abs = os.path.join(root_storage_dir_abs, sight_filepath_rel)
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
			'name': 'sérnöfn, eiginnafn (hk)',
			'root': datafiles_dir_abs,
			'dir': os.path.join('sernofn', 'mannanofn', 'islensk-hvormannsnofn', 'eigin'),
		},
		{
			'name': 'sérnöfn, kenninafn (hk)',
			'root': datafiles_dir_abs,
			'dir': os.path.join('sernofn', 'mannanofn', 'islensk-hvormannsnofn', 'kenni'),
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
	sight = {'orð': {}, 'skammstafanir': {}, 'ts': ts, 'v': version}
	for task in knowledge_tasks:
		logman.info('Accumulating "%s" knowledge ..' % (task['name'], ))
		for ord_file in sorted(pathlib.Path(os.path.join(task['root'], task['dir'])).iterdir()):
			logman.debug('File %s ..' % (os.path.join(task['dir'], ord_file.name), ))
			ord_data = None
			with ord_file.open(mode='r', encoding='utf-8') as fi:
				ord_data = json.loads(fi.read())
			if (
				ord_data['flokkur'] == 'smáorð' or
				(ord_data['flokkur'] == 'sérnafn' and ord_data['undirflokkur'] == 'miłlinafn') or
				('óbeygjanlegt' in ord_data and ord_data['óbeygjanlegt'] is True)
			):
				if 'ósjálfstætt' not in ord_data or ord_data['ósjálfstætt'] is False:
					if ord_data['orð'] not in sight['orð']:
						sight['orð'][ord_data['orð']] = []
					sight['orð'][ord_data['orð']].append([ord_data['kennistrengur'], ''])
			if 'ósjálfstætt' not in ord_data or ord_data['ósjálfstætt'] is False:
				add_myndir(ord_data, sight, '', ord_data['kennistrengur'])
	logman.info('Accumulating "skammstafanir" knowledge ..')
	for sk_file in sorted(pathlib.Path(os.path.join(task['root'], 'skammstafanir')).iterdir()):
		logman.debug('File %s ..' % (os.path.join('skammstafanir', sk_file.name), ))
		sk_data = None
		with sk_file.open(mode='r', encoding='utf-8') as fi:
			sk_data = json.loads(fi.read())
		sight['skammstafanir'][sk_data['skammstöfun']] = sk_data
	logman.info('Writing sight to "%s" ..' % (sight_filepath_rel, ))
	if use_pointless is True:
		pointless.serialize(sight, sight_filepath_abs)
	else:
		with open(sight_filepath_abs, 'wb') as file:
			pickle.dump(sight, file, protocol=pickle.HIGHEST_PROTOCOL)
	logman.info('Sight has been written.')


def add_myndir(ord_data, sight, curr_ord_mynd, ord_ks):
	ignore_keys = set([
		'orð', 'flokkur', 'undirflokkur', 'merking', 'kyn', 'tölugildi', 'samsett', 'hash',
		'kennistrengur', 'ósjálfstætt', 'óbeygjanlegt', 'persóna', 'frumlag', 'fleiryrt', 'stýrir'
	])
	if ord_data is None:
		return
	if isinstance(ord_data, str):
		if ord_data not in sight['orð']:
			sight['orð'][ord_data] = []
		sight['orð'][ord_data].append([ord_ks, curr_ord_mynd])
	elif isinstance(ord_data, dict):
		for key in ord_data:
			if key in ignore_keys:
				continue
			if isinstance(ord_data[key], (dict, str)):
				if curr_ord_mynd == '':
					next_ord_mynd = key
				else:
					next_ord_mynd = '%s-%s' % (curr_ord_mynd, key)
				add_myndir(ord_data[key], sight, next_ord_mynd, ord_ks)
			elif isinstance(ord_data[key], list):
				temp_ord_mynd = '%s-%s' % (curr_ord_mynd, key)
				if len(ord_data[key]) == 4:
					add_myndir(ord_data[key][0], sight, '%s-%s' % (temp_ord_mynd, 'nf'), ord_ks)
					add_myndir(ord_data[key][1], sight, '%s-%s' % (temp_ord_mynd, 'þf'), ord_ks)
					add_myndir(ord_data[key][2], sight, '%s-%s' % (temp_ord_mynd, 'þgf'), ord_ks)
					add_myndir(ord_data[key][3], sight, '%s-%s' % (temp_ord_mynd, 'ef'), ord_ks)
				elif len(ord_data[key]) == 3:
					add_myndir(ord_data[key][0], sight, '%s-%s' % (temp_ord_mynd, '1p'), ord_ks)
					add_myndir(ord_data[key][1], sight, '%s-%s' % (temp_ord_mynd, '2p'), ord_ks)
					add_myndir(ord_data[key][2], sight, '%s-%s' % (temp_ord_mynd, '3p'), ord_ks)
				else:
					raise Exception('Unexpected list length.')
			else:
				raise Exception('Unexpected key-value type.')
	else:
		raise Exception('Unexpected ord_data type.')


def webpack(
	words_per_pack: int = WPP, include_hash: bool = False, include_kennistrengur: bool = False
):
	"""
	Pack lokaorð JSON datafiles to more compact JSON datafiles suitable for webclient usage.
	"""
	logman.info('Running webpack.')
	ts_str = datetime.datetime.utcnow().strftime(ts_iso)
	root_storage_dir_abs = os.path.abspath(os.path.dirname(os.path.realpath(__file__)))
	webpack_dirpath_rel = os.path.join('database', 'disk', 'lokaord', 'webpack')
	webpack_min_dirpath_rel = os.path.join(webpack_dirpath_rel, 'min')
	webpack_dirpath_abs = os.path.join(root_storage_dir_abs, webpack_dirpath_rel)
	webpack_min_dirpath_abs = os.path.join(root_storage_dir_abs, webpack_min_dirpath_rel)
	if not os.path.exists(webpack_dirpath_abs):  # create directory if needed
		os.makedirs(webpack_dirpath_abs)
		logman.Logger.info('Created data directory "%s" for compact files for web.' % (
			webpack_dirpath_abs,
		))
	if not os.path.exists(webpack_min_dirpath_abs):  # create directory if needed
		os.makedirs(webpack_min_dirpath_abs)
		logman.Logger.info('Created data directory "%s" for compact files for web.' % (
			webpack_min_dirpath_abs,
		))
	datafiles_dir_abs = os.path.join(root_storage_dir_abs, 'database', 'data')
	ord_dirs = [
		'nafnord',
		'lysingarord',
		'sagnord',
		'greinir',
		os.path.join('toluord', 'fjoldatolur'),
		os.path.join('toluord', 'radtolur'),
		os.path.join('fornofn', 'abendingar'),
		os.path.join('fornofn', 'afturbeygt'),
		os.path.join('fornofn', 'eignar'),
		os.path.join('fornofn', 'oakvedin'),
		os.path.join('fornofn', 'personu'),
		os.path.join('fornofn', 'spurnar'),
		os.path.join('smaord', 'forsetning'),
		os.path.join('smaord', 'atviksord'),
		os.path.join('smaord', 'nafnhattarmerki'),
		os.path.join('smaord', 'samtenging'),
		os.path.join('smaord', 'upphropun'),
		os.path.join('sernofn', 'mannanofn', 'islensk-karlmannsnofn', 'eigin'),
		os.path.join('sernofn', 'mannanofn', 'islensk-karlmannsnofn', 'kenni'),
		os.path.join('sernofn', 'mannanofn', 'islensk-kvenmannsnofn', 'eigin'),
		os.path.join('sernofn', 'mannanofn', 'islensk-kvenmannsnofn', 'kenni'),
		os.path.join('sernofn', 'mannanofn', 'islensk-hvormannsnofn', 'eigin'),
		os.path.join('sernofn', 'mannanofn', 'islensk-hvormannsnofn', 'kenni'),
		os.path.join('sernofn', 'mannanofn', 'islensk-millinofn'),
		os.path.join('sernofn', 'gaelunofn', 'kk'),
		os.path.join('sernofn', 'gaelunofn', 'kvk'),
		os.path.join('sernofn', 'gaelunofn', 'hk'),
		os.path.join('sernofn', 'ornefni'),
	]
	repo_dir_abs = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '..'))
	repo = git.Repo(repo_dir_abs)
	head_sha = repo.head.object.hexsha
	added_kennistrengir = set()
	file_queue = deque()
	for ord_dir in ord_dirs:
		ord_dir_abs = os.path.join(datafiles_dir_abs, ord_dir)
		for ord_file in sorted(pathlib.Path(ord_dir_abs).iterdir()):
			file_queue.append(os.path.join(ord_dir_abs, ord_file.name))
	packs_count = math.ceil(len(file_queue) / words_per_pack)
	remove_keys = []
	if not include_hash:
		remove_keys.append('hash')
	if not include_kennistrengur:
		remove_keys.append('kennistrengur')
	samsett_ord_keep_keys = [
		'orð', 'flokkur', 'undirflokkur', 'merking', 'kyn', 'tölugildi', 'samsett', 'hash',
		'kennistrengur', 'ósjálfstætt', 'óbeygjanlegt', 'persóna', 'frumlag', 'fleiryrt', 'stýrir'
	]
	logman.info('Packing words ..')
	for pack in range(1, packs_count + 1):
		webpack_data = {
			'version': version,
			'timestamp': ts_str,
			'head': head_sha,
			'count': None,
			'nr': {'pack': pack, 'packs': packs_count},
			'orð': [],
		}
		word_count = 0
		while word_count < words_per_pack:
			try:
				file_path = file_queue.popleft()
			except IndexError:
				break
			logman.debug(f'Webpack orð {file_path} ({word_count}/{words_per_pack})')
			ord_data = None
			with open(file_path, 'r', encoding='utf-8') as fi:
				ord_data = json.loads(fi.read())
			# make sure kennistrengur is unique
			kennistrengur = ord_data['kennistrengur']
			if kennistrengur in added_kennistrengir:
				raise Exception('Already added? (%s)' % (kennistrengur, ))
			# remove unwanted keys
			for key in sorted(ord_data.keys()):
				if key in remove_keys:
					del ord_data[key]
			# check if orð is samsett, just add it if it's not samsett
			if 'samsett' not in ord_data:
				webpack_data['orð'].append(ord_data)
				added_kennistrengir.add(kennistrengur)
				word_count += 1
				continue
			# if samsett, check if all orðhlutar are present, add if so
			ordhlutar_all_present = True
			for ordhluti in ord_data['samsett']:
				if ordhluti['kennistrengur'] not in added_kennistrengir:
					ordhlutar_all_present = False
					break
			if ordhlutar_all_present:
				# if all ordhlutar present, then delete beygingar and then go and add it
				for key in sorted(ord_data.keys()):
					if key not in samsett_ord_keep_keys:
						del ord_data[key]
				webpack_data['orð'].append(ord_data)
				added_kennistrengir.add(kennistrengur)
				word_count += 1
				continue
			else:
				# if not all orðhlutar present, throw file_path back at end of queue
				file_queue.append(file_path)
				continue
		webpack_data['count'] = len(webpack_data['orð'])
		webpack_data_json_pretty = json.dumps(
			webpack_data, indent='\t', ensure_ascii=False, separators=(',', ': '),
			cls=MyIndentJSONEncoder
		)
		webpack_data_json_min = json.dumps(
			webpack_data, separators=(',', ':'), ensure_ascii=False, sort_keys=True,
			cls=DecimalJSONEncoder
		)
		# write to files
		webpack_filename = 'lokaord-%s.json' % (pack, )
		webpack_filename_min = 'lokaord-%s.min.json' % (pack, )
		webpack_filename_abs = os.path.join(webpack_dirpath_abs, webpack_filename)
		webpack_filename_min_abs = os.path.join(webpack_min_dirpath_abs, webpack_filename_min)
		logman.info('Writing webpacked lokaord file "%s" ..' % (webpack_filename, ))
		with open(webpack_filename_abs, mode='w', encoding='utf-8') as outfile:
			outfile.write(webpack_data_json_pretty)
		with open(webpack_filename_min_abs, mode='w', encoding='utf-8') as outfile:
			outfile.write(webpack_data_json_min)
	logman.info('Packing skammstafanir ..')
	skamm_dir = 'skammstafanir'
	skamm_dir_abs = os.path.join(datafiles_dir_abs, skamm_dir)
	skamm_file_queue = deque()
	added_skamm_kennistrengir = set()
	for skamm_file in sorted(pathlib.Path(skamm_dir_abs).iterdir()):
		skamm_file_queue.append(os.path.join(skamm_dir_abs, skamm_file.name))
	skamm_packs_count = math.ceil(len(skamm_file_queue) / words_per_pack)
	for pack in range(1, skamm_packs_count + 1):
		webpack_skamm_data = {
			'version': version,
			'timestamp': ts_str,
			'head': head_sha,
			'count': None,
			'nr': {'pack': pack, 'packs': skamm_packs_count},
			'skammstafanir': [],
		}
		skamm_count = 0
		while word_count < words_per_pack:
			try:
				file_path = skamm_file_queue.popleft()
			except IndexError:
				break
			logman.debug(f'Webpack skammstafanir {file_path}')
			skamm_data = None
			with open(file_path, 'r', encoding='utf-8') as fi:
				skamm_data = json.loads(fi.read())
			# remove unwanted keys
			kennistrengur = skamm_data['kennistrengur']
			if kennistrengur in added_skamm_kennistrengir:
				raise Exception('Already added? (%s)' % (skamm_data['kennistrengur'], ))
			for key in sorted(skamm_data.keys()):
				if key in remove_keys:
					del skamm_data[key]
			webpack_skamm_data['skammstafanir'].append(skamm_data)
			added_kennistrengir.add(kennistrengur)
			skamm_count += 1
		webpack_skamm_data['count'] = len(webpack_skamm_data['skammstafanir'])
		webpack_data_json_pretty = json.dumps(
			webpack_skamm_data, indent='\t', ensure_ascii=False, separators=(',', ': '),
			cls=MyIndentJSONEncoder
		)
		webpack_data_json_min = json.dumps(
			webpack_skamm_data, separators=(',', ':'), ensure_ascii=False, sort_keys=True,
			cls=DecimalJSONEncoder
		)
		# write to files
		webpack_filename = 'skamm-%s.json' % (pack, )
		webpack_filename_min = 'skamm-%s.min.json' % (pack, )
		webpack_filename_abs = os.path.join(webpack_dirpath_abs, webpack_filename)
		webpack_filename_min_abs = os.path.join(webpack_min_dirpath_abs, webpack_filename_min)
		logman.info('Writing webpacked skammstafanir file "%s" ..' % (webpack_filename, ))
		with open(webpack_filename_abs, mode='w', encoding='utf-8') as outfile:
			outfile.write(webpack_data_json_pretty)
		with open(webpack_filename_min_abs, mode='w', encoding='utf-8') as outfile:
			outfile.write(webpack_data_json_min)
	logman.info('Webpack: done.')


def clean_string(mystr: str) -> str:
	"""
	attempt to clean away some of the silly from the string
	"""
	cleaned_str = mystr
	replacements = [
		# skipta ákveðnum táknum út fyrir bil
		('\n', ' '),
		('\t', ' '),
		('\u202f', ' '),  # narrow no-break space
		# bæta við bilum sumstaðar
		('/', ' / '),
		('[', ' ['),
		('(', ' ('),
		# meðhöndla annarskonar kommustafaaðferð, skipta út fyrir venjubundna kommustafi
		('A\u0301', 'Á'),
		('E\u0301', 'É'),
		('I\u0301', 'Í'),
		('O\u0301', 'Ó'),
		('U\u0301', 'Ú'),
		('Y\u0301', 'Ý'),
		('O\u0308', 'Ö'),
		('a\u0301', 'á'),
		('e\u0301', 'é'),
		('i\u0301', 'í'),
		('o\u0301', 'ó'),
		('u\u0301', 'ú'),
		('y\u0301', 'ý'),
		('o\u0308', 'ö'),
		# fjarlægja óæskileg tákn
		('\xad', ''),  # stundum notað til að tilgreina skiptingu orða á vefsíðum
		('\u200b', ''),  # zero width space
	]
	for search_str, replace_str in replacements:
		cleaned_str = cleaned_str.replace(search_str, replace_str)
	return cleaned_str


def check_if_string_is_number(mystr: str) -> bool:
	'''
	couple of checks to determine if string contains number
	todo: improve maybe
	'''
	if mystr.isdigit():
		return True
	if len(mystr) >= 5 and mystr[-4] == '.' and (mystr[:-4] + mystr[-3:]).isdigit():
		# example: 100.000
		return True
	if (
		len(mystr) >= 9 and
		mystr[-4] == '.' and
		mystr[-8] == '.' and
		(mystr[:-8] + mystr[-7:-4] + mystr[-3:]).isdigit()
	):
		# example: 1.000.000
		return True
	if (
		len(mystr) >= 13 and
		mystr[-4] == '.' and
		mystr[-8] == '.' and
		mystr[-12] == '.' and
		(mystr[:-12] + mystr[-11:-8] + mystr[-7:-4] + mystr[-3:]).isdigit()
	):
		# example: 1.000.000.000
		return True
	try:
		float(mystr.replace(',', '.', 1))
		return True
	except ValueError:
		pass
	# more checks?
	return False
