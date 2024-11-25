#!/usr/bin/python
"""
Data structure definitions and validation for word files, powered mostly by pydantic.
"""
from decimal import Decimal
from enum import Enum
import os
from typing import Annotated, Any, Optional

from pydantic import BaseModel, conlist, Field, model_serializer, StringConstraints, validator


NonEmptyStr = Annotated[str, StringConstraints(strict=True, min_length=1)]


class MultiEnum(Enum):
	"""
	Custom Enum with three different values.
	- first/primary value: word group name in icelandic
	- second value: abbrevation (isl. skammstöfun)
	- third value: directory for files of given word group
	"""

	def __new__(cls, *values):
		# https://stackoverflow.com/a/43210118/2401628
		obj = object.__new__(cls)
		obj._value_ = values[0]  # first value is canonical value
		for other_value in values[1:]:
			cls._value2member_map_[other_value] = obj
		obj._all_values = values
		return obj

	def get_abbreviation(self):
		return self._all_values[1]

	def get_folder(self):
		return self._all_values[2]

	def __repr__(self):
		return '<%s.%s: %s>' % (
			self.__class__.__name__,
			self._name_,
			', '.join([repr(v) for v in self._all_values]),
		)


class Ordflokkar(MultiEnum):
	"""
	MultiEnum for primary orðflokkar.
	"""
	# fałlorð
	Nafnord = 'nafnorð', 'no', 'nafnord'
	Lysingarord = 'lýsingarorð', 'lo', 'lysingarord'
	Greinir = 'greinir', 'gr', 'greinir'
	Fornafn = 'fornafn', 'fn', 'fornofn'
	Toluord = 'töluorð', 'to', 'toluord'
	# sagnorð
	Sagnord = 'sagnorð', 'so', 'sagnord'
	# smáorð / óbeygjanleg orð
	Smaord = 'smáorð', 'smáo', 'smaord'
	# sérnöfn (mannanöfn, örnefni)
	Sernafn = 'sérnafn', 'sérn', 'sernofn'


class Fornafnaflokkar(MultiEnum):
	"""
	MultiEnum for subclasses of fornöfn.
	"""
	Personufornafn = 'persónu', 'fn.p', os.path.join('fornofn', 'personu')
	AfturbeygtFornafn = 'afturbeygt', 'fn.a', os.path.join('fornofn', 'afturbeygt')
	Eignarfornafn = 'eignar', 'fn.e', os.path.join('fornofn', 'eignar')
	Abendingarfornafn = 'ábendingar', 'fn.áb', os.path.join('fornofn', 'abendingar')
	Spurnarfornafn = 'spurnar', 'fn.sp', os.path.join('fornofn', 'spurnar')
	OakvedidFornafn = 'óákveðið', 'fn.óákv', os.path.join('fornofn', 'oakvedin')


class Toluordaflokkar(MultiEnum):
	"""
	MultiEnum for subclasses of töluorð.
	"""
	Fjoldatala = 'fjöldatala', 'to.ft', os.path.join('toluord', 'fjoldatolur')
	Radtala = 'raðtala', 'to.rt', os.path.join('toluord', 'radtolur')


class Smaordaflokkar(MultiEnum):
	"""
	MultiEnum for subclasses of smáorð.
	"""
	Forsetning = 'forsetning', 'smáo.fs', os.path.join('smaord', 'forsetning')
	Atviksord = 'atviksorð', 'smáo.ao', os.path.join('smaord', 'atviksord')
	Nafnhattarmerki = 'nafnháttarmerki', 'smáo.nhm', os.path.join('smaord', 'nafnhattarmerki')
	Samtenging = 'samtenging', 'smáo.st', os.path.join('smaord', 'samtenging')
	Upphropun = 'upphrópun', 'smáo.uh', os.path.join('smaord', 'upphropun')


class Sernafnaflokkar(MultiEnum):
	"""
	MultiEnum for subclasses of sérnöfn.
	"""
	Eiginnafn = 'eiginnafn', 'sérn.en', os.path.join('sernofn', 'mannanofn')
	Gaelunafn = 'gælunafn', 'sérn.gn', os.path.join('sernofn', 'gaelunofn')
	Kenninafn = 'kenninafn', 'sérn.kn', os.path.join('sernofn', 'mannanofn')
	Millinafn = 'miłlinafn', 'sérn.mn', os.path.join('sernofn', 'mannanofn', 'islensk-millinofn')
	Ornefni = 'örnefni', 'sérn.ön', os.path.join('sernofn', 'ornefni')


class Kyn(str, Enum):
	Kvenkyn = 'kvk'
	Karlkyn = 'kk'
	Hvorugkyn = 'hk'


class LysingarordMyndir(str, Enum):
	Frumstig_vb_kk = 'frumstig-vb-kk'
	Frumstig_vb_kvk = 'frumstig-vb-kvk'
	Frumstig_vb_hk = 'frumstig-vb-hk'
	Midstig_vb_kk = 'miðstig-vb-kk'
	Midstig_vb_kvk = 'miðstig-vb-kvk'
	Midstig_vb_hk = 'miðstig-vb-hk'
	Efstastig_vb_kk = 'efstastig-vb-kk'
	Efstastig_vb_kvk = 'efstastig-vb-kvk'
	Efstastig_vb_hk = 'efstastig-vb-hk'


class Ordasamsetningar(str, Enum):
	Stofnsamsetning = 'stofn'
	Eignarfallssamsetning = 'eignarfalls'
	Bandstafssamsetning = 'bandstafs'


class NafnordaBeygingar(str, Enum):
	Et = 'et'
	Et_ag = 'et-ág'
	Et_mg = 'et-mg'
	Ft = 'ft'
	Ft_ag = 'ft-ág'
	Ft_mg = 'ft-mg'


class LysingarordaBeygingar(str, Enum):
	# frumstig
	Frumstig = 'frumstig'
	Frumstig_sb = 'frumstig-sb'
	Frumstig_sb_et = 'frumstig-sb-et'
	Frumstig_sb_ft = 'frumstig-sb-ft'
	Frumstig_vb = 'frumstig-vb'
	Frumstig_vb_et = 'frumstig-vb-et'
	Frumstig_vb_ft = 'frumstig-vb-ft'
	# miðstig
	Midstig = 'miðstig'
	Midstig_vb_et = 'miðstig-vb-et'
	Midstig_vb_ft = 'miðstig-vb-ft'
	# efstastig
	Efstastig = 'efstastig'
	Efstastig_sb = 'efstastig-sb'
	Efstastig_sb_et = 'efstastig-sb-et'
	Efstastig_sb_ft = 'efstastig-sb-ft'
	Efstastig_vb = 'efstastig-vb'
	Efstastig_vb_et = 'efstastig-vb-et'
	Efstastig_vb_ft = 'efstastig-vb-ft'


