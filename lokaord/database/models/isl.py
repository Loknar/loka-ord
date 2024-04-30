#!/usr/bin/python
import enum

from lokaord.database.db import Base
from lokaord.database.models import utils


class Ordflokkar(enum.Enum):
	# fallorð
	Nafnord = 0
	Lysingarord = 1
	Greinir = 2  # fyrir hinn lausa greini, en viðskeyttur greinir geymdur í tvíriti í Fallbeyging
	Fornafn = 3
	Fjoldatala = 4  # - Töluorð, hafa undirflokkana Fjöldatölur og Raðtölur, til hagræðingar eru
	Radtala = 5   # / þeir listaðir beint hér sem orðflokkar í stað þess að flokka sem undirflokka
	# sagnorð
	Sagnord = 6
	# smáorð / óbeygjanleg orð, undirflokkar listaðir beint sem orðflokkar eins og töluorðin
	Forsetning = 7
	Atviksord = 8
	Nafnhattarmerki = 9
	Samtenging = 10
	Upphropun = 11
	# sérnöfn (mannanöfn, örnefni)
	Sernafn = 12


class Ordasamsetningar(enum.Enum):
	Stofnsamsetning = 0  # dæmi: eldhús
	Eignarfallssamsetning = 1  # dæmi: eldavél/eldsmatur (eignarfall ft af eldur er elda)
	Bandstafssamsetning = 2  # dæmi: eldiviður, fiskifluga, hangikjöt
	#                                (tengistafur iðulega i, en getur einnig verið a, u, s ..)


class Kyn(enum.Enum):
	Kvenkyn = 0
	Karlkyn = 1
	Hvorugkyn = 2


class Fall(enum.Enum):
	Nefnifall = 0
	Tholfall = 1
	Thagufall = 2
	Eignarfall = 3


class Persona(enum.Enum):
	Fyrsta = 0
	Onnur = 1
	Thridja = 2


class Fornafnaflokkar(enum.Enum):
	Personufornafn = 0
	AfturbeygtFornafn = 1  # (orðið sig)
	Eignarfornafn = 2
	Abendingarfornafn = 3
	Spurnarfornafn = 4
	OakvedidFornafn = 5


class FleiryrtTypa(enum.Enum):
	Hlekkjud = 0
	Laus = 1


class Sernafnaflokkar(enum.Enum):
	Eiginnafn = 0
	Gaelunafn = 1
	Kenninafn = 2
	Millinafn = 3
	Ornefni = 4


class LysingarordMyndir(enum.Enum):
	Frumstig_vb_kk = 0
	Frumstig_vb_kvk = 1
	Frumstig_vb_hk = 2
	Midstig_vb_kk = 3
	Midstig_vb_kvk = 4
	Midstig_vb_hk = 5
	Efstastig_vb_kk = 6
	Efstastig_vb_kvk = 7
	Efstastig_vb_hk = 8


# ------------------ #
# Gagnagrunns-töflur #
# ------------------ #


class Ord(Base):
	__tablename__ = 'Ord'
	Ord_id = utils.integer_primary_key()
	Ord = utils.word(nullable=False)
	Ordflokkur = utils.selection(Ordflokkar, Ordflokkar.Nafnord, nullable=False)
	Samsett = utils.boolean_default_false()
	Tolugildi = utils.decimal()
	Undantekning = utils.boolean_default_false()
	OsjalfstaedurOrdhluti = utils.boolean_default_false()
	Obeygjanlegt = utils.boolean_default_false()
	Merking = utils.word()
	Kennistrengur = utils.word(nullable=False, unique=True)
	Edited = utils.timestamp_edited()
	Created = utils.timestamp_created()


class SamsettOrd(Base):
	__tablename__ = 'SamsettOrd'
	SamsettOrd_id = utils.integer_primary_key()
	fk_Ord_id = utils.foreign_integer_primary_key('Ord')
	fk_FyrstiOrdHluti_id = utils.foreign_integer_primary_key('SamsettOrdhluti')
	Edited = utils.timestamp_edited()
	Created = utils.timestamp_created()


