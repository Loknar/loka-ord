#!/usr/bin/python
"""
Data structure definitions and validation for word files, powered mostly by pydantic.
"""
from collections import OrderedDict
from decimal import Decimal
from enum import Enum
import json
import os
from typing import Union

from pydantic import BaseModel, conlist, Field, root_validator, StrictStr, validator


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

    def get_all_names_isl():
        return [flokkur.value for flokkur in Ordflokkar]

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
    Gaelunafn = 'gælunafn', 'sérn.gn', os.path.join('sernofn', 'mannanofn')
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
    Et_ag = 'et-ág'
    Et_mg = 'et-mg'
    Ft_ag = 'ft-ág'
    Ft_mg = 'ft-mg'


class Fall(str, Enum):
    Nefnifall = 'nefnifall'
    Tholfall = 'þolfall'
    Thagufall = 'þágufall'
    Eignarfall = 'eignarfall'


class Fall2(str, Enum):
    Tholfall = 'þolfall'
    Thagufall = 'þágufall'
    Eignarfall = 'eignarfall'


class Persona(str, Enum):
    Fyrsta = 'fyrsta'
    Onnur = 'önnur'
    Thridja = 'þriðja'


class FleiryrtTypa(str, Enum):
    Hlekkjud = 'hlekkjuð'
    Laus = 'laus'


class NonEmptyStr(StrictStr):
    min_length=1


class SamsettOrdhluti(BaseModel):

    mynd: NonEmptyStr | None
    samsetning: Ordasamsetningar | None
    myndir: LysingarordMyndir | None
    orð: NonEmptyStr | None
    flokkur: Ordflokkar | None
    undirflokkur: Fornafnaflokkar | Toluordaflokkar | Smaordaflokkar | Sernafnaflokkar | None
    kyn: Kyn | None
    merking: NonEmptyStr | None
    lágstafa: bool | None = False
    hástafa: bool | None = False
    leiðir: NonEmptyStr | None
    fylgir: NonEmptyStr | None
    beygingar: conlist(NafnordaBeygingar, min_items=1, max_items=4, unique_items=True) | None
    ósjálfstætt: bool | None = False
    datahash: NonEmptyStr | None = Field(alias='hash')
    kennistrengur: NonEmptyStr | None

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

    @validator('undirflokkur')
    def undirflokkur_constraints_based_on_flokkur(cls, val, values, **kwargs):
        fl_m_ufl = (Ordflokkar.Fornafn, Ordflokkar.Toluord, Ordflokkar.Smaord, Ordflokkar.Sernafn)
        if values['flokkur'] in fl_m_ufl:
            if val is None:
                raise ValueError('missing undirflokkur')
        if values['flokkur'] is Ordflokkar.Fornafn and type(val) is not Fornafnaflokkar:
            raise ValueError('invalid fornafn undirflokkur')
        if values['flokkur'] is Ordflokkar.Toluord and type(val) is not Toluordaflokkar:
            raise ValueError('invalid töluorð undirflokkur')
        if values['flokkur'] is Ordflokkar.Smaord and type(val) is not Smaordaflokkar:
            raise ValueError('invalid smáorð undirflokkur')
        if values['flokkur'] is Ordflokkar.Sernafn and type(val) is not Sernafnaflokkar:
            raise ValueError('invalid sérnafn undirflokkur')
        return val

    @validator('kyn')
    def kyn_restrictions(cls, val, values, **kwargs):
        if val is not None and values['flokkur'] not in (
            Ordflokkar.Nafnord, Ordflokkar.Fornafn, Ordflokkar.Sernafn
        ):
            raise ValueError('kyn is set only for nafnorð, fornöfn and sérnöfn')
        return val

    @validator('hástafa')
    def hastafa_lagstafa_mutually_exclusive(cls, val, values, **kwargs):
        if val is True and 'lágstafa' in values and values['lágstafa'] is True:
            raise ValueError('hástafa and lágstafa are mutually exclusive')
        return val

    @root_validator
    def kyn_requirements_post_check(cls, values):
        if values.get('kyn') is None:
            if values.get('flokkur') == Ordflokkar.Nafnord:
                raise ValueError('kyn should always be set for nafnorð')
            if (
                values.get('flokkur') == Ordflokkar.Sernafn and
                values.get('undirflokkur') != Sernafnaflokkar.Millinafn
            ):
                raise ValueError('kyn should always be set for sérnafn other than miłlinöfn')
        return values

    def dict(self, *args, **kwargs):
        data_dict = super().dict(*args, **kwargs)
        data = OrderedDict()
        key_order = [
            'mynd', 'samsetning', 'myndir', 'orð', 'flokkur', 'undirflokkur', 'kyn', 'merking',
            'lágstafa', 'hástafa', 'leiðir', 'fylgir', 'beygingar', 'ósjálfstætt', 'datahash',
            'kennistrengur'
        ]
        key_map = {'datahash': 'hash'}
        keys_values = ('samsetning', 'myndir', 'flokkur', 'undirflokkur', 'kyn')
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
                elif key in key_map:
                    data[key_map[key]] = data_dict[key]
                elif key in keys_only_if_true:
                    if data_dict[key] is True:
                        data[key] = data_dict[key]
                else:
                    data[key] = data_dict[key]
        return data


