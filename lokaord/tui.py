#!/usr/bin/python
"""
Terminal User Interface functionality (powered by textual)

TUI for easily adding words to the dataset.

Development exec:

	$ textual run --dev lokaord/tui.py

"""
from decimal import Decimal
import sys

from textual import containers
from textual.app import App, ComposeResult
from textual.containers import Grid, ItemGrid, VerticalGroup, VerticalScroll
from textual.message import Message
from textual.screen import ModalScreen, Screen
from textual.widget import Widget
from textual.widgets import (
	Button,
	Checkbox,
	Footer,
	Input,
	Label,
	Header,
	Markdown,
	RadioButton,
	RadioSet,
	Select,
	TextArea,
)

try:
	# to make the above mentioned development execution works
	from lokaord import logman
except ModuleNotFoundError:
	sys.path.append('.')
	sys.path.append('..')
	from lokaord import logman
import lokaord
from lokaord.database import db
from lokaord.database.models import isl
from lokaord import structs
from lokaord import handlers


QuitMsg = None


class TriggerConfirmDiscard(Message):
	"""A message to signal the App that a specific action should occur."""

	def __init__(self, curr: str | None = None, prev: str | None = None):
		self.curr = curr
		self.prev = prev
		super().__init__()


class TriggerScrollToWidget(Message):
	"""A message to signal the App that a specific action should occur."""

	def __init__(self, widget, focus_id: str | None = None):
		self.widget = widget
		self.focus_id = focus_id
		super().__init__()


class ConfirmModal(ModalScreen[bool]):
	"""ModalScreen with a dialog to confirm or cancel."""

	Message = None

	def __init__(self, message: str | None = None, *args, **kwargs) -> None:
		self.Message = message
		super().__init__(*args, **kwargs)

	def compose(self) -> ComposeResult:
		yield Grid(
			Label(f'{self.Message}', id='question'),
			Button('Staðfesta', variant='error', id='btn_confirm'),
			Button('Hætta við', variant='primary', id='btn_cancel'),
			id='dialog',
		)

	def on_button_pressed(self, event: Button.Pressed) -> None:
		if event.button.id == 'btn_confirm':
			self.dismiss(True)
		else:
			self.dismiss(False)


class TilgreinaNafnord(VerticalGroup):
	DEFAULT_CLASSES = "column"

	def compose(self) -> ComposeResult:
		yield Markdown('3. Sláðu inn grunnupplýsingar nafnorðs og smelltu svo á [[ Áfram ]]')
		with containers.Grid(id='grid_tilgreina_ord'):
			yield Label('Orð')
			yield Input(placeholder='Grunnmynd', id='ord_lemma', valid_empty=True)
			yield Label('Kyn')
			with RadioSet():
				yield RadioButton('Karlkyn', id='ord_kyn_kk', value=True)
				yield RadioButton('Kvenkyn', id='ord_kyn_kvk')
				yield RadioButton('Hvorugkyn', id='ord_kyn_hk')
			yield Label('Merking')
			yield Input(placeholder='Merking (valkvætt, bara þegar þarf)', id='ord_merking')
			yield Label('Tölugildi')
			yield Input(
				type='number', placeholder='Tölugildi (valkvætt)', id='ord_tolugildi',
				valid_empty=True
			)
			yield Label('Ósjálfstætt')
			yield Checkbox(
				'Hakaðu hér ef um er að ræða ósjálfstæðan orðhluta', id='ord_osjalfstaett'
			)
			yield Label('Kennistrengur')
			yield Markdown('`---`', id='ord_kennistrengur')
			yield Label('Gagnaskrá')
			yield Markdown('`---`', id='ord_path')
			yield Label('')
			yield Button(
				'[[ Áfram ]] Sláðu inn grunnmynd orðs', variant="error", disabled=True,
				id='btn_ord_proceed'
			)