class SamsettOrdhluti(Base):
	__tablename__ = 'SamsettOrdhluti'
	SamsettOrdhluti_id = utils.integer_primary_key()
	fk_Ord_id = utils.foreign_integer_primary_key('Ord')
	Ordmynd = utils.word()
	Gerd = utils.selection(Ordasamsetningar, None)
	LysingarordMyndir = utils.selection(LysingarordMyndir, None)
	fk_NaestiOrdhluti_id = utils.foreign_integer_primary_key('SamsettOrdhluti')
	Lagstafa = utils.boolean_default_false()  # stilling til að lágstafa orðhluta
	Hastafa = utils.boolean_default_false()  # stilling til að hástafa upphafsstaf orðhluta
	Leidir = utils.word()
	Fylgir = utils.word()
	# <Beygingar-filters>
	# nafnorð/sérnöfn
	Exclude_et_ag = utils.boolean_default_false()
	Exclude_et_mg = utils.boolean_default_false()
	Exclude_ft_ag = utils.boolean_default_false()
	Exclude_ft_mg = utils.boolean_default_false()
	# lýsingarorð
	Exclude_frumstig_sb_et = utils.boolean_default_false()
	Exclude_frumstig_sb_ft = utils.boolean_default_false()
	Exclude_frumstig_vb_et = utils.boolean_default_false()
	Exclude_frumstig_vb_ft = utils.boolean_default_false()
	Exclude_midstig_vb_et = utils.boolean_default_false()
	Exclude_midstig_vb_ft = utils.boolean_default_false()
	Exclude_efstastig_sb_et = utils.boolean_default_false()
	Exclude_efstastig_sb_ft = utils.boolean_default_false()
	Exclude_efstastig_vb_et = utils.boolean_default_false()
	Exclude_efstastig_vb_ft = utils.boolean_default_false()
	# sagnorð
	Exclude_germynd_personuleg = utils.boolean_default_false()
	Exclude_germynd_opersonuleg = utils.boolean_default_false()
	Exclude_germynd_spurnarmyndir = utils.boolean_default_false()
	Exclude_midmynd_personuleg = utils.boolean_default_false()
	Exclude_midmynd_opersonuleg = utils.boolean_default_false()
	Exclude_midmynd_spurnarmyndir = utils.boolean_default_false()
	Exclude_lysingarhattur_nutidar = utils.boolean_default_false()
	Exclude_lysingarhattur_thatidar = utils.boolean_default_false()
	Exclude_lysingarhattur_thatidar_sb = utils.boolean_default_false()
	Exclude_lysingarhattur_thatidar_vb = utils.boolean_default_false()
	# </Beygingar-filters>
	Edited = utils.timestamp_edited()
	Created = utils.timestamp_created()


class Nafnord(Base):
	__tablename__ = 'Nafnord'
	Nafnord_id = utils.integer_primary_key()
	fk_Ord_id = utils.foreign_integer_primary_key('Ord')
	Kyn = utils.selection(Kyn, Kyn.Karlkyn)
	fk_et_Fallbeyging_id = utils.foreign_integer_primary_key('Fallbeyging')
	fk_et_mgr_Fallbeyging_id = utils.foreign_integer_primary_key('Fallbeyging')
	fk_ft_Fallbeyging_id = utils.foreign_integer_primary_key('Fallbeyging')
	fk_ft_mgr_Fallbeyging_id = utils.foreign_integer_primary_key('Fallbeyging')
	Edited = utils.timestamp_edited()
	Created = utils.timestamp_created()


class Lysingarord(Base):
	__tablename__ = 'Lysingarord'
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
	__tablename__ = 'Greinir'
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


class Fjoldatala(Base):  # Töluorð - Fjöldatala (einn, tveir, þrír, fjórir ..)
	__tablename__ = 'Fjoldatala'
	Fjoldatala_id = utils.integer_primary_key()
	fk_Ord_id = utils.foreign_integer_primary_key('Ord')
	Gildi = utils.decimal()
	# einungis handfylli földatalna hafa beygingar og bara fjöldatalan "einn" fyllir í allar
	# beygingarmyndir, á meðan tveir, þrír og fjórir hafa beygingar í fleirtölu,
	# þá hefur fjöldatalan hundrað fleirtölumyndina hundruð en hefur í raun bara þessum tveimur
	# beygingarmyndum að skarta
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