class OrdData(BaseModel):
    orð: NonEmptyStr
    flokkur: Ordflokkar
    undirflokkur: Fornafnaflokkar | Toluordaflokkar | Smaordaflokkar | Sernafnaflokkar | None
    merking: NonEmptyStr | None
    samsett: conlist(SamsettOrdhluti, min_items=1) | None
    tölugildi: Decimal | None
    óbeygjanlegt: bool | None
    ósjálfstætt: bool | None
    datahash: NonEmptyStr | None = Field(alias='hash')
    kennistrengur: NonEmptyStr | None

    @validator('undirflokkur')
    def undirflokkur_constraints_based_on_flokkur(cls, val, values, **kwargs):
        fl_m_ufl = (Ordflokkar.Fornafn, Ordflokkar.Toluord, Ordflokkar.Smaord, Ordflokkar.Sernafn)
        if values['flokkur'] in fl_m_ufl:
            if val is None:
                raise ValueError('missing undirflokkur')
        if values['flokkur'] is Ordflokkar.Fornafn and type(val) is not Fornafnaflokkar:
            raise ValueError('invalid fornafn undirflokkur')
        if values['flokkur'] is Ordflokkar.Toluord and type(val) is not Toluordaflokkar:
            raise ValueError('invalid töluorð undirflokkur')
        if values['flokkur'] is Ordflokkar.Smaord and type(val) is not Smaordaflokkar:
            raise ValueError('invalid smáorð undirflokkur')
        if values['flokkur'] is Ordflokkar.Sernafn and type(val) is not Sernafnaflokkar:
            raise ValueError('invalid sérnafn undirflokkur')
        return val


class NafnordBeygingarAgMgSet(BaseModel):
    ág: conlist(NonEmptyStr, min_items=4, max_items=4) | None
    mg: conlist(NonEmptyStr, min_items=4, max_items=4) | None

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

    def dict(self, *args, **kwargs):
        data_dict = super().dict(*args, **kwargs)
        data = OrderedDict()
        if 'ág' in data_dict and data_dict['ág'] is not None:
            data['ág'] = data_dict['ág']
        if 'mg' in data_dict and data_dict['mg'] is not None:
            data['mg'] = data_dict['mg']
        return data


class NafnordData(OrdData):
    kyn: Kyn
    et: NafnordBeygingarAgMgSet | None
    ft: NafnordBeygingarAgMgSet | None

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

    def dict(self, *args, **kwargs):
        data_dict = super().dict(*args, **kwargs)
        data = OrderedDict()
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
    kk: conlist(NonEmptyStr, min_items=4, max_items=4)
    kvk: conlist(NonEmptyStr, min_items=4, max_items=4)
    hk: conlist(NonEmptyStr, min_items=4, max_items=4)

    def dict(self, *args, **kwargs):
        data_dict = super().dict(*args, **kwargs)
        return OrderedDict({
            'kk': data_dict['kk'], 'kvk': data_dict['kvk'], 'hk': data_dict['hk']
        })


