#!/usr/bin/python
import json
import sys

from lokaord import cli
from lokaord import exporter
from lokaord import importer
from lokaord import logman
from lokaord import seer
from lokaord.database import db
from lokaord.database.models import isl
from lokaord.exporter import get_samsett_ord_from_db_to_ordered_dict
from lokaord.version import __version__

ArgParser = None


def get_words_count():
    '''
    collect some basic word count stats
    '''
    data = {
        'nafnorð': {
            'kyn-kjarnaorð': {
                'kk': (
                    db.Session.query(isl.Nafnord).join(isl.Ord).filter(
                        isl.Nafnord.Kyn == isl.Kyn.Karlkyn
                    ).filter(
                        isl.Ord.Samsett == False
                    ).count()
                ),
                'kvk': (
                    db.Session.query(isl.Nafnord).join(isl.Ord).filter(
                        isl.Nafnord.Kyn == isl.Kyn.Kvenkyn
                    ).filter(
                        isl.Ord.Samsett == False
                    ).count()
                ),
                'hk': (
                    db.Session.query(isl.Nafnord).join(isl.Ord).filter(
                        isl.Nafnord.Kyn == isl.Kyn.Hvorugkyn
                    ).filter(
                        isl.Ord.Samsett == False
                    ).count()
                ),
            },
            'kyn-samsett': {
                'kk': (
                    db.Session.query(isl.Nafnord).join(isl.Ord).filter(
                        isl.Nafnord.Kyn == isl.Kyn.Karlkyn
                    ).filter(
                        isl.Ord.Samsett == True
                    ).count()
                ),
                'kvk': (
                    db.Session.query(isl.Nafnord).join(isl.Ord).filter(
                        isl.Nafnord.Kyn == isl.Kyn.Kvenkyn
                    ).filter(
                        isl.Ord.Samsett == True
                    ).count()
                ),
                'hk': (
                    db.Session.query(isl.Nafnord).join(isl.Ord).filter(
                        isl.Nafnord.Kyn == isl.Kyn.Hvorugkyn
                    ).filter(
                        isl.Ord.Samsett == True
                    ).count()
                )
            },
            'kjarnaorð': db.Session.query(isl.Ord).filter_by(
                Ordflokkur=isl.Ordflokkar.Nafnord, Samsett=False
            ).count(),
            'samsett': db.Session.query(isl.Ord).filter_by(
                Ordflokkur=isl.Ordflokkar.Nafnord, Samsett=True
            ).count(),
            'samtals': db.Session.query(isl.Ord).filter_by(
                Ordflokkur=isl.Ordflokkar.Nafnord
            ).count()
        },
        'lýsingarorð': {
            'kjarnaorð': db.Session.query(isl.Ord).filter_by(
                Ordflokkur=isl.Ordflokkar.Lysingarord, Samsett=False
            ).count(),
            'samsett': db.Session.query(isl.Ord).filter_by(
                Ordflokkur=isl.Ordflokkar.Lysingarord, Samsett=True
            ).count(),
            'óbeygjanleg': db.Session.query(isl.Ord).filter_by(
                Ordflokkur=isl.Ordflokkar.Lysingarord, Obeygjanlegt=True
            ).count(),
            'samtals': db.Session.query(isl.Ord).filter_by(
                Ordflokkur=isl.Ordflokkar.Lysingarord
            ).count()
        },
        'sagnorð': {
            'kjarnaorð': db.Session.query(isl.Ord).filter_by(
                Ordflokkur=isl.Ordflokkar.Sagnord, Samsett=False
            ).count(),
            'samsett': db.Session.query(isl.Ord).filter_by(
                Ordflokkur=isl.Ordflokkar.Sagnord, Samsett=True
            ).count(),
            'samtals': db.Session.query(isl.Ord).filter_by(
                Ordflokkur=isl.Ordflokkar.Sagnord
            ).count()
        },
        'töluorð': {  # töluorð (frumtölur + raðtölur)
            'kjarnaorð': (
                db.Session.query(isl.Ord).filter_by(
                    Ordflokkur=isl.Ordflokkar.Frumtala, Samsett=False
                ).count() +
                db.Session.query(isl.Ord).filter_by(
                    Ordflokkur=isl.Ordflokkar.Radtala, Samsett=False
                ).count()
            ),
            'samsett': (
                db.Session.query(isl.Ord).filter_by(
                    Ordflokkur=isl.Ordflokkar.Frumtala, Samsett=True
                ).count() +
                db.Session.query(isl.Ord).filter_by(
                    Ordflokkur=isl.Ordflokkar.Radtala, Samsett=True
                ).count()
            ),
            'samtals': (
                db.Session.query(isl.Ord).filter_by(Ordflokkur=isl.Ordflokkar.Frumtala).count() +
                db.Session.query(isl.Ord).filter_by(Ordflokkur=isl.Ordflokkar.Radtala).count()
            )
        },
        'fornöfn': {
            'kjarnaorð': db.Session.query(isl.Ord).filter_by(
                Ordflokkur=isl.Ordflokkar.Fornafn, Samsett=False
            ).count(),
            'samsett': db.Session.query(isl.Ord).filter_by(
                Ordflokkur=isl.Ordflokkar.Fornafn, Samsett=True
            ).count(),
            'samtals': db.Session.query(isl.Ord).filter_by(
                Ordflokkur=isl.Ordflokkar.Fornafn
            ).count()
        },
        'smáorð': {
            'samtals': (
                db.Session.query(isl.Ord).filter_by(Ordflokkur=isl.Ordflokkar.Forsetning).count() +
                db.Session.query(isl.Ord).filter_by(Ordflokkur=isl.Ordflokkar.Atviksord).count() +
                db.Session.query(isl.Ord).filter_by(
                    Ordflokkur=isl.Ordflokkar.Nafnhattarmerki
                ).count() +
                db.Session.query(isl.Ord).filter_by(Ordflokkur=isl.Ordflokkar.Samtenging).count() +
                db.Session.query(isl.Ord).filter_by(Ordflokkur=isl.Ordflokkar.Upphropun).count()
            )
        },
        'allt-nema-sérnöfn': {
            'kjarnaorð': db.Session.query(isl.Ord).filter(
                isl.Ord.Ordflokkur != isl.Ordflokkar.Sernafn
            ).filter(
                isl.Ord.Samsett == False
            ).count(),
            'samsett': db.Session.query(isl.Ord).filter(
                isl.Ord.Ordflokkur != isl.Ordflokkar.Sernafn
            ).filter(
                isl.Ord.Samsett == True
            ).count(),
            'samtals': db.Session.query(isl.Ord).filter(
                isl.Ord.Ordflokkur != isl.Ordflokkar.Sernafn
            ).count()
        },
        'sérnöfn': {
            'eiginnöfn': {
                'kyn-kjarnaorð': {
                    'kk': (
                        db.Session.query(isl.Sernafn).join(isl.Ord).filter(
                            isl.Sernafn.Undirflokkur == isl.Sernafnaflokkar.Eiginnafn
                        ).filter(
                            isl.Sernafn.Kyn == isl.Kyn.Karlkyn
                        ).filter(
                            isl.Ord.Samsett == False
                        ).count()
                    ),
                    'kvk': (
                        db.Session.query(isl.Sernafn).join(isl.Ord).filter(
                            isl.Sernafn.Undirflokkur == isl.Sernafnaflokkar.Eiginnafn
                        ).filter(
                            isl.Sernafn.Kyn == isl.Kyn.Kvenkyn
                        ).filter(
                            isl.Ord.Samsett == False
                        ).count()
                    )
                },
                'kyn-samsett': {
                    'kk': (
                        db.Session.query(isl.Sernafn).join(isl.Ord).filter(
                            isl.Sernafn.Undirflokkur == isl.Sernafnaflokkar.Eiginnafn
                        ).filter(
                            isl.Sernafn.Kyn == isl.Kyn.Karlkyn
                        ).filter(
                            isl.Ord.Samsett == True
                        ).count()
                    ),
                    'kvk': (
                        db.Session.query(isl.Sernafn).join(isl.Ord).filter(
                            isl.Sernafn.Undirflokkur == isl.Sernafnaflokkar.Eiginnafn
                        ).filter(
                            isl.Sernafn.Kyn == isl.Kyn.Kvenkyn
                        ).filter(
                            isl.Ord.Samsett == True
                        ).count()
                    )
                },
                'kjarnaorð': db.Session.query(isl.Sernafn).join(isl.Ord).filter(
                    isl.Sernafn.Undirflokkur == isl.Sernafnaflokkar.Eiginnafn
                ).filter(
                    isl.Ord.Samsett == False
                ).count(),
                'samsett': db.Session.query(isl.Sernafn).join(isl.Ord).filter(
                    isl.Sernafn.Undirflokkur == isl.Sernafnaflokkar.Eiginnafn
                ).filter(
                    isl.Ord.Samsett == True
                ).count(),
                'samtals': db.Session.query(isl.Sernafn).join(isl.Ord).filter(
                    isl.Sernafn.Undirflokkur == isl.Sernafnaflokkar.Eiginnafn
                ).count()
            },
            'gælunöfn': {
                'kyn-kjarnaorð': {
                    'kk': (
                        db.Session.query(isl.Sernafn).join(isl.Ord).filter(
                            isl.Sernafn.Undirflokkur == isl.Sernafnaflokkar.Gaelunafn
                        ).filter(
                            isl.Sernafn.Kyn == isl.Kyn.Karlkyn
                        ).filter(
                            isl.Ord.Samsett == False
                        ).count()
                    ),
                    'kvk': (
                        db.Session.query(isl.Sernafn).join(isl.Ord).filter(
                            isl.Sernafn.Undirflokkur == isl.Sernafnaflokkar.Gaelunafn
                        ).filter(
                            isl.Sernafn.Kyn == isl.Kyn.Kvenkyn
                        ).filter(
                            isl.Ord.Samsett == False
                        ).count()
                    )
                },
                'kyn-samsett': {
                    'kk': (
                        db.Session.query(isl.Sernafn).join(isl.Ord).filter(
                            isl.Sernafn.Undirflokkur == isl.Sernafnaflokkar.Gaelunafn
                        ).filter(
                            isl.Sernafn.Kyn == isl.Kyn.Karlkyn
                        ).filter(
                            isl.Ord.Samsett == True
                        ).count()
                    ),
                    'kvk': (
                        db.Session.query(isl.Sernafn).join(isl.Ord).filter(
                            isl.Sernafn.Undirflokkur == isl.Sernafnaflokkar.Gaelunafn
                        ).filter(
                            isl.Sernafn.Kyn == isl.Kyn.Kvenkyn
                        ).filter(
                            isl.Ord.Samsett == True
                        ).count()
                    )
                },
                'kjarnaorð': db.Session.query(isl.Sernafn).join(isl.Ord).filter(
                    isl.Sernafn.Undirflokkur == isl.Sernafnaflokkar.Gaelunafn
                ).filter(
                    isl.Ord.Samsett == False
                ).count(),
                'samsett': db.Session.query(isl.Sernafn).join(isl.Ord).filter(
                    isl.Sernafn.Undirflokkur == isl.Sernafnaflokkar.Gaelunafn
                ).filter(
                    isl.Ord.Samsett == True
                ).count(),
                'samtals': db.Session.query(isl.Sernafn).join(isl.Ord).filter(
                    isl.Sernafn.Undirflokkur == isl.Sernafnaflokkar.Gaelunafn
                ).count()
            },
            'kenninöfn': {
                'kyn-kjarnaorð': {
                    'kk': (
                        db.Session.query(isl.Sernafn).join(isl.Ord).filter(
                            isl.Sernafn.Undirflokkur == isl.Sernafnaflokkar.Kenninafn
                        ).filter(
                            isl.Sernafn.Kyn == isl.Kyn.Karlkyn
                        ).filter(
                            isl.Ord.Samsett == False
                        ).count()
                    ),
                    'kvk': (
                        db.Session.query(isl.Sernafn).join(isl.Ord).filter(
                            isl.Sernafn.Undirflokkur == isl.Sernafnaflokkar.Kenninafn
                        ).filter(
                            isl.Sernafn.Kyn == isl.Kyn.Kvenkyn
                        ).filter(
                            isl.Ord.Samsett == False
                        ).count()
                    )
                },
                'kyn-samsett': {
                    'kk': (
                        db.Session.query(isl.Sernafn).join(isl.Ord).filter(
                            isl.Sernafn.Undirflokkur == isl.Sernafnaflokkar.Kenninafn
                        ).filter(
                            isl.Sernafn.Kyn == isl.Kyn.Karlkyn
                        ).filter(
                            isl.Ord.Samsett == True
                        ).count()
                    ),
                    'kvk': (
                        db.Session.query(isl.Sernafn).join(isl.Ord).filter(
                            isl.Sernafn.Undirflokkur == isl.Sernafnaflokkar.Kenninafn
                        ).filter(
                            isl.Sernafn.Kyn == isl.Kyn.Kvenkyn
                        ).filter(
                            isl.Ord.Samsett == True
                        ).count()
                    )
                },
                'kjarnaorð': db.Session.query(isl.Sernafn).join(isl.Ord).filter(
                    isl.Sernafn.Undirflokkur == isl.Sernafnaflokkar.Kenninafn
                ).filter(
                    isl.Ord.Samsett == False
                ).count(),
                'samsett': db.Session.query(isl.Sernafn).join(isl.Ord).filter(
                    isl.Sernafn.Undirflokkur == isl.Sernafnaflokkar.Kenninafn
                ).filter(
                    isl.Ord.Samsett == True
                ).count(),
                'samtals': db.Session.query(isl.Sernafn).join(isl.Ord).filter(
                    isl.Sernafn.Undirflokkur == isl.Sernafnaflokkar.Kenninafn
                ).count()
            },
            'millinöfn': {
                'samtals':  db.Session.query(isl.Sernafn).join(isl.Ord).filter(
                    isl.Sernafn.Undirflokkur == isl.Sernafnaflokkar.Millinafn
                ).count()
            },
            'örnefni': {
                'kyn-kjarnaorð': {
                    'kk': (
                        db.Session.query(isl.Sernafn).join(isl.Ord).filter(
                            isl.Sernafn.Undirflokkur == isl.Sernafnaflokkar.Ornefni
                        ).filter(
                            isl.Sernafn.Kyn == isl.Kyn.Karlkyn
                        ).filter(
                            isl.Ord.Samsett == False
                        ).count()
                    ),
                    'kvk': (
                        db.Session.query(isl.Sernafn).join(isl.Ord).filter(
                            isl.Sernafn.Undirflokkur == isl.Sernafnaflokkar.Ornefni
                        ).filter(
                            isl.Sernafn.Kyn == isl.Kyn.Kvenkyn
                        ).filter(
                            isl.Ord.Samsett == False
                        ).count()
                    ),
                    'hk': (
                        db.Session.query(isl.Sernafn).join(isl.Ord).filter(
                            isl.Sernafn.Undirflokkur == isl.Sernafnaflokkar.Ornefni
                        ).filter(
                            isl.Sernafn.Kyn == isl.Kyn.Hvorugkyn
                        ).filter(
                            isl.Ord.Samsett == False
                        ).count()
                    )
                },
                'kyn-samsett': {
                    'kk': (
                        db.Session.query(isl.Sernafn).join(isl.Ord).filter(
                            isl.Sernafn.Undirflokkur == isl.Sernafnaflokkar.Ornefni
                        ).filter(
                            isl.Sernafn.Kyn == isl.Kyn.Karlkyn
                        ).filter(
                            isl.Ord.Samsett == True
                        ).count()
                    ),
                    'kvk': (
                        db.Session.query(isl.Sernafn).join(isl.Ord).filter(
                            isl.Sernafn.Undirflokkur == isl.Sernafnaflokkar.Ornefni
                        ).filter(
                            isl.Sernafn.Kyn == isl.Kyn.Kvenkyn
                        ).filter(
                            isl.Ord.Samsett == True
                        ).count()
                    ),
                    'hk': (
                        db.Session.query(isl.Sernafn).join(isl.Ord).filter(
                            isl.Sernafn.Undirflokkur == isl.Sernafnaflokkar.Ornefni
                        ).filter(
                            isl.Sernafn.Kyn == isl.Kyn.Hvorugkyn
                        ).filter(
                            isl.Ord.Samsett == True
                        ).count()
                    )
                },
                'kjarnaorð': db.Session.query(isl.Sernafn).join(isl.Ord).filter(
                    isl.Sernafn.Undirflokkur == isl.Sernafnaflokkar.Ornefni
                ).filter(
                    isl.Ord.Samsett == False
                ).count(),
                'samsett': db.Session.query(isl.Sernafn).join(isl.Ord).filter(
                    isl.Sernafn.Undirflokkur == isl.Sernafnaflokkar.Ornefni
                ).filter(
                    isl.Ord.Samsett == True
                ).count(),
                'samtals': db.Session.query(isl.Sernafn).join(isl.Ord).filter(
                    isl.Sernafn.Undirflokkur == isl.Sernafnaflokkar.Ornefni
                ).count()
            },
            'kjarnaorð': db.Session.query(isl.Sernafn).join(isl.Ord).filter(
                isl.Ord.Samsett == False
            ).count(),
            'samsett': db.Session.query(isl.Sernafn).join(isl.Ord).filter(
                isl.Ord.Samsett == True
            ).count(),
            'samtals': db.Session.query(isl.Sernafn).count(),
        },
        'allt': {
            'kjarnaorð': db.Session.query(isl.Ord).filter_by(Samsett=False).count(),
            'samsett': db.Session.query(isl.Ord).filter_by(Samsett=True).count(),
            'samtals': db.Session.query(isl.Ord).count()
        }
    }
    return data