class SagnordaBeygingar(str, Enum):
	# germynd
	Germynd = 'germynd'
	Germynd_personuleg = 'germynd-persónuleg'
	Germynd_opersonuleg = 'germynd-ópersónuleg'
	Germynd_spurnarmyndir = 'germynd-spurnarmyndir'
	# miðmynd
	Midmynd = 'miðmynd'
	Midmynd_personuleg = 'miðmynd-persónuleg'
	Midmynd_opersonuleg = 'miðmynd-ópersónuleg'
	Midmynd_spurnarmyndir = 'miðmynd-spurnarmyndir'
	# lýsingarháttur
	Lysingarhattur = 'lýsingarháttur'
	Lysingarhattur_nutidar = 'lýsingarháttur-nútíðar'
	Lysingarhattur_thatidar = 'lýsingarháttur-þátíðar'
	Lysingarhattur_thatidar_sb = 'lýsingarháttur-þátíðar-sb'
	Lysingarhattur_thatidar_vb = 'lýsingarháttur-þátíðar-vb'


class Fall(str, Enum):
	Nefnifall = 'nefnifałl'
	Tholfall = 'þolfałl'
	Thagufall = 'þágufałl'
	Eignarfall = 'eignarfałl'


class Fall2(str, Enum):
	Tholfall = 'þolfałl'
	Thagufall = 'þágufałl'
	Eignarfall = 'eignarfałl'


class Persona(str, Enum):
	Fyrsta = 'fyrsta'
	Onnur = 'önnur'
	Thridja = 'þriðja'


class FleiryrtTypa(str, Enum):
	Hlekkjud = 'hlekkjuð'
	Laus = 'laus'


class SamsettOrdhluti(BaseModel):

	mynd: Optional[NonEmptyStr] = None
	samsetning: Optional[Ordasamsetningar] = None
	myndir: Optional[LysingarordMyndir] = None
	lágstafa: Optional[bool] = False
	hástafa: Optional[bool] = False
	leiðir: Optional[NonEmptyStr] = None
	fylgir: Optional[NonEmptyStr] = None
	beygingar: Optional[conlist(
		NafnordaBeygingar | LysingarordaBeygingar | SagnordaBeygingar, min_length=1, max_length=4
	)] = None
	kennistrengur: Optional[NonEmptyStr] = None

	@validator('samsetning')
	def samsetning_tied_to_mynd(cls, val, values, **kwargs):
		if val is not None:
			if 'mynd' not in values or values['mynd'] is None:
				raise ValueError('mynd should be set when samsetning is set')
		elif 'mynd' in values and values['mynd'] is not None:
			raise ValueError('mynd should not be set when samsetning is not set')
		return val

	@validator('myndir')
	def myndir_mutually_exclusive_to_mynd_and_samsetning(cls, val, values, **kwargs):
		if val is not None:
			if 'mynd' in values and values['mynd'] is not None:
				raise ValueError('mynd+samsetning should not be set when myndir is set')
		return val

	@validator('hástafa')
	def hastafa_lagstafa_mutually_exclusive(cls, val, values, **kwargs):
		if val is True and 'lágstafa' in values and values['lágstafa'] is True:
			raise ValueError('hástafa and lágstafa are mutually exclusive')
		return val

	@validator('kennistrengur')
	def check_beygingar_based_on_kennistrengur(cls, val, values, **kwargs):
		if 'beygingar' in values and values['beygingar']:
			if val.startswith('no-') or val.startswith('sérn.'):  # nafnorð/sérnöfn
				for beyging in values['beygingar']:
					if not isinstance(beyging, NafnordaBeygingar):
						raise ValueError(
							f'inappropriate beyging "{beyging}" for nafnorð/sérnöfn (orð: {val})'
						)
			elif val.startswith('lo-'):  # lýsingarorð
				if 'myndir' in values and values['myndir'] is not None:
					for beyging in values['beygingar']:
						if not isinstance(beyging, NafnordaBeygingar):
							raise ValueError(
								f'inappropriate beyging "{beyging}" for lýsingarorð with "myndir"'
								f' mapping (orð: {val})'
							)
				else:
					for beyging in values['beygingar']:
						if not isinstance(beyging, LysingarordaBeygingar):
							raise ValueError(
								f'inappropriate beyging "{beyging}" for lýsingarorð (orð: {val})'
							)
			elif val.startswith('so-'):  # sagnorð
				for beyging in values['beygingar']:
					if not isinstance(beyging, SagnordaBeygingar):
						raise ValueError(
							f'inappropriate beyging "{beyging}" for sagnorð (orð: {val})'
						)
			else:
				for beyging in values['beygingar']:
					raise ValueError(
						f'unsupported beyging "{beyging}" for orð (orð: {val})'
					)
		return val

	@model_serializer(mode='wrap')
	def serialize(self, handler) -> dict[str, Any]:
		data_dict = handler(self)
		data = dict()
		key_order = [
			'mynd', 'samsetning', 'myndir', 'lágstafa', 'hástafa', 'leiðir', 'fylgir', 'beygingar',
			'kennistrengur'
		]
		keys_values = ('samsetning', 'myndir')
		keys_list_values = ('beygingar', )
		keys_only_if_true = ('lágstafa', 'hástafa', 'ósjálfstætt')
		for key in key_order:
			if data_dict[key] is not None:
				if key in keys_values:
					data[key] = data_dict[key].value
				elif key in keys_list_values:
					data[key] = []
					for val in data_dict[key]:
						data[key].append(val.value)
				elif key in keys_only_if_true:
					if data_dict[key] is True:
						data[key] = data_dict[key]
				else:
					data[key] = data_dict[key]
		return data


