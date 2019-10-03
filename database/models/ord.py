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
    # https://is.wikipedia.org/wiki/Samsett_or%C3%B0
    Stofnsamsetning = 0
    Eignarfallssamsetning = 1
    Bandstafssamsetning = 2


class Kyn(enum.Enum):
    Kvenkyn = 0
    Karlkyn = 1
    Hvorugkyn = 2


class Fall(enum.Enum):
    Nefnifall = 0
    Tholfall = 1
    Thagufall = 2
    Eignarfall = 3


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
    __tablename__ = 'Fallbeyging'
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


class Sagnord(Base):
    Sagnord_id = utils.integer_primary_key()
    fk_Ord_id = utils.foreign_integer_primary_key('Ord')
    # tilgreina hvort sögn er sterk eða veik?
    # https://is.wikipedia.org/wiki/Sagnmyndir#Germynd
    # germynd (áherslan er á geranda setningarinnar)
    Germynd_Nafnhattur = utils.word_column()  # (dæmi: að ganga)
    # sagnbót, lýsingarháttur stendur alltaf í hvorugkyni eintölu
    Germynd_Sagnbot = utils.word_column()  # (dæmi: ég hef gengið)
    # https://is.wikipedia.org/wiki/Bo%C3%B0h%C3%A1ttur#St%C3%BDf%C3%B0ur_bo%C3%B0h%C3%A1ttur
    Germynd_Bodhattur_styfdur = utils.word_column()  # Stýfður boðháttur (dæmi: gakk (þú))
    Germynd_Bodhattur_eintala = utils.word_column()  # (dæmi: gakktu)
    Germynd_Bodhattur_fleirtala = utils.word_column()  # (dæmi: gangið)
    # framsöguháttur (ég/þú/[hann/hún/það], dæmi: ég geng)
    fk_Germynd_personuleg_framsoguhattur = utils.foreign_integer_primary_key('Sagnbeyging')
    # viðtengingarháttur (þó ég/þú/[hann/hún/það], dæmi: þó ég gangi)
    fk_Germynd_personuleg_vidtengingarhattur = utils.foreign_integer_primary_key('Sagnbeyging')
    # ópersónuleg germynd
    fk_Germynd_opersonuleg_framsoguhattur = utils.foreign_integer_primary_key('Sagnbeyging')
    fk_Germynd_opersonuleg_vidtengingarhattur = utils.foreign_integer_primary_key('Sagnbeyging')
    # https://is.wikipedia.org/wiki/Mi%C3%B0mynd
    # miðmynd (segir frá því hvað gerandi/gerendur gerir/gera við eða fyrir sjálfan/sjálfa sig)
    Midmynd_Nafnhattur = utils.word_column()  # (dæmi: að gangast)
    Midmynd_Sagnbot = utils.word_column()  # (dæmi: ég hef gengist)
    Midmynd_Bodhattur_eintala = utils.word_column()  # (dæmi: gangstu)
    Midmynd_Bodhattur_fleirtala = utils.word_column()  # (dæmi: gangist)
    # framsöguháttur (ég/þú/[hann/hún/það], dæmi: ég gengst)
    fk_Midmynd_personuleg_framsoguhattur = utils.foreign_integer_primary_key('Sagnbeyging')
    # viðtengingarháttur (þó ég/þú/[hann/hún/það], dæmi: þó ég gangist)
    fk_Midmynd_personuleg_vidtengingarhattur = utils.foreign_integer_primary_key('Sagnbeyging')
    # ópersónuleg miðmynd
    fk_Midmynd_opersonuleg_framsoguhattur = utils.foreign_integer_primary_key('Sagnbeyging')
    fk_Midmynd_opersonuleg_vidtengingarhattur = utils.foreign_integer_primary_key('Sagnbeyging')
    LysingarhatturNutidar = utils.word_column()  # (dæmi: gangandi)
    # lýsingarháttur þátíðar (þolmyndir)
    fk_LysingarhatturThatidar_SterkBeyging_id = utils.foreign_integer_primary_key('Fallbeyging')
    fk_LysingarhatturThatidar_VeikBeyging_id = utils.foreign_integer_primary_key('Fallbeyging')
    Edited = utils.timestamp_edited()
    Created = utils.timestamp_created()


class Sagnbeyging(Base):
    # persónu-, tölu- og tíðarbeyging (ég/þú/[hann/hún/það], eintala/fleirtala, nútíð/þátíð)
    __tablename__ = 'Sagnbeyging'
    Sagnbeyging_id = utils.integer_primary_key()
    # nútíð, eintala
    FyrstaPersona_eintala_nutid = utils.word_column()
    OnnurPersona_eintala_nutid = utils.word_column()
    ThridjaPersona_eintala_nutid = utils.word_column()
    # nútíð, fleirtala
    FyrstaPersona_fleirtala_nutid = utils.word_column()
    OnnurPersona_fleirtala_nutid = utils.word_column()
    ThridjaPersona_fleirtala_nutid = utils.word_column()
    # þátíð, eintala
    FyrstaPersona_eintala_thatid = utils.word_column()
    OnnurPersona_eintala_thatid = utils.word_column()
    ThridjaPersona_eintala_thatid = utils.word_column()
    # þátíð, fleirtala
    FyrstaPersona_fleirtala_thatid = utils.word_column()
    OnnurPersona_fleirtala_thatid = utils.word_column()
    ThridjaPersona_fleirtala_thatid = utils.word_column()
    Edited = utils.timestamp_edited()
    Created = utils.timestamp_created()