def get_words_count_markdown_table():
    data = get_words_count()
    md_table = (
        '|   | ób.l | kk | kvk | hk | kjarna-orð | kk | kvk | hk | samsett-orð | samtals |\n'
        '| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |\n'
        '| **Nafnorð**     |   | {no_kk} | {no_kvk} | {no_hk} | {no_k} | {no_s_kk} | {no_s_kvk} |'
        ' {no_s_hk} | {no_s} | **{no_a}** |\n'
        '| **Lýsingarorð** | {lo_obl} |   |   |   | {lo_k} |   |   |   | {lo_s} | **{lo_a}** |\n'
        '| **Sagnorð**     |   |   |   |   | {so_k} |   |   |   | {so_s} | **{so_a}** |\n'
        '| **Töluorð**     |   |   |   |   | {to_k} |   |   |   | {to_s} | **{to_a}** |\n'
        '| **Fornöfn**     |   |   |   |   | {fn_k} |   |   |   | {fn_s} | **{fn_a}** |\n'
        '| **Smáorð**      |   |   |   |   |   |   |   |   |   | **{smo_a}** |\n'
        '| **Alls** |   |   |   |   | **{a_1_k}** |   |   |   | **{a_1_s}** | **{a_1_a}** |\n'
        '\n'
        '| Sérnöfn | kk | kvk | hk | kjarna-orð | kk | kvk | hk | samsett-orð | samtals |\n'
        '| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |\n'
        '| Eiginnöfn | {sn_e_kk} | {sn_e_kvk} |   | {sn_e_k} | {sn_e_s_kk} | {sn_e_s_kvk} |   |'
        ' {sn_e_s} | **{sn_e_a}** |\n'
        '| Gælunöfn  | {sn_g_kk} | {sn_g_kvk} |   | {sn_g_k} | {sn_g_s_kk} | {sn_g_s_kvk} |   |'
        ' {sn_g_s} | **{sn_g_a}** |\n'
        '| Kenninöfn | {sn_k_kk} | {sn_k_kvk} |   | {sn_k_k} | {sn_k_s_kk} | {sn_k_s_kvk} |   |'
        ' {sn_k_s} | **{sn_k_a}** |\n'
        '| Millinöfn |   |   |   |   |   |   |   |   | **{sn_m}** |\n'
        '| Örnefni   | {sn_o_kk} | {sn_o_kvk} | {sn_o_hk} | {sn_o_k} | {sn_o_s_kk} | {sn_o_s_kvk}'
        ' | {sn_o_s_hk} | {sn_o_s} | **{sn_o_a}** |\n'
        '| **Alls**  |   |   |   | **{a_2_k}** |   |   |   | **{a_2_s}** | **{a_2_a}** |\n'
        '\n'
        '**Samtals:** {a_3_a} orð.'
    ).format(
        no_kk=data['nafnorð']['kyn-kjarnaorð']['kk'],  # fyrri tafla
        no_kvk=data['nafnorð']['kyn-kjarnaorð']['kvk'],
        no_hk=data['nafnorð']['kyn-kjarnaorð']['hk'],
        no_k=data['nafnorð']['kjarnaorð'],
        no_s_kk=data['nafnorð']['kyn-samsett']['kk'],
        no_s_kvk=data['nafnorð']['kyn-samsett']['kvk'],
        no_s_hk=data['nafnorð']['kyn-samsett']['hk'],
        no_s=data['nafnorð']['samsett'],
        no_a=data['nafnorð']['samtals'],
        lo_obl=data['lýsingarorð']['óbeygjanleg'],
        lo_k=data['lýsingarorð']['kjarnaorð'],
        lo_s=data['lýsingarorð']['samsett'],
        lo_a=data['lýsingarorð']['samtals'],
        so_k=data['sagnorð']['kjarnaorð'],
        so_s=data['sagnorð']['samsett'],
        so_a=data['sagnorð']['samtals'],
        to_k=data['töluorð']['kjarnaorð'],
        to_s=data['töluorð']['samsett'],
        to_a=data['töluorð']['samtals'],
        fn_k=data['fornöfn']['kjarnaorð'],
        fn_s=data['fornöfn']['samsett'],
        fn_a=data['fornöfn']['samtals'],
        smo_a=data['smáorð']['samtals'],
        a_1_k=data['allt-nema-sérnöfn']['kjarnaorð'],
        a_1_s=data['allt-nema-sérnöfn']['samsett'],
        a_1_a=data['allt-nema-sérnöfn']['samtals'],
        sn_e_kk=data['sérnöfn']['eiginnöfn']['kyn-kjarnaorð']['kk'],  # seinni tafla
        sn_e_kvk=data['sérnöfn']['eiginnöfn']['kyn-kjarnaorð']['kvk'],
        sn_e_k=data['sérnöfn']['eiginnöfn']['kjarnaorð'],
        sn_e_s_kk=data['sérnöfn']['eiginnöfn']['kyn-samsett']['kk'],
        sn_e_s_kvk=data['sérnöfn']['eiginnöfn']['kyn-samsett']['kvk'],
        sn_e_s=data['sérnöfn']['eiginnöfn']['samsett'],
        sn_e_a=data['sérnöfn']['eiginnöfn']['samtals'],
        sn_g_kk=data['sérnöfn']['gælunöfn']['kyn-kjarnaorð']['kk'],
        sn_g_kvk=data['sérnöfn']['gælunöfn']['kyn-kjarnaorð']['kvk'],
        sn_g_k=data['sérnöfn']['gælunöfn']['kjarnaorð'],
        sn_g_s_kk=data['sérnöfn']['gælunöfn']['kyn-samsett']['kk'],
        sn_g_s_kvk=data['sérnöfn']['gælunöfn']['kyn-samsett']['kvk'],
        sn_g_s=data['sérnöfn']['gælunöfn']['samsett'],
        sn_g_a=data['sérnöfn']['gælunöfn']['samtals'],
        sn_k_kk=data['sérnöfn']['kenninöfn']['kyn-kjarnaorð']['kk'],
        sn_k_kvk=data['sérnöfn']['kenninöfn']['kyn-kjarnaorð']['kvk'],
        sn_k_k=data['sérnöfn']['kenninöfn']['kjarnaorð'],
        sn_k_s_kk=data['sérnöfn']['kenninöfn']['kyn-samsett']['kk'],
        sn_k_s_kvk=data['sérnöfn']['kenninöfn']['kyn-samsett']['kvk'],
        sn_k_s=data['sérnöfn']['kenninöfn']['samsett'],
        sn_k_a=data['sérnöfn']['kenninöfn']['samtals'],
        sn_m=data['sérnöfn']['millinöfn']['samtals'],
        sn_o_kk=data['sérnöfn']['örnefni']['kyn-kjarnaorð']['kk'],
        sn_o_kvk=data['sérnöfn']['örnefni']['kyn-kjarnaorð']['kvk'],
        sn_o_hk=data['sérnöfn']['örnefni']['kyn-kjarnaorð']['hk'],
        sn_o_k=data['sérnöfn']['örnefni']['kjarnaorð'],
        sn_o_s_kk=data['sérnöfn']['örnefni']['kyn-samsett']['kk'],
        sn_o_s_kvk=data['sérnöfn']['örnefni']['kyn-samsett']['kvk'],
        sn_o_s_hk=data['sérnöfn']['örnefni']['kyn-samsett']['hk'],
        sn_o_s=data['sérnöfn']['örnefni']['samsett'],
        sn_o_a=data['sérnöfn']['örnefni']['samtals'],
        a_2_k=data['sérnöfn']['kjarnaorð'],
        a_2_s=data['sérnöfn']['samsett'],
        a_2_a=data['sérnöfn']['samtals'],
        a_3_a=data['allt']['samtals'],
    )
    return md_table