class OrdData(BaseModel):
	orð: NonEmptyStr
	flokkur: Ordflokkar
	undirflokkur: Optional[
		Fornafnaflokkar | Toluordaflokkar | Smaordaflokkar | Sernafnaflokkar
	] = None
	merking: Optional[NonEmptyStr] = None
	samsett: Optional[conlist(SamsettOrdhluti, min_length=1)] = None
	tölugildi: Optional[Decimal] = None
	óbeygjanlegt: Optional[bool] = None
	ósjálfstætt: Optional[bool] = None
	datahash: Optional[NonEmptyStr] = Field(default=None, alias='hash')
	kennistrengur: Optional[NonEmptyStr] = None

	@validator('undirflokkur')
	def undirflokkur_constraints_based_on_flokkur(cls, val, values, **kwargs):
		fl_m_ufl = (Ordflokkar.Fornafn, Ordflokkar.Toluord, Ordflokkar.Smaord, Ordflokkar.Sernafn)
		if values['flokkur'] in fl_m_ufl:
			if val is None:
				raise ValueError('missing undirflokkur')
		if values['flokkur'] is Ordflokkar.Fornafn and not isinstance(val, Fornafnaflokkar):
			raise ValueError('invalid fornafn undirflokkur')
		if values['flokkur'] is Ordflokkar.Toluord and not isinstance(val, Toluordaflokkar):
			raise ValueError('invalid töluorð undirflokkur')
		if values['flokkur'] is Ordflokkar.Smaord and not isinstance(val, Smaordaflokkar):
			raise ValueError('invalid smáorð undirflokkur')
		if values['flokkur'] is Ordflokkar.Sernafn and not isinstance(val, Sernafnaflokkar):
			raise ValueError('invalid sérnafn undirflokkur')
		return val


class NafnordBeygingarAgMgSet(BaseModel):
	ág: Optional[conlist(NonEmptyStr, min_length=4, max_length=4)] = None
	mg: Optional[conlist(NonEmptyStr, min_length=4, max_length=4)] = None

	@validator('ág', 'mg')
	def ag_mg_constraint(cls, val, values, **kwargs):
		if val is not None:
			if all(x is None for x in val):
				raise ValueError('fallbeyging list should contain something')
		return val

	@validator('mg')
	def mg_constraint(cls, val, values, **kwargs):
		if val is None and ('ág' not in values or values['ág'] is None):
			raise ValueError('either ág or mg must be set')
		return val

	@model_serializer(mode='wrap')
	def serialize(self, handler) -> dict[str, Any]:
		data_dict = handler(self)
		data = dict()
		if 'ág' in data_dict and data_dict['ág'] is not None:
			data['ág'] = data_dict['ág']
		if 'mg' in data_dict and data_dict['mg'] is not None:
			data['mg'] = data_dict['mg']
		return data


class NafnordData(OrdData):
	kyn: Kyn
	et: Optional[NafnordBeygingarAgMgSet] = None
	ft: Optional[NafnordBeygingarAgMgSet] = None

	@validator('flokkur')
	def should_be_nafnord(cls, val, values, **kwargs):
		if val is not Ordflokkar.Nafnord:
			raise ValueError('flokkur should be nafnorð')
		return val

	@validator('undirflokkur')
	def should_not_be_set(cls, val, values, **kwargs):
		if val is not None:
			raise ValueError('undirflokkur should not be set')
		return val

	@validator('ft')
	def ft_constraint(cls, val, values, **kwargs):
		"""either et or ft should be set"""
		if val is None:
			if 'et' not in values or values['et'] is None:
				raise ValueError('nafnorð should have either et or ft beygingar')
		return val

	@model_serializer(mode='wrap')
	def serialize(self, handler) -> dict[str, Any]:
		data_dict = handler(self)
		data = dict()
		key_order = [
			'orð', 'flokkur', 'kyn', 'tölugildi', 'merking', 'samsett', 'et', 'ft', 'ósjálfstætt',
			'kennistrengur', 'datahash'
		]
		key_map = {'datahash': 'hash'}
		keys_values = ('flokkur', 'kyn')
		keys_only_if_true = ('ósjálfstætt', )
		for key in key_order:
			if data_dict[key] is not None:
				if key in keys_values:
					data[key] = data_dict[key].value
				elif key in key_map:
					data[key_map[key]] = data_dict[key]
				elif key in keys_only_if_true:
					if data_dict[key] is True:
						data[key] = data_dict[key]
				else:
					data[key] = data_dict[key]
		return data


class LysingarordKyn(BaseModel):
	kk: Optional[conlist(Optional[NonEmptyStr], min_length=4, max_length=4)] = None
	kvk: Optional[conlist(Optional[NonEmptyStr], min_length=4, max_length=4)] = None
	hk: Optional[conlist(Optional[NonEmptyStr], min_length=4, max_length=4)] = None

	@model_serializer(mode='wrap')
	def serialize(self, handler) -> dict[str, Any]:
		data_dict = handler(self)
		data = dict()
		if data_dict['kk'] is not None:
			data['kk'] = data_dict['kk']
		if data_dict['kvk'] is not None:
			data['kvk'] = data_dict['kvk']
		if data_dict['hk'] is not None:
			data['hk'] = data_dict['hk']
		return data

	@validator('hk')
	def not_void_of_data(cls, val, values, **kwargs):
		"""at least one of kk/kvk/hk should be provided, and should have some non-None/null data"""
		has_data = False
		if val is not None:
			for beyging in val:
				if beyging is not None:
					has_data = True
		if not has_data:
			if 'kk' in values and values['kk'] is not None:
				for beyging in values['kk']:
					if beyging is not None:
						has_data = True
		if not has_data:
			if 'kvk' in values and values['kvk'] is not None:
				for beyging in values['kvk']:
					if beyging is not None:
						has_data = True
		if not has_data:
			raise ValueError('lýsingarorð kyn should not be void of data')
		return val


class LysingarordEtFt(BaseModel):
	et: Optional[LysingarordKyn] = None
	ft: Optional[LysingarordKyn] = None

	@model_serializer(mode='wrap')
	def serialize(self, handler) -> dict[str, Any]:
		data_dict = handler(self)
		data = dict()
		if 'et' in data_dict and data_dict['et'] is not None:
			data['et'] = data_dict['et']
		if 'ft' in data_dict and data_dict['ft'] is not None:
			data['ft'] = data_dict['ft']
		return data

	@validator('ft')
	def not_void_of_data(cls, val, values, **kwargs):
		if val is None:
			if 'et' not in values or values['et'] is None:
				raise ValueError('lýsingarorð et/ft should not be void of data')
		return val


class LysingarordStig(BaseModel):
	sb: Optional[LysingarordEtFt] = None
	vb: Optional[LysingarordEtFt] = None

	@model_serializer(mode='wrap')
	def serialize(self, handler) -> dict[str, Any]:
		data_dict = handler(self)
		data = dict()
		if 'sb' in data_dict and data_dict['sb'] is not None:
			data['sb'] = data_dict['sb']
		if 'vb' in data_dict and data_dict['vb'] is not None:
			data['vb'] = data_dict['vb']
		return data


