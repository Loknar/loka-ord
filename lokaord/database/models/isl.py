#!/usr/bin/python
import enum

from lokaord.database.db import Base
from lokaord.database.models import utils


class Ordflokkar(enum.Enum):
    # fallorð
    Nafnord = 0
    Lysingarord = 1
    Greinir = 2  # fyrir hinn lausa greini, en viðskeyttur greinir geymdur í tvíriti í Fallbeyging
    Frumtala = 3  # - Töluorð, hafa undirflokkana Frumtölur og Raðtölur, til einföldunar eru þeir
    Radtala = 4   # / listaðir beint hér sem orðflokkar í stað þess að flokka þá sem undirflokka
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
    Stofnsamsetning = 0  # dæmi: eldhús
    Eignarfallssamsetning = 1  # dæmi: eldavél/eldsmatur (eignarfall ft af eldur er elda)
    Bandstafssamsetning = 2  # dæmi: eldiviður, fiskifluga, hangikjöt
                             #       (tengistafur iðulega i, en getur einnig verið a, u, s ..)


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
    AfturbeygtFornafn = 1  # (orðið sig)
    Eignarfornafn = 2
    Abendingarfornafn = 3
    Spurnarfornafn = 4
    OakvedidFornafn = 5


class Persona(enum.Enum):
    Fyrsta = 0
    Onnur = 1
    Thridja = 2


class Ord(Base):
    __tablename__ = 'Ord'
    Ord_id = utils.integer_primary_key()
    Ord = utils.word_column(nullable=False)
    Ordflokkur = utils.selection(Ordflokkar, Ordflokkar.Nafnord, nullable=False)
    Samsett = utils.boolean_default_false()
    Undantekning = utils.boolean_default_false()
    OsjalfstaedurOrdhluti = utils.boolean_default_false()
    Edited = utils.timestamp_edited()
    Created = utils.timestamp_created()


class SamsettOrd(Base):
    __tablename__ = 'SamsettOrd'
    SamsettOrd_id = utils.integer_primary_key()
    fk_Ord_id = utils.foreign_integer_primary_key('Ord')
    fk_FyrstiOrdHluti_id = utils.foreign_integer_primary_key('SamsettOrdhlutar')
    Edited = utils.timestamp_edited()
    Created = utils.timestamp_created()


class SamsettOrdhlutar(Base):
    __tablename__ = 'SamsettOrdhlutar'
    SamsettOrdhlutar_id = utils.integer_primary_key()
    fk_Ord_id = utils.foreign_integer_primary_key('Ord')
    Ordmynd = utils.word_column()
    Gerd = utils.selection(Ordasamsetningar, None)
    fk_NaestiOrdhluti_id = utils.foreign_integer_primary_key('SamsettOrdhlutar')
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


class Frumtala(Base):  # Töluorð - Frumtala (einn, tveir, þrír)
    __tablename__ = 'Frumtala'
    Frumtala_id = utils.integer_primary_key()
    fk_Ord_id = utils.foreign_integer_primary_key('Ord')
    Gildi = utils.integer_default_zero()
    # einungis handfylli frumtalna hafa beygingar og bara frumtalan "einn" fyllir í allar
    # beygingarmyndir, á meðan tveir, þrír og fjórir hafa beygingar í fleirtölu,
    # þá hefur frumtalan hundrað fleirtölumyndina hundruð en hefur í raun bara þessum tveimur
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


class Radtala(Base):  # Töluorð - Raðtala (fyrsti, annar, þriðji)
    __tablename__ = 'Radtala'
    Radtala_id = utils.integer_primary_key()
    fk_Ord_id = utils.foreign_integer_primary_key('Ord')
    Gildi = utils.integer_default_zero()
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
    Nefnifall = utils.word_column()
    Tholfall = utils.word_column()
    Thagufall = utils.word_column()
    Eignarfall = utils.word_column()
    Edited = utils.timestamp_edited()
    Created = utils.timestamp_created()


