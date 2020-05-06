# Generated from /home/phdk/PycharmProjects/magiccube/magiccube/laps/traps/tree/pt_grammar.g4 by ANTLR 4.8
from antlr4 import *
if __name__ is not None and "." in __name__:
    from .pt_grammarParser import pt_grammarParser
else:
    from pt_grammarParser import pt_grammarParser

# This class defines a complete listener for a parse tree produced by pt_grammarParser.
class pt_grammarListener(ParseTreeListener):

    # Enter a parse tree produced by pt_grammarParser#start.
    def enterStart(self, ctx:pt_grammarParser.StartContext):
        pass

    # Exit a parse tree produced by pt_grammarParser#start.
    def exitStart(self, ctx:pt_grammarParser.StartContext):
        pass


    # Enter a parse tree produced by pt_grammarParser#Parenthesis.
    def enterParenthesis(self, ctx:pt_grammarParser.ParenthesisContext):
        pass

    # Exit a parse tree produced by pt_grammarParser#Parenthesis.
    def exitParenthesis(self, ctx:pt_grammarParser.ParenthesisContext):
        pass


    # Enter a parse tree produced by pt_grammarParser#Or.
    def enterOr(self, ctx:pt_grammarParser.OrContext):
        pass

    # Exit a parse tree produced by pt_grammarParser#Or.
    def exitOr(self, ctx:pt_grammarParser.OrContext):
        pass


    # Enter a parse tree produced by pt_grammarParser#And.
    def enterAnd(self, ctx:pt_grammarParser.AndContext):
        pass

    # Exit a parse tree produced by pt_grammarParser#And.
    def exitAnd(self, ctx:pt_grammarParser.AndContext):
        pass


    # Enter a parse tree produced by pt_grammarParser#Option.
    def enterOption(self, ctx:pt_grammarParser.OptionContext):
        pass

    # Exit a parse tree produced by pt_grammarParser#Option.
    def exitOption(self, ctx:pt_grammarParser.OptionContext):
        pass


    # Enter a parse tree produced by pt_grammarParser#printings.
    def enterPrintings(self, ctx:pt_grammarParser.PrintingsContext):
        pass

    # Exit a parse tree produced by pt_grammarParser#printings.
    def exitPrintings(self, ctx:pt_grammarParser.PrintingsContext):
        pass


    # Enter a parse tree produced by pt_grammarParser#CardboardExpansion.
    def enterCardboardExpansion(self, ctx:pt_grammarParser.CardboardExpansionContext):
        pass

    # Exit a parse tree produced by pt_grammarParser#CardboardExpansion.
    def exitCardboardExpansion(self, ctx:pt_grammarParser.CardboardExpansionContext):
        pass


    # Enter a parse tree produced by pt_grammarParser#CardboardPrintingId.
    def enterCardboardPrintingId(self, ctx:pt_grammarParser.CardboardPrintingIdContext):
        pass

    # Exit a parse tree produced by pt_grammarParser#CardboardPrintingId.
    def exitCardboardPrintingId(self, ctx:pt_grammarParser.CardboardPrintingIdContext):
        pass



del pt_grammarParser