class LysingarordData(OrdData):
	frumstig: Optional[LysingarordStig] = None
	miðstig: Optional[LysingarordStig] = None
	efstastig: Optional[LysingarordStig] = None

	@validator('flokkur')
	def should_be_lysingarord(cls, val, values, **kwargs):
		if val is not Ordflokkar.Lysingarord:
			raise ValueError('flokkur should be lýsingarorð')
		return val

	@validator('undirflokkur')
	def should_not_be_set(cls, val, values, **kwargs):
		if val is not None:
			raise ValueError('undirflokkur should not be set')
		return val

	@validator('efstastig')
	def have_some_data(cls, val, values, **kwargs):
		"""frumstig, miðstig and efstastig may not all be unset unless óbeygjanlegt is true"""
		if (
			val is None and
			('miðstig' not in values or values['miðstig'] is None) and
			('frumstig' not in values or values['frumstig'] is None) and
			('óbeygjanlegt' not in values or values['óbeygjanlegt'] in (None, False))
		):
			raise ValueError(
				"frumstig, miðstig and efstastig shouldn't all be unset unless óbeygjanlegt is true"
			)
		return val

	@model_serializer(mode='wrap')
	def serialize(self, handler) -> dict[str, Any]:
		data_dict = handler(self)
		data = dict()
		key_order = [
			'orð', 'flokkur', 'tölugildi', 'merking', 'samsett', 'frumstig', 'miðstig',
			'efstastig', 'ósjálfstætt', 'óbeygjanlegt', 'kennistrengur', 'datahash'
		]
		key_map = {'datahash': 'hash'}
		keys_values = ('flokkur', )
		keys_only_if_true = ('ósjálfstætt', 'óbeygjanlegt')
		for key in key_order:
			if data_dict[key] is not None:
				if key in keys_values:
					data[key] = data_dict[key].value
				elif key in key_map:
					data[key_map[key]] = data_dict[key]
				elif key in keys_only_if_true:
					if data_dict[key] is True:
						data[key] = data_dict[key]
				else:
					data[key] = data_dict[key]
		return data


class SagnordBodhattur(BaseModel):
	stýfður: Optional[NonEmptyStr] = None
	et: Optional[NonEmptyStr] = None
	ft: Optional[NonEmptyStr] = None

	@model_serializer(mode='wrap')
	def serialize(self, handler) -> dict[str, Any]:
		data_dict = handler(self)
		data = dict()
		if 'stýfður' in data_dict and data_dict['stýfður'] is not None:
			data['stýfður'] = data_dict['stýfður']
		if 'et' in data_dict and data_dict['et'] is not None:
			data['et'] = data_dict['et']
		if 'ft' in data_dict and data_dict['ft'] is not None:
			data['ft'] = data_dict['ft']
		return data


class SagnordTalaL(BaseModel):
	et: Optional[conlist(NonEmptyStr, min_length=3, max_length=3)] = None
	ft: Optional[conlist(NonEmptyStr, min_length=3, max_length=3)] = None

	@validator('ft')
	def et_ft_constraint(cls, val, values, **kwargs):
		if val is None:
			if 'et' not in values or values['et'] is None:
				raise ValueError('either et or ft should be set')
		return val

	@model_serializer(mode='wrap')
	def serialize(self, handler) -> dict[str, Any]:
		data_dict = handler(self)
		data = dict()
		if 'et' in data_dict and data_dict['et'] is not None:
			data['et'] = data_dict['et']
		if 'ft' in data_dict and data_dict['ft'] is not None:
			data['ft'] = data_dict['ft']
		return data


class SagnordTidL(BaseModel):
	nútíð: Optional[SagnordTalaL] = None
	þátíð: Optional[SagnordTalaL] = None

	@validator('þátíð')
	def nutid_thatid_constraint(cls, val, values, **kwargs):
		if val is None:
			if 'nútíð' not in values or values['nútíð'] is None:
				raise ValueError('either nútíð or þátíð should be set')
		return val

	@model_serializer(mode='wrap')
	def serialize(self, handler) -> dict[str, Any]:
		data_dict = handler(self)
		data = dict()
		if 'nútíð' in data_dict and data_dict['nútíð'] is not None:
			data['nútíð'] = data_dict['nútíð']
		if 'þátíð' in data_dict and data_dict['þátíð'] is not None:
			data['þátíð'] = data_dict['þátíð']
		return data


class SagnordHatturL(BaseModel):
	frumlag: Optional[Fall] = None
	framsöguháttur: Optional[SagnordTidL] = None
	viðtengingarháttur: Optional[SagnordTidL] = None

	@validator('viðtengingarháttur')
	def framsogu_vidtengingar_constraint(cls, val, values, **kwargs):
		if val is None:
			if 'framsöguháttur' not in values or values['framsöguháttur'] is None:
				raise ValueError('either framsöguháttur or viðtengingarháttur should be set')
		return val

	@model_serializer(mode='wrap')
	def serialize(self, handler) -> dict[str, Any]:
		data_dict = handler(self)
		data = dict()
		if 'frumlag' in data_dict and data_dict['frumlag'] is not None:
			data['frumlag'] = data_dict['frumlag']
		if 'framsöguháttur' in data_dict and data_dict['framsöguháttur'] is not None:
			data['framsöguháttur'] = data_dict['framsöguháttur']
		if 'viðtengingarháttur' in data_dict and data_dict['viðtengingarháttur'] is not None:
			data['viðtengingarháttur'] = data_dict['viðtengingarháttur']
		return data


class SagnordTala(BaseModel):
	et: Optional[NonEmptyStr] = None
	ft: Optional[NonEmptyStr] = None

	@validator('ft')
	def et_ft_constraint(cls, val, values, **kwargs):
		if val is None:
			if 'et' not in values or values['et'] is None:
				raise ValueError('either et or ft should be set')
		return val

	@model_serializer(mode='wrap')
	def serialize(self, handler) -> dict[str, Any]:
		data_dict = handler(self)
		data = dict()
		if 'et' in data_dict and data_dict['et'] is not None:
			data['et'] = data_dict['et']
		if 'ft' in data_dict and data_dict['ft'] is not None:
			data['ft'] = data_dict['ft']
		return data


class SagnordTid(BaseModel):
	nútíð: Optional[SagnordTala] = None
	þátíð: Optional[SagnordTala] = None

	@validator('þátíð')
	def nutid_thatid_constraint(cls, val, values, **kwargs):
		if val is None:
			if 'nútíð' not in values or values['nútíð'] is None:
				raise ValueError('either nútíð or þátíð should be set')
		return val

	@model_serializer(mode='wrap')
	def serialize(self, handler) -> dict[str, Any]:
		data_dict = handler(self)
		data = dict()
		if 'nútíð' in data_dict and data_dict['nútíð'] is not None:
			data['nútíð'] = data_dict['nútíð']
		if 'þátíð' in data_dict and data_dict['þátíð'] is not None:
			data['þátíð'] = data_dict['þátíð']
		return data


