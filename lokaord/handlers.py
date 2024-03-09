#!/usr/bin/python
"""
Handler classes for import/export functionality.

Importing data from files to SQL database, and exporting data from SQL database to files.
"""
import copy
import datetime
from decimal import Decimal
import hashlib
import json
import os
import pathlib
import random
import re
import string
import traceback
import types
import typing
from typing import Optional

import pydantic

from lokaord import logman
from lokaord.database import db
from lokaord.database.models import isl
from lokaord.exc import VoidKennistrengurError
from lokaord import structs
from lokaord.structs import NafnordaBeygingar, LysingarordaBeygingar, SagnordaBeygingar


class Ord:
	"""
	Orð class for deriving into icelandic word groups.
	Holds data structure and logic shared by all icelandic words.
	"""

	loaded_from_file: bool = None
	loaded_from_db: bool = None

	group: structs.Ordflokkar = None
	data: Optional[structs.OrdData] = None

	datafiles_dir = os.path.abspath(
		os.path.join(os.path.dirname(os.path.realpath(__file__)), 'database', 'data')
	)

	def __init__(self, loaded_from_file: bool = None, loaded_from_db: bool = None):
		self.loaded_from_file = loaded_from_file
		self.loaded_from_db = loaded_from_db

	def make_filename(self):
		raise Exception('Implement me in derived class.')

	def make_kennistrengur(self):
		raise Exception('Implement me in derived class.')

	def write_to_db(self) -> tuple[isl.Ord, bool]:
		"""
		adds word record if missing, else update existing record
		returns tuple containing isl.Ord and boolean true if database changes were made, else false
		"""
		changes_made = False
		isl_ord = db.Session.query(isl.Ord).filter_by(Kennistrengur=self.data.kennistrengur).first()
		if isl_ord is None:
			if self.data.samsett is not None:
				for ohl in self.data.samsett:
					isl_ord_oh = (
						db.Session.query(isl.Ord).filter_by(Kennistrengur=ohl.kennistrengur).first()
					)
					if isl_ord_oh is None:
						raise VoidKennistrengurError(
							f'Orðhluti with kennistrengur "{ohl.kennistrengur}" not found. (1)'
						)
			isl_ord = isl.Ord()
			db.Session.add(isl_ord)
			changes_made = True
		isl_ord.Ord = self.data.orð
		ordflokkur_name = self.group.name
		if self.group in (structs.Ordflokkar.Toluord, structs.Ordflokkar.Smaord):
			ordflokkur_name = self.data.undirflokkur.name
		isl_ord.Ordflokkur = isl.Ordflokkar[ordflokkur_name]
		isl_ord.Samsett = (self.data.samsett is not None)
		isl_ord.Tolugildi = self.data.tölugildi
		isl_ord.OsjalfstaedurOrdhluti = bool(self.data.ósjálfstætt)
		isl_ord.Obeygjanlegt = bool(self.data.óbeygjanlegt)
		isl_ord.Merking = self.data.merking
		isl_ord.Kennistrengur = self.data.kennistrengur
		changes_made = changes_made or db.Session.is_modified(isl_ord)
		db.Session.commit()
		if isl_ord.Samsett is True:  # add samsett data to database
			isl_samsett = db.Session.query(isl.SamsettOrd).filter_by(
				fk_Ord_id=isl_ord.Ord_id
			).first()
			if isl_samsett is None:
				isl_samsett = isl.SamsettOrd(fk_Ord_id=isl_ord.Ord_id)
				db.Session.add(isl_samsett)
				db.Session.commit()
				changes_made = True
			last_ordhluti_id = None
			for ohl in reversed(self.data.samsett):
				isl_ord_oh = (
					db.Session.query(isl.Ord).filter_by(Kennistrengur=ohl.kennistrengur).first()
				)
				if isl_ord_oh is None:
					raise VoidKennistrengurError(
						f'Orðhluti with kennistrengur "{ohl.kennistrengur}" not found. (2)'
					)
				samsetning = None
				lo_myndir = None
				# ---------------------------------------------------------------------------------
				# write beygingar config to database
				# nafnorð/sérnöfn base beygingar
				exclude_et_ag = False
				exclude_et_mg = False
				exclude_ft_ag = False
				exclude_ft_mg = False
				# lýsingarorð base beygingar
				exclude_frumstig_sb_et = False
				exclude_frumstig_sb_ft = False
				exclude_frumstig_vb_et = False
				exclude_frumstig_vb_ft = False
				exclude_midstig_vb_et = False
				exclude_midstig_vb_ft = False
				exclude_efstastig_sb_et = False
				exclude_efstastig_sb_ft = False
				exclude_efstastig_vb_et = False
				exclude_efstastig_vb_ft = False
				# sagnorð base beygingar
				exclude_germynd_personuleg = False
				exclude_germynd_opersonuleg = False
				exclude_germynd_spurnarmyndir = False
				exclude_midmynd_personuleg = False
				exclude_midmynd_opersonuleg = False
				exclude_midmynd_spurnarmyndir = False
				exclude_lysingarhattur_nutidar = False
				exclude_lysingarhattur_thatidar = False
				#
				if ohl.samsetning is not None:
					samsetning = isl.Ordasamsetningar[ohl.samsetning.name]
				if ohl.myndir is not None:
					lo_myndir = isl.LysingarordMyndir[ohl.myndir.name]
				if ohl.beygingar is not None:
					# in pydantic model we check based on orðflokkur if appropriate beygingar are
					# declared based on orðflokkur, so we should only get here with with
					# appropriate beygingar for given orðflokkur
					#
					# nafnorð/sérnöfn
					exclude_et_ag = (
						NafnordaBeygingar.Et not in ohl.beygingar and
						NafnordaBeygingar.Et_ag not in ohl.beygingar
					)
					exclude_et_mg = (
						NafnordaBeygingar.Et not in ohl.beygingar and
						NafnordaBeygingar.Et_mg not in ohl.beygingar
					)
					exclude_ft_ag = (
						NafnordaBeygingar.Ft not in ohl.beygingar and
						NafnordaBeygingar.Ft_ag not in ohl.beygingar
					)
					exclude_ft_mg = (
						NafnordaBeygingar.Ft not in ohl.beygingar and
						NafnordaBeygingar.Ft_mg not in ohl.beygingar
					)
					# lýsingarorð
					exclude_frumstig_sb_et = (
						LysingarordaBeygingar.Frumstig not in ohl.beygingar and
						LysingarordaBeygingar.Frumstig_sb not in ohl.beygingar and
						LysingarordaBeygingar.Frumstig_sb_et not in ohl.beygingar
					)
					exclude_frumstig_sb_ft = (
						LysingarordaBeygingar.Frumstig not in ohl.beygingar and
						LysingarordaBeygingar.Frumstig_sb not in ohl.beygingar and
						LysingarordaBeygingar.Frumstig_sb_ft not in ohl.beygingar
					)
					exclude_frumstig_vb_et = (
						LysingarordaBeygingar.Frumstig not in ohl.beygingar and
						LysingarordaBeygingar.Frumstig_vb not in ohl.beygingar and
						LysingarordaBeygingar.Frumstig_vb_et not in ohl.beygingar
					)
					exclude_frumstig_vb_ft = (
						LysingarordaBeygingar.Frumstig not in ohl.beygingar and
						LysingarordaBeygingar.Frumstig_vb not in ohl.beygingar and
						LysingarordaBeygingar.Frumstig_vb_ft not in ohl.beygingar
					)
					exclude_midstig_vb_et = (
						LysingarordaBeygingar.Midstig not in ohl.beygingar and
						LysingarordaBeygingar.Midstig_vb_et not in ohl.beygingar
					)
					exclude_midstig_vb_ft = (
						LysingarordaBeygingar.Midstig not in ohl.beygingar and
						LysingarordaBeygingar.Midstig_vb_ft not in ohl.beygingar
					)
					exclude_efstastig_sb_et = (
						LysingarordaBeygingar.Efstastig not in ohl.beygingar and
						LysingarordaBeygingar.Efstastig_sb not in ohl.beygingar and
						LysingarordaBeygingar.Efstastig_sb_et not in ohl.beygingar
					)
					exclude_efstastig_sb_ft = (
						LysingarordaBeygingar.Efstastig not in ohl.beygingar and
						LysingarordaBeygingar.Efstastig_sb not in ohl.beygingar and
						LysingarordaBeygingar.Efstastig_sb_ft not in ohl.beygingar
					)
					exclude_efstastig_vb_et = (
						LysingarordaBeygingar.Efstastig not in ohl.beygingar and
						LysingarordaBeygingar.Efstastig_vb not in ohl.beygingar and
						LysingarordaBeygingar.Efstastig_vb_et not in ohl.beygingar
					)
					exclude_efstastig_vb_ft = (
						LysingarordaBeygingar.Efstastig not in ohl.beygingar and
						LysingarordaBeygingar.Efstastig_vb not in ohl.beygingar and
						LysingarordaBeygingar.Efstastig_vb_ft not in ohl.beygingar
					)
					# sagnorð
					exclude_germynd_personuleg = (
						SagnordaBeygingar.Germynd not in ohl.beygingar and
						SagnordaBeygingar.Germynd_personuleg not in ohl.beygingar
					)
					exclude_germynd_opersonuleg = (
						SagnordaBeygingar.Germynd not in ohl.beygingar and
						SagnordaBeygingar.Germynd_opersonuleg not in ohl.beygingar
					)
					exclude_germynd_spurnarmyndir = (
						SagnordaBeygingar.Germynd not in ohl.beygingar and
						SagnordaBeygingar.Germynd_spurnarmyndir not in ohl.beygingar
					)
					exclude_midmynd_personuleg = (
						SagnordaBeygingar.Midmynd not in ohl.beygingar and
						SagnordaBeygingar.Midmynd_personuleg not in ohl.beygingar
					)
					exclude_midmynd_opersonuleg = (
						SagnordaBeygingar.Midmynd not in ohl.beygingar and
						SagnordaBeygingar.Midmynd_opersonuleg not in ohl.beygingar
					)
					exclude_midmynd_spurnarmyndir = (
						SagnordaBeygingar.Midmynd not in ohl.beygingar and
						SagnordaBeygingar.Midmynd_spurnarmyndir not in ohl.beygingar
					)
					exclude_lysingarhattur_nutidar = (
						SagnordaBeygingar.Lysingarhattur not in ohl.beygingar and
						SagnordaBeygingar.Lysingarhattur_nutidar not in ohl.beygingar
					)
					exclude_lysingarhattur_thatidar = (
						SagnordaBeygingar.Lysingarhattur not in ohl.beygingar and
						SagnordaBeygingar.Lysingarhattur_thatidar not in ohl.beygingar
					)
				# ---------------------------------------------------------------------------------
				isl_ordhluti_data = {
					'fk_Ord_id': isl_ord_oh.Ord_id,
					'Ordmynd': ohl.mynd,
					'Gerd': samsetning,
					'LysingarordMyndir': lo_myndir,
					'fk_NaestiOrdhluti_id': last_ordhluti_id,
					'Lagstafa': ohl.lágstafa,
					'Hastafa': ohl.hástafa,
					'Leidir': ohl.leiðir,
					'Fylgir': ohl.fylgir,
					# nafnorð/sérnöfn beygingar excluders
					'Exclude_et_ag': exclude_et_ag,
					'Exclude_et_mg': exclude_et_mg,
					'Exclude_ft_ag': exclude_ft_ag,
					'Exclude_ft_mg': exclude_ft_mg,
					# lýsingarorð beygingar excluders
					'Exclude_frumstig_sb_et': exclude_frumstig_sb_et,
					'Exclude_frumstig_sb_ft': exclude_frumstig_sb_ft,
					'Exclude_frumstig_vb_et': exclude_frumstig_vb_et,
					'Exclude_frumstig_vb_ft': exclude_frumstig_vb_ft,
					'Exclude_midstig_vb_et': exclude_midstig_vb_et,
					'Exclude_midstig_vb_ft': exclude_midstig_vb_ft,
					'Exclude_efstastig_sb_et': exclude_efstastig_sb_et,
					'Exclude_efstastig_sb_ft': exclude_efstastig_sb_ft,
					'Exclude_efstastig_vb_et': exclude_efstastig_vb_et,
					'Exclude_efstastig_vb_ft': exclude_efstastig_vb_ft,
					# sagnorð beygingar excluders
					'Exclude_germynd_personuleg': exclude_germynd_personuleg,
					'Exclude_germynd_opersonuleg': exclude_germynd_opersonuleg,
					'Exclude_germynd_spurnarmyndir': exclude_germynd_spurnarmyndir,
					'Exclude_midmynd_personuleg': exclude_midmynd_personuleg,
					'Exclude_midmynd_opersonuleg': exclude_midmynd_opersonuleg,
					'Exclude_midmynd_spurnarmyndir': exclude_midmynd_spurnarmyndir,
					'Exclude_lysingarhattur_nutidar': exclude_lysingarhattur_nutidar,
					'Exclude_lysingarhattur_thatidar': exclude_lysingarhattur_thatidar,
				}
				isl_ordhluti = (
					db.Session.query(isl.SamsettOrdhluti).filter_by(**isl_ordhluti_data).first()
				)
				if isl_ordhluti is None:
					isl_ordhluti = isl.SamsettOrdhluti(**isl_ordhluti_data)
					db.Session.add(isl_ordhluti)
					db.Session.commit()
					changes_made = True
				last_ordhluti_id = isl_ordhluti.SamsettOrdhluti_id
			if isl_samsett.fk_FyrstiOrdHluti_id != last_ordhluti_id:
				isl_samsett.fk_FyrstiOrdHluti_id = last_ordhluti_id
				db.Session.commit()
				changes_made = True
		if changes_made is True:
			isl_ord.Edited = datetime.datetime.utcnow()
			db.Session.commit()
		return (isl_ord, changes_made)

	def load_from_db(self, isl_ord: isl.Ord) -> dict:
		toluord = (isl.Ordflokkar.Fjoldatala, isl.Ordflokkar.Radtala)
		smaord = (
			isl.Ordflokkar.Forsetning, isl.Ordflokkar.Atviksord, isl.Ordflokkar.Nafnhattarmerki,
			isl.Ordflokkar.Samtenging, isl.Ordflokkar.Upphropun
		)
		if isl_ord.Ordflokkur.name in structs.Ordflokkar.__members__:
			flokkur = structs.Ordflokkar[isl_ord.Ordflokkur.name].value
			undirflokkur = None
		elif isl_ord.Ordflokkur in toluord:
			flokkur = structs.Ordflokkar.Toluord.value
			undirflokkur = structs.Toluordaflokkar[isl_ord.Ordflokkur.name].value
		elif isl_ord.Ordflokkur in smaord:
			flokkur = structs.Ordflokkar.Smaord.value
			undirflokkur = structs.Smaordaflokkar[isl_ord.Ordflokkur.name].value
		else:
			raise Exception('Should not happen.')
		ord_data = {
			'orð': isl_ord.Ord,
			'flokkur': flokkur,
			'undirflokkur': undirflokkur,
			'merking': isl_ord.Merking,
			'samsett': [],
			'tölugildi': isl_ord.Tolugildi,
			'ósjálfstætt': isl_ord.OsjalfstaedurOrdhluti,
			'óbeygjanlegt': isl_ord.Obeygjanlegt,
			'kennistrengur': isl_ord.Kennistrengur,
		}
		if isl_ord.Samsett is True:
			isl_samsett = db.Session.query(isl.SamsettOrd).filter_by(
				fk_Ord_id=isl_ord.Ord_id
			).first()
			next_ordhluti_id = isl_samsett.fk_FyrstiOrdHluti_id
			while next_ordhluti_id is not None:
				isl_ord_oh = db.Session.query(isl.SamsettOrdhluti).filter_by(
					SamsettOrdhluti_id=next_ordhluti_id
				).first()
				isl_ord_oh_ord = db.Session.query(isl.Ord).filter_by(
					Ord_id=isl_ord_oh.fk_Ord_id
				).first()
				oh_data = {}
				if isl_ord_oh.Ordmynd is not None:
					oh_data['mynd'] = isl_ord_oh.Ordmynd
				if isl_ord_oh.Gerd is not None:
					oh_data['samsetning'] = structs.Ordasamsetningar[isl_ord_oh.Gerd.name]
				if isl_ord_oh.LysingarordMyndir is not None:
					oh_data['myndir'] = (
						structs.LysingarordMyndir[isl_ord_oh.LysingarordMyndir.name]
					)
				if isl_ord_oh.Lagstafa is True:
					oh_data['lágstafa'] = True
				if isl_ord_oh.Hastafa is True:
					oh_data['hástafa'] = True
				if isl_ord_oh.Leidir is not None:
					oh_data['leiðir'] = isl_ord_oh.Leidir
				if isl_ord_oh.Fylgir is not None:
					oh_data['fylgir'] = isl_ord_oh.Fylgir
				# ---------------------------------------------------------------------------------
				# load beygingar config from database and transcribe to the json form where
				# inclusivity is declared instead of exclusivity
				if (
					isl_ord_oh.Exclude_et_ag is True or  # nafnorð/sérnöfn
					isl_ord_oh.Exclude_et_mg is True or
					isl_ord_oh.Exclude_ft_ag is True or
					isl_ord_oh.Exclude_ft_mg is True or
					isl_ord_oh.Exclude_frumstig_sb_et is True or  # lýsingarorð
					isl_ord_oh.Exclude_frumstig_sb_ft is True or
					isl_ord_oh.Exclude_frumstig_vb_et is True or
					isl_ord_oh.Exclude_frumstig_vb_ft is True or
					isl_ord_oh.Exclude_midstig_vb_et is True or
					isl_ord_oh.Exclude_midstig_vb_ft is True or
					isl_ord_oh.Exclude_efstastig_sb_et is True or
					isl_ord_oh.Exclude_efstastig_sb_ft is True or
					isl_ord_oh.Exclude_efstastig_vb_et is True or
					isl_ord_oh.Exclude_efstastig_vb_ft is True or
					isl_ord_oh.Exclude_germynd_personuleg is True or  # sagnorð
					isl_ord_oh.Exclude_germynd_opersonuleg is True or
					isl_ord_oh.Exclude_germynd_spurnarmyndir is True or
					isl_ord_oh.Exclude_midmynd_personuleg is True or
					isl_ord_oh.Exclude_midmynd_opersonuleg is True or
					isl_ord_oh.Exclude_midmynd_spurnarmyndir is True or
					isl_ord_oh.Exclude_lysingarhattur_nutidar is True or
					isl_ord_oh.Exclude_lysingarhattur_thatidar is True
				):
					oh_data['beygingar'] = []
				# nafnorð/sérnöfn
				if (
					isl_ord_oh.Exclude_et_ag is True or
					isl_ord_oh.Exclude_et_mg is True or
					isl_ord_oh.Exclude_ft_ag is True or
					isl_ord_oh.Exclude_ft_mg is True
				):
					if isl_ord_oh.Exclude_et_ag is False and isl_ord_oh.Exclude_et_mg is False:
						# oh_data['beygingar'].append('et')
						oh_data['beygingar'].append(NafnordaBeygingar.Et.value)
					else:
						if isl_ord_oh.Exclude_et_ag is False:
							oh_data['beygingar'].append(NafnordaBeygingar.Et_ag.value)
						if isl_ord_oh.Exclude_et_mg is False:
							oh_data['beygingar'].append(NafnordaBeygingar.Et_mg.value)
					if isl_ord_oh.Exclude_ft_ag is False and isl_ord_oh.Exclude_ft_mg is False:
						oh_data['beygingar'].append(NafnordaBeygingar.Ft.value)
					else:
						if isl_ord_oh.Exclude_ft_ag is False:
							oh_data['beygingar'].append(NafnordaBeygingar.Ft_ag.value)
						if isl_ord_oh.Exclude_ft_mg is False:
							oh_data['beygingar'].append(NafnordaBeygingar.Ft_mg.value)
				# lýsingarorð
				if (
					isl_ord_oh.Exclude_frumstig_sb_et is True or
					isl_ord_oh.Exclude_frumstig_sb_ft is True or
					isl_ord_oh.Exclude_frumstig_vb_et is True or
					isl_ord_oh.Exclude_frumstig_vb_ft is True or
					isl_ord_oh.Exclude_midstig_vb_et is True or
					isl_ord_oh.Exclude_midstig_vb_ft is True or
					isl_ord_oh.Exclude_efstastig_sb_et is True or
					isl_ord_oh.Exclude_efstastig_sb_ft is True or
					isl_ord_oh.Exclude_efstastig_vb_et is True or
					isl_ord_oh.Exclude_efstastig_vb_ft is True
				):
					if (
						isl_ord_oh.Exclude_frumstig_sb_et is False and
						isl_ord_oh.Exclude_frumstig_sb_ft is False and
						isl_ord_oh.Exclude_frumstig_vb_et is False and
						isl_ord_oh.Exclude_frumstig_vb_ft is False
					):
						oh_data['beygingar'].append(LysingarordaBeygingar.Frumstig.value)
					else:
						if (
							isl_ord_oh.Exclude_frumstig_sb_et is False and
							isl_ord_oh.Exclude_frumstig_sb_ft is False
						):
							oh_data['beygingar'].append(LysingarordaBeygingar.Frumstig_sb.value)
						else:
							if isl_ord_oh.Exclude_frumstig_sb_et is False:
								oh_data['beygingar'].append(
									LysingarordaBeygingar.Frumstig_sb_et.value
								)
							if isl_ord_oh.Exclude_frumstig_sb_ft is False:
								oh_data['beygingar'].append(
									LysingarordaBeygingar.Frumstig_sb_ft.value
								)
						if (
							isl_ord_oh.Exclude_frumstig_vb_et is False and
							isl_ord_oh.Exclude_frumstig_vb_ft is False
						):
							oh_data['beygingar'].append(LysingarordaBeygingar.Frumstig_vb.value)
						else:
							if isl_ord_oh.Exclude_frumstig_vb_et is False:
								oh_data['beygingar'].append(
									LysingarordaBeygingar.Frumstig_vb_et.value
								)
							if isl_ord_oh.Exclude_frumstig_vb_ft is False:
								oh_data['beygingar'].append(
									LysingarordaBeygingar.Frumstig_vb_ft.value
								)
					if (
						isl_ord_oh.Exclude_midstig_vb_et is False and
						isl_ord_oh.Exclude_midstig_vb_ft is False
					):
						oh_data['beygingar'].append(LysingarordaBeygingar.Midstig.value)
					else:
						if isl_ord_oh.Exclude_midstig_vb_et is False:
							oh_data['beygingar'].append(LysingarordaBeygingar.Midstig_vb_et.value)
						if isl_ord_oh.Exclude_midstig_vb_ft is False:
							oh_data['beygingar'].append(LysingarordaBeygingar.Midstig_vb_ft.value)
					if (
						isl_ord_oh.Exclude_efstastig_sb_et is False and
						isl_ord_oh.Exclude_efstastig_sb_ft is False and
						isl_ord_oh.Exclude_efstastig_vb_et is False and
						isl_ord_oh.Exclude_efstastig_vb_ft is False
					):
						oh_data['beygingar'].append(LysingarordaBeygingar.Efstastig.value)
					else:
						if (
							isl_ord_oh.Exclude_efstastig_sb_et is False and
							isl_ord_oh.Exclude_efstastig_sb_ft is False
						):
							oh_data['beygingar'].append(LysingarordaBeygingar.Efstastig_sb.value)
						else:
							if isl_ord_oh.Exclude_efstastig_sb_et is False:
								oh_data['beygingar'].append(
									LysingarordaBeygingar.Efstastig_sb_et.value
								)
							if isl_ord_oh.Exclude_efstastig_sb_ft is False:
								oh_data['beygingar'].append(
									LysingarordaBeygingar.Efstastig_sb_ft.value
								)
						if (
							isl_ord_oh.Exclude_efstastig_vb_et is False and
							isl_ord_oh.Exclude_efstastig_vb_ft is False
						):
							oh_data['beygingar'].append(LysingarordaBeygingar.Efstastig_vb.value)
						else:
							if isl_ord_oh.Exclude_efstastig_vb_et is False:
								oh_data['beygingar'].append(
									LysingarordaBeygingar.Efstastig_vb_et.value
								)
							if isl_ord_oh.Exclude_efstastig_vb_ft is False:
								oh_data['beygingar'].append(
									LysingarordaBeygingar.Efstastig_vb_ft.value
								)
				# sagnorð
				if (
					isl_ord_oh.Exclude_germynd_personuleg is True or
					isl_ord_oh.Exclude_germynd_opersonuleg is True or
					isl_ord_oh.Exclude_germynd_spurnarmyndir is True or
					isl_ord_oh.Exclude_midmynd_personuleg is True or
					isl_ord_oh.Exclude_midmynd_opersonuleg is True or
					isl_ord_oh.Exclude_midmynd_spurnarmyndir is True or
					isl_ord_oh.Exclude_lysingarhattur_nutidar is True or
					isl_ord_oh.Exclude_lysingarhattur_thatidar is True
				):
					if (
						isl_ord_oh.Exclude_germynd_personuleg is False and
						isl_ord_oh.Exclude_germynd_opersonuleg is False and
						isl_ord_oh.Exclude_germynd_spurnarmyndir is False
					):
						oh_data['beygingar'].append(SagnordaBeygingar.Germynd.value)
					else:
						if isl_ord_oh.Exclude_germynd_personuleg is False:
							oh_data['beygingar'].append(SagnordaBeygingar.Germynd_personuleg.value)
						if isl_ord_oh.Exclude_germynd_opersonuleg is False:
							oh_data['beygingar'].append(SagnordaBeygingar.Germynd_opersonuleg.value)
						if isl_ord_oh.Exclude_germynd_spurnarmyndir is False:
							oh_data['beygingar'].append(
								SagnordaBeygingar.Germynd_spurnarmyndir.value
							)
					if (
						isl_ord_oh.Exclude_midmynd_personuleg is False and
						isl_ord_oh.Exclude_midmynd_opersonuleg is False and
						isl_ord_oh.Exclude_midmynd_spurnarmyndir is False
					):
						oh_data['beygingar'].append(SagnordaBeygingar.Midmynd.value)
					else:
						if isl_ord_oh.Exclude_midmynd_personuleg is False:
							oh_data['beygingar'].append(SagnordaBeygingar.Midmynd_personuleg.value)
						if isl_ord_oh.Exclude_midmynd_opersonuleg is False:
							oh_data['beygingar'].append(SagnordaBeygingar.Midmynd_opersonuleg.value)
						if isl_ord_oh.Exclude_midmynd_spurnarmyndir is False:
							oh_data['beygingar'].append(
								SagnordaBeygingar.Midmynd_spurnarmyndir.value
							)
					if (
						isl_ord_oh.Exclude_lysingarhattur_nutidar is False and
						isl_ord_oh.Exclude_lysingarhattur_thatidar is False
					):
						oh_data['beygingar'].append(SagnordaBeygingar.Lysingarhattur.value)
					else:
						if isl_ord_oh.Exclude_lysingarhattur_nutidar is False:
							oh_data['beygingar'].append(
								SagnordaBeygingar.Lysingarhattur_nutidar.value
							)
						if isl_ord_oh.Exclude_lysingarhattur_thatidar is False:
							oh_data['beygingar'].append(
								SagnordaBeygingar.Lysingarhattur_thatidar.value
							)
				# ---------------------------------------------------------------------------------
				oh_data['kennistrengur'] = isl_ord_oh_ord.Kennistrengur
				ord_data['samsett'].append(oh_data)
				next_ordhluti_id = isl_ord_oh.fk_NaestiOrdhluti_id
		else:
			del ord_data['samsett']
		return ord_data

	@classmethod
	def get_files_list_sorted(cls, override_dir_rel: str = None) -> tuple[list[str], list[str]]:
		"""
		Get lists of files for the orðflokkur.

		Usage:  kjo, sao = Ord.get_files_list_sorted(override_dir_rel)
		Before: @override_dir_rel is optional, to override which relative directory within the
				"lokaord/database/data" directory to list files in
		After:  @kjo and @sao are lists of strings containing relative location of json files in
				Orð group folder, @kjo containing json files without the key "samsett" and @sao
				containing json files that have the key "samsett".
		"""
		if override_dir_rel is not None:
			files_directory_rel = override_dir_rel
		else:
			files_directory_rel = cls.group.get_folder()
		files_directory = os.path.join(cls.datafiles_dir, files_directory_rel)
		json_files_path = sorted(pathlib.Path(files_directory).iterdir())
		json_files_rel = []
		for json_file_path in json_files_path:
			if not json_file_path.is_file():
				continue
			if not json_file_path.name.endswith('.json'):
				continue
			json_file_rel = os.path.join(files_directory_rel, json_file_path.name)
			json_files_rel.append(json_file_rel)
		return cls.sort_files_to_kjarna_and_samsett_ord(json_files_rel)

	@classmethod
	def sort_files_to_kjarna_and_samsett_ord(cls, files: list[str]) -> tuple[list[str], list[str]]:
		"""
		Sort list of files to kjarnaorð and samsett orð.

		Usage:  kjo, sao = Ord.sort_files_to_kjarna_and_samsett_ord(files)
		Before: @files is a list of strings containing relative location of json files (relative to
				the directory "lokaord/database/data")
		After:  @kjo and @sao are lists of strings containing relative location of json files in
				Orð group folder, @kjo containing json files without the key "samsett" and @sao
				containing json files that have the key "samsett".
		"""
		kjarna_ord_files_list = []
		samsett_ord_files_list = []
		for json_file_rel in files:
			json_file_abs = os.path.join(cls.datafiles_dir, json_file_rel)
			json_file_path = pathlib.Path(json_file_abs)
			if not json_file_path.is_file():
				continue
			if not json_file_path.name.endswith('.json'):
				continue
			json_data = None
			try:
				with json_file_path.open(mode='r', encoding='utf-8') as fi:
					json_data = json.loads(fi.read())
			except json.decoder.JSONDecodeError:
				raise Exception(f'File "{json_file_path.name}" has invalid JSON format.')
			if 'samsett' in json_data:
				samsett_ord_files_list.append(json_file_rel)
				continue
			kjarna_ord_files_list.append(json_file_rel)
		kjarna_ord_files_list.sort()
		samsett_ord_files_list.sort()
		return (kjarna_ord_files_list, samsett_ord_files_list)

	@classmethod
	def sort_files_skammstafanir_from_ord(cls, files: list[str]) -> tuple[list[str], list[str]]:
		"""
		Like sort_files_to_kjarna_and_samsett_ord, but to sort out skammstafanir files.

		Usage:  ord_files, skammstafanir_files = Ord.sort_files_skammstafanir_from_ord(files)
		Before: @files is a list of strings containing relative location of json files (relative to
				the directory "lokaord/database/data")
		After:  @ord_files and @skammstafanir_files are lists of strings containing relative
				location of json files in "lokaord/database/data" directory,
				@ord_files containing json files without the key "skammstöfun" and
				@skammstafanir_files containing json files that have the key "skammstöfun".
		"""
		ord_files = []
		skammstafanir_files = []
		for json_file_rel in files:
			json_file_abs = os.path.join(cls.datafiles_dir, json_file_rel)
			json_file_path = pathlib.Path(json_file_abs)
			if not json_file_path.is_file():
				continue
			if not json_file_path.name.endswith('.json'):
				continue
			json_data = None
			try:
				with json_file_path.open(mode='r', encoding='utf-8') as fi:
					json_data = json.loads(fi.read())
			except json.decoder.JSONDecodeError:
				raise Exception(f'File "{json_file_path.name}" has invalid JSON format.')
			if 'skammstöfun' in json_data:
				skammstafanir_files.append(json_file_rel)
				continue
			ord_files.append(json_file_rel)
		ord_files.sort()
		skammstafanir_files.sort()
		return (ord_files, skammstafanir_files)

	@classmethod
	def load_json(cls, filename):
		with open(os.path.join(cls.datafiles_dir, filename), mode='r', encoding='utf-8') as fi:
			return json.loads(fi.read(), parse_float=Decimal)

	def load_from_file(self, filename):
		"""
		Usage:  isl_ord.load_from_file(filename)
		Before: @isl_ord is an instance of a derived class of Ord
				@filename is relative path to file containing data on a given word, it should be
				relative from the path location "lokaord/database/data", filename example:
				"nafnord/hestur-kk.json"
		After:  data has been loaded to isl_ord.data
		"""
		self.filename = filename
		self.loaded_from_file = True
		filepath_abs = os.path.join(self.datafiles_dir, filename)
		data = self.load_json(filepath_abs)
		merking = self.detect_merking_in_filename(os.path.basename(filename))
		if merking is not None and 'merking' not in data:
			data['merking'] = merking
		tracebacks = []
		for struct in list(typing.get_args(self.__annotations__['data'])):
			if struct is types.NoneType:
				continue
			try:
				self.data = struct(**data)
				break
			except pydantic.ValidationError:
				tracebacks.append(traceback.format_exc())
		if self.data is None:
			tracebacks_str = ''.join(tracebacks)
			raise ValueError((
				f'◈◈◈\n{tracebacks_str}Data didn\'t fit into any of the annotated structs.\n'
				f'  (filename: {filename})'
			))
		if 'samsett' in self.data.dict() and self.data.samsett is not None:
			data_derived_beygingar = self.derive_beygingar_from_samsett(self.data.dict())
			self.data = struct(**data_derived_beygingar)
		kennistr = self.make_kennistrengur()
		datahash = self.get_data_hash()
		if self.data.kennistrengur != kennistr:
			logman.debug(f'kennistrengur update: {self.data.kennistrengur} -> {kennistr}')
			self.data.kennistrengur = kennistr
		if self.data.datahash != datahash:
			logman.debug(f'datahash update: {self.data.datahash} -> {datahash}')
			self.data.datahash = datahash

	def write_to_file(self, filename: str = None):
		"""
		before writing to file we check if the file exists and if its contents are the same as what
		we would be writing to it
		"""
		if filename is None:
			filename = self.make_filename()
		filename_abs = os.path.join(self.datafiles_dir, filename)
		ord_data_json_str = self._ord_data_to_fancy_json_str(self.data.dict())
		current_str = None
		if os.path.isfile(filename_abs):
			with open(filename_abs, mode='r', encoding='utf-8') as fi:
				current_str = fi.read()
			if ord_data_json_str == current_str:
				return  # content of file is the same so writing to file is not needed
		else:
			logman.warning(f'Writing orð to a new file "{filename}".')  # usually human error
		with open(filename_abs, mode='w', encoding='utf-8') as fo:
			fo.write(ord_data_json_str)

	def _ord_data_to_fancy_json_str(self, data):
		return json.dumps(
			data, indent='\t', ensure_ascii=False, separators=(',', ': '), cls=MyIndentJSONEncoder
		)

	def get_data_hash(self):
		"""
		create hash from orð data
		"""
		data = self.data.dict()
		if 'hash' in data:
			del data['hash']
		if 'kennistrengur' in data:
			del data['kennistrengur']
		return hashlib.sha256(
			json.dumps(
				data, separators=(',', ':'), ensure_ascii=False, sort_keys=True,
				cls=DecimalJSONEncoder
			).encode('utf-8')
		).hexdigest()

	def detect_merking_in_filename(self, filename):
		"""
		look for "merking" in filename, for example "lofa" in filename "heita-_lofa_.json"
		if no "merking" then return None
		"""
		match = re.search(r'_([a-zA-ZáÁðÐéÉíÍłŁóÓúÚýÝæÆöÖ]*)_', filename)
		if match is not None:
			return match.group()[1:-1]
		return None

	def _fno_extras(self):
		return '%s%s' % (
			'-ó' if self.data.ósjálfstætt is True else '',
			'-_%s_' % (self.data.merking, ) if self.data.merking is not None else ''
		)

	def write_fallbeyging_to_db(self, fallbeyging_id, fallbeyging_list, changes_made=False):
		isl_fallbeyging = None
		if fallbeyging_id is None:
			isl_fallbeyging = isl.Fallbeyging()
			db.Session.add(isl_fallbeyging)
			changes_made = True
		else:
			isl_fallbeyging = db.Session.query(isl.Fallbeyging).filter_by(
				Fallbeyging_id=fallbeyging_id
			).first()
		if isl_fallbeyging is None:
			raise Exception('Should not happen.')
		isl_fallbeyging.Nefnifall = fallbeyging_list[0]
		isl_fallbeyging.Tholfall = fallbeyging_list[1]
		isl_fallbeyging.Thagufall = fallbeyging_list[2]
		isl_fallbeyging.Eignarfall = fallbeyging_list[3]
		if db.Session.is_modified(isl_fallbeyging):
			db.Session.commit()
		changes_made = changes_made or db.Session.is_modified(isl_fallbeyging)
		return (isl_fallbeyging.Fallbeyging_id, changes_made)

	def write_sagnbeyging_to_db(self, sagnbeyging_id, sagnbeyging_obj, changes_made=False):
		isl_sb = None
		if sagnbeyging_id is None:
			isl_sb = isl.Sagnbeyging()
			db.Session.add(isl_sb)
			changes_made = True
		else:
			isl_sb = db.Session.query(isl.Sagnbeyging).filter_by(
				Sagnbeyging_id=sagnbeyging_id
			).first()
		if isl_sb is None:
			raise Exception('Should never happen.')
		if 'nútíð' in sagnbeyging_obj:
			if 'et' in sagnbeyging_obj['nútíð']:
				isl_sb.FyrstaPersona_eintala_nutid = sagnbeyging_obj['nútíð']['et'][0]
				isl_sb.OnnurPersona_eintala_nutid = sagnbeyging_obj['nútíð']['et'][1]
				isl_sb.ThridjaPersona_eintala_nutid = sagnbeyging_obj['nútíð']['et'][2]
			if 'ft' in sagnbeyging_obj['nútíð']:
				isl_sb.FyrstaPersona_fleirtala_nutid = sagnbeyging_obj['nútíð']['ft'][0]
				isl_sb.OnnurPersona_fleirtala_nutid = sagnbeyging_obj['nútíð']['ft'][1]
				isl_sb.ThridjaPersona_fleirtala_nutid = sagnbeyging_obj['nútíð']['ft'][2]
		if 'þátíð' in sagnbeyging_obj:
			if 'et' in sagnbeyging_obj['þátíð']:
				isl_sb.FyrstaPersona_eintala_thatid = sagnbeyging_obj['þátíð']['et'][0]
				isl_sb.OnnurPersona_eintala_thatid = sagnbeyging_obj['þátíð']['et'][1]
				isl_sb.ThridjaPersona_eintala_thatid = sagnbeyging_obj['þátíð']['et'][2]
			if 'ft' in sagnbeyging_obj['þátíð']:
				isl_sb.FyrstaPersona_fleirtala_thatid = sagnbeyging_obj['þátíð']['ft'][0]
				isl_sb.OnnurPersona_fleirtala_thatid = sagnbeyging_obj['þátíð']['ft'][1]
				isl_sb.ThridjaPersona_fleirtala_thatid = sagnbeyging_obj['þátíð']['ft'][2]
		if db.Session.is_modified(isl_sb):
			db.Session.commit()
		changes_made = changes_made or db.Session.is_modified(isl_sb)
		return (isl_sb.Sagnbeyging_id, changes_made)

	def load_fallbeyging_from_db(self, fallbeyging_id: int) -> list:
		isl_fallbeyging = db.Session.query(isl.Fallbeyging).filter_by(
			Fallbeyging_id=fallbeyging_id
		).first()
		if isl_fallbeyging is None:
			raise Exception(f'Fałlbeyging ({fallbeyging_id}) not found.')
		return [
			isl_fallbeyging.Nefnifall, isl_fallbeyging.Tholfall, isl_fallbeyging.Thagufall,
			isl_fallbeyging.Eignarfall
		]

	def load_sagnbeyging_from_db(self, sagnbeyging_id: int) -> list:
		isl_sb = db.Session.query(isl.Sagnbeyging).filter_by(
			Sagnbeyging_id=sagnbeyging_id
		).first()
		if isl_sb is None:
			raise Exception(f'Sagnbeyging with id={sagnbeyging_id} not found.')
		data = {}
		if (
			isl_sb.FyrstaPersona_eintala_nutid is None and
			isl_sb.OnnurPersona_eintala_nutid is None and
			isl_sb.ThridjaPersona_eintala_nutid is None and
			isl_sb.FyrstaPersona_fleirtala_nutid is None and
			isl_sb.OnnurPersona_fleirtala_nutid is None and
			isl_sb.ThridjaPersona_fleirtala_nutid is None and
			isl_sb.FyrstaPersona_eintala_thatid is None and
			isl_sb.OnnurPersona_eintala_thatid is None and
			isl_sb.ThridjaPersona_eintala_thatid is None and
			isl_sb.FyrstaPersona_fleirtala_thatid is None and
			isl_sb.OnnurPersona_fleirtala_thatid is None and
			isl_sb.ThridjaPersona_fleirtala_thatid is None
		):
			raise Exception('Empty sagnbeyging?')
		if (
			isl_sb.FyrstaPersona_eintala_nutid is not None or
			isl_sb.OnnurPersona_eintala_nutid is not None or
			isl_sb.ThridjaPersona_eintala_nutid is not None or
			isl_sb.FyrstaPersona_fleirtala_nutid is not None or
			isl_sb.OnnurPersona_fleirtala_nutid is not None or
			isl_sb.ThridjaPersona_fleirtala_nutid is not None
		):
			data['nútíð'] = {}
		if (
			isl_sb.FyrstaPersona_eintala_thatid is not None or
			isl_sb.OnnurPersona_eintala_thatid is not None or
			isl_sb.ThridjaPersona_eintala_thatid is not None or
			isl_sb.FyrstaPersona_fleirtala_thatid is not None or
			isl_sb.OnnurPersona_fleirtala_thatid is not None or
			isl_sb.ThridjaPersona_fleirtala_thatid is not None
		):
			data['þátíð'] = {}
		if (
			isl_sb.FyrstaPersona_eintala_nutid is not None or
			isl_sb.OnnurPersona_eintala_nutid is not None or
			isl_sb.ThridjaPersona_eintala_nutid is not None
		):
			data['nútíð']['et'] = [
				isl_sb.FyrstaPersona_eintala_nutid,
				isl_sb.OnnurPersona_eintala_nutid,
				isl_sb.ThridjaPersona_eintala_nutid
			]
		if (
			isl_sb.FyrstaPersona_fleirtala_nutid is not None or
			isl_sb.OnnurPersona_fleirtala_nutid is not None or
			isl_sb.ThridjaPersona_fleirtala_nutid is not None
		):
			data['nútíð']['ft'] = [
				isl_sb.FyrstaPersona_fleirtala_nutid,
				isl_sb.OnnurPersona_fleirtala_nutid,
				isl_sb.ThridjaPersona_fleirtala_nutid
			]
		if (
			isl_sb.FyrstaPersona_eintala_thatid is not None or
			isl_sb.OnnurPersona_eintala_thatid is not None or
			isl_sb.ThridjaPersona_eintala_thatid is not None
		):
			data['þátíð']['et'] = [
				isl_sb.FyrstaPersona_eintala_thatid,
				isl_sb.OnnurPersona_eintala_thatid,
				isl_sb.ThridjaPersona_eintala_thatid
			]
		if (
			isl_sb.FyrstaPersona_fleirtala_thatid is not None or
			isl_sb.OnnurPersona_fleirtala_thatid is not None or
			isl_sb.ThridjaPersona_fleirtala_thatid is not None
		):
			data['þátíð']['ft'] = [
				isl_sb.FyrstaPersona_fleirtala_thatid,
				isl_sb.OnnurPersona_fleirtala_thatid,
				isl_sb.ThridjaPersona_fleirtala_thatid
			]
		return data

	def apply_ordhluti_ch_to_ord(self, ord_str: str, ordhluti: dict) -> str:
		"""
		apply certain orðhluti rules to a provided orð
		implemented rules:
		- leiðir: string in front of orð
		- fylgir: string in back of orð
		- lágstafa: lowercase orð
		- hástafa: set capital letter to first character of orð
		"""
		ord_str_ch = ''
		if 'leiðir' in ordhluti:
			ord_str_ch += ordhluti['leiðir']
		if 'lágstafa' in ordhluti and ordhluti['lágstafa'] is True:
			ord_str_ch += ord_str.lower()
		elif 'hástafa' in ordhluti and ordhluti['hástafa'] is True:
			ord_str_ch += '%s%s' % (ord_str[:1].upper(), ord_str[1:])
		else:
			ord_str_ch += ord_str
		if 'fylgir' in ordhluti:
			ord_str_ch += ordhluti['fylgir']
		return ord_str_ch

	def apply_ordhluti_ch_to_dict(self, ord_dict: dict, ordhluti: dict) -> dict:
		"""
		apply certain orðhluti rules to contents in a provided dict
		"""
		dont_change_keys = set(['frumlag'])
		for key in ord_dict:
			if key in dont_change_keys:
				continue
			if isinstance(ord_dict[key], str):
				ord_dict[key] = self.apply_ordhluti_ch_to_ord(ord_dict[key], ordhluti)
			elif isinstance(ord_dict[key], list):
				for i in range(0, len(ord_dict[key])):
					if ord_dict[key][i] is None:
						continue
					elif isinstance(ord_dict[key][i], str):
						ord_dict[key][i] = (
							self.apply_ordhluti_ch_to_ord(ord_dict[key][i], ordhluti)
						)
					elif isinstance(ord_dict[key][i], dict):
						ord_dict[key][i] = (
							self.apply_ordhluti_ch_to_dict(ord_dict[key][i], ordhluti)
						)
			elif isinstance(ord_dict[key], dict):
				ord_dict[key] = self.apply_ordhluti_ch_to_dict(ord_dict[key], ordhluti)
		return ord_dict

	def apply_beygingar_filters(self, isl_ord_dict: dict, ordhluti: dict) -> dict:
		"""
		apply beygingar filtering to contents in a provided dict
		"""
		if 'beygingar' in ordhluti:
			# nafnorð/sérnöfn
			if 'et' not in ordhluti['beygingar']:
				if 'et-ág' not in ordhluti['beygingar']:
					if 'et' in isl_ord_dict and 'ág' in isl_ord_dict['et']:
						del isl_ord_dict['et']['ág']
				if 'et-mg' not in ordhluti['beygingar']:
					if 'et' in isl_ord_dict and 'mg' in isl_ord_dict['et']:
						del isl_ord_dict['et']['mg']
			if 'ft' not in ordhluti['beygingar']:
				if 'ft-ág' not in ordhluti['beygingar']:
					if 'ft' in isl_ord_dict and 'ág' in isl_ord_dict['ft']:
						del isl_ord_dict['ft']['ág']
				if 'ft-mg' not in ordhluti['beygingar']:
					if 'ft' in isl_ord_dict and 'mg' in isl_ord_dict['ft']:
						del isl_ord_dict['ft']['mg']
			if 'et' in isl_ord_dict and len(isl_ord_dict['et'].keys()) == 0:
				del isl_ord_dict['et']
			if 'ft' in isl_ord_dict and len(isl_ord_dict['ft'].keys()) == 0:
				del isl_ord_dict['ft']
			# lýsingarorð (and not "myndir" mapped)
			if 'myndir' not in ordhluti:
				if 'frumstig' not in ordhluti['beygingar']:
					if 'frumstig-sb' not in ordhluti['beygingar']:
						if 'frumstig-sb-et' not in ordhluti['beygingar']:
							if (
								'frumstig' in isl_ord_dict and
								'sb' in isl_ord_dict['frumstig'] and
								'et' in isl_ord_dict['frumstig']['sb']
							):
								del isl_ord_dict['frumstig']['sb']['et']
						if 'frumstig-sb-ft' not in ordhluti['beygingar']:
							if (
								'frumstig' in isl_ord_dict and
								'sb' in isl_ord_dict['frumstig'] and
								'ft' in isl_ord_dict['frumstig']['sb']
							):
								del isl_ord_dict['frumstig']['sb']['ft']
						if (
							'frumstig' in isl_ord_dict and
							'sb' in isl_ord_dict['frumstig'] and
							len(isl_ord_dict['frumstig']['sb']) == 0
						):
							del isl_ord_dict['frumstig']['sb']
					if 'frumstig-vb' not in ordhluti['beygingar']:
						if 'frumstig-vb-et' not in ordhluti['beygingar']:
							if (
								'frumstig' in isl_ord_dict and
								'vb' in isl_ord_dict['frumstig'] and
								'et' in isl_ord_dict['frumstig']['vb']
							):
								del isl_ord_dict['frumstig']['vb']['et']
						if 'frumstig-vb-ft' not in ordhluti['beygingar']:
							if (
								'frumstig' in isl_ord_dict and
								'vb' in isl_ord_dict['frumstig'] and
								'ft' in isl_ord_dict['frumstig']['vb']
							):
								del isl_ord_dict['frumstig']['vb']['ft']
						if (
							'frumstig' in isl_ord_dict and
							'vb' in isl_ord_dict['frumstig'] and
							len(isl_ord_dict['frumstig']['vb']) == 0
						):
							del isl_ord_dict['frumstig']['vb']
					if (
						'frumstig' in isl_ord_dict and
						len(isl_ord_dict['frumstig']) == 0
					):
						del isl_ord_dict['frumstig']
				if 'miðstig' not in ordhluti['beygingar']:
					if 'miðstig-vb-et' not in ordhluti['beygingar']:
						if (
							'miðstig' in isl_ord_dict and
							'vb' in isl_ord_dict['miðstig'] and
							'et' in isl_ord_dict['miðstig']['vb']
						):
							del isl_ord_dict['miðstig']['vb']['et']
					if 'miðstig-vb-ft' not in ordhluti['beygingar']:
						if (
							'miðstig' in isl_ord_dict and
							'vb' in isl_ord_dict['miðstig'] and
							'ft' in isl_ord_dict['miðstig']['vb']
						):
							del isl_ord_dict['miðstig']['vb']['ft']
					if (
						'miðstig' in isl_ord_dict and
						'vb' in isl_ord_dict['miðstig'] and
						len(isl_ord_dict['miðstig']['vb']) == 0
					):
						del isl_ord_dict['miðstig']['vb']
					if (
						'miðstig' in isl_ord_dict and
						len(isl_ord_dict['miðstig']) == 0
					):
						del isl_ord_dict['miðstig']
				if 'efstastig' not in ordhluti['beygingar']:
					if 'efstastig-sb' not in ordhluti['beygingar']:
						if 'efstastig-sb-et' not in ordhluti['beygingar']:
							if (
								'efstastig' in isl_ord_dict and
								'sb' in isl_ord_dict['efstastig'] and
								'et' in isl_ord_dict['efstastig']['sb']
							):
								del isl_ord_dict['efstastig']['sb']['et']
						if 'efstastig-sb-ft' not in ordhluti['beygingar']:
							if (
								'efstastig' in isl_ord_dict and
								'sb' in isl_ord_dict['efstastig'] and
								'ft' in isl_ord_dict['efstastig']['sb']
							):
								del isl_ord_dict['efstastig']['sb']['ft']
						if (
							'efstastig' in isl_ord_dict and
							'sb' in isl_ord_dict['efstastig'] and
							len(isl_ord_dict['efstastig']['sb']) == 0
						):
							del isl_ord_dict['efstastig']['sb']
					if 'efstastig-vb' not in ordhluti['beygingar']:
						if 'efstastig-vb-et' not in ordhluti['beygingar']:
							if (
								'efstastig' in isl_ord_dict and
								'vb' in isl_ord_dict['efstastig'] and
								'et' in isl_ord_dict['efstastig']['vb']
							):
								del isl_ord_dict['efstastig']['vb']['et']
						if 'efstastig-vb-ft' not in ordhluti['beygingar']:
							if (
								'efstastig' in isl_ord_dict and
								'vb' in isl_ord_dict['efstastig'] and
								'ft' in isl_ord_dict['efstastig']['vb']
							):
								del isl_ord_dict['efstastig']['vb']['ft']
						if (
							'efstastig' in isl_ord_dict and
							'vb' in isl_ord_dict['efstastig'] and
							len(isl_ord_dict['efstastig']['vb']) == 0
						):
							del isl_ord_dict['efstastig']['vb']
					if 'efstastig' in isl_ord_dict and len(isl_ord_dict['efstastig']) == 0:
						del isl_ord_dict['efstastig']
			# sagnorð
			if 'germynd' not in ordhluti['beygingar']:
				if 'germynd-persónuleg' not in ordhluti['beygingar']:
					if (
						'germynd' in isl_ord_dict and
						'persónuleg' in isl_ord_dict['germynd']
					):
						del isl_ord_dict['germynd']['persónuleg']
				if 'germynd-ópersónuleg' not in ordhluti['beygingar']:
					if (
						'germynd' in isl_ord_dict and
						'ópersónuleg' in isl_ord_dict['germynd']
					):
						del isl_ord_dict['germynd']['ópersónuleg']
				if 'germynd-spurnarmyndir' not in ordhluti['beygingar']:
					if (
						'germynd' in isl_ord_dict and
						'spurnarmyndir' in isl_ord_dict['germynd']
					):
						del isl_ord_dict['germynd']['spurnarmyndir']
				if (
					'germynd-persónuleg' not in ordhluti['beygingar'] and
					'germynd-ópersónuleg' not in ordhluti['beygingar'] and
					'germynd-spurnarmyndir' not in ordhluti['beygingar']
				):
					if 'germynd' in isl_ord_dict:
						if 'nafnháttur' in isl_ord_dict['germynd']:
							del isl_ord_dict['germynd']['nafnháttur']
						if 'sagnbót' in isl_ord_dict['germynd']:
							del isl_ord_dict['germynd']['sagnbót']
						if 'boðháttur' in isl_ord_dict['germynd']:
							del isl_ord_dict['germynd']['boðháttur']
				if 'germynd' in isl_ord_dict and len(isl_ord_dict['germynd']) == 0:
					del isl_ord_dict['germynd']
			if 'miðmynd' not in ordhluti['beygingar']:
				if 'miðmynd-persónuleg' not in ordhluti['beygingar']:
					if (
						'miðmynd' in isl_ord_dict and
						'persónuleg' in isl_ord_dict['miðmynd']
					):
						del isl_ord_dict['miðmynd']['persónuleg']
				if 'miðmynd-ópersónuleg' not in ordhluti['beygingar']:
					if (
						'miðmynd' in isl_ord_dict and
						'ópersónuleg' in isl_ord_dict['miðmynd']
					):
						del isl_ord_dict['miðmynd']['ópersónuleg']
				if 'miðmynd-spurnarmyndir' not in ordhluti['beygingar']:
					if (
						'miðmynd' in isl_ord_dict and
						'spurnarmyndir' in isl_ord_dict['miðmynd']
					):
						del isl_ord_dict['miðmynd']['spurnarmyndir']
				if (
					'miðmynd-persónuleg' not in ordhluti['beygingar'] and
					'miðmynd-ópersónuleg' not in ordhluti['beygingar'] and
					'miðmynd-spurnarmyndir' not in ordhluti['beygingar']
				):
					if 'miðmynd' in isl_ord_dict:
						if 'nafnháttur' in isl_ord_dict['miðmynd']:
							del isl_ord_dict['miðmynd']['nafnháttur']
						if 'sagnbót' in isl_ord_dict['miðmynd']:
							del isl_ord_dict['miðmynd']['sagnbót']
						if 'boðháttur' in isl_ord_dict['miðmynd']:
							del isl_ord_dict['miðmynd']['boðháttur']
				if 'miðmynd' in isl_ord_dict and len(isl_ord_dict['miðmynd']) == 0:
					del isl_ord_dict['miðmynd']
			if 'lýsingarháttur' not in ordhluti['beygingar']:
				if 'lýsingarháttur-nútíðar' not in ordhluti['beygingar']:
					if (
						'lýsingarháttur' in isl_ord_dict and
						'nútíðar' in isl_ord_dict['lýsingarháttur']
					):
						del isl_ord_dict['lýsingarháttur']['nútíðar']
				if 'lýsingarháttur-þátíðar' not in ordhluti['beygingar']:
					if (
						'lýsingarháttur' in isl_ord_dict and
						'þátíðar' in isl_ord_dict['lýsingarháttur']
					):
						del isl_ord_dict['lýsingarháttur']['þátíðar']
				if 'lýsingarháttur' in isl_ord_dict and len(isl_ord_dict['lýsingarháttur']) == 0:
					del isl_ord_dict['lýsingarháttur']
		return isl_ord_dict

	def prepend_str_to_dict(self, ord_str: str, ord_dict: dict) -> dict:
		"""
		prepend str to all appropriate values in beygingar dict
		"""
		dont_change_keys = set(['frumlag'])
		for key in ord_dict:
			if key in dont_change_keys:
				continue
			if isinstance(ord_dict[key], str):
				ord_dict[key] = '%s%s' % (ord_str, ord_dict[key])
			elif isinstance(ord_dict[key], list):
				for i in range(0, len(ord_dict[key])):
					if ord_dict[key][i] is None:
						continue
					elif isinstance(ord_dict[key][i], str):
						ord_dict[key][i] = '%s%s' % (ord_str, ord_dict[key][i])
					elif isinstance(ord_dict[key][i], dict):
						ord_dict[key][i] = self.prepend_str_to_dict(ord_str, ord_dict[key][i])
			elif isinstance(ord_dict[key], dict):
				ord_dict[key] = self.prepend_str_to_dict(ord_str, ord_dict[key])
		return ord_dict

	def merge_dict_to_dict(self, pre_dict: dict, ord_dict: dict) -> dict:
		"""
		prepend pre beygingar dict to parallel values in beygingar dict
		"""
		dont_change_keys = set(['frumlag'])
		for key in ord_dict:
			if key in dont_change_keys:
				continue
			if key not in pre_dict:
				raise Exception('Key "%s" missing from pre_dict.' % (key, ))
			if isinstance(ord_dict[key], str):
				if not isinstance(pre_dict[key], str):
					raise Exception('Key pre_dict["%s"] should be str.' % (key, ))
				ord_dict[key] = '%s%s' % (pre_dict[key], ord_dict[key])
			elif isinstance(ord_dict[key], list):
				if not isinstance(pre_dict[key], list):
					raise Exception('Key pre_dict["%s"] should be list.' % (key, ))
				for i in range(0, len(ord_dict[key])):
					if ord_dict[key][i] is None:
						continue
					elif isinstance(ord_dict[key][i], str):
						if not isinstance(pre_dict[key][i], str):
							raise Exception('Key pre_dict["%s"][%s] should be str.' % (key, i))
						ord_dict[key][i] = '%s%s' % (pre_dict[key][i], ord_dict[key][i])
					elif isinstance(ord_dict[key][i], dict):
						if not isinstance(pre_dict[key][i], dict):
							raise Exception('Key pre_dict["%s"][%s] should be dict.' % (key, i))
						ord_dict[key][i] = (
							self.merge_dict_to_dict(pre_dict[key][i], ord_dict[key][i])
						)
			elif isinstance(ord_dict[key], dict):
				if not isinstance(pre_dict[key], dict):
					raise Exception('Key pre_dict["%s"] should be dict.' % (key, ))
				ord_dict[key] = self.merge_dict_to_dict(pre_dict[key], ord_dict[key])
		return ord_dict

	def ordhluti_get_beygingar(self, ordhluti: dict) -> dict:
		"""
		Usage:  beygingar = self.ordhluti_get_beygingar(ordhluti)
		Before: @ordhluti is a dict containing mynd and samsetning type, or myndir type, and
				kennistrengur for orð.
		After:  @beygingar is a dict containing beygingar info for orð of the @orðhluti.
		"""
		isl_ord = None
		handlers_map = {}
		for handler in list_handlers():
			handlers_map[handler.group.get_abbreviation()] = handler
		# find which handler to use
		ordhluti_flokkur_abbr = ordhluti['kennistrengur'].split('-')[0].split('.')[0]
		if ordhluti_flokkur_abbr not in handlers_map:
			raise Exception('Missing handler for kennistrengur "%s".' % (
				ordhluti['kennistrengur'],
			))
		handler = handlers_map[ordhluti_flokkur_abbr]
		isl_ord = db.Session.query(isl.Ord).filter_by(
			Kennistrengur=ordhluti['kennistrengur']
		).first()
		if isl_ord is None:
			raise VoidKennistrengurError('Orð with kennistrengur "%s" not found. (3)' % (
				ordhluti['kennistrengur'],
			))
		loaded_ord = handler()
		loaded_ord.load_from_db(isl_ord)
		isl_ord_dict = loaded_ord.data.dict()
		remove_keys = [
			'orð', 'flokkur', 'undirflokkur', 'merking', 'kyn', 'tölugildi', 'samsett', 'hash',
			'kennistrengur', 'ósjálfstætt', 'stýrir', 'fleiryrt'
		]
		for key in remove_keys:
			if key in isl_ord_dict:
				del isl_ord_dict[key]
		isl_ord_dict = self.apply_beygingar_filters(isl_ord_dict, ordhluti)
		isl_ord_dict = self.apply_ordhluti_ch_to_dict(isl_ord_dict, ordhluti)
		return isl_ord_dict

	def get_lo_myndir_beygingar(self, ordhluti: dict) -> dict:
		"""
		map lýsingarorð beygingar to nafnorð-like beygingar (also sérnafn-like)
		"""
		beygingar = self.ordhluti_get_beygingar(ordhluti)
		match ordhluti['myndir']:
			case structs.LysingarordMyndir.Frumstig_vb_kk.value:
				fallbeyging_et = beygingar['frumstig']['vb']['et']['kk'].copy()
				fallbeyging_ft = beygingar['frumstig']['vb']['ft']['kk'].copy()
			case structs.LysingarordMyndir.Frumstig_vb_kvk.value:
				fallbeyging_et = beygingar['frumstig']['vb']['et']['kvk'].copy()
				fallbeyging_ft = beygingar['frumstig']['vb']['ft']['kvk'].copy()
			case structs.LysingarordMyndir.Frumstig_vb_hk:
				fallbeyging_et = beygingar['frumstig']['vb']['et']['hk'].copy()
				fallbeyging_ft = beygingar['frumstig']['vb']['ft']['hk'].copy()
			case structs.LysingarordMyndir.Midstig_vb_kk.value:
				fallbeyging_et = beygingar['miðstig']['vb']['et']['kk'].copy()
				fallbeyging_ft = beygingar['miðstig']['vb']['ft']['kk'].copy()
			case structs.LysingarordMyndir.Midstig_vb_kvk.value:
				fallbeyging_et = beygingar['miðstig']['vb']['et']['kvk'].copy()
				fallbeyging_ft = beygingar['miðstig']['vb']['ft']['kvk'].copy()
			case structs.LysingarordMyndir.Midstig_vb_hk.value:
				fallbeyging_et = beygingar['miðstig']['vb']['et']['hk'].copy()
				fallbeyging_ft = beygingar['miðstig']['vb']['ft']['hk'].copy()
			case structs.LysingarordMyndir.Efstastig_vb_kk.value:
				fallbeyging_et = beygingar['efstastig']['vb']['et']['kk'].copy()
				fallbeyging_ft = beygingar['efstastig']['vb']['ft']['kk'].copy()
			case structs.LysingarordMyndir.Efstastig_vb_kvk.value:
				fallbeyging_et = beygingar['efstastig']['vb']['et']['kvk'].copy()
				fallbeyging_ft = beygingar['efstastig']['vb']['ft']['kvk'].copy()
			case structs.LysingarordMyndir.Efstastig_vb_hk.value:
				fallbeyging_et = beygingar['efstastig']['vb']['et']['hk'].copy()
				fallbeyging_ft = beygingar['efstastig']['vb']['ft']['hk'].copy()
			case _:
				raise Exception('Unexpected ordhluti.myndir.')
		lo_myndir_beygingar = {
			'et': {'ág': fallbeyging_et, 'mg': fallbeyging_et},
			'ft': {'ág': fallbeyging_ft, 'mg': fallbeyging_ft}
		}
		return lo_myndir_beygingar

	def merge_ordhlutar(self, samsett: list[dict:]) -> dict:
		"""
		Usage:  beygingar = self.merge_ordhlutar(samsett)
		Before: @samsett is a list of dicts containging info on combination of a orð.
		After:  @beygingar is a dict containing derived beygingar for the orð.
		"""
		if 'mynd' in samsett[-1]:
			return {}
		if 'myndir' in samsett[-1]:
			beygingar = self.get_lo_myndir_beygingar(samsett[-1])
			beygingar = self.apply_beygingar_filters(beygingar, samsett[-1])
		else:
			beygingar = self.ordhluti_get_beygingar(samsett[-1])
		for ordhluti in reversed(samsett[:-1]):
			if 'mynd' in ordhluti:
				beygingar = self.prepend_str_to_dict(ordhluti['mynd'], beygingar)
			elif 'myndir' in ordhluti:
				lo_myndir_beygingar = self.get_lo_myndir_beygingar(ordhluti)
				beygingar = self.merge_dict_to_dict(lo_myndir_beygingar, beygingar)
			else:
				oh_beygingar = self.ordhluti_get_beygingar(ordhluti)
				beygingar = self.merge_dict_to_dict(oh_beygingar, beygingar)
		return beygingar

	def derive_beygingar_from_samsett(self, data: dict) -> dict:
		"""
		Usage:  derived = self.derive_beygingar_from_samsett(data)
		Before: @data is a dict containing orð data which is combined, that is, it has a samsett
				list of one or more orð).
		After:  @derived is a dict containing orð data, but has overwritten beygingar for the orð
				based on samsett data.
		"""
		non_beygingar_keys = [
			'orð', 'flokkur', 'undirflokkur', 'merking', 'kyn', 'tölugildi', 'samsett', 'hash',
			'kennistrengur', 'ósjálfstætt', 'óbeygjanlegt', 'fleiryrt', 'stýrir'
		]
		preserve_keys = ['fleiryrt', 'stýrir']
		derived = copy.deepcopy(data)
		# delete current beygingar from orð data
		for key in data:
			if key not in non_beygingar_keys:
				del derived[key]
		derived_beygingar = self.merge_ordhlutar(derived['samsett'])
		# add derived beygingar to orð data
		for key in derived_beygingar:
			if key in non_beygingar_keys:
				raise Exception('Should not happen!')
			derived[key] = derived_beygingar[key]
		for key in preserve_keys:
			if key in data:
				derived[key] = data[key]
		if data['flokkur'] == 'lýsingarorð' and 'mynd' in data['samsett'][-1]:
			derived['óbeygjanlegt'] = True
		return derived


