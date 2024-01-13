#!/usr/bin/python
"""
Exceptions
"""


class LokaordException(Exception):
	def __init__(self, msg):
		self.msg = msg

	def __repr__(self):
		return self.msg


class VoidKennistrengurError(LokaordException):
	"""Raise when no word exists for specified kennistrengur"""
