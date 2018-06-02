import typing as t

from antlr4 import CommonTokenStream, InputStream
from antlr4.error.ErrorListener import ErrorListener

from mtgorp.db.create import CardDatabase
from mtgorp.models.persistent.printing import Printing

from magiccube.laps.traps.tree.printingtree import AllNode, AnyNode, BorderedNode
from magiccube.laps.traps.tree.gen.pt_grammarLexer import pt_grammarLexer
from magiccube.laps.traps.tree.gen.pt_grammarParser import pt_grammarParser
from magiccube.laps.traps.tree.visitor import PTVisitor, All, PrintingCollection


class PrintingTreeParserException(Exception):
	pass


class PrintingTreeListener(ErrorListener):

	def syntaxError(self, recognizer, offendingSymbol, line, column, msg, e):
		raise PrintingTreeParserException('Syntax error')

	def reportContextSensitivity(self, recognizer, dfa, startIndex, stopIndex, prediction, configs):
		raise PrintingTreeParserException('Conetext sensitivity')



class PrintingTreeParser(object):

	def __init__(self, db: CardDatabase):
		self._db = db

		self._visitor = PTVisitor(self._db)

	def _convert_to_printing_node(
		self,
		element: t.Union[PrintingCollection, Printing]
	) -> t.Union[BorderedNode, Printing]:
		if isinstance(element, Printing):
			return element

		return (
			(
				AllNode
				if isinstance(element, All) else
				AnyNode
			)(
				map(self._convert_to_printing_node, element)
			)
		)

	def parse(self, s: str) -> BorderedNode:
		parser = pt_grammarParser(
			CommonTokenStream(
				pt_grammarLexer(
					InputStream(s)
				)
			)
		)

		parser._listeners = [PrintingTreeListener()]

		return self._convert_to_printing_node(
			self._visitor.visit(
				parser.start()
			)
		)