class LysingarordEtFt(BaseModel):
    et: LysingarordKyn | None
    ft: LysingarordKyn | None

    def dict(self, *args, **kwargs):
        data_dict = super().dict(*args, **kwargs)
        return OrderedDict({'et': data_dict['et'], 'ft': data_dict['ft']})


class LysingarordStig(BaseModel):
    sb: LysingarordEtFt | None
    vb: LysingarordEtFt | None

    def dict(self, *args, **kwargs):
        data_dict = super().dict(*args, **kwargs)
        data = OrderedDict()
        if 'sb' in data_dict and data_dict['sb'] is not None:
            data['sb'] = data_dict['sb']
        if 'vb' in data_dict and data_dict['vb'] is not None:
            data['vb'] = data_dict['vb']
        return data


class LysingarordData(OrdData):
    frumstig: LysingarordStig | None
    miðstig: LysingarordStig | None
    efstastig: LysingarordStig | None

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

    def dict(self, *args, **kwargs):
        data_dict = super().dict(*args, **kwargs)
        data = OrderedDict()
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
    stýfður: NonEmptyStr | None
    et: NonEmptyStr | None
    ft: NonEmptyStr | None

    def dict(self, *args, **kwargs):
        data_dict = super().dict(*args, **kwargs)
        data = OrderedDict()
        if 'stýfður' in data_dict and data_dict['stýfður'] is not None:
            data['stýfður'] = data_dict['stýfður']
        if 'et' in data_dict and data_dict['et'] is not None:
            data['et'] = data_dict['et']
        if 'ft' in data_dict and data_dict['ft'] is not None:
            data['ft'] = data_dict['ft']
        return data


class SagnordTalaL(BaseModel):
    et: conlist(NonEmptyStr, min_items=3, max_items=3) | None
    ft: conlist(NonEmptyStr, min_items=3, max_items=3) | None

    @validator('ft')
    def et_ft_constraint(cls, val, values, **kwargs):
        if val is None:
             if 'et' not in values or values['et'] is None:
                raise ValueError('either et or ft should be set')
        return val

    def dict(self, *args, **kwargs):
        data_dict = super().dict(*args, **kwargs)
        data = OrderedDict()
        if 'et' in data_dict and data_dict['et'] is not None:
            data['et'] = data_dict['et']
        if 'ft' in data_dict and data_dict['ft'] is not None:
            data['ft'] = data_dict['ft']
        return data


class SagnordTidL(BaseModel):
    nútíð: SagnordTalaL | None
    þátíð: SagnordTalaL | None

    @validator('þátíð')
    def nutid_thatid_constraint(cls, val, values, **kwargs):
        if val is None:
             if 'nútíð' not in values or values['nútíð'] is None:
                raise ValueError('either nútíð or þátíð should be set')
        return val

    def dict(self, *args, **kwargs):
        data_dict = super().dict(*args, **kwargs)
        data = OrderedDict()
        if 'nútíð' in data_dict and data_dict['nútíð'] is not None:
            data['nútíð'] = data_dict['nútíð']
        if 'þátíð' in data_dict and data_dict['þátíð'] is not None:
            data['þátíð'] = data_dict['þátíð']
        return data


class SagnordHatturL(BaseModel):
    frumlag: Fall | None
    framsöguháttur: SagnordTidL
    viðtengingarháttur: SagnordTidL

    def dict(self, *args, **kwargs):
        data_dict = super().dict(*args, **kwargs)
        data = OrderedDict()
        if 'frumlag' in data_dict and data_dict['frumlag'] is not None:
            data['frumlag'] = data_dict['frumlag']
        data['framsöguháttur'] =  data_dict['framsöguháttur']
        data['viðtengingarháttur'] =  data_dict['viðtengingarháttur']
        return data


