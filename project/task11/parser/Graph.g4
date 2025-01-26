grammar Graph;

prog : stmt* ;

stmt : bind | add | remove | declare ;

declare : LET VAR_ID IS GRAPH ;

bind : LET VAR_ID EQUAL expr ;

remove : REMOVE (VERTEX | EDGE | VERTICES) expr FROM VAR_ID ;

add : ADD (VERTEX | EDGE) expr TO VAR_ID ;

expr : NUM | CHAR | VAR_ID | edge_expr | set_expr | regexp | select ;

set_expr : L_BRACKET expr (COMMA expr)* R_BRACKET ;

edge_expr : L_PARENS expr COMMA expr COMMA expr R_PARENS ;

regexp: term ('|' term)*;
term: factor (('.' | '&') factor)*;
factor: primary ('^' range)*;
primary: CHAR | VAR_ID | '(' regexp ')';

range : L_BRACKET NUM ELLIPSIS NUM? R_BRACKET ;

select : v_filter? v_filter? RETURN VAR_ID (COMMA VAR_ID)? WHERE VAR_ID REACHABLE FROM VAR_ID IN VAR_ID BY expr ;

v_filter : FOR VAR_ID IN expr ;


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
