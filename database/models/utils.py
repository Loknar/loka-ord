#!/usr/bin/python
import datetime

from sqlalchemy import Column, Unicode, Integer, ForeignKey, Boolean, Enum, JSON, types

Isoformat = '%Y-%m-%dT%H:%M:%S.%f'
IsoformatLength = 26

MaximumWordLength = 128


class StringyDateTime(types.TypeDecorator):
    '''
    Why are we in sqlite storing timestamps in Unicode instead of the appropriate DateTime?

    BECAUSE DateTime TENDS TO HAVE VARIOUS RANDOM ISSUES DEPENDING ON DATABASE SOFTWARE
    WHICH INTERACTS WITH sqlite ( affirmation: not an issue with sqlite )
    '''

    @property
    def python_type(self):
        return datetime.datetime

    impl = types.Unicode(IsoformatLength)

    def process_bind_param(self, input_datetime, dialect):
        output_datetime_str = None
        if input_datetime is not None:
            output_datetime_str = input_datetime.strftime(Isoformat)
        return output_datetime_str

    def process_literal_param(self, input_datetime_str, dialect):
        output_datetime = None
        if input_datetime_str is not None:
            output_datetime = datetime.datetime.strptime(input_datetime_str, Isoformat)
        return output_datetime

    def process_result_value(self, input_datetime_str, dialect):
        try:
            return datetime.datetime.strptime(input_datetime_str, Isoformat)
        except (ValueError, TypeError):
            return None


def timestamp(column_name: str, index: bool = False) -> Column:
    return Column(
        column_name,
        types.DateTime().with_variant(StringyDateTime, 'sqlite'),
        index=index,
        nullable=True
    )


def timestamp_created():
    def ts_utcnow():
        return datetime.datetime.utcnow().strftime(Isoformat)
    return Column(Unicode(IsoformatLength), default=ts_utcnow)


def timestamp_edited():
    def ts_utcnow():
        return datetime.datetime.utcnow().strftime(Isoformat)
    return Column(Unicode(IsoformatLength), default=ts_utcnow, onupdate=ts_utcnow)


def timestamp_future(minutes=(60 * 24)):
    def ts_future():
        return (
            datetime.datetime.utcnow() + datetime.timedelta(minutes=minutes)
        ).strftime(Isoformat)
    return Column(Unicode(IsoformatLength), default=ts_future)


def word_column():
    return Column(Unicode(MaximumWordLength), nullable=False, server_default='')


def boolean_default_false():
    return Column(Boolean(), nullable=False, server_default='0')


def selection(selection_enum, default):
    return Column(Enum(selection_enum), nullable=False, default=default)


def integer_primary_key():
    return Column(Integer(), primary_key=True)


def foreign_integer_primary_key(name):
    return Column(Integer(), ForeignKey('{name}.{name}_id'.format(name=name)))


def integer_default_zero():
    return Column(Integer(), nullable=False, server_default='0')


def json_object():
    # !NOTE! `(https://docs.sqlalchemy.org/en/13/core/type_basics.html#sqlalchemy.types.JSON)`
    # types.JSON is provided as a facade for vendor-specific JSON types. Since it supports JSON
    # SQL operations, it only works on backends that have an actual JSON type, currently:
    # * PostgreSQL
    # * MySQL as of version 5.7 (MariaDB as of the 10.2 series does not)
    # * SQLite as of version 3.9
    return Column(JSON(), server_default=JSON.NULL)