class SagnordTala(BaseModel):
    et: NonEmptyStr | None
    ft: NonEmptyStr | None

    @validator('ft')
    def et_ft_constraint(cls, val, values, **kwargs):
        if val is None:
             if 'et' not in values or values['et'] is None:
                raise ValueError('either et or ft should be set')
        return val

    def dict(self, *args, **kwargs):
        data_dict = super().dict(*args, **kwargs)
        data = OrderedDict()
        if 'et' in data_dict and data_dict['et'] is not None:
            data['et'] = data_dict['et']
        if 'ft' in data_dict and data_dict['ft'] is not None:
            data['ft'] = data_dict['ft']
        return data


class SagnordTid(BaseModel):
    nútíð: SagnordTala | None
    þátíð: SagnordTala | None

    @validator('þátíð')
    def nutid_thatid_constraint(cls, val, values, **kwargs):
        if val is None:
             if 'nútíð' not in values or values['nútíð'] is None:
                raise ValueError('either nútíð or þátíð should be set')
        return val

    def dict(self, *args, **kwargs):
        data_dict = super().dict(*args, **kwargs)
        data = OrderedDict()
        if 'nútíð' in data_dict and data_dict['nútíð'] is not None:
            data['nútíð'] = data_dict['nútíð']
        if 'þátíð' in data_dict and data_dict['þátíð'] is not None:
            data['þátíð'] = data_dict['þátíð']
        return data


class SagnordHattur(BaseModel):
    framsöguháttur: SagnordTid
    viðtengingarháttur: SagnordTid

    def dict(self, *args, **kwargs):
        data_dict = super().dict(*args, **kwargs)
        return OrderedDict({
            'framsöguháttur': data_dict['framsöguháttur'],
            'viðtengingarháttur': data_dict['viðtengingarháttur']
        })


class SagnordMynd(BaseModel):
    nafnháttur: NonEmptyStr
    sagnbót: NonEmptyStr | None
    boðháttur: SagnordBodhattur | None
    persónuleg: SagnordHatturL | None
    ópersónuleg: SagnordHatturL | None
    spurnarmyndir: SagnordHattur | None

    def dict(self, *args, **kwargs):
        data_dict = super().dict(*args, **kwargs)
        data = OrderedDict({
            'nafnháttur': data_dict['nafnháttur']
        })
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
    kk: conlist(NonEmptyStr, min_items=4, max_items=4)
    kvk: conlist(NonEmptyStr, min_items=4, max_items=4)
    hk: conlist(NonEmptyStr, min_items=4, max_items=4)

    def dict(self, *args, **kwargs):
        data_dict = super().dict(*args, **kwargs)
        return OrderedDict({'kk': data_dict['kk'], 'kvk': data_dict['kvk'], 'hk': data_dict['hk']})


class SagnordLhTT(BaseModel):
    et: SagnordLhTTK
    ft: SagnordLhTTK

    def dict(self, *args, **kwargs):
        data_dict = super().dict(*args, **kwargs)
        return OrderedDict({'et': data_dict['et'], 'ft': data_dict['ft']})


class SagnordLhT(BaseModel):
    sb: SagnordLhTT | None
    vb: SagnordLhTT | None

    @validator('vb')
    def sb_vb_constraint(cls, val, values, **kwargs):
        if val is None:
             if 'sb' not in values or values['sb'] is None:
                raise ValueError('either sb or vb should be set')
        return val

    def dict(self, *args, **kwargs):
        data_dict = super().dict(*args, **kwargs)
        data = OrderedDict()
        if 'sb' in data_dict and data_dict['sb'] is not None:
            data['sb'] = data_dict['sb']
        if 'vb' in data_dict and data_dict['vb'] is not None:
            data['vb'] = data_dict['vb']
        return data


