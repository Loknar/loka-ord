#!/usr/bin/python3
# -*- coding: utf-8 -*-
import enum

# from sqlalchemy import Boolean, Column, Enum, ForeignKey, Integer, Unicode, UnicodeText

from database.db import Base
from database.models import utils


class Ordflokkar(enum.Enum):
    # fallorð
    Nafnord = 0
    Lysingarord = 1
    Greinir = 2  # fyrir hinn lausa greini, en viðskeyttur greinir geymdur í tvíriti í Fallbeyging
    Frumtala = 3  # + Töluorð, hafa undirflokkana Frumtölur og Raðtölur
    Radtala = 4   # /
    Fornafn = 5
    # sagnorð
    Sagnord = 6
    # óbeygjanleg orð (smáorð)
    Forsetning = 7
    Atviksord = 8
    Nafnhattarmerki = 9
    Samtenging = 10
    Upphropun = 11


class Ordasamsetningar(enum.Enum):
    Stofnsamsetning = 0
    Eignarfallssamsetning = 1
    Bandstafssamsetning = 2


class Kyn(enum.Enum):
    Karlkyn = 0
    Kvenkyn = 1
    Hvorugkyn = 2


class Fornafnaflokkar(enum.Enum):
    Personufornafn = 0
    Eignarfornafn = 1
    AfturbeygtFornafn = 2  # (orðið sig)
    Abendingarfornafn = 3
    Spurnarfornafn = 4
    Tilvisunarfornafn = 5
    OakvedidFornafn = 6


class Toluordaflokkar(enum.Enum):
    Frumtala = 0  # (einn, tveir, þrír)
    Radtala = 1  # (fyrsti, annar, þriðji)


class Ord(Base):
    __tablename__ = 'Ord'
    Ord_id = utils.integer_primary_key()
    Ord = utils.word_column()
    Ordflokkur = utils.selection(Ordflokkar, Ordflokkar.Nafnord)
    Samsett = utils.boolean_default_false()
    Edited = utils.timestamp_edited()
    Created = utils.timestamp_created()


class SamsettOrd(Base):
    SamsettOrd_id = utils.integer_primary_key()
    fk_Ord_id = utils.foreign_integer_primary_key('Ord')
    Forhluti = utils.word_column()
    fk_OsamsettBeygingarhlutaOrd_id = utils.foreign_integer_primary_key('Ord')
    Gerd = utils.selection(Ordasamsetningar, Ordasamsetningar.Stofnsamsetning)
    Edited = utils.timestamp_edited()
    Created = utils.timestamp_created()


class Nafnord(Base):
    Nafnord_id = utils.integer_primary_key()
    fk_Ord_id = utils.foreign_integer_primary_key('Ord')
    fk_et_Fallbeyging_id = utils.foreign_integer_primary_key('Fallbeyging')
    fk_et_mgr_Fallbeyging_id = utils.foreign_integer_primary_key('Fallbeyging')
    fk_ft_Fallbeyging_id = utils.foreign_integer_primary_key('Fallbeyging')
    fk_ft_mgr_Fallbeyging_id = utils.foreign_integer_primary_key('Fallbeyging')
    Kyn = utils.selection(Kyn, Kyn.Karlkyn)
    Edited = utils.timestamp_edited()
    Created = utils.timestamp_created()


