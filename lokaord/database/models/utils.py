#!/usr/bin/python
import datetime
from decimal import Decimal

from sqlalchemy import Column, Unicode, Integer, ForeignKey, Boolean, Enum, Numeric, types

TimestampIsoformat = '%Y-%m-%dT%H:%M:%S.%f'
TimestampIsoformatLength = 26

MaxWordLength = 128


class StringyDateTime(types.TypeDecorator):
    '''
    Why are we in sqlite storing timestamps in Unicode instead of the appropriate DateTime?

    BECAUSE DateTime TENDS TO HAVE VARIOUS RANDOM ISSUES DEPENDING ON DATABASE SOFTWARE
    WHICH INTERACTS WITH sqlite ( affirmation: not an issue with sqlite )
    '''
    cache_ok = True

    @property
    def python_type(self):
        return datetime.datetime

    impl = types.Unicode(TimestampIsoformatLength)

    def process_bind_param(self, input_datetime, _):  # _ dialect
        output_datetime_str = None
        if input_datetime is not None:
            output_datetime_str = input_datetime.strftime(TimestampIsoformat)
        return output_datetime_str

    def process_literal_param(self, input_datetime_str, _):  # _ dialect
        output_datetime = None
        if input_datetime_str is not None:
            output_datetime = datetime.datetime.strptime(input_datetime_str, TimestampIsoformat)
        return output_datetime

    def process_result_value(self, input_datetime_str, _):  # _ dialect
        try:
            return datetime.datetime.strptime(input_datetime_str, TimestampIsoformat)
        except (ValueError, TypeError):
            return None


class StringyDecimal(types.TypeDecorator):
    cache_ok = True

    @property
    def python_type(self):
        return Decimal

    impl = types.Unicode(61)

    def process_bind_param(self, input_decimal, _):  # _ dialect
        output_decimal_str = None
        if input_decimal is not None:
            if isinstance(input_decimal, int):
                output_decimal_str = str(input_decimal)
            else:
                output_decimal_str = f'{input_decimal.normalize():f}'
        return output_decimal_str

    def process_literal_param(self, input_decimal_str, _):  # _ dialect
        output_decimal = None
        if input_decimal_str is not None:
            output_decimal = Decimal(input_decimal_str)
        return output_decimal

    def process_result_value(self, input_decimal_str, _):  # _ dialect
        try:
            return Decimal(input_decimal_str)
        except (ValueError, TypeError):
            return None


def timestamp_created():
    return Column(
        types.DateTime().with_variant(StringyDateTime, 'sqlite'),
        default=datetime.datetime.utcnow
    )


def timestamp_edited():
    return Column(
        types.DateTime().with_variant(StringyDateTime, 'sqlite'),
        default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.utcnow
    )


def word(nullable=True, unique=False):
    return Column(Unicode(MaxWordLength), nullable=nullable, unique=unique, server_default=None)


def boolean_default_false():
    return Column(Boolean(), nullable=False, server_default='0')


def selection(selection_enum, default, nullable=True):
    return Column(Enum(selection_enum), nullable=nullable, default=default)


def integer_primary_key():
    return Column(Integer(), primary_key=True)


def foreign_integer_primary_key(name, nullable=True):
    return Column(Integer(), ForeignKey('{name}.{name}_id'.format(name=name)), nullable=nullable)


def integer_default_zero():
    return Column(Integer(), nullable=False, server_default='0')


def decimal(nullable=True):
    return Column(
        Numeric(precision=30, scale=30).with_variant(StringyDecimal, 'sqlite'), nullable=nullable
    )


def json_object() -> Column:
    return Column(types.JSON(), nullable=True)