class SagnordLysingarhattur(BaseModel):
    nútíðar: NonEmptyStr | None
    þátíðar: SagnordLhT | None

    def dict(self, *args, **kwargs):
        data_dict = super().dict(*args, **kwargs)
        data = OrderedDict()
        if 'nútíðar' in data_dict and data_dict['nútíðar'] is not None:
            data['nútíðar'] = data_dict['nútíðar']
        if 'þátíðar' in data_dict and data_dict['þátíðar'] is not None:
            data['þátíðar'] = data_dict['þátíðar']
        return data


class SagnordData(OrdData):
    germynd: SagnordMynd | None
    miðmynd: SagnordMynd | None
    lýsingarháttur: SagnordLysingarhattur | None
    óskháttur_1p_ft: NonEmptyStr | None
    óskháttur_3p: NonEmptyStr | None

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

    def dict(self, *args, **kwargs):
        data_dict = super().dict(*args, **kwargs)
        data = OrderedDict()
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
    kk: conlist(NonEmptyStr, min_items=4, max_items=4)
    kvk: conlist(NonEmptyStr, min_items=4, max_items=4)
    hk: conlist(NonEmptyStr, min_items=4, max_items=4)

    def dict(self, *args, **kwargs):
        data_dict = super().dict(*args, **kwargs)
        return OrderedDict({
            'kk': data_dict['kk'], 'kvk': data_dict['kvk'], 'hk': data_dict['hk']
        })


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

    def dict(self, *args, **kwargs):
        data_dict = super().dict(*args, **kwargs)
        data = OrderedDict()
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
    kk: conlist(NonEmptyStr | None, min_items=4, max_items=4) | None
    kvk: conlist(NonEmptyStr | None, min_items=4, max_items=4) | None
    hk: conlist(NonEmptyStr | None, min_items=4, max_items=4) | None

    @validator('hk')
    def kk_kvk_hk_constraint(cls, val, values, **kwargs):
        if val is None:
            if 'kvk' not in values or values['kvk'] is None:
                if 'kk' not in values or values['kk'] is None:
                    raise ValueError('at least one of kk, kvk, hk should be set')
        return val

    def dict(self, *args, **kwargs):
        data_dict = super().dict(*args, **kwargs)
        data = OrderedDict()
        if 'kk' in data_dict and data_dict['kk'] is not None:
            data['kk'] = data_dict['kk']
        if 'kvk' in data_dict and data_dict['kvk'] is not None:
            data['kvk'] = data_dict['kvk']
        if 'hk' in data_dict and data_dict['hk'] is not None:
            data['hk'] = data_dict['hk']
        return data


class FornafnData(OrdData):
    persóna: Persona | None
    kyn: Kyn | None
    et: FornafnKyn | conlist(NonEmptyStr | None, min_items=4, max_items=4) | None
    ft: FornafnKyn | conlist(NonEmptyStr | None, min_items=4, max_items=4) | None

    @validator('flokkur')
    def should_be_fornafn(cls, val, values, **kwargs):
        if val is not Ordflokkar.Fornafn:
            raise ValueError('flokkur should be fornafn')
        return val

    @validator('undirflokkur')
    def should_be_set(cls, val, values, **kwargs):
        if val is None:
            raise ValueError('undirflokkur should be set')
        elif type(val) is not Fornafnaflokkar:
            raise ValueError('undirflokkur should be fornafnaflokkur')
        return val

    @validator('ft')
    def et_ft_constraint(cls, val, values, **kwargs):
        if val is not None:
            if type(val) is list:
                if 'et' in values and values['et'] is not None and type(values['et']) is not list:
                    raise ValueError('when both et and ft are set they should have same type')
            elif 'et' in values and values['et'] is not None and type(values['et']) is list:
                raise ValueError('when et and ft are both set they should have same type')
        elif 'et' not in values or values['et'] is None:
            raise ValueError('either et or ft should be set')
        return val

    def dict(self, *args, **kwargs):
        data_dict = super().dict(*args, **kwargs)
        data = OrderedDict()
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
    kk: conlist(NonEmptyStr, min_items=4, max_items=4)
    kvk: conlist(NonEmptyStr, min_items=4, max_items=4)
    hk: conlist(NonEmptyStr, min_items=4, max_items=4)

    def dict(self, *args, **kwargs):
        data_dict = super().dict(*args, **kwargs)
        return OrderedDict({
            'kk': data_dict['kk'], 'kvk': data_dict['kvk'], 'hk': data_dict['hk']
        })