class Radtala(Base):  # Töluorð - Raðtala (fyrsti, annar, þriðji, fjórði ..)
	__tablename__ = 'Radtala'
	Radtala_id = utils.integer_primary_key()
	fk_Ord_id = utils.foreign_integer_primary_key('Ord')
	Gildi = utils.decimal()
	# raðtölur hafa einungis eina (veika) beygingu, nema "fyrstur" sem hefur sterka og veika
	# raðtalan "annar" hefur eina beygingu, en hún er þó álitin sterk beyging frekar en veik
	# sterk beyging
	fk_sb_et_kk_Fallbeyging_id = utils.foreign_integer_primary_key('Fallbeyging')
	fk_sb_et_kvk_Fallbeyging_id = utils.foreign_integer_primary_key('Fallbeyging')
	fk_sb_et_hk_Fallbeyging_id = utils.foreign_integer_primary_key('Fallbeyging')
	fk_sb_ft_kk_Fallbeyging_id = utils.foreign_integer_primary_key('Fallbeyging')
	fk_sb_ft_kvk_Fallbeyging_id = utils.foreign_integer_primary_key('Fallbeyging')
	fk_sb_ft_hk_Fallbeyging_id = utils.foreign_integer_primary_key('Fallbeyging')
	# veig beyging
	fk_vb_et_kk_Fallbeyging_id = utils.foreign_integer_primary_key('Fallbeyging')
	fk_vb_et_kvk_Fallbeyging_id = utils.foreign_integer_primary_key('Fallbeyging')
	fk_vb_et_hk_Fallbeyging_id = utils.foreign_integer_primary_key('Fallbeyging')
	fk_vb_ft_kk_Fallbeyging_id = utils.foreign_integer_primary_key('Fallbeyging')
	fk_vb_ft_kvk_Fallbeyging_id = utils.foreign_integer_primary_key('Fallbeyging')
	fk_vb_ft_hk_Fallbeyging_id = utils.foreign_integer_primary_key('Fallbeyging')
	Edited = utils.timestamp_edited()
	Created = utils.timestamp_created()


class Fallbeyging(Base):
	__tablename__ = 'Fallbeyging'
	Fallbeyging_id = utils.integer_primary_key()
	Nefnifall = utils.word()
	Tholfall = utils.word()
	Thagufall = utils.word()
	Eignarfall = utils.word()
	Edited = utils.timestamp_edited()
	Created = utils.timestamp_created()


class Undantekning(Base):
	# Íslenska hefur helling undantekninga sem falla illa inn í strangar gagnagrunnsskilgreiningar,
	# til dæmis hafa sum orð fleiri en eina "rétta" beygingarmynd, ofl.
	__tablename__ = 'Undantekning'
	Undantekning_id = utils.integer_primary_key()
	fk_Ord_id = utils.foreign_integer_primary_key('Ord')
	Data = utils.json_object()
	Edited = utils.timestamp_edited()
	Created = utils.timestamp_created()


class Fornafn(Base):
	__tablename__ = 'Fornafn'
	Fornafn_id = utils.integer_primary_key()
	fk_Ord_id = utils.foreign_integer_primary_key('Ord')
	Undirflokkur = utils.selection(Fornafnaflokkar, Fornafnaflokkar.Personufornafn)
	Persona = utils.selection(Persona, None)
	Kyn = utils.selection(Kyn, None)
	# kynlausar beygingar -------------------------------------------------------------------------
	# þ.e. beygingarmyndirnar falla ekki undir, eru eins í öllum kynjum, eða eru bundin einu
	# tilgreindu (ofangreindu, í "Kyn" gildinu) kyni
	# eintala
	fk_et_Fallbeyging_id = utils.foreign_integer_primary_key('Fallbeyging')
	# fleirtala
	fk_ft_Fallbeyging_id = utils.foreign_integer_primary_key('Fallbeyging')
	# kynbundnar beygingar ------------------------------------------------------------------------
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