def main(arguments):
    logman.init(
        arguments['logger_name'], role=arguments['role'], output_dir=arguments['log_directory']
    )
    db_name = 'lokaord'
    if 'backup_db' in arguments and arguments['backup_db'] is True:
        db.backup_sqlite_db_file(db_name)
    if 'rebuild_db' in arguments and arguments['rebuild_db'] is True:
        db.delete_sqlite_db_file(db_name)
    if db.Session is None:
        db.setup_data_directory(db_name)
        db_uri = db.create_db_uri(db_name)
        db.setup_connection(db_uri, db_echo=False)
        db.init_db()
    if 'stats' in arguments and arguments['stats'] is True:
        print(json.dumps(
            get_words_count(), separators=(',', ':'), ensure_ascii=False, sort_keys=True
        ))
    if 'md_stats' in arguments and arguments['md_stats'] is True:
        print(get_words_count_markdown_table())
    if 'add_word_cli' in arguments and arguments['add_word_cli'] is True:
        cli.add_word_cli()
    if (
        'build_db' in arguments and arguments['build_db'] is True or
        'rebuild_db' in arguments and arguments['rebuild_db'] is True
    ):
        importer.build_db_from_datafiles()
    if 'write_files' in arguments and arguments['write_files'] is True:
        exporter.write_datafiles_from_db()
    if 'build_sight' in arguments and arguments['build_sight'] is True:
        seer.build_sight()
    if 'search' in arguments and arguments['search'] is not None:
        seer.search_word(arguments['search'])
    if 'scan_sentence' in arguments and arguments['scan_sentence'] is not None:
        seer.scan_sentence(arguments['scan_sentence'])
    if 'run_fiddle' in arguments and arguments['run_fiddle'] is True:
        print('Running fiddle!')
