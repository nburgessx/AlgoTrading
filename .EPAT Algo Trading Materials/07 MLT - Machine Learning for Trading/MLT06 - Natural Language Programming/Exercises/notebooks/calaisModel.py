__author__ = 'oren.hazai'

import rdflib
import sys
from collections import defaultdict
from calaisObject import CalaisObject

class CalaisModel:

	def __init__(self, filepath):
		g = rdflib.Graph()
		self.rdfObjects = dict()
		self.rdfObjectsByType = defaultdict(list)
		if (sys.version_info > (3, 0)):
			g.parse(open(filepath,encoding="utf8"))
		else: # python 2
			g.parse(open(filepath))
		for subj, pred, obj in g:
			if pred.toPython().endswith('#type'):
				id = subj.toPython()
				otype = obj.toPython()
				gco = CalaisObject(id, otype)
				self.rdfObjects[id] = gco
				self.rdfObjectsByType[otype].append(gco)
		for subj, pred, obj in g:
			id = subj.toPython()
			gco = self.rdfObjects[id]
			field = pred.toPython()
			if field.endswith('#type'): continue
			val = obj.toPython()
			if type(obj) == rdflib.term.Literal:
				gco.addLiteral(field, val)
			elif type(obj) == rdflib.term.URIRef:
				refid = val
				if refid in self.rdfObjects:
					ref_gco = self.rdfObjects[refid]
					gco.addReference(field, ref_gco)
					ref_gco.addBackReference(gco, field)
				else:
					gco.addExternalURI(field, val)

	def getAllCalaisObjects(self):
		return self.rdfObjects

	def getCalaisObjectById(self, id):
		if id in self.rdfObjects:
			return self.rdfObjects[id]
		return []

	def getCalaisObjectByType(self, obj_type):
		if obj_type in self.rdfObjectsByType:
			return self.rdfObjectsByType[obj_type]
		return []

	def getAllTypes(self):
		return self.rdfObjectsByType.keys()

