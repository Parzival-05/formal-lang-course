from antlr4 import (
    CommonTokenStream,
    InputStream,
)

from project.task11.parser.GraphLexer import GraphLexer
from project.task11.parser.GraphParser import GraphParser
from project.task12.executor import GraphLangRunner
from project.task12.typechecker import GraphLangTyper


def typing_program(program: str) -> bool:
    lexer = GraphLexer(InputStream(program))
    stream = CommonTokenStream(lexer)
    parser = GraphParser(stream)

    tree = parser.prog()
    types_visitor = GraphLangTyper()

    try:
        types_visitor.visit(tree)

        return True
    except Exception:
        return False


def exec_program(program: str) -> dict[str, set[tuple]]:
    lexer = GraphLexer(InputStream(program))
    stream = CommonTokenStream(lexer)
    parser = GraphParser(stream)

    tree = parser.prog()
    runner_visitor = GraphLangRunner()

    try:
        runner_visitor.visit(tree)
        return runner_visitor.query_result
    except Exception:
        return {}