class Nafnord(Ord):
	"""
	Nafnorð handler
	"""

	group = structs.Ordflokkar.Nafnord
	data: Optional[structs.NafnordData] = None

	def make_filename(self):
		return os.path.join(
			self.data.flokkur.get_folder(),
			'%s-%s%s.json' % (self.data.orð, self.data.kyn.value, self._fno_extras())
		)

	def make_kennistrengur(self):
		return '%s-%s-%s%s' % (
			self.data.flokkur.get_abbreviation(), self.data.orð, self.data.kyn.value,
			self._fno_extras()
		)

	def write_to_db(self) -> tuple[isl.Ord, bool]:
		isl_ord, changes_made = super().write_to_db()
		isl_no = db.Session.query(isl.Nafnord).filter_by(fk_Ord_id=isl_ord.Ord_id).first()
		if isl_no is None:
			isl_no = isl.Nafnord(fk_Ord_id=isl_ord.Ord_id)
			db.Session.add(isl_no)
			db.Session.commit()
			changes_made = True
		isl_no.Kyn = isl.Kyn[self.data.kyn.name]
		if self.data.samsett is not None:
			changes_made = changes_made or db.Session.is_modified(isl_no)
			if changes_made is True:
				isl_ord.Edited = datetime.datetime.utcnow()
				db.Session.commit()
			return (isl_ord, changes_made)
		if self.data.et is not None:
			if self.data.et.ág is not None:
				isl_no.fk_et_Fallbeyging_id, changes_made = self.write_fallbeyging_to_db(
					isl_no.fk_et_Fallbeyging_id, self.data.et.ág, changes_made
				)
			if self.data.et.mg is not None:
				isl_no.fk_et_mgr_Fallbeyging_id, changes_made = self.write_fallbeyging_to_db(
					isl_no.fk_et_mgr_Fallbeyging_id, self.data.et.mg, changes_made
				)
		if self.data.ft is not None:
			if self.data.ft.ág is not None:
				isl_no.fk_ft_Fallbeyging_id, changes_made = self.write_fallbeyging_to_db(
					isl_no.fk_ft_Fallbeyging_id, self.data.ft.ág, changes_made
				)
			if self.data.ft.mg is not None:
				isl_no.fk_ft_mgr_Fallbeyging_id, changes_made = self.write_fallbeyging_to_db(
					isl_no.fk_ft_mgr_Fallbeyging_id, self.data.ft.mg, changes_made
				)
		changes_made = changes_made or db.Session.is_modified(isl_no)
		if db.Session.is_modified(isl_no):
			db.Session.commit()
		if changes_made is True:
			isl_ord.Edited = datetime.datetime.utcnow()
			db.Session.commit()
		return (isl_ord, changes_made)

	def load_from_db(self, isl_ord: isl.Ord):
		ord_data = super().load_from_db(isl_ord)
		isl_nafnord = db.Session.query(isl.Nafnord).filter_by(fk_Ord_id=isl_ord.Ord_id).first()
		ord_data['kyn'] = structs.Kyn[isl_nafnord.Kyn.name].value
		if isl_ord.Samsett is True:
			ord_data = self.derive_beygingar_from_samsett(ord_data)
			self.data = structs.NafnordData(**ord_data)
			kennistr = self.make_kennistrengur()
			if self.data.kennistrengur != kennistr:
				raise Exception('Orð id=%s, kennistrengur mismatch, loaded="%s", derived="%s"' % (
					isl_ord.Ord_id, self.data.kennistrengur, kennistr
				))
			self.data.datahash = self.get_data_hash()
			return
		if (
			isl_nafnord.fk_et_Fallbeyging_id is not None or
			isl_nafnord.fk_et_mgr_Fallbeyging_id is not None
		):
			ord_data['et'] = {}
		if isl_nafnord.fk_et_Fallbeyging_id is not None:
			ord_data['et']['ág'] = self.load_fallbeyging_from_db(isl_nafnord.fk_et_Fallbeyging_id)
		if isl_nafnord.fk_et_mgr_Fallbeyging_id is not None:
			ord_data['et']['mg'] = self.load_fallbeyging_from_db(
				isl_nafnord.fk_et_mgr_Fallbeyging_id
			)
		if (
			isl_nafnord.fk_ft_Fallbeyging_id is not None or
			isl_nafnord.fk_ft_mgr_Fallbeyging_id is not None
		):
			ord_data['ft'] = {}
		if isl_nafnord.fk_ft_Fallbeyging_id is not None:
			ord_data['ft']['ág'] = self.load_fallbeyging_from_db(isl_nafnord.fk_ft_Fallbeyging_id)
		if isl_nafnord.fk_ft_mgr_Fallbeyging_id is not None:
			ord_data['ft']['mg'] = self.load_fallbeyging_from_db(
				isl_nafnord.fk_ft_mgr_Fallbeyging_id
			)
		self.data = structs.NafnordData(**ord_data)
		kennistr = self.make_kennistrengur()
		if self.data.kennistrengur != kennistr:
			raise Exception('Orð id=%s, kennistrengur mismatch, loaded="%s", derived="%s"' % (
				isl_ord.Ord_id, self.data.kennistrengur, kennistr
			))
		self.data.datahash = self.get_data_hash()