class TilgreinaNafnordBeygingar(VerticalGroup):
	DEFAULT_CLASSES = 'column'

	def compose(self) -> ComposeResult:
		yield Markdown((
			'4. Sláðu inn beygingarmyndir orðsins og / eða hakaðu í hvaða beygingarmyndir skuli'
			' hafa.'
		))
		with containers.Grid(id='grid_tilgreina_ord_beygingar'):
			# eintala
			yield Label('')
			yield Checkbox('Eintala', id='ord_enable_et', value=True)
			yield Label('')
			yield Label('')
			yield Checkbox('án greinis', id='ord_enable_et_ag', value=True)
			yield Checkbox('með greini', id='ord_enable_et_mg', value=True)
			yield Label('nf.')
			yield Input(placeholder='hestur', id='ord_beyging_et_ag_nf')
			yield Input(placeholder='hesturinn', id='ord_beyging_et_mg_nf')
			yield Label('þf.')
			yield Input(placeholder='hest', id='ord_beyging_et_ag_thf')
			yield Input(placeholder='hestinn', id='ord_beyging_et_mg_thf')
			yield Label('þgf.')
			yield Input(placeholder='hesti', id='ord_beyging_et_ag_thgf')
			yield Input(placeholder='hestinum', id='ord_beyging_et_mg_thgf')
			yield Label('ef.')
			yield Input(placeholder='hests', id='ord_beyging_et_ag_ef')
			yield Input(placeholder='hestsins', id='ord_beyging_et_mg_ef')
			# fleirtala
			yield Label('')
			yield Checkbox('Fleirtala', id='ord_enable_ft', value=True)
			yield Label('')
			yield Label('')
			yield Checkbox('án greinis', id='ord_enable_ft_ag', value=True)
			yield Checkbox('með greini', id='ord_enable_ft_mg', value=True)
			yield Label('nf.')
			yield Input(placeholder='hestar', id='ord_beyging_ft_ag_nf')
			yield Input(placeholder='hestarnir', id='ord_beyging_ft_mg_nf')
			yield Label('þf.')
			yield Input(placeholder='hesta', id='ord_beyging_ft_ag_thf')
			yield Input(placeholder='hestana', id='ord_beyging_ft_mg_thf')
			yield Label('þgf.')
			yield Input(placeholder='hestum', id='ord_beyging_ft_ag_thgf')
			yield Input(placeholder='hestunum', id='ord_beyging_ft_mg_thgf')
			yield Label('ef.')
			yield Input(placeholder='hesta', id='ord_beyging_ft_ag_ef')
			yield Input(placeholder='hestanna', id='ord_beyging_ft_mg_ef')
			yield Label('')
			with containers.Horizontal():
				yield Button(
					'[[ Vista ]] Fylltu inn beygingarmyndir', variant="error", disabled=True,
					id='btn_ord_commit'
				)
		yield Markdown((
			'5. Áður en smellt er á [[ Vista ]] hér fyrir ofan getur verið gott að skima yfir'
			' innslegin gögn á JSON sniði í textahólfinu hér fyrir neðan, síðan ef allt lítur þar'
			' vel út er ekkert því til fyrirstöðu að klára og vista nýja orðið.'
		))
		yield TextArea('{}', language='json', id='ord_data_json', read_only=True)


class BuildWordContainer(Widget):
	"""just a container"""

	def render(self) -> str:
		# prevent object name text in empty widget
		if not self.children:
			return ''
		return ''


class Content(VerticalScroll, can_focus=False):
	"""Non focusable vertical scroll."""


