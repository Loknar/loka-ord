#!/usr/bin/python
import json
import sys

from lokaord import cli
from lokaord import exporter
from lokaord import importer
from lokaord import logman
from lokaord.version import __version__
from lokaord.database import db
from lokaord.database.models import isl

ArgParser = None


def get_words_count():
    '''
    collect some basic word count stats
    '''
    return {
        'nafnorð': {
            'kyn': {
                'kk': db.Session.query(isl.Nafnord).filter_by(Kyn=isl.Kyn.Karlkyn).count(),
                'kvk': db.Session.query(isl.Nafnord).filter_by(Kyn=isl.Kyn.Kvenkyn).count(),
                'hk': db.Session.query(isl.Nafnord).filter_by(Kyn=isl.Kyn.Hvorugkyn).count(),
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
        'allt': {
            'kjarnaorð': db.Session.query(isl.Ord).filter_by(Samsett=False).count(),
            'samsett': db.Session.query(isl.Ord).filter_by(Samsett=True).count(),
            'samtals': db.Session.query(isl.Ord).count()
        }
    }


def get_words_count_markdown_table():
    data = get_words_count()
    md_table = (
        '|   | kk | kvk | hk | ób.l | kjarnaorð | samsett orð | samtals |\n'
        '| --- | --- | --- | --- | --- | --- | --- | --- |\n'
        '| Nafnorð     | {no_kk} | {no_kvk} | {no_hk} |   | {no_k} | {no_s} | **{no_a}** |\n'
        '| Lýsingarorð |   |   |   | {lo_obl} | {lo_k} | {lo_s} | **{lo_a}** |\n'
        '| Sagnorð     |   |   |   |   | {so_k} | {so_s} | **{so_a}** |\n'
        '| Töluorð     |   |   |   |   | {to_k} | {to_s} | **{to_a}** |\n'
        '| Fornöfn     |   |   |   |   | {fn_k} | {fn_s} | **{fn_a}** |\n'
        '| Smáorð      |   |   |   |   |   |   | **{smo_a}** |\n'
        '| **Alls**    |   |   |   |   | **{a_k}** | **{a_s}** | **{a_a}** |'
    ).format(
        no_kk=data['nafnorð']['kyn']['kk'],
        no_kvk=data['nafnorð']['kyn']['kvk'],
        no_hk=data['nafnorð']['kyn']['hk'],
        no_k=data['nafnorð']['kjarnaorð'],
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
        a_k=data['allt']['kjarnaorð'],
        a_s=data['allt']['samsett'],
        a_a=data['allt']['samtals'],
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
    if 'md-stats' in arguments and arguments['md-stats'] is True:
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
