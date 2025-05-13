#!/usr/bin/python
"""
Exporter functionality

Exporting data from SQL database to files.
"""
import datetime

from lokaord import logman
from lokaord.database import db
from lokaord.database.models import isl
from lokaord import handlers


def write_datafiles_from_db(ts: datetime.datetime = None):
	"""
	Usage:  write_datafiles_from_db(ts)
	Before: @ts is optional datetime timestamp to specify which orð to write from database to
			datafiles.
	After:  Orð from database have been written to datafiles. If @ts is provided we only export
			orð that have been edited after the @ts timestamp time period, else we export all orð.
	"""
	logman.info('Writing orð data from database to datafiles ..')
	handlers_map = handlers.get_handlers_map()
	query_isl_ord_records = db.Session.query(isl.Ord).order_by(isl.Ord.Ord_id)  # all orð
	count = query_isl_ord_records.count()
	counter = 1
	if ts is not None:
		query_isl_ord_records = (
			db.Session.query(isl.Ord).filter(isl.Ord.Edited >= ts).order_by(isl.Ord.Ord_id)
		)
		logman.info('Exporting orð edited after ts: %s.' % (ts.isoformat(), ))
	for isl_ord_record in query_isl_ord_records:
		logman.debug('Writing orð from db to file "%s" (%s)' % (
			isl_ord_record.Ord, isl_ord_record.Kennistrengur
		))
		handler = handlers_map[isl_ord_record.Ordflokkur.name]
		isl_ord = handler()
		isl_ord.load_from_db(isl_ord_record)
		isl_ord.write_to_file()
		edited_str = ''
		if ts is not None:
			edited_str = ' (edited: %s)' % (isl_ord_record.Edited.isoformat(), )
		if counter % 1000 == 0:
			logman.info('(%s/%s) Wrote orð with id=%s to file "%s"%s.' % (
				counter, count, isl_ord_record.Ord_id, isl_ord.make_filename(), edited_str
			))
		else:
			logman.debug('(%s/%s) Wrote orð with id=%s to file "%s"%s.' % (
				counter, count, isl_ord_record.Ord_id, isl_ord.make_filename(), edited_str
			))
		counter += 1
	logman.info('Writing skammstafanir data from database to datafiles ..')
	query_skammstafanir_records = (
		db.Session.query(isl.Skammstofun).order_by(isl.Skammstofun.Skammstofun_id)
	)
	if ts is not None:
		query_skammstafanir_records = db.Session.query(isl.Skammstofun).filter(
			isl.Skammstofun.Edited >= ts
		).order_by(isl.Skammstofun.Skammstofun_id)
	for skammstofun_record in query_skammstafanir_records:
		skammstofun = handlers.Skammstofun()
		skammstofun.load_from_db(skammstofun_record)
		skammstofun.write_to_file()
		edited_str = ''
		if ts is not None:
			edited_str = ' (edited: %s)' % (skammstofun_record.Edited.isoformat(), )
		logman.debug('Wrote skammstöfun with id=%s to file "%s"%s.' % (
			skammstofun_record.Skammstofun_id, skammstofun.make_filename(), edited_str
		))
	logman.info('Done writing data from database to datafiles.')
