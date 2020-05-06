
grammar pt_grammar;

start : operation EOF;

operation :
    printings #Option
    | '(' operation ')' #Parenthesis
    | operation ';' operation #And
    | operation '||' operation #Or
;

printings :
    printing
    | NUMBER '#' printing
;

printing :
    CARDBOARD '|' EXPANSION #CardboardExpansion
    | CARDBOARD '|' NUMBER #CardboardPrintingId
;

NUMBER : [0-9]+;
EXPANSION : [A-Z0-9]+;
CARDBOARD : ~[();|# \n\t\r](~[();|#])*~[();|# \n\t\r];

WHITESPACE : [ \n\t\r] -> skip;