class Undantekning(Base):
    # Íslenska hefur helling undantekninga sem falla illa inn í strangar gagnagrunnsskilgreiningar,
    # til dæmis hafa sum orð fleiri en eina "rétta" beygingarmynd, sum orð tilheyra orðflokkum sem
    # oftast hafa enga beygingarmynd, dæmi um þetta, frumtölururnar einn, tveir, þrír og fjórir
    # fallbeygjast, sem og aðrar frumtölur sem enda á þeim, eins og tuttugu-og-einn, en aðrar
    # frumtölur fallbeygjast ekki, svo fátt eitt sé nefnt. Sum orð tilheyra fleiri en einum
    # orðflokki ofl.
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
    Typa = utils.selection(Fornafnaflokkar, Fornafnaflokkar.Personufornafn)
    Kyn = utils.selection(Kyn, None)
    Persona = utils.selection(Persona, None)
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
    Germynd_Nafnhattur = utils.word_column()  # (dæmi: að ganga)
    # sagnbót, lýsingarháttur stendur alltaf í hvorugkyni eintölu
    Germynd_Sagnbot = utils.word_column()  # (dæmi: ég hef gengið)
    # https://is.wikipedia.org/wiki/Bo%C3%B0h%C3%A1ttur#St%C3%BDf%C3%B0ur_bo%C3%B0h%C3%A1ttur
    Germynd_Bodhattur_styfdur = utils.word_column()  # Stýfður boðháttur (dæmi: gakk (þú))
    Germynd_Bodhattur_et = utils.word_column()  # (dæmi: gakktu)
    Germynd_Bodhattur_ft = utils.word_column()  # (dæmi: gangið)
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
    Germynd_spurnarmyndir_framsoguhattur_nutid_et = utils.word_column()
    Germynd_spurnarmyndir_framsoguhattur_nutid_ft = utils.word_column()
    Germynd_spurnarmyndir_framsoguhattur_thatid_et = utils.word_column()
    Germynd_spurnarmyndir_framsoguhattur_thatid_ft = utils.word_column()
    Germynd_spurnarmyndir_vidtengingarhattur_nutid_et = utils.word_column()
    Germynd_spurnarmyndir_vidtengingarhattur_nutid_ft = utils.word_column()
    Germynd_spurnarmyndir_vidtengingarhattur_thatid_et = utils.word_column()
    Germynd_spurnarmyndir_vidtengingarhattur_thatid_ft = utils.word_column()
    # https://is.wikipedia.org/wiki/Mi%C3%B0mynd
    # miðmynd (segir frá því hvað gerandi/gerendur gerir/gera við eða fyrir sjálfan/sjálfa sig)
    Midmynd_Nafnhattur = utils.word_column()  # (dæmi: að gefast)
    Midmynd_Sagnbot = utils.word_column()  # (dæmi: ég hef gefist)
    Midmynd_Bodhattur_et = utils.word_column()  # (dæmi: gefstu upp)
    Midmynd_Bodhattur_ft = utils.word_column()  # (dæmi: gefist upp)
    # framsöguháttur (ég/þú/[hann/hún/það], dæmi: ég gengst)
    fk_Midmynd_personuleg_framsoguhattur = utils.foreign_integer_primary_key('Sagnbeyging')
    # viðtengingarháttur (þó ég/þú/[hann/hún/það], dæmi: þó ég gangist)
    fk_Midmynd_personuleg_vidtengingarhattur = utils.foreign_integer_primary_key('Sagnbeyging')
    # ópersónuleg miðmynd
    Midmynd_opersonuleg_frumlag = utils.selection(Fall, None)
    fk_Midmynd_opersonuleg_framsoguhattur = utils.foreign_integer_primary_key('Sagnbeyging')
    fk_Midmynd_opersonuleg_vidtengingarhattur = utils.foreign_integer_primary_key('Sagnbeyging')
    # spurnarmyndir, önnur persóna samtengd sögn (dæmi: býst þú -> býstu, gefst þú -> gefstu)
    # ATH:
    # veit ekki um sagnorð sem hafa fleirtölu í spurnarmyndum í miðmynd, ef slíkt væri til þá væru
    # það orðmyndir eins og "gefisti", "gáfusti" og "gæfusti" fyrir sögnina að gefa, vissulega væri
    # hægt að skapa venju fyrir slíkum myndum en það hefur ekki verið venja hingað til
    Midmynd_spurnarmyndir_framsoguhattur_nutid_et = utils.word_column()
    # Midmynd_spurnarmyndir_framsoguhattur_nutid_ft = utils.word_column()
    Midmynd_spurnarmyndir_framsoguhattur_thatid_et = utils.word_column()
    # Midmynd_spurnarmyndir_framsoguhattur_thatid_ft = utils.word_column()
    Midmynd_spurnarmyndir_vidtengingarhattur_nutid_et = utils.word_column()
    # Midmynd_spurnarmyndir_vidtengingarhattur_nutid_ft = utils.word_column()
    Midmynd_spurnarmyndir_vidtengingarhattur_thatid_et = utils.word_column()
    # Midmynd_spurnarmyndir_vidtengingarhattur_thatid_ft = utils.word_column()
    # lýsingarháttur nútíðar
    LysingarhatturNutidar = utils.word_column()  # (dæmi: gangandi)
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


class Karlmannsnafn(Base):
    __tablename__ = 'Karlmannsnafn'
    Karlmannsnafn_id = utils.integer_primary_key()
    Nafn = utils.word_column()
    fk_Fallbeyging_id = utils.foreign_integer_primary_key('Fallbeyging')
    Edited = utils.timestamp_edited()
    Created = utils.timestamp_created()


class Kvenmannsnafn(Base):
    __tablename__ = 'Kvenmannsnafn'
    Kvenmannsnafn_id = utils.integer_primary_key()
    Nafn = utils.word_column()
    fk_Fallbeyging_id = utils.foreign_integer_primary_key('Fallbeyging')
    Edited = utils.timestamp_edited()
    Created = utils.timestamp_created()
