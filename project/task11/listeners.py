from antlr4 import (
    ParseTreeListener,
    TerminalNode,
)
from antlr4.error.ErrorListener import ErrorListener


class NodesCountListener(ParseTreeListener):
    def __init__(self):
        super().__init__()
        self.__count = 0

    def visitTerminal(self, node: TerminalNode):
        self.__count += 1

    @property
    def nodes_count(self):
        return self.__count


class ProgramTextListener(ParseTreeListener):
    def __init__(self):
        super().__init__()
        self.__terminals_text = []

    def visitTerminal(self, node: TerminalNode):
        self.__terminals_text.append(node.getText())

    @property
    def program_text(self):
        return " ".join(self.__terminals_text)


class MyErrorListener(ErrorListener):
    def syntaxError(self, recognizer, offendingSymbol, line, column, msg, e):
        raise Exception(f"error while parsing ({line},{column}): {msg}\n")