class SagnordHattur(BaseModel):
	framsöguháttur: SagnordTid
	viðtengingarháttur: SagnordTid

	@model_serializer(mode='wrap')
	def serialize(self, handler) -> dict[str, Any]:
		data_dict = handler(self)
		data = dict()
		data['framsöguháttur'] = data_dict['framsöguháttur']
		data['viðtengingarháttur'] = data_dict['viðtengingarháttur']
		return data


class SagnordMynd(BaseModel):
	nafnháttur: NonEmptyStr
	sagnbót: Optional[NonEmptyStr] = None
	boðháttur: Optional[SagnordBodhattur] = None
	persónuleg: Optional[SagnordHatturL] = None
	ópersónuleg: Optional[SagnordHatturL] = None
	spurnarmyndir: Optional[SagnordHattur] = None

	@model_serializer(mode='wrap')
	def serialize(self, handler) -> dict[str, Any]:
		data_dict = handler(self)
		data = dict()
		data['nafnháttur'] = data_dict['nafnháttur']
		if 'sagnbót' in data_dict and data_dict['sagnbót'] is not None:
			data['sagnbót'] = data_dict['sagnbót']
		if 'boðháttur' in data_dict and data_dict['boðháttur'] is not None:
			data['boðháttur'] = data_dict['boðháttur']
		if 'persónuleg' in data_dict and data_dict['persónuleg'] is not None:
			data['persónuleg'] = data_dict['persónuleg']
		if 'ópersónuleg' in data_dict and data_dict['ópersónuleg'] is not None:
			data['ópersónuleg'] = data_dict['ópersónuleg']
		if 'spurnarmyndir' in data_dict and data_dict['spurnarmyndir'] is not None:
			data['spurnarmyndir'] = data_dict['spurnarmyndir']
		return data


class SagnordLhTTK(BaseModel):
	kk: conlist(NonEmptyStr, min_length=4, max_length=4)
	kvk: conlist(NonEmptyStr, min_length=4, max_length=4)
	hk: conlist(NonEmptyStr, min_length=4, max_length=4)

	@model_serializer(mode='wrap')
	def serialize(self, handler) -> dict[str, Any]:
		data_dict = handler(self)
		data = dict()
		data['kk'] = data_dict['kk']
		data['kvk'] = data_dict['kvk']
		data['hk'] = data_dict['hk']
		return data


class SagnordLhTT(BaseModel):
	et: SagnordLhTTK
	ft: SagnordLhTTK

	@model_serializer(mode='wrap')
	def serialize(self, handler) -> dict[str, Any]:
		data_dict = handler(self)
		data = dict()
		data['et'] = data_dict['et']
		data['ft'] = data_dict['ft']
		return data


class SagnordLhT(BaseModel):
	sb: Optional[SagnordLhTT] = None
	vb: Optional[SagnordLhTT] = None

	@validator('vb')
	def sb_vb_constraint(cls, val, values, **kwargs):
		if val is None:
			if 'sb' not in values or values['sb'] is None:
				raise ValueError('either sb or vb should be set')
		return val

	@model_serializer(mode='wrap')
	def serialize(self, handler) -> dict[str, Any]:
		data_dict = handler(self)
		data = dict()
		if 'sb' in data_dict and data_dict['sb'] is not None:
			data['sb'] = data_dict['sb']
		if 'vb' in data_dict and data_dict['vb'] is not None:
			data['vb'] = data_dict['vb']
		return data


class SagnordLysingarhattur(BaseModel):
	nútíðar: Optional[NonEmptyStr] = None
	þátíðar: Optional[SagnordLhT] = None

	@model_serializer(mode='wrap')
	def serialize(self, handler) -> dict[str, Any]:
		data_dict = handler(self)
		data = dict()
		if 'nútíðar' in data_dict and data_dict['nútíðar'] is not None:
			data['nútíðar'] = data_dict['nútíðar']
		if 'þátíðar' in data_dict and data_dict['þátíðar'] is not None:
			data['þátíðar'] = data_dict['þátíðar']
		return data


class SagnordData(OrdData):
	germynd: Optional[SagnordMynd] = None
	miðmynd: Optional[SagnordMynd] = None
	lýsingarháttur: Optional[SagnordLysingarhattur] = None
	óskháttur_1p_ft: Optional[NonEmptyStr] = None
	óskháttur_3p: Optional[NonEmptyStr] = None

	@validator('flokkur')
	def should_be_sagnord(cls, val, values, **kwargs):
		if val is not Ordflokkar.Sagnord:
			raise ValueError('flokkur should be sagnorð')
		return val

	@validator('undirflokkur')
	def should_not_be_set(cls, val, values, **kwargs):
		if val is not None:
			raise ValueError('undirflokkur should not be set')
		return val

	@model_serializer(mode='wrap')
	def serialize(self, handler) -> dict[str, Any]:
		data_dict = handler(self)
		data = dict()
		key_order = [
			'orð', 'flokkur', 'tölugildi', 'merking', 'samsett', 'germynd', 'miðmynd',
			'lýsingarháttur', 'óskháttur_1p_ft', 'óskháttur_3p', 'ósjálfstætt', 'óbeygjanlegt',
			'kennistrengur', 'datahash'
		]
		key_map = {'datahash': 'hash'}
		keys_values = ('flokkur', )
		keys_only_if_true = ('ósjálfstætt', 'óbeygjanlegt')
		for key in key_order:
			if data_dict[key] is not None:
				if key in keys_values:
					data[key] = data_dict[key].value
				elif key in key_map:
					data[key_map[key]] = data_dict[key]
				elif key in keys_only_if_true:
					if data_dict[key] is True:
						data[key] = data_dict[key]
				else:
					data[key] = data_dict[key]
		return data


class GreinirKyn(BaseModel):
	kk: conlist(NonEmptyStr, min_length=4, max_length=4)
	kvk: conlist(NonEmptyStr, min_length=4, max_length=4)
	hk: conlist(NonEmptyStr, min_length=4, max_length=4)

	@model_serializer(mode='wrap')
	def serialize(self, handler) -> dict[str, Any]:
		data_dict = handler(self)
		data = dict()
		data['kk'] = data_dict['kk']
		data['kvk'] = data_dict['kvk']
		data['hk'] = data_dict['hk']
		return data