class Lysingarord(Ord):
	"""
	Lýsingarorð handler
	"""

	group = structs.Ordflokkar.Lysingarord
	data: Optional[structs.LysingarordData] = None

	def make_filename(self):
		return os.path.join(
			self.data.flokkur.get_folder(), '%s%s.json' % (self.data.orð, self._fno_extras())
		)

	def make_kennistrengur(self):
		return '%s-%s%s' % (
			self.data.flokkur.get_abbreviation(), self.data.orð, self._fno_extras()
		)

	def write_to_db(self) -> tuple[isl.Ord, bool]:
		isl_ord, changes_made = super().write_to_db()
		if self.data.samsett is not None:
			return (isl_ord, changes_made)
		isl_lo = db.Session.query(isl.Lysingarord).filter_by(fk_Ord_id=isl_ord.Ord_id).first()
		if isl_lo is None:
			isl_lo = isl.Lysingarord(fk_Ord_id=isl_ord.Ord_id)
			db.Session.add(isl_lo)
			db.Session.commit()
			changes_made = True
		if self.data.frumstig is not None:
			if self.data.frumstig.sb is not None:
				if self.data.frumstig.sb.et is not None:
					if self.data.frumstig.sb.et.kk is not None:
						isl_lo.fk_Frumstig_sb_et_kk_Fallbeyging_id, changes_made = (
							self.write_fallbeyging_to_db(
								isl_lo.fk_Frumstig_sb_et_kk_Fallbeyging_id,
								self.data.frumstig.sb.et.kk,
								changes_made
							)
						)
					if self.data.frumstig.sb.et.kvk is not None:
						isl_lo.fk_Frumstig_sb_et_kvk_Fallbeyging_id, changes_made = (
							self.write_fallbeyging_to_db(
								isl_lo.fk_Frumstig_sb_et_kvk_Fallbeyging_id,
								self.data.frumstig.sb.et.kvk,
								changes_made
							)
						)
					if self.data.frumstig.sb.et.hk is not None:
						isl_lo.fk_Frumstig_sb_et_hk_Fallbeyging_id, changes_made = (
							self.write_fallbeyging_to_db(
								isl_lo.fk_Frumstig_sb_et_hk_Fallbeyging_id,
								self.data.frumstig.sb.et.hk,
								changes_made
							)
						)
				if self.data.frumstig.sb.ft is not None:
					if self.data.frumstig.sb.ft.kk is not None:
						isl_lo.fk_Frumstig_sb_ft_kk_Fallbeyging_id, changes_made = (
							self.write_fallbeyging_to_db(
								isl_lo.fk_Frumstig_sb_ft_kk_Fallbeyging_id,
								self.data.frumstig.sb.ft.kk,
								changes_made
							)
						)
					if self.data.frumstig.sb.ft.kvk is not None:
						isl_lo.fk_Frumstig_sb_ft_kvk_Fallbeyging_id, changes_made = (
							self.write_fallbeyging_to_db(
								isl_lo.fk_Frumstig_sb_ft_kvk_Fallbeyging_id,
								self.data.frumstig.sb.ft.kvk,
								changes_made
							)
						)
					if self.data.frumstig.sb.ft.hk is not None:
						isl_lo.fk_Frumstig_sb_ft_hk_Fallbeyging_id, changes_made = (
							self.write_fallbeyging_to_db(
								isl_lo.fk_Frumstig_sb_ft_hk_Fallbeyging_id,
								self.data.frumstig.sb.ft.hk,
								changes_made
							)
						)
			if self.data.frumstig.vb is not None:
				if self.data.frumstig.vb.et is not None:
					if self.data.frumstig.vb.et.kk is not None:
						isl_lo.fk_Frumstig_vb_et_kk_Fallbeyging_id, changes_made = (
							self.write_fallbeyging_to_db(
								isl_lo.fk_Frumstig_vb_et_kk_Fallbeyging_id,
								self.data.frumstig.vb.et.kk,
								changes_made
							)
						)
					if self.data.frumstig.vb.et.kvk is not None:
						isl_lo.fk_Frumstig_vb_et_kvk_Fallbeyging_id, changes_made = (
							self.write_fallbeyging_to_db(
								isl_lo.fk_Frumstig_vb_et_kvk_Fallbeyging_id,
								self.data.frumstig.vb.et.kvk,
								changes_made
							)
						)
					if self.data.frumstig.vb.et.hk is not None:
						isl_lo.fk_Frumstig_vb_et_hk_Fallbeyging_id, changes_made = (
							self.write_fallbeyging_to_db(
								isl_lo.fk_Frumstig_vb_et_hk_Fallbeyging_id,
								self.data.frumstig.vb.et.hk,
								changes_made
							)
						)
				if self.data.frumstig.vb.ft is not None:
					if self.data.frumstig.vb.ft.kk is not None:
						isl_lo.fk_Frumstig_vb_ft_kk_Fallbeyging_id, changes_made = (
							self.write_fallbeyging_to_db(
								isl_lo.fk_Frumstig_vb_ft_kk_Fallbeyging_id,
								self.data.frumstig.vb.ft.kk,
								changes_made
							)
						)
					if self.data.frumstig.vb.ft.kvk is not None:
						isl_lo.fk_Frumstig_vb_ft_kvk_Fallbeyging_id, changes_made = (
							self.write_fallbeyging_to_db(
								isl_lo.fk_Frumstig_vb_ft_kvk_Fallbeyging_id,
								self.data.frumstig.vb.ft.kvk,
								changes_made
							)
						)
					if self.data.frumstig.vb.ft.hk is not None:
						isl_lo.fk_Frumstig_vb_ft_hk_Fallbeyging_id, changes_made = (
							self.write_fallbeyging_to_db(
								isl_lo.fk_Frumstig_vb_ft_hk_Fallbeyging_id,
								self.data.frumstig.vb.ft.hk,
								changes_made
							)
						)
		if self.data.miðstig is not None:
			if self.data.miðstig.vb is not None:
				if self.data.miðstig.vb.et is not None:
					if self.data.miðstig.vb.et.kk is not None:
						isl_lo.fk_Midstig_vb_et_kk_Fallbeyging_id, changes_made = (
							self.write_fallbeyging_to_db(
								isl_lo.fk_Midstig_vb_et_kk_Fallbeyging_id,
								self.data.miðstig.vb.et.kk,
								changes_made
							)
						)
					if self.data.miðstig.vb.et.kvk is not None:
						isl_lo.fk_Midstig_vb_et_kvk_Fallbeyging_id, changes_made = (
							self.write_fallbeyging_to_db(
								isl_lo.fk_Midstig_vb_et_kvk_Fallbeyging_id,
								self.data.miðstig.vb.et.kvk,
								changes_made
							)
						)
					if self.data.miðstig.vb.et.hk is not None:
						isl_lo.fk_Midstig_vb_et_hk_Fallbeyging_id, changes_made = (
							self.write_fallbeyging_to_db(
								isl_lo.fk_Midstig_vb_et_hk_Fallbeyging_id,
								self.data.miðstig.vb.et.hk,
								changes_made
							)
						)
				if self.data.miðstig.vb.ft is not None:
					if self.data.miðstig.vb.ft.kk is not None:
						isl_lo.fk_Midstig_vb_ft_kk_Fallbeyging_id, changes_made = (
							self.write_fallbeyging_to_db(
								isl_lo.fk_Midstig_vb_ft_kk_Fallbeyging_id,
								self.data.miðstig.vb.ft.kk,
								changes_made
							)
						)
					if self.data.miðstig.vb.ft.kvk is not None:
						isl_lo.fk_Midstig_vb_ft_kvk_Fallbeyging_id, changes_made = (
							self.write_fallbeyging_to_db(
								isl_lo.fk_Midstig_vb_ft_kvk_Fallbeyging_id,
								self.data.miðstig.vb.ft.kvk,
								changes_made
							)
						)
					if self.data.miðstig.vb.ft.hk is not None:
						isl_lo.fk_Midstig_vb_ft_hk_Fallbeyging_id, changes_made = (
							self.write_fallbeyging_to_db(
								isl_lo.fk_Midstig_vb_ft_hk_Fallbeyging_id,
								self.data.miðstig.vb.ft.hk,
								changes_made
							)
						)
		if self.data.efstastig is not None:
			if self.data.efstastig.sb is not None:
				if self.data.efstastig.sb.et is not None:
					if self.data.efstastig.sb.et.kk is not None:
						isl_lo.fk_Efstastig_sb_et_kk_Fallbeyging_id, changes_made = (
							self.write_fallbeyging_to_db(
								isl_lo.fk_Efstastig_sb_et_kk_Fallbeyging_id,
								self.data.efstastig.sb.et.kk,
								changes_made
							)
						)
					if self.data.efstastig.sb.et.kvk is not None:
						isl_lo.fk_Efstastig_sb_et_kvk_Fallbeyging_id, changes_made = (
							self.write_fallbeyging_to_db(
								isl_lo.fk_Efstastig_sb_et_kvk_Fallbeyging_id,
								self.data.efstastig.sb.et.kvk,
								changes_made
							)
						)
					if self.data.efstastig.sb.et.hk is not None:
						isl_lo.fk_Efstastig_sb_et_hk_Fallbeyging_id, changes_made = (
							self.write_fallbeyging_to_db(
								isl_lo.fk_Efstastig_sb_et_hk_Fallbeyging_id,
								self.data.efstastig.sb.et.hk,
								changes_made
							)
						)
				if self.data.efstastig.sb.ft is not None:
					if self.data.efstastig.sb.ft.kk is not None:
						isl_lo.fk_Efstastig_sb_ft_kk_Fallbeyging_id, changes_made = (
							self.write_fallbeyging_to_db(
								isl_lo.fk_Efstastig_sb_ft_kk_Fallbeyging_id,
								self.data.efstastig.sb.ft.kk,
								changes_made
							)
						)
					if self.data.efstastig.sb.ft.kvk is not None:
						isl_lo.fk_Efstastig_sb_ft_kvk_Fallbeyging_id, changes_made = (
							self.write_fallbeyging_to_db(
								isl_lo.fk_Efstastig_sb_ft_kvk_Fallbeyging_id,
								self.data.efstastig.sb.ft.kvk,
								changes_made
							)
						)
					if self.data.efstastig.sb.ft.hk is not None:
						isl_lo.fk_Efstastig_sb_ft_hk_Fallbeyging_id, changes_made = (
							self.write_fallbeyging_to_db(
								isl_lo.fk_Efstastig_sb_ft_hk_Fallbeyging_id,
								self.data.efstastig.sb.ft.hk,
								changes_made
							)
						)
			if self.data.efstastig.vb is not None:
				if self.data.efstastig.vb.et is not None:
					if self.data.efstastig.vb.et.kk is not None:
						isl_lo.fk_Efstastig_vb_et_kk_Fallbeyging_id, changes_made = (
							self.write_fallbeyging_to_db(
								isl_lo.fk_Efstastig_vb_et_kk_Fallbeyging_id,
								self.data.efstastig.vb.et.kk,
								changes_made
							)
						)
					if self.data.efstastig.vb.et.kvk is not None:
						isl_lo.fk_Efstastig_vb_et_kvk_Fallbeyging_id, changes_made = (
							self.write_fallbeyging_to_db(
								isl_lo.fk_Efstastig_vb_et_kvk_Fallbeyging_id,
								self.data.efstastig.vb.et.kvk,
								changes_made
							)
						)
					if self.data.efstastig.vb.et.hk is not None:
						isl_lo.fk_Efstastig_vb_et_hk_Fallbeyging_id, changes_made = (
							self.write_fallbeyging_to_db(
								isl_lo.fk_Efstastig_vb_et_hk_Fallbeyging_id,
								self.data.efstastig.vb.et.hk,
								changes_made
							)
						)
				if self.data.efstastig.vb.ft is not None:
					if self.data.efstastig.vb.ft.kk is not None:
						isl_lo.fk_Efstastig_vb_ft_kk_Fallbeyging_id, changes_made = (
							self.write_fallbeyging_to_db(
								isl_lo.fk_Efstastig_vb_ft_kk_Fallbeyging_id,
								self.data.efstastig.vb.ft.kk,
								changes_made
							)
						)
					if self.data.efstastig.vb.ft.kvk is not None:
						isl_lo.fk_Efstastig_vb_ft_kvk_Fallbeyging_id, changes_made = (
							self.write_fallbeyging_to_db(
								isl_lo.fk_Efstastig_vb_ft_kvk_Fallbeyging_id,
								self.data.efstastig.vb.ft.kvk,
								changes_made
							)
						)
					if self.data.efstastig.vb.ft.hk is not None:
						isl_lo.fk_Efstastig_vb_ft_hk_Fallbeyging_id, changes_made = (
							self.write_fallbeyging_to_db(
								isl_lo.fk_Efstastig_vb_ft_hk_Fallbeyging_id,
								self.data.efstastig.vb.ft.hk,
								changes_made
							)
						)
		changes_made = changes_made or db.Session.is_modified(isl_lo)
		if db.Session.is_modified(isl_lo):
			db.Session.commit()
		if changes_made is True:
			isl_ord.Edited = datetime.datetime.utcnow()
			db.Session.commit()
		return (isl_ord, changes_made)

	def load_from_db(self, isl_ord: isl.Ord):
		ord_data = super().load_from_db(isl_ord)
		if isl_ord.Samsett is True:
			ord_data = self.derive_beygingar_from_samsett(ord_data)
			self.data = structs.LysingarordData(**ord_data)
			kennistr = self.make_kennistrengur()
			if self.data.kennistrengur != kennistr:
				raise Exception(
					'Orð id=%s, from db, kennistrengur mismatch, loaded="%s", derived="%s"' % (
						isl_ord.Ord_id, self.data.kennistrengur, kennistr
					)
				)
			self.data.datahash = self.get_data_hash()
			return
		isl_lo = db.Session.query(isl.Lysingarord).filter_by(fk_Ord_id=isl_ord.Ord_id).first()
		# fetch lýsingarorð beygingar
		if (
			isl_lo.fk_Frumstig_sb_et_kk_Fallbeyging_id is not None or
			isl_lo.fk_Frumstig_sb_et_kvk_Fallbeyging_id is not None or
			isl_lo.fk_Frumstig_sb_et_hk_Fallbeyging_id is not None or
			isl_lo.fk_Frumstig_sb_ft_kk_Fallbeyging_id is not None or
			isl_lo.fk_Frumstig_sb_ft_kvk_Fallbeyging_id is not None or
			isl_lo.fk_Frumstig_sb_ft_hk_Fallbeyging_id is not None or
			isl_lo.fk_Frumstig_vb_et_kk_Fallbeyging_id is not None or
			isl_lo.fk_Frumstig_vb_et_kvk_Fallbeyging_id is not None or
			isl_lo.fk_Frumstig_vb_et_hk_Fallbeyging_id is not None or
			isl_lo.fk_Frumstig_vb_ft_kk_Fallbeyging_id is not None or
			isl_lo.fk_Frumstig_vb_ft_kvk_Fallbeyging_id is not None or
			isl_lo.fk_Frumstig_vb_ft_hk_Fallbeyging_id is not None
		):
			ord_data['frumstig'] = {}
		if (
			isl_lo.fk_Frumstig_sb_et_kk_Fallbeyging_id is not None or
			isl_lo.fk_Frumstig_sb_et_kvk_Fallbeyging_id is not None or
			isl_lo.fk_Frumstig_sb_et_hk_Fallbeyging_id is not None or
			isl_lo.fk_Frumstig_sb_ft_kk_Fallbeyging_id is not None or
			isl_lo.fk_Frumstig_sb_ft_kvk_Fallbeyging_id is not None or
			isl_lo.fk_Frumstig_sb_ft_hk_Fallbeyging_id is not None
		):
			ord_data['frumstig']['sb'] = {}
		if (
			isl_lo.fk_Frumstig_sb_et_kk_Fallbeyging_id is not None or
			isl_lo.fk_Frumstig_sb_et_kvk_Fallbeyging_id is not None or
			isl_lo.fk_Frumstig_sb_et_hk_Fallbeyging_id is not None
		):
			ord_data['frumstig']['sb']['et'] = {}
		if (
			isl_lo.fk_Frumstig_sb_ft_kk_Fallbeyging_id is not None or
			isl_lo.fk_Frumstig_sb_ft_kvk_Fallbeyging_id is not None or
			isl_lo.fk_Frumstig_sb_ft_hk_Fallbeyging_id is not None
		):
			ord_data['frumstig']['sb']['ft'] = {}
		if (
			isl_lo.fk_Frumstig_vb_et_kk_Fallbeyging_id is not None or
			isl_lo.fk_Frumstig_vb_et_kvk_Fallbeyging_id is not None or
			isl_lo.fk_Frumstig_vb_et_hk_Fallbeyging_id is not None or
			isl_lo.fk_Frumstig_vb_ft_kk_Fallbeyging_id is not None or
			isl_lo.fk_Frumstig_vb_ft_kvk_Fallbeyging_id is not None or
			isl_lo.fk_Frumstig_vb_ft_hk_Fallbeyging_id is not None
		):
			ord_data['frumstig']['vb'] = {}
		if (
			isl_lo.fk_Frumstig_vb_et_kk_Fallbeyging_id is not None or
			isl_lo.fk_Frumstig_vb_et_kvk_Fallbeyging_id is not None or
			isl_lo.fk_Frumstig_vb_et_hk_Fallbeyging_id is not None
		):
			ord_data['frumstig']['vb']['et'] = {}
		if (
			isl_lo.fk_Frumstig_vb_ft_kk_Fallbeyging_id is not None or
			isl_lo.fk_Frumstig_vb_ft_kvk_Fallbeyging_id is not None or
			isl_lo.fk_Frumstig_vb_ft_hk_Fallbeyging_id is not None
		):
			ord_data['frumstig']['vb']['ft'] = {}
		if (
			isl_lo.fk_Midstig_vb_et_kk_Fallbeyging_id is not None or
			isl_lo.fk_Midstig_vb_et_kvk_Fallbeyging_id is not None or
			isl_lo.fk_Midstig_vb_et_hk_Fallbeyging_id is not None or
			isl_lo.fk_Midstig_vb_ft_kk_Fallbeyging_id is not None or
			isl_lo.fk_Midstig_vb_ft_kvk_Fallbeyging_id is not None or
			isl_lo.fk_Midstig_vb_ft_hk_Fallbeyging_id is not None
		):
			ord_data['miðstig'] = {}
			ord_data['miðstig']['vb'] = {}
		if (
			isl_lo.fk_Midstig_vb_et_kk_Fallbeyging_id is not None or
			isl_lo.fk_Midstig_vb_et_kvk_Fallbeyging_id is not None or
			isl_lo.fk_Midstig_vb_et_hk_Fallbeyging_id is not None
		):
			ord_data['miðstig']['vb']['et'] = {}
		if (
			isl_lo.fk_Midstig_vb_ft_kk_Fallbeyging_id is not None or
			isl_lo.fk_Midstig_vb_ft_kvk_Fallbeyging_id is not None or
			isl_lo.fk_Midstig_vb_ft_hk_Fallbeyging_id is not None
		):
			ord_data['miðstig']['vb']['ft'] = {}
		if (
			isl_lo.fk_Efstastig_sb_et_kk_Fallbeyging_id is not None or
			isl_lo.fk_Efstastig_sb_et_kvk_Fallbeyging_id is not None or
			isl_lo.fk_Efstastig_sb_et_hk_Fallbeyging_id is not None or
			isl_lo.fk_Efstastig_sb_ft_kk_Fallbeyging_id is not None or
			isl_lo.fk_Efstastig_sb_ft_kvk_Fallbeyging_id is not None or
			isl_lo.fk_Efstastig_sb_ft_hk_Fallbeyging_id is not None or
			isl_lo.fk_Efstastig_vb_et_kk_Fallbeyging_id is not None or
			isl_lo.fk_Efstastig_vb_et_kvk_Fallbeyging_id is not None or
			isl_lo.fk_Efstastig_vb_et_hk_Fallbeyging_id is not None or
			isl_lo.fk_Efstastig_vb_ft_kk_Fallbeyging_id is not None or
			isl_lo.fk_Efstastig_vb_ft_kvk_Fallbeyging_id is not None or
			isl_lo.fk_Efstastig_vb_ft_hk_Fallbeyging_id is not None
		):
			ord_data['efstastig'] = {}
		if (
			isl_lo.fk_Efstastig_sb_et_kk_Fallbeyging_id is not None or
			isl_lo.fk_Efstastig_sb_et_kvk_Fallbeyging_id is not None or
			isl_lo.fk_Efstastig_sb_et_hk_Fallbeyging_id is not None or
			isl_lo.fk_Efstastig_sb_ft_kk_Fallbeyging_id is not None or
			isl_lo.fk_Efstastig_sb_ft_kvk_Fallbeyging_id is not None or
			isl_lo.fk_Efstastig_sb_ft_hk_Fallbeyging_id is not None
		):
			ord_data['efstastig']['sb'] = {}
		if (
			isl_lo.fk_Efstastig_sb_et_kk_Fallbeyging_id is not None or
			isl_lo.fk_Efstastig_sb_et_kvk_Fallbeyging_id is not None or
			isl_lo.fk_Efstastig_sb_et_hk_Fallbeyging_id is not None
		):
			ord_data['efstastig']['sb']['et'] = {}
		if (
			isl_lo.fk_Efstastig_sb_ft_kk_Fallbeyging_id is not None or
			isl_lo.fk_Efstastig_sb_ft_kvk_Fallbeyging_id is not None or
			isl_lo.fk_Efstastig_sb_ft_hk_Fallbeyging_id is not None
		):
			ord_data['efstastig']['sb']['ft'] = {}
		if (
			isl_lo.fk_Efstastig_vb_et_kk_Fallbeyging_id is not None or
			isl_lo.fk_Efstastig_vb_et_kvk_Fallbeyging_id is not None or
			isl_lo.fk_Efstastig_vb_et_hk_Fallbeyging_id is not None or
			isl_lo.fk_Efstastig_vb_ft_kk_Fallbeyging_id is not None or
			isl_lo.fk_Efstastig_vb_ft_kvk_Fallbeyging_id is not None or
			isl_lo.fk_Efstastig_vb_ft_hk_Fallbeyging_id is not None
		):
			ord_data['efstastig']['vb'] = {}
		if (
			isl_lo.fk_Efstastig_vb_et_kk_Fallbeyging_id is not None or
			isl_lo.fk_Efstastig_vb_et_kvk_Fallbeyging_id is not None or
			isl_lo.fk_Efstastig_vb_et_hk_Fallbeyging_id is not None
		):
			ord_data['efstastig']['vb']['et'] = {}
		if (
			isl_lo.fk_Efstastig_vb_ft_kk_Fallbeyging_id is not None or
			isl_lo.fk_Efstastig_vb_ft_kvk_Fallbeyging_id is not None or
			isl_lo.fk_Efstastig_vb_ft_hk_Fallbeyging_id is not None
		):
			ord_data['efstastig']['vb']['ft'] = {}
		# Frumstig, sterk beyging
		if isl_lo.fk_Frumstig_sb_et_kk_Fallbeyging_id is not None:
			ord_data['frumstig']['sb']['et']['kk'] = self.load_fallbeyging_from_db(
				isl_lo.fk_Frumstig_sb_et_kk_Fallbeyging_id
			)
		if isl_lo.fk_Frumstig_sb_et_kvk_Fallbeyging_id is not None:
			ord_data['frumstig']['sb']['et']['kvk'] = self.load_fallbeyging_from_db(
				isl_lo.fk_Frumstig_sb_et_kvk_Fallbeyging_id
			)
		if isl_lo.fk_Frumstig_sb_et_hk_Fallbeyging_id is not None:
			ord_data['frumstig']['sb']['et']['hk'] = self.load_fallbeyging_from_db(
				isl_lo.fk_Frumstig_sb_et_hk_Fallbeyging_id
			)
		if isl_lo.fk_Frumstig_sb_ft_kk_Fallbeyging_id is not None:
			ord_data['frumstig']['sb']['ft']['kk'] = self.load_fallbeyging_from_db(
				isl_lo.fk_Frumstig_sb_ft_kk_Fallbeyging_id
			)
		if isl_lo.fk_Frumstig_sb_ft_kvk_Fallbeyging_id is not None:
			ord_data['frumstig']['sb']['ft']['kvk'] = self.load_fallbeyging_from_db(
				isl_lo.fk_Frumstig_sb_ft_kvk_Fallbeyging_id
			)
		if isl_lo.fk_Frumstig_sb_ft_hk_Fallbeyging_id is not None:
			ord_data['frumstig']['sb']['ft']['hk'] = self.load_fallbeyging_from_db(
				isl_lo.fk_Frumstig_sb_ft_hk_Fallbeyging_id
			)
		# Frumstig, veik beyging
		if isl_lo.fk_Frumstig_vb_et_kk_Fallbeyging_id is not None:
			ord_data['frumstig']['vb']['et']['kk'] = self.load_fallbeyging_from_db(
				isl_lo.fk_Frumstig_vb_et_kk_Fallbeyging_id
			)
		if isl_lo.fk_Frumstig_vb_et_kvk_Fallbeyging_id is not None:
			ord_data['frumstig']['vb']['et']['kvk'] = self.load_fallbeyging_from_db(
				isl_lo.fk_Frumstig_vb_et_kvk_Fallbeyging_id
			)
		if isl_lo.fk_Frumstig_vb_et_hk_Fallbeyging_id is not None:
			ord_data['frumstig']['vb']['et']['hk'] = self.load_fallbeyging_from_db(
				isl_lo.fk_Frumstig_vb_et_hk_Fallbeyging_id
			)
		if isl_lo.fk_Frumstig_vb_ft_kk_Fallbeyging_id is not None:
			ord_data['frumstig']['vb']['ft']['kk'] = self.load_fallbeyging_from_db(
				isl_lo.fk_Frumstig_vb_ft_kk_Fallbeyging_id
			)
		if isl_lo.fk_Frumstig_vb_ft_kvk_Fallbeyging_id is not None:
			ord_data['frumstig']['vb']['ft']['kvk'] = self.load_fallbeyging_from_db(
				isl_lo.fk_Frumstig_vb_ft_kvk_Fallbeyging_id
			)
		if isl_lo.fk_Frumstig_vb_ft_hk_Fallbeyging_id is not None:
			ord_data['frumstig']['vb']['ft']['hk'] = self.load_fallbeyging_from_db(
				isl_lo.fk_Frumstig_vb_ft_hk_Fallbeyging_id
			)
		# Miðstig, veik beyging (miðstig hafa enga sterka beygingu)
		if isl_lo.fk_Midstig_vb_et_kk_Fallbeyging_id is not None:
			ord_data['miðstig']['vb']['et']['kk'] = self.load_fallbeyging_from_db(
				isl_lo.fk_Midstig_vb_et_kk_Fallbeyging_id
			)
		if isl_lo.fk_Midstig_vb_et_kvk_Fallbeyging_id is not None:
			ord_data['miðstig']['vb']['et']['kvk'] = self.load_fallbeyging_from_db(
				isl_lo.fk_Midstig_vb_et_kvk_Fallbeyging_id
			)
		if isl_lo.fk_Midstig_vb_et_hk_Fallbeyging_id is not None:
			ord_data['miðstig']['vb']['et']['hk'] = self.load_fallbeyging_from_db(
				isl_lo.fk_Midstig_vb_et_hk_Fallbeyging_id
			)
		if isl_lo.fk_Midstig_vb_ft_kk_Fallbeyging_id is not None:
			ord_data['miðstig']['vb']['ft']['kk'] = self.load_fallbeyging_from_db(
				isl_lo.fk_Midstig_vb_ft_kk_Fallbeyging_id
			)
		if isl_lo.fk_Midstig_vb_ft_kvk_Fallbeyging_id is not None:
			ord_data['miðstig']['vb']['ft']['kvk'] = self.load_fallbeyging_from_db(
				isl_lo.fk_Midstig_vb_ft_kvk_Fallbeyging_id
			)
		if isl_lo.fk_Midstig_vb_ft_hk_Fallbeyging_id is not None:
			ord_data['miðstig']['vb']['ft']['hk'] = self.load_fallbeyging_from_db(
				isl_lo.fk_Midstig_vb_ft_hk_Fallbeyging_id
			)
		# Efsta stig, sterk beyging
		if isl_lo.fk_Efstastig_sb_et_kk_Fallbeyging_id is not None:
			ord_data['efstastig']['sb']['et']['kk'] = self.load_fallbeyging_from_db(
				isl_lo.fk_Efstastig_sb_et_kk_Fallbeyging_id
			)
		if isl_lo.fk_Efstastig_sb_et_kvk_Fallbeyging_id is not None:
			ord_data['efstastig']['sb']['et']['kvk'] = self.load_fallbeyging_from_db(
				isl_lo.fk_Efstastig_sb_et_kvk_Fallbeyging_id
			)
		if isl_lo.fk_Efstastig_sb_et_hk_Fallbeyging_id is not None:
			ord_data['efstastig']['sb']['et']['hk'] = self.load_fallbeyging_from_db(
				isl_lo.fk_Efstastig_sb_et_hk_Fallbeyging_id
			)
		if isl_lo.fk_Efstastig_sb_ft_kk_Fallbeyging_id is not None:
			ord_data['efstastig']['sb']['ft']['kk'] = self.load_fallbeyging_from_db(
				isl_lo.fk_Efstastig_sb_ft_kk_Fallbeyging_id
			)
		if isl_lo.fk_Efstastig_sb_ft_kvk_Fallbeyging_id is not None:
			ord_data['efstastig']['sb']['ft']['kvk'] = self.load_fallbeyging_from_db(
				isl_lo.fk_Efstastig_sb_ft_kvk_Fallbeyging_id
			)
		if isl_lo.fk_Efstastig_sb_ft_hk_Fallbeyging_id is not None:
			ord_data['efstastig']['sb']['ft']['hk'] = self.load_fallbeyging_from_db(
				isl_lo.fk_Efstastig_sb_ft_hk_Fallbeyging_id
			)
		# Efsta stig, veik beyging
		if isl_lo.fk_Efstastig_vb_et_kk_Fallbeyging_id is not None:
			ord_data['efstastig']['vb']['et']['kk'] = self.load_fallbeyging_from_db(
				isl_lo.fk_Efstastig_vb_et_kk_Fallbeyging_id
			)
		if isl_lo.fk_Efstastig_vb_et_kvk_Fallbeyging_id is not None:
			ord_data['efstastig']['vb']['et']['kvk'] = self.load_fallbeyging_from_db(
				isl_lo.fk_Efstastig_vb_et_kvk_Fallbeyging_id
			)
		if isl_lo.fk_Efstastig_vb_et_hk_Fallbeyging_id is not None:
			ord_data['efstastig']['vb']['et']['hk'] = self.load_fallbeyging_from_db(
				isl_lo.fk_Efstastig_vb_et_hk_Fallbeyging_id
			)
		if isl_lo.fk_Efstastig_vb_ft_kk_Fallbeyging_id is not None:
			ord_data['efstastig']['vb']['ft']['kk'] = self.load_fallbeyging_from_db(
				isl_lo.fk_Efstastig_vb_ft_kk_Fallbeyging_id
			)
		if isl_lo.fk_Efstastig_vb_ft_kvk_Fallbeyging_id is not None:
			ord_data['efstastig']['vb']['ft']['kvk'] = self.load_fallbeyging_from_db(
				isl_lo.fk_Efstastig_vb_ft_kvk_Fallbeyging_id
			)
		if isl_lo.fk_Efstastig_vb_ft_hk_Fallbeyging_id is not None:
			ord_data['efstastig']['vb']['ft']['hk'] = self.load_fallbeyging_from_db(
				isl_lo.fk_Efstastig_vb_ft_hk_Fallbeyging_id
			)
		self.data = structs.LysingarordData(**ord_data)
		kennistr = self.make_kennistrengur()
		if self.data.kennistrengur != kennistr:
			raise Exception(
				'Orð id=%s, loaded from db, kennistrengur mismatch, loaded="%s", derived="%s"' % (
					isl_ord.Ord_id, self.data.kennistrengur, kennistr
				)
			)
		self.data.datahash = self.get_data_hash()