class Sagnord(Base):
	__tablename__ = 'Sagnord'
	Sagnord_id = utils.integer_primary_key()
	fk_Ord_id = utils.foreign_integer_primary_key('Ord')
	# https://is.wikipedia.org/wiki/H%C3%A6ttir_sagna_%C3%AD_%C3%ADslensku
	# tilgreina hvort sögn er sterk eða veik?
	# https://is.wikipedia.org/wiki/Sagnmyndir#Germynd
	# germynd (áherslan er á geranda setningarinnar)
	Germynd_Nafnhattur = utils.word()  # (dæmi: að ganga)
	# sagnbót, lýsingarháttur stendur alltaf í hvorugkyni eintölu
	Germynd_Sagnbot = utils.word()  # (dæmi: ég hef gengið)
	# https://is.wikipedia.org/wiki/Bo%C3%B0h%C3%A1ttur#St%C3%BDf%C3%B0ur_bo%C3%B0h%C3%A1ttur
	Germynd_Bodhattur_styfdur = utils.word()  # Stýfður boðháttur (dæmi: gakk (þú))
	Germynd_Bodhattur_et = utils.word()  # (dæmi: gakktu)
	Germynd_Bodhattur_ft = utils.word()  # (dæmi: gangið)
	# framsöguháttur (ég/þú/[hann/hún/það], dæmi: ég geng)
	fk_Germynd_personuleg_framsoguhattur = utils.foreign_integer_primary_key('Sagnbeyging')
	# viðtengingarháttur (þó ég/þú/[hann/hún/það], dæmi: þó ég gangi)
	fk_Germynd_personuleg_vidtengingarhattur = utils.foreign_integer_primary_key('Sagnbeyging')
	# ópersónuleg germynd (frumlag í þolfalli, þó mig/þig/[hann/hana/það], dæmi: þó mig minni, eða
	# í þágufalli, þó mér/þér/[honum/henni/því], dæmi: þó mér þyki)
	Germynd_opersonuleg_frumlag = utils.selection(Fall, None)
	fk_Germynd_opersonuleg_framsoguhattur = utils.foreign_integer_primary_key('Sagnbeyging')
	fk_Germynd_opersonuleg_vidtengingarhattur = utils.foreign_integer_primary_key('Sagnbeyging')
	# spurnarmyndir, önnur persóna samtengd sögn (dæmi: býrð þú -> býrðu, gefur þú -> gefurðu)
	Germynd_spurnarmyndir_framsoguhattur_nutid_et = utils.word()
	Germynd_spurnarmyndir_framsoguhattur_nutid_ft = utils.word()
	Germynd_spurnarmyndir_framsoguhattur_thatid_et = utils.word()
	Germynd_spurnarmyndir_framsoguhattur_thatid_ft = utils.word()
	Germynd_spurnarmyndir_vidtengingarhattur_nutid_et = utils.word()
	Germynd_spurnarmyndir_vidtengingarhattur_nutid_ft = utils.word()
	Germynd_spurnarmyndir_vidtengingarhattur_thatid_et = utils.word()
	Germynd_spurnarmyndir_vidtengingarhattur_thatid_ft = utils.word()
	# https://is.wikipedia.org/wiki/Mi%C3%B0mynd
	# miðmynd (segir frá því hvað gerandi/gerendur gerir/gera við eða fyrir sjálfan/sjálfa sig)
	Midmynd_Nafnhattur = utils.word()  # (dæmi: að gefast)
	Midmynd_Sagnbot = utils.word()  # (dæmi: ég hef gefist)
	Midmynd_Bodhattur_et = utils.word()  # (dæmi: gefstu upp)
	Midmynd_Bodhattur_ft = utils.word()  # (dæmi: gefist upp)
	# framsöguháttur (ég/þú/[hann/hún/það], dæmi: ég gengst)
	fk_Midmynd_personuleg_framsoguhattur = utils.foreign_integer_primary_key('Sagnbeyging')
	# viðtengingarháttur (þó ég/þú/[hann/hún/það], dæmi: þó ég gangist)
	fk_Midmynd_personuleg_vidtengingarhattur = utils.foreign_integer_primary_key('Sagnbeyging')
	# ópersónuleg miðmynd
	Midmynd_opersonuleg_frumlag = utils.selection(Fall, None)
	fk_Midmynd_opersonuleg_framsoguhattur = utils.foreign_integer_primary_key('Sagnbeyging')
	fk_Midmynd_opersonuleg_vidtengingarhattur = utils.foreign_integer_primary_key('Sagnbeyging')
	# spurnarmyndir, önnur persóna samtengd sögn (dæmi: býst þú -> býstu, gefst þú -> gefstu)
	Midmynd_spurnarmyndir_framsoguhattur_nutid_et = utils.word()
	Midmynd_spurnarmyndir_framsoguhattur_nutid_ft = utils.word()
	Midmynd_spurnarmyndir_framsoguhattur_thatid_et = utils.word()
	Midmynd_spurnarmyndir_framsoguhattur_thatid_ft = utils.word()
	Midmynd_spurnarmyndir_vidtengingarhattur_nutid_et = utils.word()
	Midmynd_spurnarmyndir_vidtengingarhattur_nutid_ft = utils.word()
	Midmynd_spurnarmyndir_vidtengingarhattur_thatid_et = utils.word()
	Midmynd_spurnarmyndir_vidtengingarhattur_thatid_ft = utils.word()
	# lýsingarháttur nútíðar
	LysingarhatturNutidar = utils.word()  # (dæmi: gangandi)
	# lýsingarháttur þátíðar (þolmyndir)
	fk_LysingarhatturThatidar_sb_et_kk_id = utils.foreign_integer_primary_key('Fallbeyging')
	fk_LysingarhatturThatidar_sb_et_kvk_id = utils.foreign_integer_primary_key('Fallbeyging')
	fk_LysingarhatturThatidar_sb_et_hk_id = utils.foreign_integer_primary_key('Fallbeyging')
	fk_LysingarhatturThatidar_sb_ft_kk_id = utils.foreign_integer_primary_key('Fallbeyging')
	fk_LysingarhatturThatidar_sb_ft_kvk_id = utils.foreign_integer_primary_key('Fallbeyging')
	fk_LysingarhatturThatidar_sb_ft_hk_id = utils.foreign_integer_primary_key('Fallbeyging')
	fk_LysingarhatturThatidar_vb_et_kk_id = utils.foreign_integer_primary_key('Fallbeyging')
	fk_LysingarhatturThatidar_vb_et_kvk_id = utils.foreign_integer_primary_key('Fallbeyging')
	fk_LysingarhatturThatidar_vb_et_hk_id = utils.foreign_integer_primary_key('Fallbeyging')
	fk_LysingarhatturThatidar_vb_ft_kk_id = utils.foreign_integer_primary_key('Fallbeyging')
	fk_LysingarhatturThatidar_vb_ft_kvk_id = utils.foreign_integer_primary_key('Fallbeyging')
	fk_LysingarhatturThatidar_vb_ft_hk_id = utils.foreign_integer_primary_key('Fallbeyging')
	# Óskháttur
	# https://is.wikipedia.org/wiki/%C3%93skh%C3%A1ttur
	Oskhattur_1p_ft = utils.word()
	Oskhattur_3p = utils.word()
	Edited = utils.timestamp_edited()
	Created = utils.timestamp_created()