class HomeScreen(Screen):
	"""Textual UI for adding words."""

	DEFAULT_CLASSES = 'column'

	ADD_WORD_INSTRUCTIONS_MD = '''\
# Stofna nýtt orð

Hér geturðu búið til nýtt orð.

Ferlið er svohljóðandi:

1. Tilgreindu hvort um sé að ræða kjarnaorð eða samsett orð
2. Veldu orðflokk
'''

	ORDFLOKKAR = [flokkur.value.title() for flokkur in structs.Ordflokkar]

	ORD_SAMSETT = False
	ORD_STATE = {'orð': None, 'flokkur': None}

	def handle_updated_ord_state(self):
		if self.ORD_STATE['flokkur'] is None:
			return
		if self.ORD_STATE['flokkur'] != 'nafnorð':
			self.notify('todo: implement other orðflokkar')
			return
		ord_path = self.query_one('#ord_path', Markdown)
		ord_kennistrengur = self.query_one('#ord_kennistrengur', Markdown)
		ord_button = self.query_one('#btn_ord_proceed', Button)
		if self.ORD_STATE['orð'] in ('', None):
			ord_path.update('`---`')
			ord_kennistrengur.update('`---`')
			ord_button.label = '[[ Áfram ]] Sláðu inn grunnmynd orðs'
			ord_button.variant = 'error'
			ord_button.disabled = True
			el_ord_data_json = self.query_one('#ord_data_json', TextArea)
			el_ord_data_json.text = '{}'
		else:
			handler = handlers.Nafnord()
			handler.load_from_dict(self.ORD_STATE)
			kennistrengur = handler.make_kennistrengur()
			isl_ord = db.Session.query(isl.Ord).filter_by(Kennistrengur=kennistrengur).first()
			if isl_ord is None:
				ord_button.label = '[[ Áfram ]]'
				ord_button.variant = 'primary'
				ord_button.disabled = False
			else:
				ord_button.label = '[[ Áfram ]] Orð nú þegar til'
				ord_button.variant = 'error'
				ord_button.disabled = True
			new_path = handler.make_filename()
			ord_path.update(f'`lokaord/database/data/{new_path}`')
			ord_kennistrengur.update(f'`{kennistrengur}`')
		self.handle_ord_data_change()

	def on_button_pressed(self, event: Button.Pressed) -> None:
		global QuitMsg
		btn_id = event.button.id
		if btn_id == "btn_ord_proceed":
			el_tilgr_beyg = self.query_one('#el_tilgreina_beygingar', TilgreinaNafnordBeygingar)
			el_tilgr_beyg.remove_class('hidden')
			self.post_message(
				TriggerScrollToWidget(widget=el_tilgr_beyg, focus_id='#ord_beyging_et_ag_nf')
			)
		elif btn_id == "btn_ord_commit":
			handler = handlers.Nafnord()
			handler.load_from_dict(self.ORD_STATE)
			filename = handler.make_filename()
			handler.write_to_db()
			handler.write_to_file()
			# global QuitMsg hack to get a single log line to stdout after textual closes
			QuitMsg = f'add-word: orð vistað í skrá "{filename}"'
			self.app.exit()

	def on_checkbox_changed(self, event: Checkbox.Changed):
		ch_id = event.checkbox.id
		if ch_id == 'ord_osjalfstaett':
			if event.checkbox.value is False and 'ósjálfstætt' in self.ORD_STATE:
				del self.ORD_STATE['ósjálfstætt']
			else:
				self.ORD_STATE['ósjálfstætt'] = True
			self.handle_updated_ord_state()
		elif ch_id.startswith('ord_enable_'):
			self.handle_ord_data_change()
		else:
			self.notify(f'checkbox "{ch_id}"')


	def on_input_changed(self, event: Input.Changed) -> None:
		i_id = event.input.id
		i_val = event.input.value
		if i_id == 'ord_lemma':
			self.ORD_STATE['orð'] = i_val if i_val != '' else None
		elif i_id == 'ord_merking':
			if i_val == '':
				if 'merking' in self.ORD_STATE:
					del self.ORD_STATE['merking']
			else:
				self.ORD_STATE['merking'] = i_val
		elif i_id == 'ord_tolugildi':
			if i_val == '':
				if 'tölugildi' in self.ORD_STATE:
					del self.ORD_STATE['tölugildi']
			else:
				self.ORD_STATE['tölugildi'] = Decimal(i_val)
		elif i_id.startswith('ord_beyging_'):
			self.handle_ord_data_change()
		self.handle_updated_ord_state()

	def on_radio_set_changed(self, event: RadioSet.Changed) -> None:
		if event.pressed.id in ('kjarnaord', 'samsett_ord'):
			self.ORD_SAMSETT = (event.pressed.id == 'samsett_ord')
			self.handle_updated_ord_state()
		elif event.pressed.id in ('ord_kyn_kk', 'ord_kyn_kvk', 'ord_kyn_hk'):
			match event.pressed.id:
				case 'ord_kyn_kk':
					self.ORD_STATE['kyn'] = 'kk'
				case 'ord_kyn_kvk':
					self.ORD_STATE['kyn'] = 'kvk'
				case 'ord_kyn_hk':
					self.ORD_STATE['kyn'] = 'hk'
			self.handle_updated_ord_state()

	def on_select_changed(self, event: Select.Changed) -> None:
		if event.select.id == 'ordflokkur':
			sel_ordfl = event.select.value
			sel_ordfl_lower = sel_ordfl if sel_ordfl != Select.BLANK else None
			prev_ordfl = None
			if self.ORD_STATE['flokkur'] is not None:
				prev_ordfl = self.ORD_STATE['flokkur'].capitalize()
			if sel_ordfl == prev_ordfl:
				# gerist þegar verið er að bakfæra Select yfir í núverandi orðsmíðaflokk
				# sjá on_trigger_confirm_discard
				return
			if (
				self.ORD_STATE['orð'] is not None and
				self.ORD_STATE['flokkur'] is not None and
				sel_ordfl_lower != self.ORD_STATE['flokkur']
			):
				# UX
				# biðja notanda um að staðfesta fleygingu núverandi innsleginna gagna
				#
				# þegar breytt er um orðflokk með óvistað orð viljum við láta notandann staðfesta
				# til að minnka líkur á að óvart sé hent innslegnum upplýsingum
				self.post_message(TriggerConfirmDiscard(curr=sel_ordfl, prev=prev_ordfl))
			else:
				self.handle_ordflokkur_selection_change(sel_ordfl)

	def handle_ordflokkur_selection_change(self, sel_ordfl: str):
		chbox_samsett_ord = self.query_one('#samsett_ord', RadioButton)
		if sel_ordfl == 'Nafnorð' and chbox_samsett_ord.value is False:
			self.ORD_STATE['flokkur'] = 'nafnorð'
			self.ORD_STATE['kyn'] = 'kk'  # default
			el_build_word = self.query_one('#el_build_word', BuildWordContainer)
			tilgreina_nafnord = TilgreinaNafnord()
			el_build_word.mount(tilgreina_nafnord)
			tilgreina_beygingar = TilgreinaNafnordBeygingar(
				classes='hidden', id='el_tilgreina_beygingar'
			)
			el_build_word.mount(tilgreina_beygingar)
		else:  # event.select.value == Select.BLANK:
			unimplmemented = (
				'Lýsingarorð', 'Fornafn', 'Töluorð', 'Sagnorð', 'Smáorð', 'Sérnafn'
			)
			if sel_ordfl in unimplmemented:
				self.notify(f'TODO: útfæra UI fyrir orðflokk "{sel_ordfl}"')
			elif chbox_samsett_ord.value is True:
				self.notify(f'TODO: útfæra UI fyrir samsett orð og orðflokk "{sel_ordfl}"')
			self.ORD_STATE = {'orð': None, 'flokkur': None}
			el_build_word_container = self.query_one('#el_build_word', BuildWordContainer)
			el_build_word_container.query('*').remove()

	def handle_ord_data_change(self):
		input_empty = '---'
		# et checkboxes
		chbox_et = self.query_one('#ord_enable_et', Checkbox)
		chbox_et_ag = self.query_one('#ord_enable_et_ag', Checkbox)
		chbox_et_mg = self.query_one('#ord_enable_et_mg', Checkbox)
		# et ág
		beyging_et_ag_nf = self.query_one('#ord_beyging_et_ag_nf', Input)
		beyging_et_ag_thf = self.query_one('#ord_beyging_et_ag_thf', Input)
		beyging_et_ag_thgf = self.query_one('#ord_beyging_et_ag_thgf', Input)
		beyging_et_ag_ef = self.query_one('#ord_beyging_et_ag_ef', Input)
		# et mg
		beyging_et_mg_nf = self.query_one('#ord_beyging_et_mg_nf', Input)
		beyging_et_mg_thf = self.query_one('#ord_beyging_et_mg_thf', Input)
		beyging_et_mg_thgf = self.query_one('#ord_beyging_et_mg_thgf', Input)
		beyging_et_mg_ef = self.query_one('#ord_beyging_et_mg_ef', Input)
		# ft checkboxes
		chbox_ft = self.query_one('#ord_enable_ft', Checkbox)
		chbox_ft_ag = self.query_one('#ord_enable_ft_ag', Checkbox)
		chbox_ft_mg = self.query_one('#ord_enable_ft_mg', Checkbox)
		# ft ág
		beyging_ft_ag_nf = self.query_one('#ord_beyging_ft_ag_nf', Input)
		beyging_ft_ag_thf = self.query_one('#ord_beyging_ft_ag_thf', Input)
		beyging_ft_ag_thgf = self.query_one('#ord_beyging_ft_ag_thgf', Input)
		beyging_ft_ag_ef = self.query_one('#ord_beyging_ft_ag_ef', Input)
		# ft mg
		beyging_ft_mg_nf = self.query_one('#ord_beyging_ft_mg_nf', Input)
		beyging_ft_mg_thf = self.query_one('#ord_beyging_ft_mg_thf', Input)
		beyging_ft_mg_thgf = self.query_one('#ord_beyging_ft_mg_thgf', Input)
		beyging_ft_mg_ef = self.query_one('#ord_beyging_ft_mg_ef', Input)
		# button commit
		btn_ord_commit = self.query_one('#btn_ord_commit', Button)
		# json textarea
		el_ord_data_json = self.query_one('#ord_data_json', TextArea)
		# read data from ui, then update ord data and ui
		if chbox_et.value is True:
			if 'et' not in self.ORD_STATE:
				self.ORD_STATE['et'] = {}
			if chbox_et_ag.value is True:
				beyging_et_ag_nf.remove_class('ghost')
				beyging_et_ag_thf.remove_class('ghost')
				beyging_et_ag_thgf.remove_class('ghost')
				beyging_et_ag_ef.remove_class('ghost')
				self.ORD_STATE['et']['ág'] = [
					beyging_et_ag_nf.value or input_empty,
					beyging_et_ag_thf.value or input_empty,
					beyging_et_ag_thgf.value or input_empty,
					beyging_et_ag_ef.value or input_empty
				]
			elif 'ág' in self.ORD_STATE['et']:
				beyging_et_ag_nf.add_class('ghost')
				beyging_et_ag_thf.add_class('ghost')
				beyging_et_ag_thgf.add_class('ghost')
				beyging_et_ag_ef.add_class('ghost')
				del self.ORD_STATE['et']['ág']
			if chbox_et_mg.value is True:
				beyging_et_mg_nf.remove_class('ghost')
				beyging_et_mg_thf.remove_class('ghost')
				beyging_et_mg_thgf.remove_class('ghost')
				beyging_et_mg_ef.remove_class('ghost')
				self.ORD_STATE['et']['mg'] = [
					beyging_et_mg_nf.value or input_empty,
					beyging_et_mg_thf.value or input_empty,
					beyging_et_mg_thgf.value or input_empty,
					beyging_et_mg_ef.value or input_empty
				]
			elif 'mg' in self.ORD_STATE['et']:
				beyging_et_mg_nf.add_class('ghost')
				beyging_et_mg_thf.add_class('ghost')
				beyging_et_mg_thgf.add_class('ghost')
				beyging_et_mg_ef.add_class('ghost')
				del self.ORD_STATE['et']['mg']
			if chbox_et_ag.value is False and chbox_et_mg.value is False:
				del self.ORD_STATE['et']
		elif 'et' in self.ORD_STATE:
			beyging_et_ag_nf.add_class('ghost')
			beyging_et_ag_thf.add_class('ghost')
			beyging_et_ag_thgf.add_class('ghost')
			beyging_et_ag_ef.add_class('ghost')
			beyging_et_mg_nf.add_class('ghost')
			beyging_et_mg_thf.add_class('ghost')
			beyging_et_mg_thgf.add_class('ghost')
			beyging_et_mg_ef.add_class('ghost')
			del self.ORD_STATE['et']
		if chbox_ft.value is True:
			if 'ft' not in self.ORD_STATE:
				self.ORD_STATE['ft'] = {}
			if chbox_ft_ag.value is True:
				beyging_ft_ag_nf.remove_class('ghost')
				beyging_ft_ag_thf.remove_class('ghost')
				beyging_ft_ag_thgf.remove_class('ghost')
				beyging_ft_ag_ef.remove_class('ghost')
				self.ORD_STATE['ft']['ág'] = [
					beyging_ft_ag_nf.value or input_empty,
					beyging_ft_ag_thf.value or input_empty,
					beyging_ft_ag_thgf.value or input_empty,
					beyging_ft_ag_ef.value or input_empty
				]
			elif 'ág' in self.ORD_STATE['ft']:
				beyging_ft_ag_nf.add_class('ghost')
				beyging_ft_ag_thf.add_class('ghost')
				beyging_ft_ag_thgf.add_class('ghost')
				beyging_ft_ag_ef.add_class('ghost')
				del self.ORD_STATE['ft']['ág']
			if chbox_ft_mg.value is True:
				beyging_ft_mg_nf.remove_class('ghost')
				beyging_ft_mg_thf.remove_class('ghost')
				beyging_ft_mg_thgf.remove_class('ghost')
				beyging_ft_mg_ef.remove_class('ghost')
				self.ORD_STATE['ft']['mg'] = [
					beyging_ft_mg_nf.value or input_empty,
					beyging_ft_mg_thf.value or input_empty,
					beyging_ft_mg_thgf.value or input_empty,
					beyging_ft_mg_ef.value or input_empty
				]
			elif 'mg' in self.ORD_STATE['ft']:
				beyging_ft_mg_nf.add_class('ghost')
				beyging_ft_mg_thf.add_class('ghost')
				beyging_ft_mg_thgf.add_class('ghost')
				beyging_ft_mg_ef.add_class('ghost')
				del self.ORD_STATE['ft']['mg']
			if chbox_ft_ag.value is False and chbox_ft_mg.value is False:
				del self.ORD_STATE['ft']
		elif 'ft' in self.ORD_STATE:
			beyging_ft_ag_nf.add_class('ghost')
			beyging_ft_ag_thf.add_class('ghost')
			beyging_ft_ag_thgf.add_class('ghost')
			beyging_ft_ag_ef.add_class('ghost')
			beyging_ft_mg_nf.add_class('ghost')
			beyging_ft_mg_thf.add_class('ghost')
			beyging_ft_mg_thgf.add_class('ghost')
			beyging_ft_mg_ef.add_class('ghost')
			del self.ORD_STATE['ft']
		# update JSON text
		isl_ord = None
		if self.ORD_STATE['orð'] in ('', None):
			el_ord_data_json.text = '{}'
		else:
			handler = handlers.Nafnord()
			handler.load_from_dict(self.ORD_STATE)
			json_str = handler._ord_data_to_fancy_json_str(handler.data.dict())
			el_ord_data_json.text = json_str
			kennistrengur = handler.make_kennistrengur()
			isl_ord = db.Session.query(isl.Ord).filter_by(Kennistrengur=kennistrengur).first()
		# determine if ord is acceptable for saving, then update commit button accordingly
		fulfilled_et_ag = (
			chbox_et.value is False or
			chbox_et_ag.value is False or (
				beyging_et_ag_nf.value and
				beyging_et_ag_thf.value and
				beyging_et_ag_thgf.value and
				beyging_et_ag_ef.value
			)
		)
		fulfilled_et_mg = (
			chbox_et.value is False or
			chbox_et_mg.value is False or (
				beyging_et_mg_nf.value and
				beyging_et_mg_thf.value and
				beyging_et_mg_thgf.value and
				beyging_et_mg_ef.value
			)
		)
		fulfilled_ft_ag = (
			chbox_ft.value is False or
			chbox_ft_ag.value is False or (
				beyging_ft_ag_nf.value and
				beyging_ft_ag_thf.value and
				beyging_ft_ag_thgf.value and
				beyging_ft_ag_ef.value
			)
		)
		fulfilled_ft_mg = (
			chbox_ft.value is False or
			chbox_ft_mg.value is False or (
				beyging_ft_mg_nf.value and
				beyging_ft_mg_thf.value and
				beyging_ft_mg_thgf.value and
				beyging_ft_mg_ef.value
			)
		)
		if self.ORD_STATE['orð'] in ('', None):
			btn_ord_commit.label = '[[ Vista ]] Sláðu inn grunnmynd orðs'
			btn_ord_commit.variant = 'error'
			btn_ord_commit.disabled = True
		elif isl_ord is not None:
			btn_ord_commit.label = '[[ Vista ]] Orð nú þegar til'
			btn_ord_commit.variant = 'error'
			btn_ord_commit.disabled = True
		elif (
			not fulfilled_et_ag or not fulfilled_et_mg or not fulfilled_ft_ag or not fulfilled_ft_mg
		):
			btn_ord_commit.label = '[[ Vista ]] Fylltu inn beygingarmyndir'
			btn_ord_commit.variant = 'error'
			btn_ord_commit.disabled = True
		elif 'et' not in self.ORD_STATE and 'ft' not in self.ORD_STATE:
			btn_ord_commit.label = '[[ Vista ]] Tilgreindu beygingarmyndir'
			btn_ord_commit.variant = 'error'
			btn_ord_commit.disabled = True
		else:
			btn_ord_commit.label = '[[ Vista ]]'
			btn_ord_commit.variant = 'primary'
			btn_ord_commit.disabled = False

	def compose(self) -> ComposeResult:
		yield Header()
		with Content(id='main_content'):
			yield Markdown(self.ADD_WORD_INSTRUCTIONS_MD)
			with ItemGrid(min_column_width=20, regular=True):
				with RadioSet():
					yield RadioButton('Kjarnaorð', id='kjarnaord', value=True)
					# samsett orð disabled for now
					yield RadioButton('Samsett orð', id='samsett_ord', disabled=True)
				yield Select.from_values(self.ORDFLOKKAR, prompt='Veldu orðflokk ..', id='ordflokkur')
			yield BuildWordContainer(id='el_build_word', classes='box')
		yield Footer()

	def action_print_state(self):
		self.notify(f'print_state:\nsamsett: {self.ORD_SAMSETT}\nord_state: {self.ORD_STATE}')


