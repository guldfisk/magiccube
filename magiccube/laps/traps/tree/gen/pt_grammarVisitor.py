# Generated from /home/phdk/PycharmProjects/magiccube/magiccube/laps/traps/tree/pt_grammar.g4 by ANTLR 4.8
from antlr4 import *


if __name__ is not None and "." in __name__:
    from .pt_grammarParser import pt_grammarParser
else:
    from pt_grammarParser import pt_grammarParser

# This class defines a complete generic visitor for a parse tree produced by pt_grammarParser.


class pt_grammarVisitor(ParseTreeVisitor):
    # Visit a parse tree produced by pt_grammarParser#start.
    def visitStart(self, ctx: pt_grammarParser.StartContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by pt_grammarParser#Parenthesis.
    def visitParenthesis(self, ctx: pt_grammarParser.ParenthesisContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by pt_grammarParser#Or.
    def visitOr(self, ctx: pt_grammarParser.OrContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by pt_grammarParser#And.
    def visitAnd(self, ctx: pt_grammarParser.AndContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by pt_grammarParser#Option.
    def visitOption(self, ctx: pt_grammarParser.OptionContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by pt_grammarParser#printings.
    def visitPrintings(self, ctx: pt_grammarParser.PrintingsContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by pt_grammarParser#CardboardExpansion.
    def visitCardboardExpansion(self, ctx: pt_grammarParser.CardboardExpansionContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by pt_grammarParser#CardboardPrintingId.
    def visitCardboardPrintingId(self, ctx: pt_grammarParser.CardboardPrintingIdContext):
        return self.visitChildren(ctx)


del pt_grammarParser