class Sagnbeyging(Base):
	# persónu-, tölu- og tíðarbeyging (ég/þú/[hann/hún/það], eintala/fleirtala, nútíð/þátíð)
	__tablename__ = 'Sagnbeyging'
	Sagnbeyging_id = utils.integer_primary_key()
	# nútíð, eintala
	FyrstaPersona_eintala_nutid = utils.word()
	OnnurPersona_eintala_nutid = utils.word()
	ThridjaPersona_eintala_nutid = utils.word()
	# nútíð, fleirtala
	FyrstaPersona_fleirtala_nutid = utils.word()
	OnnurPersona_fleirtala_nutid = utils.word()
	ThridjaPersona_fleirtala_nutid = utils.word()
	# þátíð, eintala
	FyrstaPersona_eintala_thatid = utils.word()
	OnnurPersona_eintala_thatid = utils.word()
	ThridjaPersona_eintala_thatid = utils.word()
	# þátíð, fleirtala
	FyrstaPersona_fleirtala_thatid = utils.word()
	OnnurPersona_fleirtala_thatid = utils.word()
	ThridjaPersona_fleirtala_thatid = utils.word()
	Edited = utils.timestamp_edited()
	Created = utils.timestamp_created()


class Forsetning(Base):
	# Forsetning er óbeygjanlegt smáorð sem stendur oftast á undan fallorði og stýrir fallinu
	# (veldur því að fallorðið standi í aukafalli—þolfalli, þágufalli eða eignarfalli).
	#
	# Margar forsetningar stýra aðeins einu ákveðnu falli.
	#
	# Sumar forsetningar geta stýrt tveimur föllum, t.d. Í stofuna (þf.), Í stofunni (þgf.).
	# Merking ræður þessu, hreyfing eða stefna er alltaf í þolfalli en dvöl eða kyrrstaða í
	# þágufalli.
	#
	# Forsetning getur staðið ein og sér, þ.e. án fallorðs, en þjónar þá stöðu atviksorðs, t.d. ég
	# þakka fyrir (fallorði sleppt). Að sama skapi eru margar forsetningar upprunalega atviksorð
	# sem verða að forsetningum þegar þau stýra falli, t.d. garðurinn er neðan árinnar.
	#
	# - https://is.wikipedia.org/wiki/Forsetning
	__tablename__ = 'Forsetning'
	Forsetning_id = utils.integer_primary_key()
	fk_Ord_id = utils.foreign_integer_primary_key('Ord')
	StyrirTholfalli = utils.boolean_default_false()
	StyrirThagufalli = utils.boolean_default_false()
	StyrirEignarfalli = utils.boolean_default_false()
	Edited = utils.timestamp_edited()
	Created = utils.timestamp_created()