class GreinirData(OrdData):
	et: GreinirKyn
	ft: GreinirKyn

	@validator('flokkur')
	def should_be_greinir(cls, val, values, **kwargs):
		if val is not Ordflokkar.Greinir:
			raise ValueError('flokkur should be greinir')
		return val

	@validator('undirflokkur')
	def should_not_be_set(cls, val, values, **kwargs):
		if val is not None:
			raise ValueError('undirflokkur should not be set')
		return val

	@model_serializer(mode='wrap')
	def serialize(self, handler) -> dict[str, Any]:
		data_dict = handler(self)
		data = dict()
		key_order = [
			'orð', 'flokkur', 'merking', 'samsett', 'tölugildi', 'et', 'ft', 'kennistrengur',
			'datahash'
		]
		key_map = {'datahash': 'hash'}
		keys_values = ('flokkur', )
		for key in key_order:
			if data_dict[key] is not None:
				if key in keys_values:
					data[key] = data_dict[key].value
				elif key in key_map:
					data[key_map[key]] = data_dict[key]
				else:
					data[key] = data_dict[key]
		return data


class FornafnKyn(BaseModel):
	kk: Optional[conlist(Optional[NonEmptyStr], min_length=4, max_length=4)] = None
	kvk: Optional[conlist(Optional[NonEmptyStr], min_length=4, max_length=4)] = None
	hk: Optional[conlist(Optional[NonEmptyStr], min_length=4, max_length=4)] = None

	@validator('hk')
	def kk_kvk_hk_constraint(cls, val, values, **kwargs):
		if val is None:
			if 'kvk' not in values or values['kvk'] is None:
				if 'kk' not in values or values['kk'] is None:
					raise ValueError('at least one of kk, kvk, hk should be set')
		return val

	@model_serializer(mode='wrap')
	def serialize(self, handler) -> dict[str, Any]:
		data_dict = handler(self)
		data = dict()
		if 'kk' in data_dict and data_dict['kk'] is not None:
			data['kk'] = data_dict['kk']
		if 'kvk' in data_dict and data_dict['kvk'] is not None:
			data['kvk'] = data_dict['kvk']
		if 'hk' in data_dict and data_dict['hk'] is not None:
			data['hk'] = data_dict['hk']
		return data


class FornafnData(OrdData):
	persóna: Optional[Persona] = None
	kyn: Optional[Kyn] = None
	et: Optional[FornafnKyn | conlist(Optional[NonEmptyStr], min_length=4, max_length=4)] = None
	ft: Optional[FornafnKyn | conlist(Optional[NonEmptyStr], min_length=4, max_length=4)] = None

	@validator('flokkur')
	def should_be_fornafn(cls, val, values, **kwargs):
		if val is not Ordflokkar.Fornafn:
			raise ValueError('flokkur should be fornafn')
		return val

	@validator('undirflokkur')
	def should_be_set(cls, val, values, **kwargs):
		if val is None:
			raise ValueError('undirflokkur should be set')
		elif not isinstance(val, Fornafnaflokkar):
			raise ValueError('undirflokkur should be fornafnaflokkur')
		return val

	@validator('ft')
	def et_ft_constraint(cls, val, values, **kwargs):
		if val is not None:
			if isinstance(val, list):
				if (
					'et' in values and values['et'] is not None and
					not isinstance(values['et'], list)
				):
					raise ValueError('when both et and ft are set they should have same type')
			elif 'et' in values and values['et'] is not None and isinstance(values['et'], list):
				raise ValueError('when et and ft are both set they should have same type')
		elif 'et' not in values or values['et'] is None:
			raise ValueError('either et or ft should be set')
		return val

	@model_serializer(mode='wrap')
	def serialize(self, handler) -> dict[str, Any]:
		data_dict = handler(self)
		data = dict()
		key_order = [
			'orð', 'flokkur', 'undirflokkur', 'merking', 'samsett', 'persóna', 'kyn', 'samsett',
			'et', 'ft', 'ósjálfstætt', 'óbeygjanlegt', 'kennistrengur', 'datahash'
		]
		key_map = {'datahash': 'hash'}
		keys_values = ('flokkur', 'undirflokkur')
		keys_only_if_true = ('ósjálfstætt', 'óbeygjanlegt')
		for key in key_order:
			if data_dict[key] is not None:
				if key in keys_values:
					data[key] = data_dict[key].value
				elif key in key_map:
					data[key_map[key]] = data_dict[key]
				elif key in keys_only_if_true:
					if data_dict[key] is True:
						data[key] = data_dict[key]
				else:
					data[key] = data_dict[key]
		return data


class ToluordKyn(BaseModel):
	kk: conlist(NonEmptyStr, min_length=4, max_length=4)
	kvk: conlist(NonEmptyStr, min_length=4, max_length=4)
	hk: conlist(NonEmptyStr, min_length=4, max_length=4)

	@model_serializer(mode='wrap')
	def serialize(self, handler) -> dict[str, Any]:
		data_dict = handler(self)
		data = dict()
		data['kk'] = data_dict['kk']
		data['kvk'] = data_dict['kvk']
		data['hk'] = data_dict['hk']
		return data


class ToluordEtFt(BaseModel):
	et: ToluordKyn
	ft: ToluordKyn


class FjoldatalaData(OrdData):
	tölugildi: Decimal
	et: Optional[ToluordKyn] = None
	ft: Optional[ToluordKyn] = None

	@validator('flokkur')
	def should_be_toluord(cls, val, values, **kwargs):
		if val is not Ordflokkar.Toluord:
			raise ValueError('flokkur should be töluorð')
		return val

	@validator('undirflokkur')
	def should_be_set(cls, val, values, **kwargs):
		if val is None:
			raise ValueError('undirflokkur should be set')
		elif val is not Toluordaflokkar.Fjoldatala:
			raise ValueError('undirflokkur should be fjöldatala')
		return val

	@validator('ft')
	def et_ft_constraint(cls, val, values, **kwargs):
		if val is None:
			if 'et' not in values or values['et'] is None:
				if 'óbeygjanlegt' not in values or values['óbeygjanlegt'] is None:
					raise ValueError('et and ft can both be unset only if óbeygjanlegt')
		return val

	@model_serializer(mode='wrap')
	def serialize(self, handler) -> dict[str, Any]:
		data_dict = handler(self)
		data = dict()
		key_order = [
			'orð', 'flokkur', 'undirflokkur', 'tölugildi', 'merking', 'samsett', 'et', 'ft',
			'ósjálfstætt', 'óbeygjanlegt', 'kennistrengur', 'datahash'
		]
		key_map = {'datahash': 'hash'}
		keys_values = ('flokkur', 'undirflokkur')
		keys_only_if_true = ('ósjálfstætt', 'óbeygjanlegt')
		for key in key_order:
			if data_dict[key] is not None:
				if key in keys_values:
					data[key] = data_dict[key].value
				elif key in key_map:
					data[key_map[key]] = data_dict[key]
				elif key in keys_only_if_true:
					if data_dict[key] is True:
						data[key] = data_dict[key]
				else:
					data[key] = data_dict[key]
		return data


