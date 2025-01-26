import logging
from antlr4 import CommonTokenStream, ParserRuleContext, InputStream, TerminalNode
from project.task11.parser.GraphLexer import GraphLexer
from project.task11.parser.GraphParser import GraphParser
from antlr4.error.ErrorListener import ErrorListener


#
class MyErrorListener(ErrorListener):
    def syntaxError(self, recognizer, offendingSymbol, line, column, msg, e):
        raise Exception(f"Failed to parse:\n({line},{column}): {msg}\n")


def program_to_tree(program: str) -> tuple[ParserRuleContext, bool]:
    EOF = "EOF"
    program = program.replace(f"<{EOF}>", EOF)
    error_listener = MyErrorListener()

    lexer = GraphLexer(InputStream(program))
    stream = CommonTokenStream(lexer)
    parser = GraphParser(stream)

    lexer.addErrorListener(error_listener)
    parser.addErrorListener(error_listener)

    try:
        tree = parser.prog()
        return (tree, True)
    except Exception as e:
        logging.error(e, exc_info=True)
        return (None, False)


def nodes_count(tree: ParserRuleContext) -> int:
    count = 1
    for child in tree.children:
        if isinstance(child, ParserRuleContext):
            count += nodes_count(child)
    return count


def tree_to_program(tree: ParserRuleContext) -> str:
    result = ""
    for child in tree.children:
        if isinstance(child, TerminalNode):
            result += child.getText() + " "
        elif isinstance(child, ParserRuleContext):
            result += tree_to_program(child)
    return result
