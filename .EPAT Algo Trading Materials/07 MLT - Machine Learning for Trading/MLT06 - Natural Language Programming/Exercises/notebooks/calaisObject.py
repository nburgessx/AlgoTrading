__author__ = 'benny.vaknin'
from collections import defaultdict

class CalaisObject:

	def __init__(self, subject, type_of_object):
		self._object_id = subject
		self._type = type_of_object
		self._literals = defaultdict(list)
		self._references = defaultdict(list)
		self._back_references = defaultdict(dict)
		self._external_uris = defaultdict(list)

	def getObjectId(self):
		return self._object_id

	def getType(self):
		return self._type

	def getLiterals(self):
		return self._literals

	def getReferences(self):
		return self._references

	def getBackReferences(self):
		return self._back_references

	def getBackReferencesByFieldName(self, field):
		return self._back_references[field]

	def getExternalURIs(self):
		return self._external_uris

	def addLiteral(self, field, value):
		self._literals[field].append(value)

	def addReference(self, field, value):
		self._references[field].append(value)

	def addBackReference(self, gco, field):
		if gco.getType() in self._back_references[field]:
			self._back_references[field][gco.getType()].append(gco)
		else:
			self._back_references[field][gco.getType()] = [gco]

	def addExternalURI(self, field, value):
		self._external_uris[field] = value