class RadtalaData(OrdData):
	tölugildi: Decimal
	sb: Optional[ToluordEtFt] = None
	vb: Optional[ToluordEtFt] = None

	@validator('flokkur')
	def should_be_toluord(cls, val, values, **kwargs):
		if val is not Ordflokkar.Toluord:
			raise ValueError('flokkur should be töluorð')
		return val

	@validator('undirflokkur')
	def should_be_set(cls, val, values, **kwargs):
		if val is None:
			raise ValueError('undirflokkur should be set')
		elif val is not Toluordaflokkar.Radtala:
			raise ValueError('undirflokkur should be raðtala')
		return val

	@model_serializer(mode='wrap')
	def serialize(self, handler) -> dict[str, Any]:
		data_dict = handler(self)
		data = dict()
		key_order = [
			'orð', 'flokkur', 'undirflokkur', 'tölugildi', 'merking', 'samsett', 'sb', 'vb',
			'ósjálfstætt', 'óbeygjanlegt', 'kennistrengur', 'datahash'
		]
		key_map = {'datahash': 'hash'}
		keys_values = ('flokkur', 'undirflokkur')
		keys_only_if_true = ('ósjálfstætt', 'óbeygjanlegt')
		for key in key_order:
			if data_dict[key] is not None:
				if key in keys_values:
					data[key] = data_dict[key].value
				elif key in key_map:
					data[key_map[key]] = data_dict[key]
				elif key in keys_only_if_true:
					if data_dict[key] is True:
						data[key] = data_dict[key]
				else:
					data[key] = data_dict[key]
		return data


class ForsetningData(OrdData):
	stýrir: conlist(Fall2, min_length=1, max_length=3)

	@validator('flokkur')
	def should_be_smaord(cls, val, values, **kwargs):
		if val is not Ordflokkar.Smaord:
			raise ValueError('flokkur should be smáorð')
		return val

	@validator('undirflokkur')
	def should_be_set(cls, val, values, **kwargs):
		if val is None:
			raise ValueError('undirflokkur should be set')
		elif val is not Smaordaflokkar.Forsetning:
			raise ValueError('undirflokkur should be forsetning')
		return val

	@model_serializer(mode='wrap')
	def serialize(self, handler) -> dict[str, Any]:
		data_dict = handler(self)
		data = dict()
		key_order = [
			'orð', 'flokkur', 'undirflokkur', 'tölugildi', 'merking', 'samsett', 'stýrir',
			'ósjálfstætt', 'óbeygjanlegt', 'kennistrengur', 'datahash'
		]
		key_map = {'datahash': 'hash'}
		keys_values = ('flokkur', 'undirflokkur')
		keys_only_if_true = ('ósjálfstætt', 'óbeygjanlegt')
		for key in key_order:
			if data_dict[key] is not None:
				if key in keys_values:
					data[key] = data_dict[key].value
				elif key in key_map:
					data[key_map[key]] = data_dict[key]
				elif key in keys_only_if_true:
					if data_dict[key] is True:
						data[key] = data_dict[key]
				else:
					data[key] = data_dict[key]
		return data


class AtviksordData(OrdData):
	miðstig: Optional[NonEmptyStr] = None
	efstastig: Optional[NonEmptyStr] = None

	@validator('flokkur')
	def should_be_smaord(cls, val, values, **kwargs):
		if val is not Ordflokkar.Smaord:
			raise ValueError('flokkur should be smáorð')
		return val

	@validator('undirflokkur')
	def should_be_set(cls, val, values, **kwargs):
		if val is None:
			raise ValueError('undirflokkur should be set')
		elif val is not Smaordaflokkar.Atviksord:
			raise ValueError('undirflokkur should be atviksorð')
		return val

	@model_serializer(mode='wrap')
	def serialize(self, handler) -> dict[str, Any]:
		data_dict = handler(self)
		data = dict()
		key_order = [
			'orð', 'flokkur', 'undirflokkur', 'tölugildi', 'merking', 'samsett', 'miðstig',
			'efstastig', 'ósjálfstætt', 'óbeygjanlegt', 'kennistrengur', 'datahash'
		]
		key_map = {'datahash': 'hash'}
		keys_values = ('flokkur', 'undirflokkur')
		keys_only_if_true = ('ósjálfstætt', 'óbeygjanlegt')
		for key in key_order:
			if data_dict[key] is not None:
				if key in keys_values:
					data[key] = data_dict[key].value
				elif key in key_map:
					data[key_map[key]] = data_dict[key]
				elif key in keys_only_if_true:
					if data_dict[key] is True:
						data[key] = data_dict[key]
				else:
					data[key] = data_dict[key]
		return data


class NafnhattarmerkiData(OrdData):

	@validator('flokkur')
	def should_be_smaord(cls, val, values, **kwargs):
		if val is not Ordflokkar.Smaord:
			raise ValueError('flokkur should be smáorð')
		return val

	@validator('undirflokkur')
	def should_be_set(cls, val, values, **kwargs):
		if val is None:
			raise ValueError('undirflokkur should be set')
		elif val is not Smaordaflokkar.Nafnhattarmerki:
			raise ValueError('undirflokkur should be nafnháttarmerki')
		return val

	@model_serializer(mode='wrap')
	def serialize(self, handler) -> dict[str, Any]:
		data_dict = handler(self)
		data = dict()
		key_order = [
			'orð', 'flokkur', 'undirflokkur', 'tölugildi', 'merking', 'samsett', 'ósjálfstætt',
			'óbeygjanlegt', 'kennistrengur', 'datahash'
		]
		key_map = {'datahash': 'hash'}
		keys_values = ('flokkur', 'undirflokkur')
		keys_only_if_true = ('ósjálfstætt', 'óbeygjanlegt')
		for key in key_order:
			if data_dict[key] is not None:
				if key in keys_values:
					data[key] = data_dict[key].value
				elif key in key_map:
					data[key_map[key]] = data_dict[key]
				elif key in keys_only_if_true:
					if data_dict[key] is True:
						data[key] = data_dict[key]
				else:
					data[key] = data_dict[key]
		return data


class SamtengingFleiryrt(BaseModel):
	týpa: FleiryrtTypa
	fylgiorð: conlist(NonEmptyStr, min_length=1, max_length=5)