class Sagnord(Ord):
	"""
	Sagnorð handler
	"""

	group = structs.Ordflokkar.Sagnord
	data: Optional[structs.SagnordData] = None

	def make_filename(self):
		return os.path.join(
			self.data.flokkur.get_folder(), '%s%s.json' % (self.data.orð, self._fno_extras())
		)

	def make_kennistrengur(self):
		return '%s-%s%s' % (
			self.data.flokkur.get_abbreviation(), self.data.orð, self._fno_extras()
		)

	def write_to_db(self) -> tuple[isl.Ord, bool]:
		isl_ord, changes_made = super().write_to_db()
		if self.data.samsett is not None:
			return (isl_ord, changes_made)
		isl_so = db.Session.query(isl.Sagnord).filter_by(fk_Ord_id=isl_ord.Ord_id).first()
		if isl_so is None:
			isl_so = isl.Sagnord(fk_Ord_id=isl_ord.Ord_id)
			db.Session.add(isl_so)
			db.Session.commit()
			changes_made = True
		if self.data.germynd is not None:
			isl_so.Germynd_Nafnhattur = self.data.germynd.nafnháttur
			isl_so.Germynd_Sagnbot = self.data.germynd.sagnbót
			if self.data.germynd.boðháttur is not None:
				isl_so.Germynd_Bodhattur_styfdur = self.data.germynd.boðháttur.stýfður
				isl_so.Germynd_Bodhattur_et = self.data.germynd.boðháttur.et
				isl_so.Germynd_Bodhattur_ft = self.data.germynd.boðháttur.ft
			if self.data.germynd.persónuleg is not None:
				if self.data.germynd.persónuleg.framsöguháttur is not None:
					isl_so.fk_Germynd_personuleg_framsoguhattur, changes_made = (
						self.write_sagnbeyging_to_db(
							isl_so.fk_Germynd_personuleg_framsoguhattur,
							self.data.germynd.persónuleg.framsöguháttur.dict(),
							changes_made
						)
					)
				if self.data.germynd.persónuleg.viðtengingarháttur is not None:
					isl_so.fk_Germynd_personuleg_vidtengingarhattur, changes_made = (
						self.write_sagnbeyging_to_db(
							isl_so.fk_Germynd_personuleg_vidtengingarhattur,
							self.data.germynd.persónuleg.viðtengingarháttur.dict(),
							changes_made
						)
					)
			if self.data.germynd.ópersónuleg is not None:
				if self.data.germynd.ópersónuleg.frumlag is not None:
					isl_so.Germynd_opersonuleg_frumlag = (
						isl.Fall[self.data.germynd.ópersónuleg.frumlag.name]
					)
				if self.data.germynd.ópersónuleg.framsöguháttur is not None:
					isl_so.fk_Germynd_opersonuleg_framsoguhattur, changes_made = (
						self.write_sagnbeyging_to_db(
							isl_so.fk_Germynd_opersonuleg_framsoguhattur,
							self.data.germynd.ópersónuleg.framsöguháttur.dict(),
							changes_made
						)
					)
				if self.data.germynd.ópersónuleg.viðtengingarháttur is not None:
					isl_so.fk_Germynd_opersonuleg_vidtengingarhattur, changes_made = (
						self.write_sagnbeyging_to_db(
							isl_so.fk_Germynd_opersonuleg_vidtengingarhattur,
							self.data.germynd.ópersónuleg.viðtengingarháttur.dict(),
							changes_made
						)
					)
			if self.data.germynd.spurnarmyndir is not None:
				if self.data.germynd.spurnarmyndir.framsöguháttur is not None:
					if self.data.germynd.spurnarmyndir.framsöguháttur.nútíð is not None:
						if self.data.germynd.spurnarmyndir.framsöguháttur.nútíð.et is not None:
							isl_so.Germynd_spurnarmyndir_framsoguhattur_nutid_et = (
								self.data.germynd.spurnarmyndir.framsöguháttur.nútíð.et
							)
						if self.data.germynd.spurnarmyndir.framsöguháttur.nútíð.ft is not None:
							isl_so.Germynd_spurnarmyndir_framsoguhattur_nutid_ft = (
								self.data.germynd.spurnarmyndir.framsöguháttur.nútíð.ft
							)
					if self.data.germynd.spurnarmyndir.framsöguháttur.þátíð is not None:
						if self.data.germynd.spurnarmyndir.framsöguháttur.þátíð.et is not None:
							isl_so.Germynd_spurnarmyndir_framsoguhattur_thatid_et = (
								self.data.germynd.spurnarmyndir.framsöguháttur.þátíð.et
							)
						if self.data.germynd.spurnarmyndir.framsöguháttur.þátíð.ft is not None:
							isl_so.Germynd_spurnarmyndir_framsoguhattur_thatid_ft = (
								self.data.germynd.spurnarmyndir.framsöguháttur.þátíð.ft
							)
				if self.data.germynd.spurnarmyndir.viðtengingarháttur is not None:
					if self.data.germynd.spurnarmyndir.viðtengingarháttur.nútíð is not None:
						if self.data.germynd.spurnarmyndir.viðtengingarháttur.nútíð.et is not None:
							isl_so.Germynd_spurnarmyndir_vidtengingarhattur_nutid_et = (
								self.data.germynd.spurnarmyndir.viðtengingarháttur.nútíð.et
							)
						if self.data.germynd.spurnarmyndir.viðtengingarháttur.nútíð.ft is not None:
							isl_so.Germynd_spurnarmyndir_vidtengingarhattur_nutid_ft = (
								self.data.germynd.spurnarmyndir.viðtengingarháttur.nútíð.ft
							)
					if self.data.germynd.spurnarmyndir.viðtengingarháttur.þátíð is not None:
						if self.data.germynd.spurnarmyndir.viðtengingarháttur.þátíð.et is not None:
							isl_so.Germynd_spurnarmyndir_vidtengingarhattur_thatid_et = (
								self.data.germynd.spurnarmyndir.viðtengingarháttur.þátíð.et
							)
						if self.data.germynd.spurnarmyndir.viðtengingarháttur.þátíð.ft is not None:
							isl_so.Germynd_spurnarmyndir_vidtengingarhattur_thatid_ft = (
								self.data.germynd.spurnarmyndir.viðtengingarháttur.þátíð.ft
							)
		if self.data.miðmynd is not None:
			isl_so.Midmynd_Nafnhattur = self.data.miðmynd.nafnháttur
			isl_so.Midmynd_Sagnbot = self.data.miðmynd.sagnbót
			if self.data.miðmynd.boðháttur is not None:
				isl_so.Midmynd_Bodhattur_et = self.data.miðmynd.boðháttur.et
				isl_so.Midmynd_Bodhattur_ft = self.data.miðmynd.boðháttur.ft
			if self.data.miðmynd.persónuleg is not None:
				if self.data.miðmynd.persónuleg.framsöguháttur is not None:
					isl_so.fk_Midmynd_personuleg_framsoguhattur, changes_made = (
						self.write_sagnbeyging_to_db(
							isl_so.fk_Midmynd_personuleg_framsoguhattur,
							self.data.miðmynd.persónuleg.framsöguháttur.dict(),
							changes_made
						)
					)
				if self.data.miðmynd.persónuleg.viðtengingarháttur is not None:
					isl_so.fk_Midmynd_personuleg_vidtengingarhattur, changes_made = (
						self.write_sagnbeyging_to_db(
							isl_so.fk_Midmynd_personuleg_vidtengingarhattur,
							self.data.miðmynd.persónuleg.viðtengingarháttur.dict(),
							changes_made
						)
					)
			if self.data.miðmynd.ópersónuleg is not None:
				if self.data.miðmynd.ópersónuleg.frumlag is not None:
					isl_so.Midmynd_opersonuleg_frumlag = (
						isl.Fall[self.data.miðmynd.ópersónuleg.frumlag.name]
					)
				if self.data.miðmynd.ópersónuleg.framsöguháttur is not None:
					isl_so.fk_Midmynd_opersonuleg_framsoguhattur, changes_made = (
						self.write_sagnbeyging_to_db(
							isl_so.fk_Midmynd_opersonuleg_framsoguhattur,
							self.data.miðmynd.ópersónuleg.framsöguháttur.dict(),
							changes_made
						)
					)
				if self.data.miðmynd.ópersónuleg.viðtengingarháttur is not None:
					isl_so.fk_Midmynd_opersonuleg_vidtengingarhattur, changes_made = (
						self.write_sagnbeyging_to_db(
							isl_so.fk_Midmynd_opersonuleg_vidtengingarhattur,
							self.data.miðmynd.ópersónuleg.viðtengingarháttur.dict(),
							changes_made
						)
					)
			if self.data.miðmynd.spurnarmyndir is not None:
				if self.data.miðmynd.spurnarmyndir.framsöguháttur is not None:
					if self.data.miðmynd.spurnarmyndir.framsöguháttur.nútíð is not None:
						if self.data.miðmynd.spurnarmyndir.framsöguháttur.nútíð.et is not None:
							isl_so.Midmynd_spurnarmyndir_framsoguhattur_nutid_et = (
								self.data.miðmynd.spurnarmyndir.framsöguháttur.nútíð.et
							)
						if self.data.miðmynd.spurnarmyndir.framsöguháttur.nútíð.ft is not None:
							isl_so.Midmynd_spurnarmyndir_framsoguhattur_nutid_ft = (
								self.data.miðmynd.spurnarmyndir.framsöguháttur.nútíð.ft
							)
					if self.data.miðmynd.spurnarmyndir.framsöguháttur.þátíð is not None:
						if self.data.miðmynd.spurnarmyndir.framsöguháttur.þátíð.et is not None:
							isl_so.Midmynd_spurnarmyndir_framsoguhattur_thatid_et = (
								self.data.miðmynd.spurnarmyndir.framsöguháttur.þátíð.et
							)
						if self.data.miðmynd.spurnarmyndir.framsöguháttur.þátíð.ft is not None:
							isl_so.Midmynd_spurnarmyndir_framsoguhattur_thatid_ft = (
								self.data.miðmynd.spurnarmyndir.framsöguháttur.þátíð.ft
							)
				if self.data.miðmynd.spurnarmyndir.viðtengingarháttur is not None:
					if self.data.miðmynd.spurnarmyndir.viðtengingarháttur.nútíð is not None:
						if self.data.miðmynd.spurnarmyndir.viðtengingarháttur.nútíð.et is not None:
							isl_so.Midmynd_spurnarmyndir_vidtengingarhattur_nutid_et = (
								self.data.miðmynd.spurnarmyndir.viðtengingarháttur.nútíð.et
							)
						if self.data.miðmynd.spurnarmyndir.viðtengingarháttur.nútíð.ft is not None:
							isl_so.Midmynd_spurnarmyndir_vidtengingarhattur_nutid_ft = (
								self.data.miðmynd.spurnarmyndir.viðtengingarháttur.nútíð.ft
							)
					if self.data.miðmynd.spurnarmyndir.viðtengingarháttur.þátíð is not None:
						if self.data.miðmynd.spurnarmyndir.viðtengingarháttur.þátíð.et is not None:
							isl_so.Midmynd_spurnarmyndir_vidtengingarhattur_thatid_et = (
								self.data.miðmynd.spurnarmyndir.viðtengingarháttur.þátíð.et
							)
						if self.data.miðmynd.spurnarmyndir.viðtengingarháttur.þátíð.ft is not None:
							isl_so.Midmynd_spurnarmyndir_vidtengingarhattur_thatid_ft = (
								self.data.miðmynd.spurnarmyndir.viðtengingarháttur.þátíð.ft
							)
		if self.data.lýsingarháttur is not None:
			if self.data.lýsingarháttur.nútíðar is not None:
				isl_so.LysingarhatturNutidar = self.data.lýsingarháttur.nútíðar
			if self.data.lýsingarháttur.þátíðar is not None:
				if self.data.lýsingarháttur.þátíðar.sb is not None:
					if self.data.lýsingarháttur.þátíðar.sb.et is not None:
						if self.data.lýsingarháttur.þátíðar.sb.et.kk is not None:
							isl_so.fk_LysingarhatturThatidar_sb_et_kk_id, changes_made = (
								self.write_fallbeyging_to_db(
									isl_so.fk_LysingarhatturThatidar_sb_et_kk_id,
									self.data.lýsingarháttur.þátíðar.sb.et.kk,
									changes_made
								)
							)
						if self.data.lýsingarháttur.þátíðar.sb.et.kvk is not None:
							isl_so.fk_LysingarhatturThatidar_sb_et_kvk_id, changes_made = (
								self.write_fallbeyging_to_db(
									isl_so.fk_LysingarhatturThatidar_sb_et_kvk_id,
									self.data.lýsingarháttur.þátíðar.sb.et.kvk,
									changes_made
								)
							)
						if self.data.lýsingarháttur.þátíðar.sb.et.hk is not None:
							isl_so.fk_LysingarhatturThatidar_sb_et_hk_id, changes_made = (
								self.write_fallbeyging_to_db(
									isl_so.fk_LysingarhatturThatidar_sb_et_hk_id,
									self.data.lýsingarháttur.þátíðar.sb.et.hk,
									changes_made
								)
							)
					if self.data.lýsingarháttur.þátíðar.sb.ft is not None:
						if self.data.lýsingarháttur.þátíðar.sb.ft.kk is not None:
							isl_so.fk_LysingarhatturThatidar_sb_ft_kk_id, changes_made = (
								self.write_fallbeyging_to_db(
									isl_so.fk_LysingarhatturThatidar_sb_ft_kk_id,
									self.data.lýsingarháttur.þátíðar.sb.ft.kk,
									changes_made
								)
							)
						if self.data.lýsingarháttur.þátíðar.sb.ft.kvk is not None:
							isl_so.fk_LysingarhatturThatidar_sb_ft_kvk_id, changes_made = (
								self.write_fallbeyging_to_db(
									isl_so.fk_LysingarhatturThatidar_sb_ft_kvk_id,
									self.data.lýsingarháttur.þátíðar.sb.ft.kvk,
									changes_made
								)
							)
						if self.data.lýsingarháttur.þátíðar.sb.ft.hk is not None:
							isl_so.fk_LysingarhatturThatidar_sb_ft_hk_id, changes_made = (
								self.write_fallbeyging_to_db(
									isl_so.fk_LysingarhatturThatidar_sb_ft_hk_id,
									self.data.lýsingarháttur.þátíðar.sb.ft.hk,
									changes_made
								)
							)
				if self.data.lýsingarháttur.þátíðar.vb is not None:
					if self.data.lýsingarháttur.þátíðar.vb.et is not None:
						if self.data.lýsingarháttur.þátíðar.vb.et.kk is not None:
							isl_so.fk_LysingarhatturThatidar_vb_et_kk_id, changes_made = (
								self.write_fallbeyging_to_db(
									isl_so.fk_LysingarhatturThatidar_vb_et_kk_id,
									self.data.lýsingarháttur.þátíðar.vb.et.kk,
									changes_made
								)
							)
						if self.data.lýsingarháttur.þátíðar.vb.et.kvk is not None:
							isl_so.fk_LysingarhatturThatidar_vb_et_kvk_id, changes_made = (
								self.write_fallbeyging_to_db(
									isl_so.fk_LysingarhatturThatidar_vb_et_kvk_id,
									self.data.lýsingarháttur.þátíðar.vb.et.kvk,
									changes_made
								)
							)
						if self.data.lýsingarháttur.þátíðar.vb.et.hk is not None:
							isl_so.fk_LysingarhatturThatidar_vb_et_hk_id, changes_made = (
								self.write_fallbeyging_to_db(
									isl_so.fk_LysingarhatturThatidar_vb_et_hk_id,
									self.data.lýsingarháttur.þátíðar.vb.et.hk,
									changes_made
								)
							)
					if self.data.lýsingarháttur.þátíðar.vb.ft is not None:
						if self.data.lýsingarháttur.þátíðar.vb.ft.kk is not None:
							isl_so.fk_LysingarhatturThatidar_vb_ft_kk_id, changes_made = (
								self.write_fallbeyging_to_db(
									isl_so.fk_LysingarhatturThatidar_vb_ft_kk_id,
									self.data.lýsingarháttur.þátíðar.vb.ft.kk,
									changes_made
								)
							)
						if self.data.lýsingarháttur.þátíðar.vb.ft.kvk is not None:
							isl_so.fk_LysingarhatturThatidar_vb_ft_kvk_id, changes_made = (
								self.write_fallbeyging_to_db(
									isl_so.fk_LysingarhatturThatidar_vb_ft_kvk_id,
									self.data.lýsingarháttur.þátíðar.vb.ft.kvk,
									changes_made
								)
							)
						if self.data.lýsingarháttur.þátíðar.vb.ft.hk is not None:
							isl_so.fk_LysingarhatturThatidar_vb_ft_hk_id, changes_made = (
								self.write_fallbeyging_to_db(
									isl_so.fk_LysingarhatturThatidar_vb_ft_hk_id,
									self.data.lýsingarháttur.þátíðar.vb.ft.hk,
									changes_made
								)
							)
		if self.data.óskháttur_1p_ft is not None:
			isl_so.Oskhattur_1p_ft = self.data.óskháttur_1p_ft
		if self.data.óskháttur_3p is not None:
			isl_so.Oskhattur_3p = self.data.óskháttur_3p
		changes_made = changes_made or db.Session.is_modified(isl_so)
		if db.Session.is_modified(isl_so):
			db.Session.commit()
		if changes_made is True:
			isl_ord.Edited = datetime.datetime.utcnow()
			db.Session.commit()
		return (isl_ord, changes_made)

	def load_from_db(self, isl_ord: isl.Ord):
		ord_data = super().load_from_db(isl_ord)
		if isl_ord.Samsett is True:
			ord_data = self.derive_beygingar_from_samsett(ord_data)
			self.data = structs.SagnordData(**ord_data)
			kennistr = self.make_kennistrengur()
			if self.data.kennistrengur != kennistr:
				raise Exception('Orð id=%s, kennistrengur mismatch, loaded="%s", derived="%s"' % (
					isl_ord.Ord_id, self.data.kennistrengur, kennistr
				))
			self.data.datahash = self.get_data_hash()
			return
		isl_so = db.Session.query(isl.Sagnord).filter_by(fk_Ord_id=isl_ord.Ord_id).first()
		if (
			isl_so.Germynd_Nafnhattur is not None or
			isl_so.Germynd_Sagnbot is not None or
			isl_so.Germynd_Bodhattur_styfdur is not None or
			isl_so.Germynd_Bodhattur_et is not None or
			isl_so.Germynd_Bodhattur_ft is not None or
			isl_so.fk_Germynd_personuleg_framsoguhattur is not None or
			isl_so.fk_Germynd_personuleg_vidtengingarhattur is not None or
			isl_so.Germynd_opersonuleg_frumlag is not None or
			isl_so.fk_Germynd_opersonuleg_framsoguhattur is not None or
			isl_so.fk_Germynd_opersonuleg_vidtengingarhattur is not None or
			isl_so.Germynd_spurnarmyndir_framsoguhattur_nutid_et is not None or
			isl_so.Germynd_spurnarmyndir_framsoguhattur_nutid_ft is not None or
			isl_so.Germynd_spurnarmyndir_framsoguhattur_thatid_et is not None or
			isl_so.Germynd_spurnarmyndir_framsoguhattur_thatid_ft is not None or
			isl_so.Germynd_spurnarmyndir_vidtengingarhattur_nutid_et is not None or
			isl_so.Germynd_spurnarmyndir_vidtengingarhattur_nutid_ft is not None or
			isl_so.Germynd_spurnarmyndir_vidtengingarhattur_thatid_et is not None or
			isl_so.Germynd_spurnarmyndir_vidtengingarhattur_thatid_ft is not None
		):
			ord_data['germynd'] = {}
			# germynd nafnháttur
			if isl_so.Germynd_Nafnhattur is not None:
				ord_data['germynd']['nafnháttur'] = isl_so.Germynd_Nafnhattur
			# germynd sagnbót
			if isl_so.Germynd_Sagnbot is not None:
				ord_data['germynd']['sagnbót'] = isl_so.Germynd_Sagnbot
			if (
				isl_so.Germynd_Bodhattur_styfdur is not None or
				isl_so.Germynd_Bodhattur_et is not None or
				isl_so.Germynd_Bodhattur_ft is not None
			):
				ord_data['germynd']['boðháttur'] = {}
			if (
				isl_so.fk_Germynd_personuleg_framsoguhattur is not None or
				isl_so.fk_Germynd_personuleg_vidtengingarhattur is not None
			):
				ord_data['germynd']['persónuleg'] = {}
			if (
				isl_so.Germynd_opersonuleg_frumlag is not None or
				isl_so.fk_Germynd_opersonuleg_framsoguhattur is not None or
				isl_so.fk_Germynd_opersonuleg_vidtengingarhattur is not None
			):
				ord_data['germynd']['ópersónuleg'] = {}
			if (
				isl_so.Germynd_spurnarmyndir_framsoguhattur_nutid_et is not None or
				isl_so.Germynd_spurnarmyndir_framsoguhattur_nutid_ft is not None or
				isl_so.Germynd_spurnarmyndir_framsoguhattur_thatid_et is not None or
				isl_so.Germynd_spurnarmyndir_framsoguhattur_thatid_ft is not None or
				isl_so.Germynd_spurnarmyndir_vidtengingarhattur_nutid_et is not None or
				isl_so.Germynd_spurnarmyndir_vidtengingarhattur_nutid_ft is not None or
				isl_so.Germynd_spurnarmyndir_vidtengingarhattur_thatid_et is not None or
				isl_so.Germynd_spurnarmyndir_vidtengingarhattur_thatid_ft is not None
			):
				ord_data['germynd']['spurnarmyndir'] = {}
				if (
					isl_so.Germynd_spurnarmyndir_framsoguhattur_nutid_et is not None or
					isl_so.Germynd_spurnarmyndir_framsoguhattur_nutid_ft is not None or
					isl_so.Germynd_spurnarmyndir_framsoguhattur_thatid_et is not None or
					isl_so.Germynd_spurnarmyndir_framsoguhattur_thatid_ft is not None
				):
					ord_data['germynd']['spurnarmyndir']['framsöguháttur'] = {}
					if (
						isl_so.Germynd_spurnarmyndir_framsoguhattur_nutid_et is not None or
						isl_so.Germynd_spurnarmyndir_framsoguhattur_nutid_ft is not None
					):
						ord_data['germynd']['spurnarmyndir']['framsöguháttur']['nútíð'] = {}
					if (
						isl_so.Germynd_spurnarmyndir_framsoguhattur_thatid_et is not None or
						isl_so.Germynd_spurnarmyndir_framsoguhattur_thatid_ft is not None
					):
						ord_data['germynd']['spurnarmyndir']['framsöguháttur']['þátíð'] = {}
				if (
					isl_so.Germynd_spurnarmyndir_vidtengingarhattur_nutid_et is not None or
					isl_so.Germynd_spurnarmyndir_vidtengingarhattur_nutid_ft is not None or
					isl_so.Germynd_spurnarmyndir_vidtengingarhattur_thatid_et is not None or
					isl_so.Germynd_spurnarmyndir_vidtengingarhattur_thatid_ft is not None
				):
					ord_data['germynd']['spurnarmyndir']['viðtengingarháttur'] = {}
					if (
						isl_so.Germynd_spurnarmyndir_vidtengingarhattur_nutid_et is not None or
						isl_so.Germynd_spurnarmyndir_vidtengingarhattur_nutid_ft is not None
					):
						ord_data['germynd']['spurnarmyndir']['viðtengingarháttur']['nútíð'] = {}
					if (
						isl_so.Germynd_spurnarmyndir_vidtengingarhattur_thatid_et is not None or
						isl_so.Germynd_spurnarmyndir_vidtengingarhattur_thatid_ft is not None
					):
						ord_data['germynd']['spurnarmyndir']['viðtengingarháttur']['þátíð'] = {}
		if (
			isl_so.Midmynd_Nafnhattur is not None or
			isl_so.Midmynd_Sagnbot is not None or
			isl_so.Midmynd_Bodhattur_et is not None or
			isl_so.Midmynd_Bodhattur_ft is not None or
			isl_so.fk_Midmynd_personuleg_framsoguhattur is not None or
			isl_so.fk_Midmynd_personuleg_vidtengingarhattur is not None or
			isl_so.Midmynd_opersonuleg_frumlag is not None or
			isl_so.fk_Midmynd_opersonuleg_framsoguhattur is not None or
			isl_so.fk_Midmynd_opersonuleg_vidtengingarhattur is not None or
			isl_so.Midmynd_spurnarmyndir_framsoguhattur_nutid_et is not None or
			isl_so.Midmynd_spurnarmyndir_framsoguhattur_nutid_ft is not None or
			isl_so.Midmynd_spurnarmyndir_framsoguhattur_thatid_et is not None or
			isl_so.Midmynd_spurnarmyndir_framsoguhattur_thatid_ft is not None or
			isl_so.Midmynd_spurnarmyndir_vidtengingarhattur_nutid_et is not None or
			isl_so.Midmynd_spurnarmyndir_vidtengingarhattur_nutid_ft is not None or
			isl_so.Midmynd_spurnarmyndir_vidtengingarhattur_thatid_et is not None or
			isl_so.Midmynd_spurnarmyndir_vidtengingarhattur_thatid_ft is not None
		):
			ord_data['miðmynd'] = {}
			# miðmynd nafnháttur
			if isl_so.Midmynd_Nafnhattur is not None:
				ord_data['miðmynd']['nafnháttur'] = isl_so.Midmynd_Nafnhattur
			# miðmynd sagnbót
			if isl_so.Midmynd_Sagnbot is not None:
				ord_data['miðmynd']['sagnbót'] = isl_so.Midmynd_Sagnbot
			if (
				isl_so.Midmynd_Bodhattur_et is not None or
				isl_so.Midmynd_Bodhattur_ft is not None
			):
				ord_data['miðmynd']['boðháttur'] = {}
			if (
				isl_so.fk_Midmynd_personuleg_framsoguhattur is not None or
				isl_so.fk_Midmynd_personuleg_vidtengingarhattur is not None
			):
				ord_data['miðmynd']['persónuleg'] = {}
			if (
				isl_so.Midmynd_opersonuleg_frumlag is not None or
				isl_so.fk_Midmynd_opersonuleg_framsoguhattur is not None or
				isl_so.fk_Midmynd_opersonuleg_vidtengingarhattur is not None
			):
				ord_data['miðmynd']['ópersónuleg'] = {}
			if (
				isl_so.Midmynd_spurnarmyndir_framsoguhattur_nutid_et is not None or
				isl_so.Midmynd_spurnarmyndir_framsoguhattur_nutid_ft is not None or
				isl_so.Midmynd_spurnarmyndir_framsoguhattur_thatid_et is not None or
				isl_so.Midmynd_spurnarmyndir_framsoguhattur_thatid_ft is not None or
				isl_so.Midmynd_spurnarmyndir_vidtengingarhattur_nutid_et is not None or
				isl_so.Midmynd_spurnarmyndir_vidtengingarhattur_nutid_ft is not None or
				isl_so.Midmynd_spurnarmyndir_vidtengingarhattur_thatid_et is not None or
				isl_so.Midmynd_spurnarmyndir_vidtengingarhattur_thatid_ft is not None
			):
				ord_data['miðmynd']['spurnarmyndir'] = {}
				if (
					isl_so.Midmynd_spurnarmyndir_framsoguhattur_nutid_et is not None or
					isl_so.Midmynd_spurnarmyndir_framsoguhattur_nutid_ft is not None or
					isl_so.Midmynd_spurnarmyndir_framsoguhattur_thatid_et is not None or
					isl_so.Midmynd_spurnarmyndir_framsoguhattur_thatid_ft is not None
				):
					ord_data['miðmynd']['spurnarmyndir']['framsöguháttur'] = {}
					if (
						isl_so.Midmynd_spurnarmyndir_framsoguhattur_nutid_et is not None or
						isl_so.Midmynd_spurnarmyndir_framsoguhattur_nutid_ft is not None
					):
						ord_data['miðmynd']['spurnarmyndir']['framsöguháttur']['nútíð'] = (
							{}
						)
					if (
						isl_so.Midmynd_spurnarmyndir_framsoguhattur_thatid_et is not None or
						isl_so.Midmynd_spurnarmyndir_framsoguhattur_thatid_ft is not None
					):
						ord_data['miðmynd']['spurnarmyndir']['framsöguháttur']['þátíð'] = (
							{}
						)
				if (
					isl_so.Midmynd_spurnarmyndir_vidtengingarhattur_nutid_et is not None or
					isl_so.Midmynd_spurnarmyndir_vidtengingarhattur_nutid_ft is not None or
					isl_so.Midmynd_spurnarmyndir_vidtengingarhattur_thatid_et is not None or
					isl_so.Midmynd_spurnarmyndir_vidtengingarhattur_thatid_ft is not None
				):
					ord_data['miðmynd']['spurnarmyndir']['viðtengingarháttur'] = {}
					if (
						isl_so.Midmynd_spurnarmyndir_vidtengingarhattur_nutid_et is not None or
						isl_so.Midmynd_spurnarmyndir_vidtengingarhattur_nutid_ft is not None
					):
						ord_data['miðmynd']['spurnarmyndir']['viðtengingarháttur']['nútíð'] = (
							{}
						)
					if (
						isl_so.Midmynd_spurnarmyndir_vidtengingarhattur_thatid_et is not None or
						isl_so.Midmynd_spurnarmyndir_vidtengingarhattur_thatid_ft is not None
					):
						ord_data['miðmynd']['spurnarmyndir']['viðtengingarháttur']['þátíð'] = (
							{}
						)
		if (
			isl_so.LysingarhatturNutidar is not None or
			isl_so.fk_LysingarhatturThatidar_sb_et_kk_id is not None or
			isl_so.fk_LysingarhatturThatidar_sb_et_kvk_id is not None or
			isl_so.fk_LysingarhatturThatidar_sb_et_hk_id is not None or
			isl_so.fk_LysingarhatturThatidar_sb_ft_kk_id is not None or
			isl_so.fk_LysingarhatturThatidar_sb_ft_kvk_id is not None or
			isl_so.fk_LysingarhatturThatidar_sb_ft_hk_id is not None or
			isl_so.fk_LysingarhatturThatidar_vb_et_kk_id is not None or
			isl_so.fk_LysingarhatturThatidar_vb_et_kvk_id is not None or
			isl_so.fk_LysingarhatturThatidar_vb_et_hk_id is not None or
			isl_so.fk_LysingarhatturThatidar_vb_ft_kk_id is not None or
			isl_so.fk_LysingarhatturThatidar_vb_ft_kvk_id is not None or
			isl_so.fk_LysingarhatturThatidar_vb_ft_hk_id is not None
		):
			ord_data['lýsingarháttur'] = {}
			# lýsingarháttur nútíðar
			if isl_so.LysingarhatturNutidar is not None:
				ord_data['lýsingarháttur']['nútíðar'] = isl_so.LysingarhatturNutidar
			if (
				isl_so.fk_LysingarhatturThatidar_sb_et_kk_id is not None or
				isl_so.fk_LysingarhatturThatidar_sb_et_kvk_id is not None or
				isl_so.fk_LysingarhatturThatidar_sb_et_hk_id is not None or
				isl_so.fk_LysingarhatturThatidar_sb_ft_kk_id is not None or
				isl_so.fk_LysingarhatturThatidar_sb_ft_kvk_id is not None or
				isl_so.fk_LysingarhatturThatidar_sb_ft_hk_id is not None or
				isl_so.fk_LysingarhatturThatidar_vb_et_kk_id is not None or
				isl_so.fk_LysingarhatturThatidar_vb_et_kvk_id is not None or
				isl_so.fk_LysingarhatturThatidar_vb_et_hk_id is not None or
				isl_so.fk_LysingarhatturThatidar_vb_ft_kk_id is not None or
				isl_so.fk_LysingarhatturThatidar_vb_ft_kvk_id is not None or
				isl_so.fk_LysingarhatturThatidar_vb_ft_hk_id is not None
			):
				ord_data['lýsingarháttur']['þátíðar'] = {}
				if (
					isl_so.fk_LysingarhatturThatidar_sb_et_kk_id is not None or
					isl_so.fk_LysingarhatturThatidar_sb_et_kvk_id is not None or
					isl_so.fk_LysingarhatturThatidar_sb_et_hk_id is not None or
					isl_so.fk_LysingarhatturThatidar_sb_ft_kk_id is not None or
					isl_so.fk_LysingarhatturThatidar_sb_ft_kvk_id is not None or
					isl_so.fk_LysingarhatturThatidar_sb_ft_hk_id is not None
				):
					ord_data['lýsingarháttur']['þátíðar']['sb'] = {}
					if (
						isl_so.fk_LysingarhatturThatidar_sb_et_kk_id is not None or
						isl_so.fk_LysingarhatturThatidar_sb_et_kvk_id is not None or
						isl_so.fk_LysingarhatturThatidar_sb_et_hk_id is not None
					):
						ord_data['lýsingarháttur']['þátíðar']['sb']['et'] = {}
					if (
						isl_so.fk_LysingarhatturThatidar_sb_ft_kk_id is not None or
						isl_so.fk_LysingarhatturThatidar_sb_ft_kvk_id is not None or
						isl_so.fk_LysingarhatturThatidar_sb_ft_hk_id is not None
					):
						ord_data['lýsingarháttur']['þátíðar']['sb']['ft'] = {}
				if (
					isl_so.fk_LysingarhatturThatidar_vb_et_kk_id is not None or
					isl_so.fk_LysingarhatturThatidar_vb_et_kvk_id is not None or
					isl_so.fk_LysingarhatturThatidar_vb_et_hk_id is not None or
					isl_so.fk_LysingarhatturThatidar_vb_ft_kk_id is not None or
					isl_so.fk_LysingarhatturThatidar_vb_ft_kvk_id is not None or
					isl_so.fk_LysingarhatturThatidar_vb_ft_hk_id is not None
				):
					ord_data['lýsingarháttur']['þátíðar']['vb'] = {}
					if (
						isl_so.fk_LysingarhatturThatidar_vb_et_kk_id is not None or
						isl_so.fk_LysingarhatturThatidar_vb_et_kvk_id is not None or
						isl_so.fk_LysingarhatturThatidar_vb_et_hk_id is not None
					):
						ord_data['lýsingarháttur']['þátíðar']['vb']['et'] = {}
					if (
						isl_so.fk_LysingarhatturThatidar_vb_ft_kk_id is not None or
						isl_so.fk_LysingarhatturThatidar_vb_ft_kvk_id is not None or
						isl_so.fk_LysingarhatturThatidar_vb_ft_hk_id is not None
					):
						ord_data['lýsingarháttur']['þátíðar']['vb']['ft'] = {}
		# germynd boðháttur
		if isl_so.Germynd_Bodhattur_styfdur is not None:
			ord_data['germynd']['boðháttur']['stýfður'] = isl_so.Germynd_Bodhattur_styfdur
			ord_data['germynd']['boðháttur']['et'] = isl_so.Germynd_Bodhattur_et
			ord_data['germynd']['boðháttur']['ft'] = isl_so.Germynd_Bodhattur_ft
		# germynd persónuleg
		if isl_so.fk_Germynd_personuleg_framsoguhattur is not None:
			ord_data['germynd']['persónuleg']['framsöguháttur'] = (
				self.load_sagnbeyging_from_db(isl_so.fk_Germynd_personuleg_framsoguhattur)
			)
		if isl_so.fk_Germynd_personuleg_vidtengingarhattur is not None:
			ord_data['germynd']['persónuleg']['viðtengingarháttur'] = (
				self.load_sagnbeyging_from_db(isl_so.fk_Germynd_personuleg_vidtengingarhattur)
			)
		# germynd ópersónuleg
		if isl_so.Germynd_opersonuleg_frumlag == isl.Fall.Tholfall:
			ord_data['germynd']['ópersónuleg']['frumlag'] = 'þolfall'
		elif isl_so.Germynd_opersonuleg_frumlag == isl.Fall.Thagufall:
			ord_data['germynd']['ópersónuleg']['frumlag'] = 'þágufall'
		elif isl_so.Germynd_opersonuleg_frumlag == isl.Fall.Eignarfall:
			ord_data['germynd']['ópersónuleg']['frumlag'] = 'eignarfall'
		if isl_so.fk_Germynd_opersonuleg_framsoguhattur is not None:
			ord_data['germynd']['ópersónuleg']['framsöguháttur'] = (
				self.load_sagnbeyging_from_db(isl_so.fk_Germynd_opersonuleg_framsoguhattur)
			)
		if isl_so.fk_Germynd_opersonuleg_vidtengingarhattur is not None:
			ord_data['germynd']['ópersónuleg']['viðtengingarháttur'] = (
				self.load_sagnbeyging_from_db(isl_so.fk_Germynd_opersonuleg_vidtengingarhattur)
			)
		# germynd spurnarmyndir
		if isl_so.Germynd_spurnarmyndir_framsoguhattur_nutid_et is not None:
			ord_data['germynd']['spurnarmyndir']['framsöguháttur']['nútíð']['et'] = (
				isl_so.Germynd_spurnarmyndir_framsoguhattur_nutid_et
			)
		if isl_so.Germynd_spurnarmyndir_framsoguhattur_nutid_ft is not None:
			ord_data['germynd']['spurnarmyndir']['framsöguháttur']['nútíð']['ft'] = (
				isl_so.Germynd_spurnarmyndir_framsoguhattur_nutid_ft
			)
		if isl_so.Germynd_spurnarmyndir_framsoguhattur_thatid_et is not None:
			ord_data['germynd']['spurnarmyndir']['framsöguháttur']['þátíð']['et'] = (
				isl_so.Germynd_spurnarmyndir_framsoguhattur_thatid_et
			)
		if isl_so.Germynd_spurnarmyndir_framsoguhattur_thatid_ft is not None:
			ord_data['germynd']['spurnarmyndir']['framsöguháttur']['þátíð']['ft'] = (
				isl_so.Germynd_spurnarmyndir_framsoguhattur_thatid_ft
			)
		#
		if isl_so.Germynd_spurnarmyndir_vidtengingarhattur_nutid_et is not None:
			ord_data['germynd']['spurnarmyndir']['viðtengingarháttur']['nútíð']['et'] = (
				isl_so.Germynd_spurnarmyndir_vidtengingarhattur_nutid_et
			)
		if isl_so.Germynd_spurnarmyndir_vidtengingarhattur_nutid_ft is not None:
			ord_data['germynd']['spurnarmyndir']['viðtengingarháttur']['nútíð']['ft'] = (
				isl_so.Germynd_spurnarmyndir_vidtengingarhattur_nutid_ft
			)
		if isl_so.Germynd_spurnarmyndir_vidtengingarhattur_thatid_et is not None:
			ord_data['germynd']['spurnarmyndir']['viðtengingarháttur']['þátíð']['et'] = (
				isl_so.Germynd_spurnarmyndir_vidtengingarhattur_thatid_et
			)
		if isl_so.Germynd_spurnarmyndir_vidtengingarhattur_thatid_ft is not None:
			ord_data['germynd']['spurnarmyndir']['viðtengingarháttur']['þátíð']['ft'] = (
				isl_so.Germynd_spurnarmyndir_vidtengingarhattur_thatid_ft
			)
		# miðmynd boðháttur
		if isl_so.Midmynd_Bodhattur_et is not None:
			ord_data['miðmynd']['boðháttur']['et'] = isl_so.Midmynd_Bodhattur_et
		if isl_so.Midmynd_Bodhattur_ft is not None:
			ord_data['miðmynd']['boðháttur']['ft'] = isl_so.Midmynd_Bodhattur_ft
		# miðmynd persónuleg
		if isl_so.fk_Midmynd_personuleg_framsoguhattur is not None:
			ord_data['miðmynd']['persónuleg']['framsöguháttur'] = (
				self.load_sagnbeyging_from_db(isl_so.fk_Midmynd_personuleg_framsoguhattur)
			)
		if isl_so.fk_Midmynd_personuleg_vidtengingarhattur is not None:
			ord_data['miðmynd']['persónuleg']['viðtengingarháttur'] = (
				self.load_sagnbeyging_from_db(isl_so.fk_Midmynd_personuleg_vidtengingarhattur)
			)
		# miðmynd ópersónuleg
		if isl_so.Midmynd_opersonuleg_frumlag == isl.Fall.Tholfall:
			ord_data['miðmynd']['ópersónuleg']['frumlag'] = 'þolfall'
		elif isl_so.Midmynd_opersonuleg_frumlag == isl.Fall.Thagufall:
			ord_data['miðmynd']['ópersónuleg']['frumlag'] = 'þágufall'
		elif isl_so.Midmynd_opersonuleg_frumlag == isl.Fall.Eignarfall:
			ord_data['miðmynd']['ópersónuleg']['frumlag'] = 'eignarfall'
		if isl_so.fk_Midmynd_opersonuleg_framsoguhattur is not None:
			ord_data['miðmynd']['ópersónuleg']['framsöguháttur'] = (
				self.load_sagnbeyging_from_db(isl_so.fk_Midmynd_opersonuleg_framsoguhattur)
			)
		if isl_so.fk_Midmynd_opersonuleg_vidtengingarhattur is not None:
			ord_data['miðmynd']['ópersónuleg']['viðtengingarháttur'] = (
				self.load_sagnbeyging_from_db(isl_so.fk_Midmynd_opersonuleg_vidtengingarhattur)
			)
		# miðmynd spurnarmyndir
		if isl_so.Midmynd_spurnarmyndir_framsoguhattur_nutid_et is not None:
			ord_data['miðmynd']['spurnarmyndir']['framsöguháttur']['nútíð']['et'] = (
				isl_so.Midmynd_spurnarmyndir_framsoguhattur_nutid_et
			)
		if isl_so.Midmynd_spurnarmyndir_framsoguhattur_nutid_ft is not None:
			ord_data['miðmynd']['spurnarmyndir']['framsöguháttur']['nútíð']['ft'] = (
				isl_so.Midmynd_spurnarmyndir_framsoguhattur_nutid_ft
			)
		if isl_so.Midmynd_spurnarmyndir_framsoguhattur_thatid_et is not None:
			ord_data['miðmynd']['spurnarmyndir']['framsöguháttur']['þátíð']['et'] = (
				isl_so.Midmynd_spurnarmyndir_framsoguhattur_thatid_et
			)
		if isl_so.Midmynd_spurnarmyndir_framsoguhattur_thatid_ft is not None:
			ord_data['miðmynd']['spurnarmyndir']['framsöguháttur']['þátíð']['ft'] = (
				isl_so.Midmynd_spurnarmyndir_framsoguhattur_thatid_ft
			)
		#
		if isl_so.Midmynd_spurnarmyndir_vidtengingarhattur_nutid_et is not None:
			ord_data['miðmynd']['spurnarmyndir']['viðtengingarháttur']['nútíð']['et'] = (
				isl_so.Midmynd_spurnarmyndir_vidtengingarhattur_nutid_et
			)
		if isl_so.Midmynd_spurnarmyndir_vidtengingarhattur_nutid_ft is not None:
			ord_data['miðmynd']['spurnarmyndir']['viðtengingarháttur']['nútíð']['ft'] = (
				isl_so.Midmynd_spurnarmyndir_vidtengingarhattur_nutid_ft
			)
		if isl_so.Midmynd_spurnarmyndir_vidtengingarhattur_thatid_et is not None:
			ord_data['miðmynd']['spurnarmyndir']['viðtengingarháttur']['þátíð']['et'] = (
				isl_so.Midmynd_spurnarmyndir_vidtengingarhattur_thatid_et
			)
		if isl_so.Midmynd_spurnarmyndir_vidtengingarhattur_thatid_ft is not None:
			ord_data['miðmynd']['spurnarmyndir']['viðtengingarháttur']['þátíð']['ft'] = (
				isl_so.Midmynd_spurnarmyndir_vidtengingarhattur_thatid_ft
			)
		# lýsingarháttur þátíðar
		if isl_so.fk_LysingarhatturThatidar_sb_et_kk_id is not None:
			ord_data['lýsingarháttur']['þátíðar']['sb']['et']['kk'] = (
				self.load_fallbeyging_from_db(isl_so.fk_LysingarhatturThatidar_sb_et_kk_id)
			)
		if isl_so.fk_LysingarhatturThatidar_sb_et_kvk_id is not None:
			ord_data['lýsingarháttur']['þátíðar']['sb']['et']['kvk'] = (
				self.load_fallbeyging_from_db(isl_so.fk_LysingarhatturThatidar_sb_et_kvk_id)
			)
		if isl_so.fk_LysingarhatturThatidar_sb_et_hk_id is not None:
			ord_data['lýsingarháttur']['þátíðar']['sb']['et']['hk'] = (
				self.load_fallbeyging_from_db(isl_so.fk_LysingarhatturThatidar_sb_et_hk_id)
			)
		if isl_so.fk_LysingarhatturThatidar_sb_ft_kk_id is not None:
			ord_data['lýsingarháttur']['þátíðar']['sb']['ft']['kk'] = (
				self.load_fallbeyging_from_db(isl_so.fk_LysingarhatturThatidar_sb_ft_kk_id)
			)
		if isl_so.fk_LysingarhatturThatidar_sb_ft_kvk_id is not None:
			ord_data['lýsingarháttur']['þátíðar']['sb']['ft']['kvk'] = (
				self.load_fallbeyging_from_db(isl_so.fk_LysingarhatturThatidar_sb_ft_kvk_id)
			)
		if isl_so.fk_LysingarhatturThatidar_sb_ft_hk_id is not None:
			ord_data['lýsingarháttur']['þátíðar']['sb']['ft']['hk'] = (
				self.load_fallbeyging_from_db(isl_so.fk_LysingarhatturThatidar_sb_ft_hk_id)
			)
		#
		if isl_so.fk_LysingarhatturThatidar_vb_et_kk_id is not None:
			ord_data['lýsingarháttur']['þátíðar']['vb']['et']['kk'] = (
				self.load_fallbeyging_from_db(isl_so.fk_LysingarhatturThatidar_vb_et_kk_id)
			)
		if isl_so.fk_LysingarhatturThatidar_vb_et_kvk_id is not None:
			ord_data['lýsingarháttur']['þátíðar']['vb']['et']['kvk'] = (
				self.load_fallbeyging_from_db(isl_so.fk_LysingarhatturThatidar_vb_et_kvk_id)
			)
		if isl_so.fk_LysingarhatturThatidar_vb_et_hk_id is not None:
			ord_data['lýsingarháttur']['þátíðar']['vb']['et']['hk'] = (
				self.load_fallbeyging_from_db(isl_so.fk_LysingarhatturThatidar_vb_et_hk_id)
			)
		if isl_so.fk_LysingarhatturThatidar_vb_ft_kk_id is not None:
			ord_data['lýsingarháttur']['þátíðar']['vb']['ft']['kk'] = (
				self.load_fallbeyging_from_db(isl_so.fk_LysingarhatturThatidar_vb_ft_kk_id)
			)
		if isl_so.fk_LysingarhatturThatidar_vb_ft_kvk_id is not None:
			ord_data['lýsingarháttur']['þátíðar']['vb']['ft']['kvk'] = (
				self.load_fallbeyging_from_db(isl_so.fk_LysingarhatturThatidar_vb_ft_kvk_id)
			)
		if isl_so.fk_LysingarhatturThatidar_vb_ft_hk_id is not None:
			ord_data['lýsingarháttur']['þátíðar']['vb']['ft']['hk'] = (
				self.load_fallbeyging_from_db(isl_so.fk_LysingarhatturThatidar_vb_ft_hk_id)
			)
		if isl_so.Oskhattur_1p_ft is not None:
			ord_data['óskháttur_1p_ft'] = isl_so.Oskhattur_1p_ft
		if isl_so.Oskhattur_1p_ft is not None:
			ord_data['óskháttur_3p'] = isl_so.Oskhattur_3p
		if isl_ord.OsjalfstaedurOrdhluti is True:
			ord_data['ósjálfstætt'] = True
		self.data = structs.SagnordData(**ord_data)
		kennistr = self.make_kennistrengur()
		if self.data.kennistrengur != kennistr:
			raise Exception('Orð id=%s, kennistrengur mismatch, loaded="%s", derived="%s"' % (
				isl_ord.Ord_id, self.data.kennistrengur, kennistr
			))
		self.data.datahash = self.get_data_hash()