class ToluordEtFt(BaseModel):
    et: ToluordKyn
    ft: ToluordKyn


class FjoldatalaData(OrdData):
    tölugildi: Decimal
    et: ToluordKyn | None
    ft: ToluordKyn | None

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

    def dict(self, *args, **kwargs):
        data_dict = super().dict(*args, **kwargs)
        data = OrderedDict()
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
    sb: ToluordEtFt | None
    vb: ToluordEtFt | None

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

    def dict(self, *args, **kwargs):
        data_dict = super().dict(*args, **kwargs)
        data = OrderedDict()
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
    stýrir: conlist(Fall2, min_items=1, max_items=3)

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

    def dict(self, *args, **kwargs):
        data_dict = super().dict(*args, **kwargs)
        data = OrderedDict()
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
    miðstig: NonEmptyStr | None
    efstastig: NonEmptyStr | None

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

    def dict(self, *args, **kwargs):
        data_dict = super().dict(*args, **kwargs)
        data = OrderedDict()
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

    def dict(self, *args, **kwargs):
        data_dict = super().dict(*args, **kwargs)
        data = OrderedDict()
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
    fylgiorð: conlist(NonEmptyStr, min_items=1, max_items=5)


class SamtengingData(OrdData):
    fleiryrt: conlist(SamtengingFleiryrt, min_items=1, max_items=5) | None

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

    def dict(self, *args, **kwargs):
        data_dict = super().dict(*args, **kwargs)
        data = OrderedDict()
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

    def dict(self, *args, **kwargs):
        data_dict = super().dict(*args, **kwargs)
        data = OrderedDict()
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
    ág: conlist(NonEmptyStr, min_items=4, max_items=4) | None
    mg: conlist(NonEmptyStr, min_items=4, max_items=4) | None

    @validator('mg')
    def mg_constraint(cls, val, values, **kwargs):
        if val is None and ('ág' not in values or values['ág'] is None):
            raise ValueError('either ág or mg must be set')
        return val

    def dict(self, *args, **kwargs):
        data_dict = super().dict(*args, **kwargs)
        data = OrderedDict()
        if 'ág' in data_dict and data_dict['ág'] is not None:
            data['ág'] = data_dict['ág']
        if 'mg' in data_dict and data_dict['mg'] is not None:
            data['mg'] = data_dict['mg']
        return data


class SernafnData(OrdData):
    kyn: Kyn | None
    et: SernafnBeygingarAgMgSet | None
    ft: SernafnBeygingarAgMgSet | None

    @validator('flokkur')
    def should_be_sernafn(cls, val, values, **kwargs):
        if val is not Ordflokkar.Sernafn:
            raise ValueError('flokkur should be sérnafn')
        return val

    @validator('undirflokkur')
    def should_be_set(cls, val, values, **kwargs):
        if val is None:
            raise ValueError('undirflokkur should be set')
        elif type(val) is not Sernafnaflokkar:
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

    def dict(self, *args, **kwargs):
        data_dict = super().dict(*args, **kwargs)
        data = OrderedDict()
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
    merking: NonEmptyStr | None
    frasi: conlist(NonEmptyStr, min_items=1)
    myndir: conlist(NonEmptyStr, min_items=1)
    datahash: NonEmptyStr | None = Field(alias='hash')
    kennistrengur: NonEmptyStr | None

    def dict(self, *args, **kwargs):
        data_dict = super().dict(*args, **kwargs)
        data = OrderedDict()
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