class SamtengingData(OrdData):
	fleiryrt: Optional[conlist(SamtengingFleiryrt, min_length=1, max_length=5)] = None

	@validator('flokkur')
	def should_be_smaord(cls, val, values, **kwargs):
		if val is not Ordflokkar.Smaord:
			raise ValueError('flokkur should be smáorð')
		return val

	@validator('undirflokkur')
	def should_be_set(cls, val, values, **kwargs):
		if val is None:
			raise ValueError('undirflokkur should be set')
		elif val is not Smaordaflokkar.Samtenging:
			raise ValueError('undirflokkur should be samtenging')
		return val

	@model_serializer(mode='wrap')
	def serialize(self, handler) -> dict[str, Any]:
		data_dict = handler(self)
		data = dict()
		key_order = [
			'orð', 'flokkur', 'undirflokkur', 'tölugildi', 'merking', 'samsett', 'fleiryrt',
			'ósjálfstætt', 'óbeygjanlegt', 'kennistrengur', 'datahash'
		]
		key_map = {'datahash': 'hash'}
		keys_values = ('flokkur', 'undirflokkur')
		keys_only_if_true = ('ósjálfstætt', 'óbeygjanlegt')
		for key in key_order:
			if data_dict[key] is not None:
				if key in keys_values:
					data[key] = data_dict[key].value
				elif key in key_map:
					data[key_map[key]] = data_dict[key]
				elif key in keys_only_if_true:
					if data_dict[key] is True:
						data[key] = data_dict[key]
				else:
					data[key] = data_dict[key]
		return data


class UpphropunData(OrdData):

	@validator('flokkur')
	def should_be_smaord(cls, val, values, **kwargs):
		if val is not Ordflokkar.Smaord:
			raise ValueError('flokkur should be smáorð')
		return val

	@validator('undirflokkur')
	def should_be_set(cls, val, values, **kwargs):
		if val is None:
			raise ValueError('undirflokkur should be set')
		elif val is not Smaordaflokkar.Upphropun:
			raise ValueError('undirflokkur should be upphrópun')
		return val

	@model_serializer(mode='wrap')
	def serialize(self, handler) -> dict[str, Any]:
		data_dict = handler(self)
		data = dict()
		key_order = [
			'orð', 'flokkur', 'undirflokkur', 'tölugildi', 'merking', 'samsett', 'ósjálfstætt',
			'óbeygjanlegt', 'kennistrengur', 'datahash'
		]
		key_map = {'datahash': 'hash'}
		keys_values = ('flokkur', 'undirflokkur')
		keys_only_if_true = ('ósjálfstætt', 'óbeygjanlegt')
		for key in key_order:
			if data_dict[key] is not None:
				if key in keys_values:
					data[key] = data_dict[key].value
				elif key in key_map:
					data[key_map[key]] = data_dict[key]
				elif key in keys_only_if_true:
					if data_dict[key] is True:
						data[key] = data_dict[key]
				else:
					data[key] = data_dict[key]
		return data


class SernafnBeygingarAgMgSet(BaseModel):
	ág: Optional[conlist(NonEmptyStr, min_length=4, max_length=4)] = None
	mg: Optional[conlist(NonEmptyStr, min_length=4, max_length=4)] = None

	@validator('mg')
	def mg_constraint(cls, val, values, **kwargs):
		if val is None and ('ág' not in values or values['ág'] is None):
			raise ValueError('either ág or mg must be set')
		return val

	@model_serializer(mode='wrap')
	def serialize(self, handler) -> dict[str, Any]:
		data_dict = handler(self)
		data = dict()
		if 'ág' in data_dict and data_dict['ág'] is not None:
			data['ág'] = data_dict['ág']
		if 'mg' in data_dict and data_dict['mg'] is not None:
			data['mg'] = data_dict['mg']
		return data


class SernafnData(OrdData):
	kyn: Optional[Kyn] = None
	et: Optional[SernafnBeygingarAgMgSet] = None
	ft: Optional[SernafnBeygingarAgMgSet] = None

	@validator('flokkur')
	def should_be_sernafn(cls, val, values, **kwargs):
		if val is not Ordflokkar.Sernafn:
			raise ValueError('flokkur should be sérnafn')
		return val

	@validator('undirflokkur')
	def should_be_set(cls, val, values, **kwargs):
		if val is None:
			raise ValueError('undirflokkur should be set')
		elif not isinstance(val, Sernafnaflokkar):
			raise ValueError('undirflokkur should be sérnafn undirflokkur')
		return val

	@validator('kyn')
	def kyn_constraint(cls, val, values, **kwargs):
		"""should be set for all sérnöfn except miłlinöfn"""
		if val is None:
			if values['undirflokkur'] is not Sernafnaflokkar.Millinafn:
				raise ValueError('sérnafn should have kyn set when not miłlinafn')
		elif values['undirflokkur'] is Sernafnaflokkar.Millinafn:
			raise ValueError('miłlinafn should not have kyn')
		return val

	@model_serializer(mode='wrap')
	def serialize(self, handler) -> dict[str, Any]:
		data_dict = handler(self)
		data = dict()
		key_order = [
			'orð', 'flokkur', 'undirflokkur', 'kyn', 'tölugildi', 'merking', 'samsett', 'et', 'ft',
			'ósjálfstætt', 'kennistrengur', 'datahash'
		]
		key_map = {'datahash': 'hash'}
		keys_values = ('flokkur', 'undirflokkur', 'kyn')
		keys_only_if_true = ('ósjálfstætt', 'óbeygjanlegt')
		for key in key_order:
			if data_dict[key] is not None:
				if key in keys_values:
					data[key] = data_dict[key].value
				elif key in key_map:
					data[key_map[key]] = data_dict[key]
				elif key in keys_only_if_true:
					if data_dict[key] is True:
						data[key] = data_dict[key]
				else:
					data[key] = data_dict[key]
		return data


class SkammstofunData(BaseModel):
	skammstöfun: NonEmptyStr
	merking: Optional[NonEmptyStr] = None
	frasi: conlist(NonEmptyStr, min_length=1)
	myndir: conlist(NonEmptyStr, min_length=1)
	datahash: Optional[NonEmptyStr] = Field(default=None, alias='hash')
	kennistrengur: Optional[NonEmptyStr] = None

	@model_serializer(mode='wrap')
	def serialize(self, handler) -> dict[str, Any]:
		data_dict = handler(self)
		data = dict()
		key_order = [
			'skammstöfun', 'merking', 'frasi', 'myndir', 'kennistrengur', 'datahash'
		]
		key_map = {'datahash': 'hash'}
		for key in key_order:
			if data_dict[key] is not None:
				if key in key_map:
					data[key_map[key]] = data_dict[key]
				else:
					data[key] = data_dict[key]
		return data
