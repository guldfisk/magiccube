# Generated from /home/phdk/PycharmProjects/magiccube/magiccube/laps/traps/tree/pt_grammar.g4 by ANTLR 4.8
# encoding: utf-8
from antlr4 import *
from io import StringIO
import sys
if sys.version_info[1] > 5:
	from typing import TextIO
else:
	from typing.io import TextIO


def serializedATN():
    with StringIO() as buf:
        buf.write("\3\u608b\ua72a\u8133\ub9ed\u417c\u3be7\u7786\u5964\3\f")
        buf.write("/\4\2\t\2\4\3\t\3\4\4\t\4\4\5\t\5\3\2\3\2\3\2\3\3\3\3")
        buf.write("\3\3\3\3\3\3\3\3\5\3\24\n\3\3\3\3\3\3\3\3\3\3\3\3\3\7")
        buf.write("\3\34\n\3\f\3\16\3\37\13\3\3\4\3\4\3\4\3\4\5\4%\n\4\3")
        buf.write("\5\3\5\3\5\3\5\3\5\3\5\5\5-\n\5\3\5\2\3\4\6\2\4\6\b\2")
        buf.write("\2\2/\2\n\3\2\2\2\4\23\3\2\2\2\6$\3\2\2\2\b,\3\2\2\2\n")
        buf.write("\13\5\4\3\2\13\f\7\2\2\3\f\3\3\2\2\2\r\16\b\3\1\2\16\24")
        buf.write("\5\6\4\2\17\20\7\3\2\2\20\21\5\4\3\2\21\22\7\4\2\2\22")
        buf.write("\24\3\2\2\2\23\r\3\2\2\2\23\17\3\2\2\2\24\35\3\2\2\2\25")
        buf.write("\26\f\4\2\2\26\27\7\5\2\2\27\34\5\4\3\5\30\31\f\3\2\2")
        buf.write("\31\32\7\6\2\2\32\34\5\4\3\4\33\25\3\2\2\2\33\30\3\2\2")
        buf.write("\2\34\37\3\2\2\2\35\33\3\2\2\2\35\36\3\2\2\2\36\5\3\2")
        buf.write("\2\2\37\35\3\2\2\2 %\5\b\5\2!\"\7\t\2\2\"#\7\7\2\2#%\5")
        buf.write("\b\5\2$ \3\2\2\2$!\3\2\2\2%\7\3\2\2\2&\'\7\13\2\2\'(\7")
        buf.write("\b\2\2(-\7\n\2\2)*\7\13\2\2*+\7\b\2\2+-\7\t\2\2,&\3\2")
        buf.write("\2\2,)\3\2\2\2-\t\3\2\2\2\7\23\33\35$,")
        return buf.getvalue()