class Atviksord(Base):
	# Atviksorð líkjast lýsingarorðum enda hafa atviksorð þá sérstöðu á meðal smáorða að sum
	# atviksorð stigbreytast (eins og ‚aftur - aftar - aftast‘; ‚lengi - lengur - lengst‘;
	# ‚inn - innar - innst‘; ‚vel - betur - best‘), en eru þau þó annars eðlis en lýsingarorð.
	__tablename__ = 'Atviksord'
	Atviksord_id = utils.integer_primary_key()
	fk_Ord_id = utils.foreign_integer_primary_key('Ord')
	Midstig = utils.word()
	Efstastig = utils.word()
	Edited = utils.timestamp_edited()
	Created = utils.timestamp_created()


class SamtengingFleiryrt(Base):
	# https://is.wikipedia.org/wiki/Samtenging
	# https://is.wikipedia.org/wiki/Fleiryrt_samtenging
	__tablename__ = 'SamtengingFleiryrt'
	SamtengingFleiryrt_id = utils.integer_primary_key()
	fk_Ord_id = utils.foreign_integer_primary_key('Ord')
	Ord = utils.word(nullable=False)
	fk_SamtengingFleiryrt_id = utils.foreign_integer_primary_key('SamtengingFleiryrt')
	Typa = utils.selection(FleiryrtTypa, None)
	Edited = utils.timestamp_edited()
	Created = utils.timestamp_created()


class Sernafn(Base):
	__tablename__ = 'Sernafn'
	Sernafn_id = utils.integer_primary_key()
	fk_Ord_id = utils.foreign_integer_primary_key('Ord')
	Undirflokkur = utils.selection(Sernafnaflokkar, Sernafnaflokkar.Eiginnafn)
	Kyn = utils.selection(Kyn, None)
	fk_et_Fallbeyging_id = utils.foreign_integer_primary_key('Fallbeyging')
	fk_et_mgr_Fallbeyging_id = utils.foreign_integer_primary_key('Fallbeyging')
	fk_ft_Fallbeyging_id = utils.foreign_integer_primary_key('Fallbeyging')
	fk_ft_mgr_Fallbeyging_id = utils.foreign_integer_primary_key('Fallbeyging')
	Edited = utils.timestamp_edited()
	Created = utils.timestamp_created()


class Skammstofun(Base):
	__tablename__ = 'Skammstofun'
	Skammstofun_id = utils.integer_primary_key()
	Skammstofun = utils.word(nullable=False)
	Merking = utils.word()
	Kennistrengur = utils.word(nullable=False, unique=True)
	Edited = utils.timestamp_edited()
	Created = utils.timestamp_created()


class SkammstofunFrasi(Base):
	__tablename__ = 'SkammstofunFrasi'
	SkammstofunFrasi_id = utils.integer_primary_key()
	fk_Skammstofun_id = utils.foreign_integer_primary_key('Skammstofun')
	fk_Ord_id = utils.foreign_integer_primary_key('Ord')
	Edited = utils.timestamp_edited()
	Created = utils.timestamp_created()


class SkammstofunMynd(Base):
	__tablename__ = 'SkammstofunMynd'
	SkammstofunMynd_id = utils.integer_primary_key()
	fk_Skammstofun_id = utils.foreign_integer_primary_key('Skammstofun')
	Mynd = utils.word(nullable=False)
	Edited = utils.timestamp_edited()
	Created = utils.timestamp_created()