class Greinir(Ord):
	"""
	Greinir handler
	"""

	group = structs.Ordflokkar.Greinir
	data: Optional[structs.GreinirData] = None

	def make_filename(self):
		return os.path.join(
			self.data.flokkur.get_folder(), '%s%s.json' % (self.data.orð, self._fno_extras())
		)

	def make_kennistrengur(self):
		return '%s-%s%s' % (
			self.data.flokkur.get_abbreviation(), self.data.orð, self._fno_extras()
		)

	def write_to_db(self) -> tuple[isl.Ord, bool]:
		isl_ord, changes_made = super().write_to_db()
		if self.data.samsett is not None:
			return (isl_ord, changes_made)
		isl_gr = db.Session.query(isl.Greinir).filter_by(fk_Ord_id=isl_ord.Ord_id).first()
		if isl_gr is None:
			isl_gr = isl.Greinir(fk_Ord_id=isl_ord.Ord_id)
			db.Session.add(isl_gr)
			db.Session.commit()
			changes_made = True
		isl_gr.fk_et_kk_Fallbeyging_id, changes_made = self.write_fallbeyging_to_db(
			isl_gr.fk_et_kk_Fallbeyging_id,
			self.data.et.kk,
			changes_made
		)
		isl_gr.fk_et_kvk_Fallbeyging_id, changes_made = self.write_fallbeyging_to_db(
			isl_gr.fk_et_kvk_Fallbeyging_id,
			self.data.et.kvk,
			changes_made
		)
		isl_gr.fk_et_hk_Fallbeyging_id, changes_made = self.write_fallbeyging_to_db(
			isl_gr.fk_et_hk_Fallbeyging_id,
			self.data.et.hk,
			changes_made
		)
		isl_gr.fk_ft_kk_Fallbeyging_id, changes_made = self.write_fallbeyging_to_db(
			isl_gr.fk_ft_kk_Fallbeyging_id,
			self.data.ft.kk,
			changes_made
		)
		isl_gr.fk_ft_kvk_Fallbeyging_id, changes_made = self.write_fallbeyging_to_db(
			isl_gr.fk_ft_kvk_Fallbeyging_id,
			self.data.ft.kvk,
			changes_made
		)
		isl_gr.fk_ft_hk_Fallbeyging_id, changes_made = self.write_fallbeyging_to_db(
			isl_gr.fk_ft_hk_Fallbeyging_id,
			self.data.ft.hk,
			changes_made
		)
		changes_made = changes_made or db.Session.is_modified(isl_gr)
		if db.Session.is_modified(isl_gr):
			db.Session.commit()
		if changes_made is True:
			isl_ord.Edited = datetime.datetime.utcnow()
			db.Session.commit()
		return (isl_ord, changes_made)

	def load_from_db(self, isl_ord: isl.Ord):
		ord_data = super().load_from_db(isl_ord)
		if isl_ord.Samsett is True:
			ord_data = self.derive_beygingar_from_samsett(ord_data)
		else:
			isl_gr = db.Session.query(isl.Greinir).filter_by(fk_Ord_id=isl_ord.Ord_id).first()
			# et
			if (
				isl_gr.fk_et_kk_Fallbeyging_id is not None or
				isl_gr.fk_et_kvk_Fallbeyging_id is not None or
				isl_gr.fk_et_hk_Fallbeyging_id is not None
			):
				ord_data['et'] = {}
			# ft
			if (
				isl_gr.fk_ft_kk_Fallbeyging_id is not None or
				isl_gr.fk_ft_kvk_Fallbeyging_id is not None or
				isl_gr.fk_ft_hk_Fallbeyging_id is not None
			):
				ord_data['ft'] = {}
			# et
			if isl_gr.fk_et_kk_Fallbeyging_id is not None:
				ord_data['et']['kk'] = (
					self.load_fallbeyging_from_db(isl_gr.fk_et_kk_Fallbeyging_id)
				)
			if isl_gr.fk_et_kvk_Fallbeyging_id is not None:
				ord_data['et']['kvk'] = (
					self.load_fallbeyging_from_db(isl_gr.fk_et_kvk_Fallbeyging_id)
				)
			if isl_gr.fk_et_hk_Fallbeyging_id is not None:
				ord_data['et']['hk'] = (
					self.load_fallbeyging_from_db(isl_gr.fk_et_hk_Fallbeyging_id)
				)
			# ft
			if isl_gr.fk_ft_kk_Fallbeyging_id is not None:
				ord_data['ft']['kk'] = (
					self.load_fallbeyging_from_db(isl_gr.fk_ft_kk_Fallbeyging_id)
				)
			if isl_gr.fk_ft_kvk_Fallbeyging_id is not None:
				ord_data['ft']['kvk'] = (
					self.load_fallbeyging_from_db(isl_gr.fk_ft_kvk_Fallbeyging_id)
				)
			if isl_gr.fk_ft_hk_Fallbeyging_id is not None:
				ord_data['ft']['hk'] = (
					self.load_fallbeyging_from_db(isl_gr.fk_ft_hk_Fallbeyging_id)
				)
		self.data = structs.GreinirData(**ord_data)
		kennistr = self.make_kennistrengur()
		if self.data.kennistrengur != kennistr:
			raise Exception('Orð id=%s, kennistrengur mismatch, loaded="%s", derived="%s"' % (
				isl_ord.Ord_id, self.data.kennistrengur, kennistr
			))
		self.data.datahash = self.get_data_hash()


