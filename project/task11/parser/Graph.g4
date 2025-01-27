grammar Graph;

prog : stmt* ;

stmt : bind | add | remove | declare ;

declare : LET var IS GRAPH ;

bind : LET var EQUAL expr ;

remove : REMOVE (VERTEX | EDGE | VERTICES) expr FROM var ;

add : ADD (VERTEX | EDGE) expr TO var ;

expr : num | char | var | edge_expr | set_expr | regexp | select ;

set_expr : L_BRACKET expr (COMMA expr)* R_BRACKET ;

edge_expr : L_PARENS expr COMMA expr COMMA expr R_PARENS ;

regexp: char
        | var
        | L_PARENS regexp R_PARENS
        | regexp CIRCUMFLEX range
        | regexp DOT regexp
        | regexp PIPE regexp
        | regexp AMPERSAND regexp;

range : L_BRACKET num ELLIPSIS? num? R_BRACKET ;

select : v_filter? v_filter? RETURN var (COMMA var)? WHERE var REACHABLE FROM var IN var BY expr ;

v_filter : FOR var IN expr ;

num: NUM ;
char: CHAR ;
var: VAR_ID ;

// Lexer rules
LET:            'let' ;
IS:             'is' ;
GRAPH:          'graph' ;
REMOVE:         'remove' ;
WHERE:          'where' ;
REACHABLE:      'reachable' ;
RETURN:         'return' ;
BY:             'by' ;
VERTEX:         'vertex' ;
EDGE:           'edge' ;
VERTICES:       'vertices' ;
FROM:           'from' ;
ADD:            'add' ;
TO:             'to' ;
FOR:            'for' ;
IN:             'in' ;

EQUAL:          '=' ;
L_BRACKET:   '[' ;
L_PARENS:  '(' ;
R_BRACKET:   ']' ;
R_PARENS:  ')' ;
COMMA:          ',' ;
CIRCUMFLEX:     '^' ;
DOT:            '.' ;
AMPERSAND:      '&' ;
ELLIPSIS:       '..' ;
PIPE:           '|' ;

VAR_ID : [a-zA-Z] [a-zA-Z0-9]* ;
NUM : [0-9]+ ;
CHAR : '"' [a-z] '"' | '\'' [a-z] '\'' ;

WS : [ \t\r\n\f]+ -> skip ;
