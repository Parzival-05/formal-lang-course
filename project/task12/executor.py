from typing import Optional, Set, Tuple

from networkx import MultiDiGraph
from pyformlang.finite_automaton import EpsilonNFA

from project.task8 import tensor_based_cfpq
from project.task11.parser.GraphParser import GraphParser
from project.task11.parser.GraphVisitor import GraphVisitor
from project.task12.regex import (
    build_rsm,
    concatenate,
    group,
    intersect,
    nfa_from_char,
    nfa_from_var,
    repeat_range,
    union,
)


class GraphLangRunner(GraphVisitor):
    def __init__(self):
        super(GraphVisitor, self).__init__()
        self.__variables = {}
        self.query_result = {}
        # Special for adding new query results
        self.__query_was_completed = False

    def visitProg(self, ctx: GraphParser.ProgContext):
        self.visitChildren(ctx)

    def visitStmt(self, ctx: GraphParser.StmtContext):
        self.visitChildren(ctx)

    def visitDeclare(self, ctx: GraphParser.DeclareContext):
        var_name = self.__get_var_name(ctx.var())

        self.__variables[var_name] = MultiDiGraph()

    def visitBind(self, ctx: GraphParser.BindContext):
        var_name: str = self.__get_var_name(ctx.var())
        expr_value = self.visitExpr(ctx.expr())

        self.__variables[var_name] = expr_value

        if self.__query_was_completed:
            self.__query_was_completed = False

            self.query_result[var_name] = expr_value

    def visitExpr(self, ctx: GraphParser.ExprContext):
        return self.visitChildren(ctx)

    def visitRegexp(self, ctx: GraphParser.RegexpContext):
        regexpInBrackets = ctx.L_PARENS() and ctx.R_PARENS()

        if ctx.char():
            return nfa_from_char(self.visitChar(ctx.char()))
        elif ctx.var():
            return nfa_from_var(ctx.var().getText())
        elif regexpInBrackets:
            return group(self.visitRegexp(ctx.regexp(0)))
        else:
            if ctx.CIRCUMFLEX():
                left_regexp, range = (
                    self.visitRegexp(ctx.regexp(0)),
                    self.visitRange(ctx.range_()),
                )

                return repeat_range(
                    left_regexp, self.visitNum(range[0]), self.visitNum(range[1])
                )
            else:
                left_regexp, right_regexp = (
                    self.visitRegexp(ctx.regexp(0)),
                    self.visitRegexp(ctx.regexp(1)),
                )

                if ctx.PIPE():
                    return union(left_regexp, right_regexp)
                elif ctx.DOT():
                    return concatenate(left_regexp, right_regexp)
                elif ctx.AMPERSAND():
                    return intersect(left_regexp, right_regexp)

    def visitSelect(self, ctx: GraphParser.SelectContext):
        # for v in [start_set_expr]
        for_var_name_1, for_nodes_set_1 = self.visitV_filter(ctx.v_filter(0))
        # for u in [final_set_expr]
        for_var_name_2, for_nodes_set_2 = self.visitV_filter(ctx.v_filter(1))

        # ... IN <graph> ...
        var_list = ctx.var()
        graph: MultiDiGraph = self.visitVar(var_list[-1])

        nfa_subs_dict: dict[str, EpsilonNFA] = {}

        for key, value in self.__variables.items():
            if isinstance(value, EpsilonNFA):
                nfa_subs_dict[key] = value
            elif isinstance(value, str):
                nfa_subs_dict[key] = nfa_from_char(value)

        query = build_rsm(self.__expr_to_nfa(ctx.expr()), nfa_subs_dict)

        start_var_name = self.__get_var_name(var_list[-2])
        final_var_name = self.__get_var_name(var_list[-3])

        start_nodes, final_nodes = None, None

        # get start/final nodes from FOR:

        # for v in ... from v ...
        if start_var_name == for_var_name_1:
            start_nodes = for_nodes_set_1
        # for v in ... from u ...
        else:
            start_nodes = for_var_name_2
        # for v in ... where v ...
        if final_var_name == for_var_name_2:
            final_nodes = for_nodes_set_2
        # for v in ... where u ...
        else:
            final_nodes = for_var_name_1

        cfpq_result = tensor_based_cfpq(query, graph, start_nodes, final_nodes)
        select_result = set()

        # return first_return_var, second_return_var
        first_return_var = ctx.var(0).getText()
        second_return_var = ctx.var(1).getText()

        # return <start>, <final> where <final> reachable from <start>
        start_var_name = ctx.var()[-2].getText()
        final_var_name = ctx.var()[-3].getText()

        # return <start>
        if first_return_var == start_var_name and not second_return_var:
            for res in cfpq_result:
                select_result.add(res[0])
        # return <final>
        elif first_return_var == final_var_name and not second_return_var:
            for res in cfpq_result:
                select_result.add(res[1])
        # return <start>, <final>
        else:
            select_result = cfpq_result

        # Mark that for BIND
        self.__query_was_completed = True

        return select_result

    def visitV_filter(self, ctx: GraphParser.V_filterContext) -> Tuple[str, Set[int]]:
        if not ctx:
            return (None, None)

        var_name = ctx.var().getText()
        set_expr = self.visitExpr(ctx.expr())

        return (var_name, set_expr)

    def visitAdd(self, ctx: GraphParser.AddContext):
        graph: MultiDiGraph = self.visitVar(ctx.var())

        if ctx.EDGE():
            edge: Tuple[int, str, int] = self.visitExpr(ctx.expr())

            graph.add_edge(edge[0], edge[2], label=edge[1])
        else:
            vertex: int = self.visitExpr(ctx.expr())

            graph.add_node(vertex)

    def visitRemove(self, ctx: GraphParser.RemoveContext):
        # Check variable type
        graph: MultiDiGraph = self.visitVar(ctx.var())

        if ctx.EDGE():
            edge: Tuple[int, str, int] = self.visitExpr(ctx.expr())

            graph.remove_edge(edge[0], edge[2])
        elif ctx.VERTEX():
            vertex: int = self.visitExpr(ctx.expr())

            graph.remove_node(vertex)
        else:
            vertices: set[int] = self.visitExpr(ctx.expr())

            for vertex in vertices:
                graph.remove_node(vertex)

    def visitSet_expr(self, ctx: GraphParser.Set_exprContext) -> Set:
        exprs = ctx.expr()

        result_set: Set[int] = set()

        for expr in exprs:
            num = self.visitExpr(expr)
            result_set.add(num)

        return result_set

    def visitEdge_expr(self, ctx: GraphParser.Edge_exprContext) -> Tuple[int, str, int]:
        edge_exprs = ctx.expr()

        left_num = self.visitExpr(edge_exprs[0])
        char = self.visitExpr(edge_exprs[1])
        right_num = self.visitExpr(edge_exprs[2])

        edge = (left_num, char, right_num)

        return edge

    def visitRange(self, ctx: GraphParser.RangeContext) -> Tuple[int, Optional[int]]:
        return (ctx.num(0), ctx.num(1))

    def visitNum(self, ctx: GraphParser.NumContext):
        return int(ctx.NUM().getText())

    def visitChar(self, ctx: GraphParser.CharContext):
        return str(ctx.CHAR().getText()[1])

    def __expr_to_nfa(self, ctx: GraphParser.ExprContext) -> EpsilonNFA:
        expr_value = self.visitExpr(ctx)

        if isinstance(expr_value, EpsilonNFA):
            return expr_value
        elif isinstance(expr_value, str):
            return nfa_from_char(expr_value)
        else:
            raise Exception(
                f"illegal type '{expr_value}', it can't be coverted to EpsilonNFA."
            )

    def __get_var_name(self, ctx: GraphParser.VarContext) -> str:
        return str(ctx.VAR_ID().getText())

    def visitVar(self, ctx: GraphParser.VarContext):
        var_name = self.__get_var_name(ctx)
        if var_name not in self.__variables:
            raise Exception(f"Variable '{var_name}' doesn't exist.")

        return self.__variables[var_name]