class Fornafn(Ord):
	"""
	Fornafn handler
	"""

	group = structs.Ordflokkar.Fornafn
	data: Optional[structs.FornafnData] = None

	def make_filename(self):
		return os.path.join(
			self.data.undirflokkur.get_folder(), '%s%s.json' % (self.data.orð, self._fno_extras())
		)

	def make_kennistrengur(self):
		return '%s-%s%s' % (
			self.data.undirflokkur.get_abbreviation(), self.data.orð, self._fno_extras()
		)

	def write_to_db(self) -> tuple[isl.Ord, bool]:
		isl_ord, changes_made = super().write_to_db()
		isl_fn = db.Session.query(isl.Fornafn).filter_by(fk_Ord_id=isl_ord.Ord_id).first()
		if isl_fn is None:
			isl_fn = isl.Fornafn(
				fk_Ord_id=isl_ord.Ord_id,
				Undirflokkur=isl.Fornafnaflokkar[self.data.undirflokkur.name]
			)
			db.Session.add(isl_fn)
			db.Session.commit()
			changes_made = True
		if self.data.persóna is not None:
			isl_fn.Persona = isl.Persona[self.data.persóna.name]
		if self.data.kyn is not None:
			isl_fn.Kyn = isl.Kyn[self.data.kyn.name]
		if self.data.samsett is not None:
			changes_made = changes_made or db.Session.is_modified(isl_fn)
			if changes_made is True:
				isl_ord.Edited = datetime.datetime.utcnow()
				db.Session.commit()
			return (isl_ord, changes_made)
		if isinstance(self.data.et, list):
			isl_fn.fk_et_Fallbeyging_id, changes_made = self.write_fallbeyging_to_db(
				isl_fn.fk_et_Fallbeyging_id,
				self.data.et,
				changes_made
			)
		if isinstance(self.data.ft, list):
			isl_fn.fk_ft_Fallbeyging_id, changes_made = self.write_fallbeyging_to_db(
				isl_fn.fk_ft_Fallbeyging_id,
				self.data.ft,
				changes_made
			)
		if self.data.et is not None and not isinstance(self.data.et, list):
			if self.data.et.kk is not None:
				isl_fn.fk_et_kk_Fallbeyging_id, changes_made = self.write_fallbeyging_to_db(
					isl_fn.fk_et_kk_Fallbeyging_id,
					self.data.et.kk,
					changes_made
				)
			if self.data.et.kvk is not None:
				isl_fn.fk_et_kvk_Fallbeyging_id, changes_made = self.write_fallbeyging_to_db(
					isl_fn.fk_et_kvk_Fallbeyging_id,
					self.data.et.kvk,
					changes_made
				)
			if self.data.et.hk is not None:
				isl_fn.fk_et_hk_Fallbeyging_id, changes_made = self.write_fallbeyging_to_db(
					isl_fn.fk_et_hk_Fallbeyging_id,
					self.data.et.hk,
					changes_made
				)
		if self.data.ft is not None and not isinstance(self.data.ft, list):
			if self.data.ft.kk is not None:
				isl_fn.fk_ft_kk_Fallbeyging_id, changes_made = self.write_fallbeyging_to_db(
					isl_fn.fk_ft_kk_Fallbeyging_id,
					self.data.ft.kk,
					changes_made
				)
			if self.data.ft.kvk is not None:
				isl_fn.fk_ft_kvk_Fallbeyging_id, changes_made = self.write_fallbeyging_to_db(
					isl_fn.fk_ft_kvk_Fallbeyging_id,
					self.data.ft.kvk,
					changes_made
				)
			if self.data.ft.hk is not None:
				isl_fn.fk_ft_hk_Fallbeyging_id, changes_made = self.write_fallbeyging_to_db(
					isl_fn.fk_ft_hk_Fallbeyging_id,
					self.data.ft.hk,
					changes_made
				)
		changes_made = changes_made or db.Session.is_modified(isl_fn)
		if db.Session.is_modified(isl_fn):
			db.Session.commit()
		if changes_made is True:
			isl_ord.Edited = datetime.datetime.utcnow()
			db.Session.commit()
		return (isl_ord, changes_made)

	@classmethod
	def get_files_list_sorted(cls):
		kjarna_ord_files_list = []
		samsett_ord_files_list = []
		for ufl in structs.Fornafnaflokkar:
			kja_list, sam_list = super().get_files_list_sorted(override_dir_rel=ufl.get_folder())
			kjarna_ord_files_list += kja_list
			samsett_ord_files_list += sam_list
		return (kjarna_ord_files_list, samsett_ord_files_list)

	def load_from_db(self, isl_ord: isl.Ord):
		ord_data = super().load_from_db(isl_ord)
		isl_fn = db.Session.query(isl.Fornafn).filter_by(fk_Ord_id=isl_ord.Ord_id).first()
		ord_data['undirflokkur'] = structs.Fornafnaflokkar[isl_fn.Undirflokkur.name].value
		if isl_fn.Persona is not None:
			ord_data['persóna'] = structs.Persona[isl_fn.Persona.name].value
		if isl_fn.Kyn is not None:
			ord_data['kyn'] = structs.Kyn[isl_fn.Kyn.name].value
		if isl_ord.Samsett is True:
			ord_data = self.derive_beygingar_from_samsett(ord_data)
		else:
			# et
			if isl_fn.fk_et_Fallbeyging_id is not None:
				ord_data['et'] = self.load_fallbeyging_from_db(isl_fn.fk_et_Fallbeyging_id)
				if (
					isl_fn.fk_et_kk_Fallbeyging_id is not None or
					isl_fn.fk_et_kvk_Fallbeyging_id is not None or
					isl_fn.fk_et_hk_Fallbeyging_id is not None
				):
					raise Exception(
						'eintala fallbeyging should not be set for both genderless and gendered'
					)
			elif (
				isl_fn.fk_et_kk_Fallbeyging_id is not None or
				isl_fn.fk_et_kvk_Fallbeyging_id is not None or
				isl_fn.fk_et_hk_Fallbeyging_id is not None
			):
				ord_data['et'] = {}
			# ft
			if isl_fn.fk_ft_Fallbeyging_id is not None:
				ord_data['ft'] = self.load_fallbeyging_from_db(isl_fn.fk_ft_Fallbeyging_id)
				if (
					isl_fn.fk_ft_kk_Fallbeyging_id is not None or
					isl_fn.fk_ft_kvk_Fallbeyging_id is not None or
					isl_fn.fk_ft_hk_Fallbeyging_id is not None
				):
					raise Exception(
						'eintala fallbeyging should not be set for both genderless and gendered'
					)
			elif (
				isl_fn.fk_ft_kk_Fallbeyging_id is not None or
				isl_fn.fk_ft_kvk_Fallbeyging_id is not None or
				isl_fn.fk_ft_hk_Fallbeyging_id is not None
			):
				ord_data['ft'] = {}
			# et
			if isl_fn.fk_et_kk_Fallbeyging_id is not None:
				ord_data['et']['kk'] = (
					self.load_fallbeyging_from_db(isl_fn.fk_et_kk_Fallbeyging_id)
				)
			if isl_fn.fk_et_kvk_Fallbeyging_id is not None:
				ord_data['et']['kvk'] = (
					self.load_fallbeyging_from_db(isl_fn.fk_et_kvk_Fallbeyging_id)
				)
			if isl_fn.fk_et_hk_Fallbeyging_id is not None:
				ord_data['et']['hk'] = (
					self.load_fallbeyging_from_db(isl_fn.fk_et_hk_Fallbeyging_id)
				)
			# ft
			if isl_fn.fk_ft_kk_Fallbeyging_id is not None:
				ord_data['ft']['kk'] = (
					self.load_fallbeyging_from_db(isl_fn.fk_ft_kk_Fallbeyging_id)
				)
			if isl_fn.fk_ft_kvk_Fallbeyging_id is not None:
				ord_data['ft']['kvk'] = (
					self.load_fallbeyging_from_db(isl_fn.fk_ft_kvk_Fallbeyging_id)
				)
			if isl_fn.fk_ft_hk_Fallbeyging_id is not None:
				ord_data['ft']['hk'] = (
					self.load_fallbeyging_from_db(isl_fn.fk_ft_hk_Fallbeyging_id)
				)
		self.data = structs.FornafnData(**ord_data)
		kennistr = self.make_kennistrengur()
		if self.data.kennistrengur != kennistr:
			raise Exception('Orð id=%s, kennistrengur mismatch, loaded="%s", derived="%s"' % (
				isl_ord.Ord_id, self.data.kennistrengur, kennistr
			))
		self.data.datahash = self.get_data_hash()