class Lysingarord(Base):
    Lysingarord_id = utils.integer_primary_key()
    fk_Ord_id = utils.foreign_integer_primary_key('Ord')
    # Frumstig, sterk beyging
    fk_Frumstig_sb_et_kk_Fallbeyging_id = utils.foreign_integer_primary_key('Fallbeyging')
    fk_Frumstig_sb_et_kvk_Fallbeyging_id = utils.foreign_integer_primary_key('Fallbeyging')
    fk_Frumstig_sb_et_hk_Fallbeyging_id = utils.foreign_integer_primary_key('Fallbeyging')
    fk_Frumstig_sb_ft_kk_Fallbeyging_id = utils.foreign_integer_primary_key('Fallbeyging')
    fk_Frumstig_sb_ft_kvk_Fallbeyging_id = utils.foreign_integer_primary_key('Fallbeyging')
    fk_Frumstig_sb_ft_hk_Fallbeyging_id = utils.foreign_integer_primary_key('Fallbeyging')
    # Frumstig, veik beyging
    fk_Frumstig_vb_et_kk_Fallbeyging_id = utils.foreign_integer_primary_key('Fallbeyging')
    fk_Frumstig_vb_et_kvk_Fallbeyging_id = utils.foreign_integer_primary_key('Fallbeyging')
    fk_Frumstig_vb_et_hk_Fallbeyging_id = utils.foreign_integer_primary_key('Fallbeyging')
    fk_Frumstig_vb_ft_kk_Fallbeyging_id = utils.foreign_integer_primary_key('Fallbeyging')
    fk_Frumstig_vb_ft_kvk_Fallbeyging_id = utils.foreign_integer_primary_key('Fallbeyging')
    fk_Frumstig_vb_ft_hk_Fallbeyging_id = utils.foreign_integer_primary_key('Fallbeyging')
    # Miðstig, veik beyging (miðstig hafa enga sterka beygingu)
    fk_Midstig_vb_et_kk_Fallbeyging_id = utils.foreign_integer_primary_key('Fallbeyging')
    fk_Midstig_vb_et_kvk_Fallbeyging_id = utils.foreign_integer_primary_key('Fallbeyging')
    fk_Midstig_vb_et_hk_Fallbeyging_id = utils.foreign_integer_primary_key('Fallbeyging')
    fk_Midstig_vb_ft_kk_Fallbeyging_id = utils.foreign_integer_primary_key('Fallbeyging')
    fk_Midstig_vb_ft_kvk_Fallbeyging_id = utils.foreign_integer_primary_key('Fallbeyging')
    fk_Midstig_vb_ft_hk_Fallbeyging_id = utils.foreign_integer_primary_key('Fallbeyging')
    # Efsta stig, sterk beyging
    fk_Efstastig_sb_et_kk_Fallbeyging_id = utils.foreign_integer_primary_key('Fallbeyging')
    fk_Efstastig_sb_et_kvk_Fallbeyging_id = utils.foreign_integer_primary_key('Fallbeyging')
    fk_Efstastig_sb_et_hk_Fallbeyging_id = utils.foreign_integer_primary_key('Fallbeyging')
    fk_Efstastig_sb_ft_kk_Fallbeyging_id = utils.foreign_integer_primary_key('Fallbeyging')
    fk_Efstastig_sb_ft_kvk_Fallbeyging_id = utils.foreign_integer_primary_key('Fallbeyging')
    fk_Efstastig_sb_ft_hk_Fallbeyging_id = utils.foreign_integer_primary_key('Fallbeyging')
    # Efsta stig, veik beyging
    fk_Efstastig_vb_et_kk_Fallbeyging_id = utils.foreign_integer_primary_key('Fallbeyging')
    fk_Efstastig_vb_et_kvk_Fallbeyging_id = utils.foreign_integer_primary_key('Fallbeyging')
    fk_Efstastig_vb_et_hk_Fallbeyging_id = utils.foreign_integer_primary_key('Fallbeyging')
    fk_Efstastig_vb_ft_kk_Fallbeyging_id = utils.foreign_integer_primary_key('Fallbeyging')
    fk_Efstastig_vb_ft_kvk_Fallbeyging_id = utils.foreign_integer_primary_key('Fallbeyging')
    fk_Efstastig_vb_ft_hk_Fallbeyging_id = utils.foreign_integer_primary_key('Fallbeyging')
    #
    Edited = utils.timestamp_edited()
    Created = utils.timestamp_created()


