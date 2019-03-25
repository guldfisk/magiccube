
from mtgorp.db.create import CardDatabase
from mtgorp.models.persistent.printing import Printing

from magiccube.laps.traps.tree.gen.pt_grammarParser import pt_grammarParser
from magiccube.laps.traps.tree.gen.pt_grammarVisitor import pt_grammarVisitor


class PrintingCollection(list):

	def __init__(self, *args, **kwargs) -> None:
		super().__init__(*args, **kwargs)
		self.locked = False

	def __repr__(self):
		return '{}({})'.format(
			self.__class__.__name__,
			super().__repr__(),
		)


class All(PrintingCollection):
	pass


class Any(PrintingCollection):
	pass


class CardboardParseException(Exception):
	pass


class PTVisitor(pt_grammarVisitor):

	def __init__(self, db: CardDatabase) -> None:
		self._db = db

	def _get_printing(self, name: str, code: str = None) -> Printing:

		try:
			cardboard = self._db.cardboards[name]
		except KeyError:
			raise CardboardParseException('bad cardboard: "{}"'.format(name))

		if code is not None:
			try:
				printing = cardboard.from_expansion(code)
			except KeyError:
				raise CardboardParseException('bad expansion for cardboard: "{}", "{}"'.format(code, cardboard))
		else:
			try:
				printing = cardboard.printing
			except StopIteration:
				raise CardboardParseException('bad cardboard: has no printings: "{}"'.format(cardboard))

		return printing

	def visitStart(self, ctx: pt_grammarParser.StartContext):
		result = self.visit(ctx.operation())
		if isinstance(result, PrintingCollection):
			return result
		return All((result,))

	def visitParenthesis(self, ctx: pt_grammarParser.ParenthesisContext):
		contains = self.visit(ctx.operation())
		if isinstance(contains, PrintingCollection):
			contains.locked = True
		return contains

	def visitOr(self, ctx: pt_grammarParser.OrContext):
		first, second = self.visit(ctx.operation(0)), self.visit(ctx.operation(1))

		if isinstance(first, Any):
			if isinstance(second, Any):
				first.extend(second)
				return first
			first.append(second)
			return first

		if isinstance(second, Any):
			if isinstance(first, Any):
				second.extend(first)
				return second
			second.append(first)
			return second

		return Any((first, second))

	def visitAnd(self, ctx: pt_grammarParser.AndContext):
		first, second = self.visit(ctx.operation(0)), self.visit(ctx.operation(1))

		if isinstance(first, All) and not first.locked:
			if isinstance(second, All) and not second.locked:
				first.extend(second)
				return first
			first.append(second)
			return first

		if isinstance(second, All) and not second.locked:
			if isinstance(first, All) and not first.locked:
				second.extend(first)
				return second
			second.append(first)
			return second

		return All((first, second))

	def visitOption(self, ctx: pt_grammarParser.OptionContext):
		return self.visit(ctx.printings())

	def visitPrintings(self, ctx: pt_grammarParser.PrintingsContext):
		printing = self.visit(ctx.printing())
		return printing if not ctx.MULTIPLICITY() else All((printing,) * int(str(ctx.MULTIPLICITY())))

	def visitCardboardExpansion(self, ctx: pt_grammarParser.CardboardExpansionContext):
		return self._get_printing(
			str(ctx.CARDBOARD()),
			(
				str(ctx.EXPANSION())
				if ctx.EXPANSION() is not None else
				None
			)
		)

	def visitCardboardPrintingId(self, ctx: pt_grammarParser.CardboardPrintingIdContext):
		try:
			return self._db.printings[int(ctx.PRINTING_ID().getText())]

		except KeyError:
			raise CardboardParseException(f'bad printing id: "{ctx.PRINTING_ID()}"')