class pt_grammarParser ( Parser ):

    grammarFileName = "pt_grammar.g4"

    atn = ATNDeserializer().deserialize(serializedATN())

    decisionsToDFA = [ DFA(ds, i) for i, ds in enumerate(atn.decisionToState) ]

    sharedContextCache = PredictionContextCache()

    literalNames = [ "<INVALID>", "'('", "')'", "';'", "'||'", "'#'", "'|'" ]

    symbolicNames = [ "<INVALID>", "<INVALID>", "<INVALID>", "<INVALID>", 
                      "<INVALID>", "<INVALID>", "<INVALID>", "NUMBER", "EXPANSION", 
                      "CARDBOARD", "WHITESPACE" ]

    RULE_start = 0
    RULE_operation = 1
    RULE_printings = 2
    RULE_printing = 3

    ruleNames =  [ "start", "operation", "printings", "printing" ]

    EOF = Token.EOF
    T__0=1
    T__1=2
    T__2=3
    T__3=4
    T__4=5
    T__5=6
    NUMBER=7
    EXPANSION=8
    CARDBOARD=9
    WHITESPACE=10

    def __init__(self, input:TokenStream, output:TextIO = sys.stdout):
        super().__init__(input, output)
        self.checkVersion("4.8")
        self._interp = ParserATNSimulator(self, self.atn, self.decisionsToDFA, self.sharedContextCache)
        self._predicates = None




    class StartContext(ParserRuleContext):

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def operation(self):
            return self.getTypedRuleContext(pt_grammarParser.OperationContext,0)


        def EOF(self):
            return self.getToken(pt_grammarParser.EOF, 0)

        def getRuleIndex(self):
            return pt_grammarParser.RULE_start

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterStart" ):
                listener.enterStart(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitStart" ):
                listener.exitStart(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitStart" ):
                return visitor.visitStart(self)
            else:
                return visitor.visitChildren(self)




    def start(self):

        localctx = pt_grammarParser.StartContext(self, self._ctx, self.state)
        self.enterRule(localctx, 0, self.RULE_start)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 8
            self.operation(0)
            self.state = 9
            self.match(pt_grammarParser.EOF)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class OperationContext(ParserRuleContext):

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser


        def getRuleIndex(self):
            return pt_grammarParser.RULE_operation

     
        def copyFrom(self, ctx:ParserRuleContext):
            super().copyFrom(ctx)


    class ParenthesisContext(OperationContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a pt_grammarParser.OperationContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def operation(self):
            return self.getTypedRuleContext(pt_grammarParser.OperationContext,0)


        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterParenthesis" ):
                listener.enterParenthesis(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitParenthesis" ):
                listener.exitParenthesis(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitParenthesis" ):
                return visitor.visitParenthesis(self)
            else:
                return visitor.visitChildren(self)


    class OrContext(OperationContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a pt_grammarParser.OperationContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def operation(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(pt_grammarParser.OperationContext)
            else:
                return self.getTypedRuleContext(pt_grammarParser.OperationContext,i)


        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterOr" ):
                listener.enterOr(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitOr" ):
                listener.exitOr(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitOr" ):
                return visitor.visitOr(self)
            else:
                return visitor.visitChildren(self)


    class AndContext(OperationContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a pt_grammarParser.OperationContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def operation(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(pt_grammarParser.OperationContext)
            else:
                return self.getTypedRuleContext(pt_grammarParser.OperationContext,i)


        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterAnd" ):
                listener.enterAnd(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitAnd" ):
                listener.exitAnd(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitAnd" ):
                return visitor.visitAnd(self)
            else:
                return visitor.visitChildren(self)


    class OptionContext(OperationContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a pt_grammarParser.OperationContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def printings(self):
            return self.getTypedRuleContext(pt_grammarParser.PrintingsContext,0)


        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterOption" ):
                listener.enterOption(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitOption" ):
                listener.exitOption(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitOption" ):
                return visitor.visitOption(self)
            else:
                return visitor.visitChildren(self)



    def operation(self, _p:int=0):
        _parentctx = self._ctx
        _parentState = self.state
        localctx = pt_grammarParser.OperationContext(self, self._ctx, _parentState)
        _prevctx = localctx
        _startState = 2
        self.enterRecursionRule(localctx, 2, self.RULE_operation, _p)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 17
            self._errHandler.sync(self)
            token = self._input.LA(1)
            if token in [pt_grammarParser.NUMBER, pt_grammarParser.CARDBOARD]:
                localctx = pt_grammarParser.OptionContext(self, localctx)
                self._ctx = localctx
                _prevctx = localctx

                self.state = 12
                self.printings()
                pass
            elif token in [pt_grammarParser.T__0]:
                localctx = pt_grammarParser.ParenthesisContext(self, localctx)
                self._ctx = localctx
                _prevctx = localctx
                self.state = 13
                self.match(pt_grammarParser.T__0)
                self.state = 14
                self.operation(0)
                self.state = 15
                self.match(pt_grammarParser.T__1)
                pass
            else:
                raise NoViableAltException(self)

            self._ctx.stop = self._input.LT(-1)
            self.state = 27
            self._errHandler.sync(self)
            _alt = self._interp.adaptivePredict(self._input,2,self._ctx)
            while _alt!=2 and _alt!=ATN.INVALID_ALT_NUMBER:
                if _alt==1:
                    if self._parseListeners is not None:
                        self.triggerExitRuleEvent()
                    _prevctx = localctx
                    self.state = 25
                    self._errHandler.sync(self)
                    la_ = self._interp.adaptivePredict(self._input,1,self._ctx)
                    if la_ == 1:
                        localctx = pt_grammarParser.AndContext(self, pt_grammarParser.OperationContext(self, _parentctx, _parentState))
                        self.pushNewRecursionContext(localctx, _startState, self.RULE_operation)
                        self.state = 19
                        if not self.precpred(self._ctx, 2):
                            from antlr4.error.Errors import FailedPredicateException
                            raise FailedPredicateException(self, "self.precpred(self._ctx, 2)")
                        self.state = 20
                        self.match(pt_grammarParser.T__2)
                        self.state = 21
                        self.operation(3)
                        pass

                    elif la_ == 2:
                        localctx = pt_grammarParser.OrContext(self, pt_grammarParser.OperationContext(self, _parentctx, _parentState))
                        self.pushNewRecursionContext(localctx, _startState, self.RULE_operation)
                        self.state = 22
                        if not self.precpred(self._ctx, 1):
                            from antlr4.error.Errors import FailedPredicateException
                            raise FailedPredicateException(self, "self.precpred(self._ctx, 1)")
                        self.state = 23
                        self.match(pt_grammarParser.T__3)
                        self.state = 24
                        self.operation(2)
                        pass

             
                self.state = 29
                self._errHandler.sync(self)
                _alt = self._interp.adaptivePredict(self._input,2,self._ctx)

        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.unrollRecursionContexts(_parentctx)
        return localctx


    class PrintingsContext(ParserRuleContext):

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def printing(self):
            return self.getTypedRuleContext(pt_grammarParser.PrintingContext,0)


        def NUMBER(self):
            return self.getToken(pt_grammarParser.NUMBER, 0)

        def getRuleIndex(self):
            return pt_grammarParser.RULE_printings

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterPrintings" ):
                listener.enterPrintings(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitPrintings" ):
                listener.exitPrintings(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitPrintings" ):
                return visitor.visitPrintings(self)
            else:
                return visitor.visitChildren(self)




    def printings(self):

        localctx = pt_grammarParser.PrintingsContext(self, self._ctx, self.state)
        self.enterRule(localctx, 4, self.RULE_printings)
        try:
            self.state = 34
            self._errHandler.sync(self)
            token = self._input.LA(1)
            if token in [pt_grammarParser.CARDBOARD]:
                self.enterOuterAlt(localctx, 1)
                self.state = 30
                self.printing()
                pass
            elif token in [pt_grammarParser.NUMBER]:
                self.enterOuterAlt(localctx, 2)
                self.state = 31
                self.match(pt_grammarParser.NUMBER)
                self.state = 32
                self.match(pt_grammarParser.T__4)
                self.state = 33
                self.printing()
                pass
            else:
                raise NoViableAltException(self)

        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class PrintingContext(ParserRuleContext):

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser


        def getRuleIndex(self):
            return pt_grammarParser.RULE_printing

     
        def copyFrom(self, ctx:ParserRuleContext):
            super().copyFrom(ctx)



    class CardboardPrintingIdContext(PrintingContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a pt_grammarParser.PrintingContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def CARDBOARD(self):
            return self.getToken(pt_grammarParser.CARDBOARD, 0)
        def NUMBER(self):
            return self.getToken(pt_grammarParser.NUMBER, 0)

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterCardboardPrintingId" ):
                listener.enterCardboardPrintingId(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitCardboardPrintingId" ):
                listener.exitCardboardPrintingId(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitCardboardPrintingId" ):
                return visitor.visitCardboardPrintingId(self)
            else:
                return visitor.visitChildren(self)


    class CardboardExpansionContext(PrintingContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a pt_grammarParser.PrintingContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def CARDBOARD(self):
            return self.getToken(pt_grammarParser.CARDBOARD, 0)
        def EXPANSION(self):
            return self.getToken(pt_grammarParser.EXPANSION, 0)

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterCardboardExpansion" ):
                listener.enterCardboardExpansion(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitCardboardExpansion" ):
                listener.exitCardboardExpansion(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitCardboardExpansion" ):
                return visitor.visitCardboardExpansion(self)
            else:
                return visitor.visitChildren(self)



    def printing(self):

        localctx = pt_grammarParser.PrintingContext(self, self._ctx, self.state)
        self.enterRule(localctx, 6, self.RULE_printing)
        try:
            self.state = 42
            self._errHandler.sync(self)
            la_ = self._interp.adaptivePredict(self._input,4,self._ctx)
            if la_ == 1:
                localctx = pt_grammarParser.CardboardExpansionContext(self, localctx)
                self.enterOuterAlt(localctx, 1)
                self.state = 36
                self.match(pt_grammarParser.CARDBOARD)
                self.state = 37
                self.match(pt_grammarParser.T__5)
                self.state = 38
                self.match(pt_grammarParser.EXPANSION)
                pass

            elif la_ == 2:
                localctx = pt_grammarParser.CardboardPrintingIdContext(self, localctx)
                self.enterOuterAlt(localctx, 2)
                self.state = 39
                self.match(pt_grammarParser.CARDBOARD)
                self.state = 40
                self.match(pt_grammarParser.T__5)
                self.state = 41
                self.match(pt_grammarParser.NUMBER)
                pass


        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx



    def sempred(self, localctx:RuleContext, ruleIndex:int, predIndex:int):
        if self._predicates == None:
            self._predicates = dict()
        self._predicates[1] = self.operation_sempred
        pred = self._predicates.get(ruleIndex, None)
        if pred is None:
            raise Exception("No predicate with index:" + str(ruleIndex))
        else:
            return pred(localctx, predIndex)

    def operation_sempred(self, localctx:OperationContext, predIndex:int):
            if predIndex == 0:
                return self.precpred(self._ctx, 2)
         

            if predIndex == 1:
                return self.precpred(self._ctx, 1)
         