class Greinir(Base):  # laus greinir (hinn)
    Greinir_id = utils.integer_primary_key()
    fk_Ord_id = utils.foreign_integer_primary_key('Ord')
    # eintala
    fk_et_kk_Fallbeyging_id = utils.foreign_integer_primary_key('Fallbeyging')
    fk_et_kvk_Fallbeyging_id = utils.foreign_integer_primary_key('Fallbeyging')
    fk_et_hk_Fallbeyging_id = utils.foreign_integer_primary_key('Fallbeyging')
    # fleirtala
    fk_ft_kk_Fallbeyging_id = utils.foreign_integer_primary_key('Fallbeyging')
    fk_ft_kvk_Fallbeyging_id = utils.foreign_integer_primary_key('Fallbeyging')
    fk_ft_hk_Fallbeyging_id = utils.foreign_integer_primary_key('Fallbeyging')
    Edited = utils.timestamp_edited()
    Created = utils.timestamp_created()


class Frumtala(Base):  # Töluorð - Frumtala
    Frumtala_id = utils.integer_primary_key()
    fk_Ord_id = utils.foreign_integer_primary_key('Ord')
    Gildi = utils.integer_default_zero()
    Edited = utils.timestamp_edited()
    Created = utils.timestamp_created()


class Radtala(Base):  # Töluorð - Raðtala
    Radtala_id = utils.integer_primary_key()
    fk_Ord_id = utils.foreign_integer_primary_key('Ord')
    # raðtölur hafa einungis eina (veika) beygingu, nema "fyrstur" sem hefur sterka og veika
    fk_et_kk_Fallbeyging_id = utils.foreign_integer_primary_key('Fallbeyging')
    fk_et_kvk_Fallbeyging_id = utils.foreign_integer_primary_key('Fallbeyging')
    fk_et_hk_Fallbeyging_id = utils.foreign_integer_primary_key('Fallbeyging')
    fk_ft_kk_Fallbeyging_id = utils.foreign_integer_primary_key('Fallbeyging')
    fk_ft_kvk_Fallbeyging_id = utils.foreign_integer_primary_key('Fallbeyging')
    fk_ft_hk_Fallbeyging_id = utils.foreign_integer_primary_key('Fallbeyging')
    Gildi = utils.integer_default_zero()
    Edited = utils.timestamp_edited()
    Created = utils.timestamp_created()


class Fallbeyging(Base):
    Fallbeyging_id = utils.integer_primary_key()
    Nefnifall = utils.word_column()
    Tholfall = utils.word_column()
    Thagufall = utils.word_column()
    Eignarfall = utils.word_column()
    Edited = utils.timestamp_edited()
    Created = utils.timestamp_created()


class Undantekning(Base):
    # Íslenska hefur urmul undantekninga sem falla illa inn í strangar gagnagrunnsskilgreiningar,
    # til dæmis hafa sum orð fleiri en eina rétt beygingarmynd, sum orð tilheyra orðflokkum sem
    # venjulega hafa enga beygingarmynd, frumtölururnar einn, tveir, þrír og fjórir fallbeygjast,
    # sem og aðrar frumtölur sem enda á þeim, eins og tuttuguogeinn, en aðrar frumtölur
    # fallbeygjast ekki, svo fátt eitt sé nefnt.
    Undantekning_id = utils.integer_primary_key()
    fk_Ord_id = utils.foreign_integer_primary_key('Ord')
    Data = utils.json_object()
    Edited = utils.timestamp_edited()
    Created = utils.timestamp_created()


class Fornafn(Base):
    Fornafn_id = utils.integer_primary_key()
    fk_Ord_id = utils.foreign_integer_primary_key('Ord')
    Typa = utils.selection(Fornafnaflokkar, Fornafnaflokkar.Personufornafn)
    Data = utils.json_object()
    Edited = utils.timestamp_edited()
    Created = utils.timestamp_created()