class Toluord(Ord):
	"""
	Töluorð handler
	"""

	group = structs.Ordflokkar.Toluord
	data: Optional[structs.FjoldatalaData | structs.RadtalaData] = None

	def make_filename(self):
		return os.path.join(
			self.data.undirflokkur.get_folder(), '%s%s.json' % (self.data.orð, self._fno_extras())
		)

	def make_kennistrengur(self):
		return '%s-%s%s' % (
			self.data.undirflokkur.get_abbreviation(), self.data.orð, self._fno_extras()
		)

	def write_to_db(self) -> tuple[isl.Ord, bool]:
		match self.data.undirflokkur:
			case structs.Toluordaflokkar.Fjoldatala:
				return self.write_fjoldatala_to_db()
			case structs.Toluordaflokkar.Radtala:
				return self.write_radtala_to_db()
		raise Exception('Should not happen.')

	def write_fjoldatala_to_db(self) -> tuple[isl.Ord, bool]:
		isl_ord, changes_made = super().write_to_db()
		isl_ft = db.Session.query(isl.Fjoldatala).filter_by(fk_Ord_id=isl_ord.Ord_id).first()
		if isl_ft is None:
			isl_ft = isl.Fjoldatala(fk_Ord_id=isl_ord.Ord_id)
			db.Session.add(isl_ft)
			db.Session.commit()
			changes_made = True
		isl_ft.Gildi = self.data.tölugildi
		if self.data.samsett is not None:
			changes_made = changes_made or db.Session.is_modified(isl_ft)
			if changes_made is True:
				isl_ord.Edited = datetime.datetime.utcnow()
				db.Session.commit()
			return (isl_ord, changes_made)
		if self.data.et is not None:
			if self.data.et.kk is not None:
				isl_ft.fk_et_kk_Fallbeyging_id, changes_made = self.write_fallbeyging_to_db(
					isl_ft.fk_et_kk_Fallbeyging_id, self.data.et.kk, changes_made
				)
			if self.data.et.kvk is not None:
				isl_ft.fk_et_kvk_Fallbeyging_id, changes_made = self.write_fallbeyging_to_db(
					isl_ft.fk_et_kvk_Fallbeyging_id, self.data.et.kvk, changes_made
				)
			if self.data.et.hk is not None:
				isl_ft.fk_et_hk_Fallbeyging_id, changes_made = self.write_fallbeyging_to_db(
					isl_ft.fk_et_hk_Fallbeyging_id, self.data.et.hk, changes_made
				)
		if self.data.ft is not None:
			if self.data.ft.kk is not None:
				isl_ft.fk_ft_kk_Fallbeyging_id, changes_made = self.write_fallbeyging_to_db(
					isl_ft.fk_ft_kk_Fallbeyging_id, self.data.ft.kk, changes_made
				)
			if self.data.ft.kvk is not None:
				isl_ft.fk_ft_kvk_Fallbeyging_id, changes_made = self.write_fallbeyging_to_db(
					isl_ft.fk_ft_kvk_Fallbeyging_id, self.data.ft.kvk, changes_made
				)
			if self.data.ft.hk is not None:
				isl_ft.fk_ft_hk_Fallbeyging_id, changes_made = self.write_fallbeyging_to_db(
					isl_ft.fk_ft_hk_Fallbeyging_id, self.data.ft.hk, changes_made
				)
		changes_made = changes_made or db.Session.is_modified(isl_ft)
		if db.Session.is_modified(isl_ft):
			db.Session.commit()
		if changes_made is True:
			isl_ord.Edited = datetime.datetime.utcnow()
			db.Session.commit()
		return (isl_ord, changes_made)

	def write_radtala_to_db(self) -> tuple[isl.Ord, bool]:
		isl_ord, changes_made = super().write_to_db()
		isl_rt = db.Session.query(isl.Radtala).filter_by(fk_Ord_id=isl_ord.Ord_id).first()
		if isl_rt is None:
			isl_rt = isl.Radtala(fk_Ord_id=isl_ord.Ord_id)
			db.Session.add(isl_rt)
			db.Session.commit()
			changes_made = True
		isl_rt.Gildi = self.data.tölugildi
		if self.data.samsett is not None:
			changes_made = changes_made or db.Session.is_modified(isl_rt)
			if changes_made is True:
				isl_ord.Edited = datetime.datetime.utcnow()
				db.Session.commit()
			return (isl_ord, changes_made)
		if self.data.sb is not None:
			if self.data.sb.et is not None:
				if self.data.sb.et.kk is not None:
					isl_rt.fk_sb_et_kk_Fallbeyging_id, changes_made = self.write_fallbeyging_to_db(
						isl_rt.fk_sb_et_kk_Fallbeyging_id, self.data.sb.et.kk, changes_made
					)
				if self.data.sb.et.kvk is not None:
					isl_rt.fk_sb_et_kvk_Fallbeyging_id, changes_made = self.write_fallbeyging_to_db(
						isl_rt.fk_sb_et_kvk_Fallbeyging_id, self.data.sb.et.kvk, changes_made
					)
				if self.data.sb.et.hk is not None:
					isl_rt.fk_sb_et_hk_Fallbeyging_id, changes_made = self.write_fallbeyging_to_db(
						isl_rt.fk_sb_et_hk_Fallbeyging_id, self.data.sb.et.hk, changes_made
					)
			if self.data.sb.ft is not None:
				if self.data.sb.ft.kk is not None:
					isl_rt.fk_sb_ft_kk_Fallbeyging_id, changes_made = self.write_fallbeyging_to_db(
						isl_rt.fk_sb_ft_kk_Fallbeyging_id, self.data.sb.ft.kk, changes_made
					)
				if self.data.sb.ft.kvk is not None:
					isl_rt.fk_sb_ft_kvk_Fallbeyging_id, changes_made = self.write_fallbeyging_to_db(
						isl_rt.fk_sb_ft_kvk_Fallbeyging_id, self.data.sb.ft.kvk, changes_made
					)
				if self.data.sb.ft.hk is not None:
					isl_rt.fk_sb_ft_hk_Fallbeyging_id, changes_made = self.write_fallbeyging_to_db(
						isl_rt.fk_sb_ft_hk_Fallbeyging_id, self.data.sb.ft.hk, changes_made
					)
		if self.data.vb is not None:
			if self.data.vb.et is not None:
				if self.data.vb.et.kk is not None:
					isl_rt.fk_vb_et_kk_Fallbeyging_id, changes_made = self.write_fallbeyging_to_db(
						isl_rt.fk_vb_et_kk_Fallbeyging_id, self.data.vb.et.kk, changes_made
					)
				if self.data.vb.et.kvk is not None:
					isl_rt.fk_vb_et_kvk_Fallbeyging_id, changes_made = self.write_fallbeyging_to_db(
						isl_rt.fk_vb_et_kvk_Fallbeyging_id, self.data.vb.et.kvk, changes_made
					)
				if self.data.vb.et.hk is not None:
					isl_rt.fk_vb_et_hk_Fallbeyging_id, changes_made = self.write_fallbeyging_to_db(
						isl_rt.fk_vb_et_hk_Fallbeyging_id, self.data.vb.et.hk, changes_made
					)
			if self.data.vb.ft is not None:
				if self.data.vb.ft.kk is not None:
					isl_rt.fk_vb_ft_kk_Fallbeyging_id, changes_made = self.write_fallbeyging_to_db(
						isl_rt.fk_vb_ft_kk_Fallbeyging_id, self.data.vb.ft.kk, changes_made
					)
				if self.data.vb.ft.kvk is not None:
					isl_rt.fk_vb_ft_kvk_Fallbeyging_id, changes_made = self.write_fallbeyging_to_db(
						isl_rt.fk_vb_ft_kvk_Fallbeyging_id, self.data.vb.ft.kvk, changes_made
					)
				if self.data.vb.ft.hk is not None:
					isl_rt.fk_vb_ft_hk_Fallbeyging_id, changes_made = self.write_fallbeyging_to_db(
						isl_rt.fk_vb_ft_hk_Fallbeyging_id, self.data.vb.ft.hk, changes_made
					)
		changes_made = changes_made or db.Session.is_modified(isl_rt)
		if db.Session.is_modified(isl_rt):
			db.Session.commit()
		if changes_made is True:
			isl_ord.Edited = datetime.datetime.utcnow()
			db.Session.commit()
		return (isl_ord, changes_made)

	@classmethod
	def get_files_list_sorted(cls):
		kjarna_ord_files_list = []
		samsett_ord_files_list = []
		for ufl in structs.Toluordaflokkar:
			kja_list, sam_list = super().get_files_list_sorted(override_dir_rel=ufl.get_folder())
			kjarna_ord_files_list += kja_list
			samsett_ord_files_list += sam_list
		return (kjarna_ord_files_list, samsett_ord_files_list)

	def load_from_db(self, isl_ord: isl.Ord):
		match isl_ord.Ordflokkur:
			case isl.Ordflokkar.Fjoldatala:
				self.load_fjoldatala_from_db(isl_ord)
			case isl.Ordflokkar.Radtala:
				self.load_radtala_from_db(isl_ord)
			case _:
				raise Exception('Should not happen.')
		kennistr = self.make_kennistrengur()
		if self.data.kennistrengur != kennistr:
			raise Exception(
				'Orð id=%s, loaded from db, kennistrengur mismatch, loaded="%s", derived="%s"' % (
					isl_ord.Ord_id, self.data.kennistrengur, kennistr
				)
			)
		self.data.datahash = self.get_data_hash()

	def load_fjoldatala_from_db(self, isl_ord: isl.Ord):
		ord_data = super().load_from_db(isl_ord)
		isl_ft = db.Session.query(isl.Fjoldatala).filter_by(fk_Ord_id=isl_ord.Ord_id).first()
		if isl_ft.Gildi is not None:
			ord_data['tölugildi'] = isl_ft.Gildi
		if isl_ord.Samsett is True:
			ord_data = self.derive_beygingar_from_samsett(ord_data)
		else:
			if (
				isl_ft.fk_et_kk_Fallbeyging_id is not None or
				isl_ft.fk_et_kvk_Fallbeyging_id is not None or
				isl_ft.fk_et_hk_Fallbeyging_id is not None
			):
				ord_data['et'] = {}
			if (
				isl_ft.fk_ft_kk_Fallbeyging_id is not None or
				isl_ft.fk_ft_kvk_Fallbeyging_id is not None or
				isl_ft.fk_ft_hk_Fallbeyging_id is not None
			):
				ord_data['ft'] = {}
			# et
			if isl_ft.fk_et_kk_Fallbeyging_id is not None:
				ord_data['et']['kk'] = self.load_fallbeyging_from_db(isl_ft.fk_et_kk_Fallbeyging_id)
			if isl_ft.fk_et_kvk_Fallbeyging_id is not None:
				ord_data['et']['kvk'] = self.load_fallbeyging_from_db(
					isl_ft.fk_et_kvk_Fallbeyging_id
				)
			if isl_ft.fk_et_hk_Fallbeyging_id is not None:
				ord_data['et']['hk'] = self.load_fallbeyging_from_db(isl_ft.fk_et_hk_Fallbeyging_id)
			# ft
			if isl_ft.fk_ft_kk_Fallbeyging_id is not None:
				ord_data['ft']['kk'] = self.load_fallbeyging_from_db(isl_ft.fk_ft_kk_Fallbeyging_id)
			if isl_ft.fk_ft_kvk_Fallbeyging_id is not None:
				ord_data['ft']['kvk'] = self.load_fallbeyging_from_db(
					isl_ft.fk_ft_kvk_Fallbeyging_id
				)
			if isl_ft.fk_ft_hk_Fallbeyging_id is not None:
				ord_data['ft']['hk'] = self.load_fallbeyging_from_db(isl_ft.fk_ft_hk_Fallbeyging_id)
			if 'et' not in ord_data and 'ft' not in ord_data:
				if 'óbeygjanlegt' not in ord_data or ord_data['óbeygjanlegt'] is False:
					raise Exception('fjöldatala with no beyging should be flagged óbeygjanlegt')
		self.data = structs.FjoldatalaData(**ord_data)

	def load_radtala_from_db(self, isl_ord: isl.Ord):
		ord_data = super().load_from_db(isl_ord)
		isl_rt = db.Session.query(isl.Radtala).filter_by(fk_Ord_id=isl_ord.Ord_id).first()
		if isl_rt.Gildi is not None:
			ord_data['tölugildi'] = isl_rt.Gildi
		if isl_ord.Samsett is True:
			ord_data = self.derive_beygingar_from_samsett(ord_data)
		else:
			if (
				isl_rt.fk_sb_et_kk_Fallbeyging_id is not None or
				isl_rt.fk_sb_et_kvk_Fallbeyging_id is not None or
				isl_rt.fk_sb_et_hk_Fallbeyging_id is not None or
				isl_rt.fk_sb_ft_kk_Fallbeyging_id is not None or
				isl_rt.fk_sb_ft_kvk_Fallbeyging_id is not None or
				isl_rt.fk_sb_ft_hk_Fallbeyging_id is not None
			):
				ord_data['sb'] = {}
			if (
				isl_rt.fk_sb_et_kk_Fallbeyging_id is not None or
				isl_rt.fk_sb_et_kvk_Fallbeyging_id is not None or
				isl_rt.fk_sb_et_hk_Fallbeyging_id is not None
			):
				ord_data['sb']['et'] = {}
			if (
				isl_rt.fk_sb_ft_kk_Fallbeyging_id is not None or
				isl_rt.fk_sb_ft_kvk_Fallbeyging_id is not None or
				isl_rt.fk_sb_ft_hk_Fallbeyging_id is not None
			):
				ord_data['sb']['ft'] = {}
			if (
				isl_rt.fk_vb_et_kk_Fallbeyging_id is not None or
				isl_rt.fk_vb_et_kvk_Fallbeyging_id is not None or
				isl_rt.fk_vb_et_hk_Fallbeyging_id is not None or
				isl_rt.fk_vb_ft_kk_Fallbeyging_id is not None or
				isl_rt.fk_vb_ft_kvk_Fallbeyging_id is not None or
				isl_rt.fk_vb_ft_hk_Fallbeyging_id is not None
			):
				ord_data['vb'] = {}
			if (
				isl_rt.fk_vb_et_kk_Fallbeyging_id is not None or
				isl_rt.fk_vb_et_kvk_Fallbeyging_id is not None or
				isl_rt.fk_vb_et_hk_Fallbeyging_id is not None
			):
				ord_data['vb']['et'] = {}
			if (
				isl_rt.fk_vb_ft_kk_Fallbeyging_id is not None or
				isl_rt.fk_vb_ft_kvk_Fallbeyging_id is not None or
				isl_rt.fk_vb_ft_hk_Fallbeyging_id is not None
			):
				ord_data['vb']['ft'] = {}
			# sb et
			if isl_rt.fk_sb_et_kk_Fallbeyging_id is not None:
				ord_data['sb']['et']['kk'] = (
					self.load_fallbeyging_from_db(isl_rt.fk_sb_et_kk_Fallbeyging_id)
				)
			if isl_rt.fk_sb_et_kvk_Fallbeyging_id is not None:
				ord_data['sb']['et']['kvk'] = (
					self.load_fallbeyging_from_db(isl_rt.fk_sb_et_kvk_Fallbeyging_id)
				)
			if isl_rt.fk_sb_et_hk_Fallbeyging_id is not None:
				ord_data['sb']['et']['hk'] = (
					self.load_fallbeyging_from_db(isl_rt.fk_sb_et_hk_Fallbeyging_id)
				)
			# sb ft
			if isl_rt.fk_sb_ft_kk_Fallbeyging_id is not None:
				ord_data['sb']['ft']['kk'] = (
					self.load_fallbeyging_from_db(isl_rt.fk_sb_ft_kk_Fallbeyging_id)
				)
			if isl_rt.fk_sb_ft_kvk_Fallbeyging_id is not None:
				ord_data['sb']['ft']['kvk'] = (
					self.load_fallbeyging_from_db(isl_rt.fk_sb_ft_kvk_Fallbeyging_id)
				)
			if isl_rt.fk_sb_ft_hk_Fallbeyging_id is not None:
				ord_data['sb']['ft']['hk'] = (
					self.load_fallbeyging_from_db(isl_rt.fk_sb_ft_hk_Fallbeyging_id)
				)
			# vb et
			if isl_rt.fk_vb_et_kk_Fallbeyging_id is not None:
				ord_data['vb']['et']['kk'] = (
					self.load_fallbeyging_from_db(isl_rt.fk_vb_et_kk_Fallbeyging_id)
				)
			if isl_rt.fk_vb_et_kvk_Fallbeyging_id is not None:
				ord_data['vb']['et']['kvk'] = (
					self.load_fallbeyging_from_db(isl_rt.fk_vb_et_kvk_Fallbeyging_id)
				)
			if isl_rt.fk_vb_et_hk_Fallbeyging_id is not None:
				ord_data['vb']['et']['hk'] = (
					self.load_fallbeyging_from_db(isl_rt.fk_vb_et_hk_Fallbeyging_id)
				)
			# vb ft
			if isl_rt.fk_vb_ft_kk_Fallbeyging_id is not None:
				ord_data['vb']['ft']['kk'] = (
					self.load_fallbeyging_from_db(isl_rt.fk_vb_ft_kk_Fallbeyging_id)
				)
			if isl_rt.fk_vb_ft_kvk_Fallbeyging_id is not None:
				ord_data['vb']['ft']['kvk'] = (
					self.load_fallbeyging_from_db(isl_rt.fk_vb_ft_kvk_Fallbeyging_id)
				)
			if isl_rt.fk_vb_ft_hk_Fallbeyging_id is not None:
				ord_data['vb']['ft']['hk'] = (
					self.load_fallbeyging_from_db(isl_rt.fk_vb_ft_hk_Fallbeyging_id)
				)
		self.data = structs.RadtalaData(**ord_data)