class AddWordTUI(App):
	"""Add word TUI"""

	CSS_PATH = 'tcss/main.tcss'
	BINDINGS = [
		('d', 'toggle_dark', 'Toggle dark mode'),
		# ('s', 'print_state', 'Print state (dev)'),
	]
	HOMESCREEN = None

	def get_default_screen(self) -> Screen:
		self.HOMESCREEN = HomeScreen()
		return self.HOMESCREEN

	def on_mount(self) -> None:
		self.title = 'Loka-Orð'
		self.sub_title = 'Stofna nýtt orð'

	def action_toggle_dark(self) -> None:
		"""An action to toggle dark mode."""
		self.theme = 'textual-dark' if self.theme == 'nord' else 'nord'

	def on_trigger_confirm_discard(self, msg) -> None:
		def check_confirm(confirm: bool) -> None:
			if confirm is True:
				self.HOMESCREEN.handle_ordflokkur_selection_change(msg.curr)
			else:
				el_select_ordflokkur = self.query_one('#ordflokkur', Select)
				el_select_ordflokkur.value = msg.prev
		self.push_screen(
			ConfirmModal((
				'Þu ert að skipta um valinn orðflokk, núverandi innslegið orð hefur ekki verið'
				' vistað og verður fleygt, ertu viss?'
			)),
			check_confirm
		)

	def on_trigger_scroll_to_widget(self, msg) -> None:
		el_content = self.query_one('#main_content', Content)
		self.call_after_refresh(el_content.scroll_to_widget, msg.widget)
		el_focus = self.query_one(msg.focus_id)
		el_focus.focus()

	def action_print_state(self) -> None:
		self.HOMESCREEN.action_print_state()


def add_word_tui():
	app = AddWordTUI()
	app.run()
	if isinstance(QuitMsg, str):
		logman.info(QuitMsg)


if __name__ == '__main__':
	# $ textual run --dev lokaord/tui.py
	if logman.Logger is None:
		logman.init('lokaord-tui-dev')
	if db.Session is None:
		db.init(lokaord.Name)
	add_word_tui()
