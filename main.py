#!/usr/bin/python
import datetime
from pathlib import Path
import sys

from typing import Annotated
from typing import Optional

import typer
from typer import Option

import lokaord
from lokaord import logman

app = typer.Typer(
	chain=True,
	name=lokaord.Name,
	context_settings={'help_option_names': ['-h', '--help']},
	add_completion=False
)


def version(value: bool):
	if value:
		print('%s %s' % (lokaord.Name, lokaord.__version__))
		raise typer.Exit()


@app.callback(invoke_without_command=True)
def common(
	version: Annotated[
		Optional[bool], Option(
			'--version', '-v', callback=version, help='Print version and exit.'
		)
	] = None,
	logger_name: Annotated[str, Option('--logger-name', '-ln')] = lokaord.Name,
	loglevel: Annotated[lokaord.LogLevel, Option('--loglevel', '-ll')] = 'info',
	log_directory: Annotated[
		Path, Option(
			'--log-directory', '-ldir', help='Directory to write logs in. Should already exist.'
		)
	] = './logs/',
	role: Annotated[lokaord.LoggerRoles, Option('--role', '-r')] = 'cli'
):
	lokaord.Ts = datetime.datetime.now()
	if log_directory.match('logs') and not log_directory.exists():
		log_directory.mkdir()
	log_directory = log_directory.resolve()
	if not log_directory.exists():
		raise typer.BadParameter(f'Please ensure provided log-directory "{log_directory}" exists.')
	if not log_directory.is_dir():
		raise typer.BadParameter(f'Provided log-directory "{log_directory}" is not a directory.')
	lokaord.logman.init(logger_name, level=loglevel, role=role, output_dir=log_directory)
	if len(sys.argv) <= 1:
		print(
			'Usage: lokaord [OPTIONS] COMMAND1 [ARGS]... [COMMAND2 [ARGS]...]...\n'
			'Try \'lokaord -h\' for help.'
		)


@app.command('build-db', help='Import words from JSON datafiles to database.')
def build_db(
	rebuild: Annotated[Optional[bool], Option('--rebuild', '-r')] = False,
	changes_only: Annotated[Optional[bool], Option('--changes-only', '-ch')] = False
):
	if rebuild and changes_only:
		raise typer.BadParameter('build-db: --rebuild and --changes-only are mutually exclusive.')
	lokaord.build_db(rebuild, changes_only)


@app.command('backup-db', help='Create backup of current SQLite database file.')
def backup_db():
	lokaord.backup_db()


@app.command(help='Write words from database to JSON datafiles.')
def write_files(
	timestamp: Annotated[Optional[datetime.datetime], Option('--timestamp', '-ts')] = None,
	time_offset: Annotated[Optional[lokaord.TimeOffset], Option('--time-offset', '-to')] = None,
	this_run: Annotated[Optional[bool], Option('--this-run', '-tr')] = False
):
	if timestamp is not None and time_offset is not None:
		logman.warning('Both timestamp and time_offset specified, using timestamp.')
	ts = timestamp
	if ts is None and time_offset is not None:
		ts = lokaord.get_offset_time(time_offset)
	if this_run is True:
		if ts is not None:
			logman.warning('Overriding timestamp with this_run.')
		ts = lokaord.Ts
	lokaord.write_files(ts)


@app.command(help='Build word search.')
def build_sight():
	lokaord.build_sight()


@app.command(help='Pack word files into packed JSON files intended for web use.')
def webpack(wpp: Annotated[Optional[int], Option('--words-per-pack', '-wpp')] = lokaord.seer.WPP):
	lokaord.webpack(words_per_pack=wpp)


@app.command(help='Search for a single word in sight file.')
def search(word: str):
	if word == '':
		raise typer.BadParameter('Word can\'t be empty string.')
	lokaord.search(word)


@app.command(help='Search for words in a sentence in sight file.')
def scan_sentence(
	sentence: str,
	hide_matches: Annotated[Optional[bool], Option('--hide-matches', '-hm')] = False
):
	if sentence == '':
		raise typer.BadParameter('Sentence can\'t be empty string.')
	lokaord.scan_sentence(sentence, hide_matches)
	lokaord.get_runtime()


@app.command(help='Short for the "scan-sentence" command.')
def ss(
	sentence: str,
	hide_matches: Annotated[Optional[bool], Option('--hide-matches', '-hm')] = False
):
	scan_sentence(sentence, hide_matches)


@app.command(help='Print database word count data in JSON string.')
def stats():
	lokaord.get_stats()


@app.command(help='Print database word count in Markdown table.')
def md_stats(update_readme: Annotated[Optional[bool], Option('--update-readme', '-ur')] = False):
	print(lokaord.get_md_stats(update_readme_table=update_readme))


@app.command(help='Print runtime of script so far.')
def runtime():
	lokaord.get_runtime()


@app.command(help='Initialize lokaord (same as: "build-db write-files build-sight md-stats").')
def init(
	rebuild: Annotated[Optional[bool], Option('--rebuild', '-r')] = False,
	update_readme: Annotated[Optional[bool], Option('--update-readme', '-ur')] = False
):
	lokaord.build_db(rebuild)
	lokaord.write_files()
	lokaord.build_sight()
	print(lokaord.get_md_stats(update_readme_table=update_readme))
	lokaord.get_runtime()


@app.command(help='Update lokaord (same as: "build-db -ch write-files -tr build-sight md-stats").')
def update(update_readme: Annotated[Optional[bool], Option('--update-readme', '-ur')] = False):
	lokaord.build_db(changes_only=True)
	lokaord.write_files(lokaord.Ts)
	lokaord.build_sight()
	print(lokaord.get_md_stats(update_readme_table=update_readme))
	lokaord.get_runtime()


@app.command(help='Add word CLI.')
def add_word():
	lokaord.logman.error('todo: fix this command')
	raise typer.Exit()
	lokaord.add_word()


@app.command(help='Check if git repo is clean, raise exception if not.')
def assert_clean_git():
	lokaord.assert_clean_git()


@app.command(help='Run fiddle.')
def run_fiddle():
	lokaord.run_fiddle()


if __name__ == '__main__':
	app(prog_name=lokaord.Name)