class Smaord(Ord):
	"""
	Smáorð handler
	"""

	group = structs.Ordflokkar.Smaord
	data: Optional[
		structs.ForsetningData | structs.AtviksordData | structs.NafnhattarmerkiData |
		structs.SamtengingData | structs.UpphropunData
	] = None

	def make_filename(self):
		return os.path.join(
			self.data.undirflokkur.get_folder(), '%s%s.json' % (self.data.orð, self._fno_extras())
		)

	def make_kennistrengur(self):
		return '%s-%s%s' % (
			self.data.undirflokkur.get_abbreviation(), self.data.orð, self._fno_extras()
		)

	def write_to_db(self) -> tuple[isl.Ord, bool]:
		match self.data.undirflokkur:
			case structs.Smaordaflokkar.Forsetning:
				return self.write_forsetning_to_db()
			case structs.Smaordaflokkar.Atviksord:
				return self.write_atviksord_to_db()
			case structs.Smaordaflokkar.Nafnhattarmerki:
				return self.write_nafnhattarmerki_to_db()
			case structs.Smaordaflokkar.Samtenging:
				return self.write_samtenging_to_db()
			case structs.Smaordaflokkar.Upphropun:
				return self.write_upphropun_to_db()
		raise Exception('Should not happen.')

	def write_forsetning_to_db(self) -> tuple[isl.Ord, bool]:
		isl_ord, changes_made = super().write_to_db()
		isl_fs = db.Session.query(isl.Forsetning).filter_by(fk_Ord_id=isl_ord.Ord_id).first()
		if isl_fs is None:
			isl_fs = isl.Forsetning(fk_Ord_id=isl_ord.Ord_id)
			db.Session.add(isl_fs)
			db.Session.commit()
			changes_made = True
		if self.data.stýrir is not None:
			isl_fs.StyrirTholfalli = structs.Fall2.Tholfall in self.data.stýrir
			isl_fs.StyrirThagufalli = structs.Fall2.Thagufall in self.data.stýrir
			isl_fs.StyrirEignarfalli = structs.Fall2.Eignarfall in self.data.stýrir
		else:
			isl_fs.StyrirTholfalli = False
			isl_fs.StyrirThagufalli = False
			isl_fs.StyrirEignarfalli = False
		changes_made = changes_made or db.Session.is_modified(isl_fs)
		if db.Session.is_modified(isl_fs):
			db.Session.commit()
		if changes_made is True:
			isl_ord.Edited = datetime.datetime.utcnow()
			db.Session.commit()
		return (isl_ord, changes_made)

	def write_atviksord_to_db(self) -> tuple[isl.Ord, bool]:
		isl_ord, changes_made = super().write_to_db()
		if isl_ord.Samsett is True:
			return (isl_ord, changes_made)
		isl_ao = db.Session.query(isl.Atviksord).filter_by(fk_Ord_id=isl_ord.Ord_id).first()
		if isl_ao is None:
			isl_ao = isl.Atviksord(fk_Ord_id=isl_ord.Ord_id)
			db.Session.add(isl_ao)
			db.Session.commit()
			changes_made = True
		isl_ao.Midstig = self.data.miðstig
		isl_ao.Efstastig = self.data.efstastig
		changes_made = changes_made or db.Session.is_modified(isl_ao)
		if db.Session.is_modified(isl_ao):
			db.Session.commit()
		if changes_made is True:
			isl_ord.Edited = datetime.datetime.utcnow()
			db.Session.commit()
		return (isl_ord, changes_made)

	def write_nafnhattarmerki_to_db(self) -> tuple[isl.Ord, bool]:
		return super().write_to_db()

	def write_samtenging_to_db(self) -> tuple[isl.Ord, bool]:
		isl_ord, changes_made = super().write_to_db()
		if self.data.fleiryrt is not None:
			for fleiryrt in self.data.fleiryrt:
				first_word = True
				last_samtenging_fleiryrt_id = None
				for fylgiord in fleiryrt.fylgiorð:
					isl_ord_id = None
					fleiryrt_typa = None
					if first_word is True:
						isl_ord_id = isl_ord.Ord_id
						fleiryrt_typa = isl.FleiryrtTypa[fleiryrt.týpa.name]
					isl_st_fy = db.Session.query(isl.SamtengingFleiryrt).filter_by(
						fk_Ord_id=isl_ord_id,
						Ord=fylgiord,
						fk_SamtengingFleiryrt_id=last_samtenging_fleiryrt_id,
						Typa=fleiryrt_typa
					).first()
					if isl_st_fy is None:
						isl_st_fy = isl.SamtengingFleiryrt(
							fk_Ord_id=isl_ord_id,
							Ord=fylgiord,
							fk_SamtengingFleiryrt_id=last_samtenging_fleiryrt_id,
							Typa=fleiryrt_typa
						)
						db.Session.add(isl_st_fy)
						db.Session.commit()
						changes_made = True
					first_word = False
					last_samtenging_fleiryrt_id = isl_st_fy.SamtengingFleiryrt_id
		if changes_made is True:
			isl_ord.Edited = datetime.datetime.utcnow()
			db.Session.commit()
		return (isl_ord, changes_made)

	def write_upphropun_to_db(self) -> tuple[isl.Ord, bool]:
		return super().write_to_db()

	@classmethod
	def get_files_list_sorted(cls):
		kjarna_ord_files_list = []
		samsett_ord_files_list = []
		for ufl in structs.Smaordaflokkar:
			kja_list, sam_list = super().get_files_list_sorted(override_dir_rel=ufl.get_folder())
			kjarna_ord_files_list += kja_list
			samsett_ord_files_list += sam_list
		return (kjarna_ord_files_list, samsett_ord_files_list)

	def load_from_db(self, isl_ord: isl.Ord):
		match isl_ord.Ordflokkur:
			case isl.Ordflokkar.Forsetning:
				self.load_forsetning_from_db(isl_ord)
			case isl.Ordflokkar.Atviksord:
				self.load_atviksord_from_db(isl_ord)
			case isl.Ordflokkar.Nafnhattarmerki:
				self.load_nafnhattarmerki_from_db(isl_ord)
			case isl.Ordflokkar.Samtenging:
				self.load_samtenging_from_db(isl_ord)
			case isl.Ordflokkar.Upphropun:
				self.load_upphropun_from_db(isl_ord)
			case _:
				raise Exception('Unsupported or invalid undirflokkur?')
		kennistr = self.make_kennistrengur()
		if self.data.kennistrengur != kennistr:
			raise Exception(
				'Orð id=%s, loaded from db, kennistrengur mismatch, loaded="%s", derived="%s"' % (
					isl_ord.Ord_id, self.data.kennistrengur, kennistr
				)
			)
		self.data.datahash = self.get_data_hash()

	def load_forsetning_from_db(self, isl_ord: isl.Ord):
		ord_data = super().load_from_db(isl_ord)
		isl_fs = db.Session.query(isl.Forsetning).filter_by(fk_Ord_id=isl_ord.Ord_id).first()
		if (
			isl_fs.StyrirTholfalli is True or
			isl_fs.StyrirThagufalli is True or
			isl_fs.StyrirEignarfalli is True
		):
			ord_data['stýrir'] = []
		if isl_fs.StyrirTholfalli is True:
			ord_data['stýrir'].append(structs.Fall2.Tholfall.value)
		if isl_fs.StyrirThagufalli is True:
			ord_data['stýrir'].append(structs.Fall2.Thagufall.value)
		if isl_fs.StyrirEignarfalli is True:
			ord_data['stýrir'].append(structs.Fall2.Eignarfall.value)
		self.data = structs.ForsetningData(**ord_data)

	def load_atviksord_from_db(self, isl_ord: isl.Ord):
		ord_data = super().load_from_db(isl_ord)
		if isl_ord.Samsett is True:
			ord_data = self.derive_beygingar_from_samsett(ord_data)
		else:
			isl_ao = db.Session.query(isl.Atviksord).filter_by(fk_Ord_id=isl_ord.Ord_id).first()
			if isl_ao.Midstig is not None:
				ord_data['miðstig'] = isl_ao.Midstig
			if isl_ao.Efstastig is not None:
				ord_data['efstastig'] = isl_ao.Efstastig
		self.data = structs.AtviksordData(**ord_data)

	def load_nafnhattarmerki_from_db(self, isl_ord: isl.Ord):
		ord_data = super().load_from_db(isl_ord)
		self.data = structs.NafnhattarmerkiData(**ord_data)

	def load_samtenging_from_db(self, isl_ord: isl.Ord):
		ord_data = super().load_from_db(isl_ord)
		isl_samtenging_fleiryrt_query = db.Session.query(isl.SamtengingFleiryrt).filter_by(
			fk_Ord_id=isl_ord.Ord_id
		).order_by(isl.SamtengingFleiryrt.Ord, isl.SamtengingFleiryrt.SamtengingFleiryrt_id)
		isl_samtenging_fleiryrt_list = isl_samtenging_fleiryrt_query.all()
		if len(isl_samtenging_fleiryrt_list) > 0:
			ord_data['fleiryrt'] = []
			for isl_samtenging_fleiryrt in isl_samtenging_fleiryrt_list:
				fleiryrt_option = {
					'týpa': structs.FleiryrtTypa[isl_samtenging_fleiryrt.Typa.name],
					'fylgiorð': [isl_samtenging_fleiryrt.Ord],
				}
				possible_more_words = True
				current_isl_samtenging_fleiryrt_id = isl_samtenging_fleiryrt.SamtengingFleiryrt_id
				while possible_more_words is True:
					isl_next_samtenging_fleiryrt_query = db.Session.query(
						isl.SamtengingFleiryrt
					).filter_by(fk_SamtengingFleiryrt_id=current_isl_samtenging_fleiryrt_id)
					if len(isl_next_samtenging_fleiryrt_query.all()) not in (0, 1):
						raise Exception('Should be just one or zero.')
					isl_next_samtenging_fleiryrt = isl_next_samtenging_fleiryrt_query.first()
					if isl_next_samtenging_fleiryrt is not None:
						fleiryrt_option['fylgiorð'].append(isl_next_samtenging_fleiryrt.Ord)
						current_isl_samtenging_fleiryrt_id = (
							isl_next_samtenging_fleiryrt.SamtengingFleiryrt_id
						)
					else:
						possible_more_words = False
				ord_data['fleiryrt'].append(fleiryrt_option)
		self.data = structs.SamtengingData(**ord_data)

	def load_upphropun_from_db(self, isl_ord: isl.Ord):
		ord_data = super().load_from_db(isl_ord)
		self.data = structs.UpphropunData(**ord_data)


class Sernafn(Ord):
	"""
	Sérnafn handler
	"""

	group = structs.Ordflokkar.Sernafn
	data: Optional[structs.SernafnData] = None

	def make_filename(self):
		if self.data.undirflokkur in (
			structs.Sernafnaflokkar.Eiginnafn, structs.Sernafnaflokkar.Kenninafn
		):
			match self.data.kyn:
				case structs.Kyn.Kvenkyn:
					subfolder_1 = 'islensk-kvenmannsnofn'
				case structs.Kyn.Karlkyn:
					subfolder_1 = 'islensk-karlmannsnofn'
				case structs.Kyn.Hvorugkyn:
					subfolder_1 = 'islensk-hvormannsnofn'
				case _:
					raise Exception('unexpected kyn')
			match self.data.undirflokkur:
				case structs.Sernafnaflokkar.Eiginnafn:
					subfolder_2 = 'eigin'
				case structs.Sernafnaflokkar.Kenninafn:
					subfolder_2 = 'kenni'
				case _:
					raise Exception('unexpected sérnafnaundirflokkur')
			return os.path.join(
				self.data.undirflokkur.get_folder(),
				subfolder_1,
				subfolder_2,
				'%s%s.json' % (self.data.orð, self._fno_extras())
			)
		if self.data.undirflokkur is structs.Sernafnaflokkar.Gaelunafn:
			return os.path.join(
				self.data.undirflokkur.get_folder(),
				self.data.kyn.value,
				'%s%s.json' % (self.data.orð, self._fno_extras())
			)
		if self.data.undirflokkur is structs.Sernafnaflokkar.Ornefni:
			return os.path.join(
				self.data.undirflokkur.get_folder(),
				'%s-%s%s.json' % (self.data.orð, self.data.kyn.value, self._fno_extras())
			)
		return os.path.join(
			self.data.undirflokkur.get_folder(), '%s%s.json' % (self.data.orð, self._fno_extras())
		)

	def make_kennistrengur(self):
		if self.data.kyn is not None:
			return '%s-%s-%s%s' % (
				self.data.undirflokkur.get_abbreviation(), self.data.orð, self.data.kyn.value,
				self._fno_extras()
			)
		return '%s-%s%s' % (
			self.data.undirflokkur.get_abbreviation(), self.data.orð, self._fno_extras()
		)

	def write_to_db(self) -> tuple[isl.Ord, bool]:
		isl_ord, changes_made = super().write_to_db()
		isl_sn = db.Session.query(isl.Sernafn).filter_by(fk_Ord_id=isl_ord.Ord_id).first()
		if isl_sn is None:
			isl_sn = isl.Sernafn(fk_Ord_id=isl_ord.Ord_id)
			db.Session.add(isl_sn)
			db.Session.commit()
			changes_made = True
		isl_sn.Undirflokkur = isl.Sernafnaflokkar[self.data.undirflokkur.name]
		if self.data.kyn is not None:
			isl_sn.Kyn = isl.Kyn[self.data.kyn.name]
		if self.data.samsett is not None:
			changes_made = changes_made or db.Session.is_modified(isl_sn)
			if changes_made is True:
				isl_ord.Edited = datetime.datetime.utcnow()
				db.Session.commit()
			return (isl_ord, changes_made)
		if self.data.et is not None:
			if self.data.et.ág is not None:
				isl_sn.fk_et_Fallbeyging_id, changes_made = self.write_fallbeyging_to_db(
					isl_sn.fk_et_Fallbeyging_id, self.data.et.ág, changes_made
				)
			if self.data.et.mg is not None:
				isl_sn.fk_et_mgr_Fallbeyging_id, changes_made = self.write_fallbeyging_to_db(
					isl_sn.fk_et_mgr_Fallbeyging_id, self.data.et.mg, changes_made
				)
		if self.data.ft is not None:
			if self.data.ft.ág is not None:
				isl_sn.fk_ft_Fallbeyging_id, changes_made = self.write_fallbeyging_to_db(
					isl_sn.fk_ft_Fallbeyging_id, self.data.ft.ág, changes_made
				)
			if self.data.ft.mg is not None:
				isl_sn.fk_ft_mgr_Fallbeyging_id, changes_made = self.write_fallbeyging_to_db(
					isl_sn.fk_ft_mgr_Fallbeyging_id, self.data.ft.mg, changes_made
				)
		changes_made = changes_made or db.Session.is_modified(isl_sn)
		if db.Session.is_modified(isl_sn):
			db.Session.commit()
		if changes_made is True:
			isl_ord.Edited = datetime.datetime.utcnow()
			db.Session.commit()
		return (isl_ord, changes_made)

	@classmethod
	def get_files_list_sorted(cls):
		kjarna_ord_files_list = []
		samsett_ord_files_list = []
		ufl_folders = [  # list folders instead of structs.Sernafnaflokkar get_folder shenanigans
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
		for ufl_folder in ufl_folders:
			kja_list, sam_list = super().get_files_list_sorted(override_dir_rel=ufl_folder)
			kjarna_ord_files_list += kja_list
			samsett_ord_files_list += sam_list
		return (kjarna_ord_files_list, samsett_ord_files_list)

	def load_from_db(self, isl_ord: isl.Ord):
		ord_data = super().load_from_db(isl_ord)
		isl_sn = db.Session.query(isl.Sernafn).filter_by(fk_Ord_id=isl_ord.Ord_id).first()
		ord_data['undirflokkur'] = structs.Sernafnaflokkar[isl_sn.Undirflokkur.name].value
		if isl_sn.Kyn is not None:  # miłlinöfn are genderless
			ord_data['kyn'] = structs.Kyn[isl_sn.Kyn.name].value
		if isl_ord.Samsett is True:
			ord_data = self.derive_beygingar_from_samsett(ord_data)
		else:
			if (
				isl_sn.fk_et_Fallbeyging_id is not None or
				isl_sn.fk_et_mgr_Fallbeyging_id is not None
			):
				ord_data['et'] = {}
			if isl_sn.fk_et_Fallbeyging_id is not None:
				ord_data['et']['ág'] = self.load_fallbeyging_from_db(isl_sn.fk_et_Fallbeyging_id)
			if isl_sn.fk_et_mgr_Fallbeyging_id is not None:
				ord_data['et']['mg'] = self.load_fallbeyging_from_db(
					isl_sn.fk_et_mgr_Fallbeyging_id
				)
			if (
				isl_sn.fk_ft_Fallbeyging_id is not None or
				isl_sn.fk_ft_mgr_Fallbeyging_id is not None
			):
				ord_data['ft'] = {}
			if isl_sn.fk_ft_Fallbeyging_id is not None:
				ord_data['ft']['ág'] = self.load_fallbeyging_from_db(isl_sn.fk_ft_Fallbeyging_id)
			if isl_sn.fk_ft_mgr_Fallbeyging_id is not None:
				ord_data['ft']['mg'] = self.load_fallbeyging_from_db(
					isl_sn.fk_ft_mgr_Fallbeyging_id
				)
		self.data = structs.SernafnData(**ord_data)
		kennistr = self.make_kennistrengur()
		if self.data.kennistrengur != kennistr:
			raise Exception('Orð id=%s, kennistrengur mismatch, loaded="%s", derived="%s"' % (
				isl_ord.Ord_id, self.data.kennistrengur, kennistr
			))
		self.data.datahash = self.get_data_hash()


class Skammstofun(Ord):
	"""
	Skammstöfun handler
	"""
	data: Optional[structs.SkammstofunData] = None

	def make_filename(self):
		return os.path.join(
			'skammstafanir', '%s%s.json' % (self.data.skammstöfun, self._fno_extras())
		)

	def make_kennistrengur(self):
		return 'skammst-%s%s' % (self.data.skammstöfun, self._fno_extras())

	def _fno_extras(self):
		return '-_%s_' % (self.data.merking, ) if self.data.merking is not None else ''

	@classmethod
	def get_files_list_sorted(cls):
		files_directory_rel = 'skammstafanir'
		files_directory = os.path.join(cls.datafiles_dir, files_directory_rel)
		files_list = []
		for json_file in sorted(pathlib.Path(files_directory).iterdir()):
			if not json_file.is_file():
				continue
			if not json_file.name.endswith('.json'):
				continue
			try:
				with json_file.open(mode='r', encoding='utf-8') as fi:
					json.loads(fi.read())
			except json.decoder.JSONDecodeError:
				raise Exception(f'File "{json_file.name}" has invalid JSON format.')
			json_file_rel = os.path.join(files_directory_rel, json_file.name)
			files_list.append(json_file_rel)
		files_list.sort()
		return files_list

	def write_to_db(self) -> tuple[isl.Skammstofun, bool]:
		changes_made = False
		isl_sk = db.Session.query(isl.Skammstofun).filter_by(
			Skammstofun=self.data.skammstöfun, Merking=self.data.merking
		).first()
		if isl_sk is None:
			isl_sk = isl.Skammstofun(
				Skammstofun=self.data.skammstöfun,
				Merking=self.data.merking,
				Kennistrengur=self.data.kennistrengur
			)
			db.Session.add(isl_sk)
			db.Session.commit()
			changes_made = True
		if isl_sk.Kennistrengur != self.data.kennistrengur:
			isl_sk.Kennistrengur = self.data.kennistrengur
			db.Session.commit()
			changes_made = True
		isl_sk_frasar = db.Session.query(isl.SkammstofunFrasi).filter_by(
			fk_Skammstofun_id=isl_sk.Skammstofun_id
		).order_by(isl.SkammstofunFrasi.SkammstofunFrasi_id).all()
		data_frasi_count = len(self.data.frasi)
		db_frasi_count = len(isl_sk_frasar)
		for i in range(0, max(data_frasi_count, db_frasi_count)):
			if i < data_frasi_count:
				kennistrengur = self.data.frasi[i]
				if kennistrengur is None:
					raise Exception('missing kennistrengur')
				isl_ord = db.Session.query(isl.Ord).filter_by(Kennistrengur=kennistrengur).first()
				if isl_ord is None:
					raise Exception(f'no orð with kennistrengur "{kennistrengur}"?')
				if i < db_frasi_count:
					if isl_sk_frasar[i].fk_Ord_id != isl_ord.Ord_id:
						isl_sk_frasar[i].fk_Ord_id = isl_ord.Ord_id
						db.Session.commit()
						changes_made = True
				else:
					isl_sk_frasi = isl.SkammstofunFrasi(
						fk_Skammstofun_id=isl_sk.Skammstofun_id,
						fk_Ord_id=isl_ord.Ord_id
					)
					db.Session.add(isl_sk_frasi)
					db.Session.commit()
					changes_made = True
			else:
				db.Session.delete(isl_sk_frasar[i])
				db.Session.commit()
				changes_made = True
		isl_sk_myndir = db.Session.query(isl.SkammstofunMynd).filter_by(
			fk_Skammstofun_id=isl_sk.Skammstofun_id
		).order_by(isl.SkammstofunMynd.SkammstofunMynd_id).all()
		data_myndir_count = len(self.data.myndir)
		db_myndir_count = len(isl_sk_myndir)
		for j in range(0, max(data_myndir_count, db_myndir_count)):
			if j < data_myndir_count:
				if j < db_myndir_count:
					if isl_sk_myndir[j].Mynd != self.data.myndir[j]:
						isl_sk_myndir[j].Mynd = self.data.myndir[j]
						db.Session.commit()
						changes_made = True
				else:
					isl_sk_mynd = isl.SkammstofunMynd(
						fk_Skammstofun_id=isl_sk.Skammstofun_id,
						Mynd=self.data.myndir[j]
					)
					db.Session.add(isl_sk_mynd)
					db.Session.commit()
					changes_made = True
			else:
				db.Session.delete(isl_sk_myndir[j])
				db.Session.commit()
				changes_made = True
		return (isl_sk, changes_made)

	def load_from_db(self, isl_sk: isl.Skammstofun):
		sk_data = {
			'skammstöfun': isl_sk.Skammstofun,
			'frasi': [],
			'myndir': [],
			'kennistrengur': isl_sk.Kennistrengur,
		}
		if isl_sk.Merking is not None:
			sk_data['merking'] = isl_sk.Merking
		isl_sk_frasi = db.Session.query(isl.SkammstofunFrasi).filter_by(
			fk_Skammstofun_id=isl_sk.Skammstofun_id
		).order_by(isl.SkammstofunFrasi.SkammstofunFrasi_id).all()
		if len(isl_sk_frasi) == 0:
			raise Exception('there should be frasi')
		for frasi_ord in isl_sk_frasi:
			isl_ord = db.Session.query(isl.Ord).filter_by(Ord_id=frasi_ord.fk_Ord_id).first()
			sk_data['frasi'].append(isl_ord.Kennistrengur)
		isl_sk_myndir = db.Session.query(isl.SkammstofunMynd).filter_by(
			fk_Skammstofun_id=isl_sk.Skammstofun_id
		).order_by(isl.SkammstofunMynd.SkammstofunMynd_id).all()
		if len(isl_sk_myndir) == 0:
			raise Exception('there should be myndir')
		for mynd in isl_sk_myndir:
			sk_data['myndir'].append(mynd.Mynd)
		self.data = structs.SkammstofunData(**sk_data)
		kennistr = self.make_kennistrengur()
		if self.data.kennistrengur != kennistr:
			raise Exception(
				'Skammstöfun id=%s, kennistrengur mismatch, loaded="%s", derived="%s"' % (
					isl_ord.Ord_id, self.data.kennistrengur, kennistr
				)
			)
		self.data.datahash = self.get_data_hash()


class MyIndentJSONEncoder(json.JSONEncoder):
	'''
	json encoder for doing a little bit of custom json string indentation

	this encoder class is a complete hack, but the damn thing works and I'm running with it
	'''
	r_strengur = ''.join(
		random.choices(string.ascii_uppercase + string.ascii_lowercase + string.digits, k=20)
	)

	def default(self, obj):
		if isinstance(obj, Decimal):
			return (
				f'<-FJARLAEGJA_GAESALAPPIR_{self.r_strengur}'
				f'{obj.normalize():f}'
				f'FJARLAEGJA_GAESALAPPIR_{self.r_strengur}->'
			)
		return super(MyIndentJSONEncoder, self).default(obj)

	def iterencode(self, o, _one_shot=False):
		list_lvl = 0
		keys_to_differently_encode = [
			'ág', 'mg', 'kk', 'kvk', 'hk', 'et', 'ft', 'stýrir', 'fylgiorð', 'beygingar'
		]
		state = 0
		for s in super(MyIndentJSONEncoder, self).iterencode(o, _one_shot=_one_shot):
			if state == 0:
				if s.startswith('"') and s.endswith('"') and s[1:-1] in keys_to_differently_encode:
					state += 1
			elif state == 1:
				if s == ': ':
					state += 1
				else:
					state = 0
			elif state == 2:
				if s.startswith('['):
					list_lvl += 1
					s = ''.join([x.strip() for x in s.split('\n')])
				elif 0 < list_lvl:
					s = ''.join([x.strip() for x in s.split('\n')])
					if s and s.startswith(','):
						s = ', ' + s[1:]
				if s.endswith(']'):
					list_lvl -= 1
					state = 0
				if s.endswith('}'):
					state = 0
			if f'"<-FJARLAEGJA_GAESALAPPIR_{self.r_strengur}' in s:
				s = s.replace(f'"<-FJARLAEGJA_GAESALAPPIR_{self.r_strengur}', '')
			if f'FJARLAEGJA_GAESALAPPIR_{self.r_strengur}->"' in s:
				s = s.replace(f'FJARLAEGJA_GAESALAPPIR_{self.r_strengur}->"', '')
			yield s


class DecimalJSONEncoder(json.JSONEncoder):
	r_strengur = ''.join(
		random.choices(string.ascii_uppercase + string.ascii_lowercase + string.digits, k=20)
	)

	def default(self, obj):
		if isinstance(obj, Decimal):
			return (
				f'<-FJARLAEGJA_GAESALAPPIR_{self.r_strengur}'
				f'{obj.normalize():f}'
				f'FJARLAEGJA_GAESALAPPIR_{self.r_strengur}->'
			)
		return super(DecimalJSONEncoder, self).default(obj)

	def iterencode(self, o, _one_shot=False):
		for s in super(DecimalJSONEncoder, self).iterencode(o, _one_shot=_one_shot):
			if f'"<-FJARLAEGJA_GAESALAPPIR_{self.r_strengur}' in s:
				s = s.replace(f'"<-FJARLAEGJA_GAESALAPPIR_{self.r_strengur}', '')
			if f'FJARLAEGJA_GAESALAPPIR_{self.r_strengur}->"' in s:
				s = s.replace(f'FJARLAEGJA_GAESALAPPIR_{self.r_strengur}->"', '')
			yield s


def list_handlers():
	return [Nafnord, Lysingarord, Greinir, Fornafn, Toluord, Sagnord, Smaord, Sernafn]


def get_handlers_map():
	handlers = list_handlers()
	handlers_map = {}
	for handler in handlers:
		handlers_map[handler.group.name] = handler
		handlers_map[handler.group.value] = handler
	for ordflokkur in isl.Ordflokkar:
		if ordflokkur.name in handlers_map:
			continue
		if ordflokkur.name in structs.Toluordaflokkar.__members__.keys():
			handlers_map[ordflokkur.name] = Toluord
			handlers_map[structs.Toluordaflokkar[ordflokkur.name].value] = Toluord
		elif ordflokkur.name in structs.Smaordaflokkar.__members__.keys():
			handlers_map[ordflokkur.name] = Smaord
			handlers_map[structs.Smaordaflokkar[ordflokkur.name].value] = Smaord
	return handlers_map
