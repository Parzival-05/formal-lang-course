from project.task11.parser.GraphParser import GraphParser
from project.task11.parser.GraphVisitor import GraphVisitor


class GraphLangType:
    EDGE = "edge"
    NUM = "num"
    CHAR = "char"
    GRAPH = "graph"
    FA = "FA"
    RSM = "RSM"
    SET = "SET<int>"
    PAIR_SET = "SET<int * int>"
    RANGE = "RANGE"
    UNKNOWN = "ERROR"


class VariableStore:
    """A wrapper class for managing variables."""

    def __init__(self):
        self.__variable_types: dict[str, GraphLangType] = {}

    def add_variable(self, name: str, type: GraphLangType):
        assert (
            type != GraphLangType.UNKNOWN
        ), "Attempt to assign unknown type to variable"
        self.__variable_types[name] = type

    def get_variable(self, name: str) -> GraphLangType:
        return self.__variable_types[name]

    def contain_variable(self, name: str) -> bool:
        return name in self.__variable_types.keys()

    def get_all_variables(self) -> dict[str, GraphLangType]:
        return self.__variable_types.copy()

    def clear(self):
        self.__variable_types.clear()

    def __len__(self) -> int:
        return len(self.__variable_types)

    def __contains__(self, name: str) -> bool:
        return self.contain_variable(name)

    def __nonzero__(self) -> bool:
        return len(self.__variable_types) > 0


class GraphLangTyper(GraphVisitor):
    def __init__(self):
        super(GraphVisitor, self).__init__()
        self.__variables = VariableStore()

    def visitProg(self, ctx: GraphParser.ProgContext):
        self.visitChildren(ctx)

    def visitStmt(self, ctx: GraphParser.StmtContext):
        self.visitChildren(ctx)

    def visitDeclare(self, ctx: GraphParser.DeclareContext):
        var_name = self.__get_var_name(ctx.var())

        self.__variables.add_variable(var_name, GraphLangType.GRAPH)

    def visitAdd(self, ctx: GraphParser.AddContext):
        # Check variable type
        var_name = self.__get_var_name(ctx.var())

        if self.visitVar(ctx.var()) != GraphLangType.GRAPH:
            raise Exception(
                f"Variable '{var_name}' have to be GRAPH, not '{self.__variables.get_variable(var_name)}'!"
            )

        # Check expr type
        added_entity_type = self.visitExpr(ctx.expr())

        if ctx.EDGE() and added_entity_type != GraphLangType.EDGE:
            raise Exception(
                f"Illegal edge construction, it can't be added to '{var_name}'."
            )
        elif ctx.VERTEX() and added_entity_type != GraphLangType.NUM:
            raise Exception(
                f"Illegal vertex construction, it can't be added to '{var_name}'."
            )
        else:
            return

    def visitRemove(self, ctx: GraphParser.RemoveContext):
        # Check variable type
        var_name = self.__get_var_name(ctx.var())
        var_type = self.visitVar(ctx.var())

        if var_type != GraphLangType.GRAPH:
            raise Exception(
                f"Variable '{var_name}' have to be GRAPH, not '{self.__variables.get_variable(var_name)}'!"
            )

        # Check expr type
        removed_entity_type = self.visitExpr(ctx.expr())

        if ctx.EDGE() and removed_entity_type != GraphLangType.EDGE:
            raise Exception(
                f"Illegal edge construction, it can't be removed from '{var_name}'."
            )
        elif ctx.VERTEX() and removed_entity_type != GraphLangType.NUM:
            raise Exception(
                f"Illegal vertex construction, it can't be removed from '{var_name}'."
            )
        elif ctx.VERTICES() and removed_entity_type != GraphLangType.SET:
            raise Exception(
                f"Illegal vertices construction, it can't be removed from '{var_name}'"
            )
        else:
            return

    def visitBind(self, ctx: GraphParser.BindContext):
        var_name: str = self.__get_var_name(ctx.var())
        bind_expr_type = self.visitExpr(ctx.expr())

        self.__variables.add_variable(var_name, bind_expr_type)

    def visitExpr(self, ctx: GraphParser.ExprContext):
        return self.visitChildren(ctx)

    def visitRegexp(self, ctx: GraphParser.RegexpContext) -> GraphLangType:
        regexpInBrackets = ctx.L_PARENS() and ctx.R_PARENS()

        if ctx.char():
            return GraphLangType.FA
        elif ctx.var():
            var_name = self.__get_var_name(ctx.var())

            if not self.__variables.contain_variable(var_name):
                return GraphLangType.RSM
            else:
                var_type = self.visitVar(ctx.var())

                if var_type in [GraphLangType.FA, GraphLangType.CHAR]:
                    return GraphLangType.FA

                elif var_type == GraphLangType.RSM:
                    return GraphLangType.RSM

                else:
                    raise Exception(
                        f"Illegal variable type '{var_type}' occured in regexp: '{var_name}'"
                    )

        elif regexpInBrackets:
            return self.visitRegexp(ctx.regexp(0))
        else:
            if ctx.CIRCUMFLEX():
                left_regexp, range = ctx.regexp(0), ctx.range_()

                left_regexp_type = self.visitRegexp(left_regexp)
                range_type = self.visitRange(range)

                if range_type != GraphLangType.RANGE:
                    raise Exception(
                        f"Illegal type in regexp: '{range_type}' instead of '{GraphLangType.RANGE}"
                    )

                if left_regexp_type == GraphLangType.FA:
                    return GraphLangType.FA
                elif left_regexp_type == GraphLangType.RSM:
                    return GraphLangType.RSM
                else:
                    raise Exception(
                        f"Type '{left_regexp_type}' can't be in Repeat (^) operation."
                    )

            else:
                left_regexp, right_regexp = ctx.regexp(0), ctx.regexp(1)

                left_regexp_type, right_regexp_type = (
                    self.visitRegexp(left_regexp),
                    self.visitRegexp(right_regexp),
                )

                if ctx.PIPE() or ctx.DOT():
                    return (
                        GraphLangType.RSM
                        if left_regexp_type == GraphLangType.RSM
                        or right_regexp_type == GraphLangType.RSM
                        else GraphLangType.FA
                    )
                elif ctx.AMPERSAND():
                    if (
                        left_regexp_type == GraphLangType.RSM
                        and right_regexp_type == GraphLangType.RSM
                    ):
                        raise Exception(
                            f'Can\'t intersect two RSMs: "{ctx.getText()}".'
                        )

                    return (
                        GraphLangType.RSM
                        if left_regexp_type == GraphLangType.RSM
                        or right_regexp_type == GraphLangType.RSM
                        else GraphLangType.FA
                    )

        return GraphLangType.UNKNOWN

    def visitSelect(self, ctx: GraphParser.SelectContext):
        # Check v_filters
        self.visitV_filter(ctx.v_filter(0))
        self.visitV_filter(ctx.v_filter(1))

        # Check vars
        var_list: list = ctx.var()

        in_var = self.__get_var_name(var_list[-1])
        from_var = self.__get_var_name(var_list[-2])
        where_var = self.__get_var_name(var_list[-3])

        if self.__variables.get_variable(in_var) != GraphLangType.GRAPH:
            raise Exception(f"Variable '{in_var}' should be graph!")

        # Check result vars
        result_var_1 = self.__get_var_name(var_list[0])
        result_var_2 = self.__get_var_name(var_list[1]) if ctx.COMMA() else None

        if result_var_1 not in [where_var, from_var]:
            raise Exception(
                f"Result variable '{result_var_1}' should be '{from_var}' or '{where_var}'."
            )

        if result_var_2 and (result_var_1 not in [where_var, from_var]):
            raise Exception(
                f"Result variable '{result_var_2}' should be '{from_var}' or '{where_var}'."
            )

        # check expr
        expr_type = self.visitExpr(ctx.expr())

        if expr_type not in [GraphLangType.FA, GraphLangType.RSM, GraphLangType.CHAR]:
            raise Exception(f"Illegal expression in SELECT with type '{expr_type}'.")

        return GraphLangType.SET if not result_var_2 else GraphLangType.PAIR_SET

    def visitV_filter(self, ctx: GraphParser.V_filterContext) -> str:
        if not ctx:
            return None

        var_name = self.__get_var_name(ctx.var())

        # Create new SET variable
        if self.__variables.contain_variable(var_name):
            raise Exception(
                f"Variable '{var_name}' already exists in global context. It can't be used in FOR."
            )

        expr_type = self.visitExpr(ctx.expr())

        if expr_type == GraphLangType.SET:
            return var_name
        else:
            raise Exception(
                f"Filter expression has type '{expr_type}': '{ctx.getText()}'."
            )

    def visitSet_expr(self, ctx: GraphParser.Set_exprContext) -> GraphLangType:
        exprs = ctx.expr()

        for expr in exprs:
            if self.visitExpr(expr) != GraphLangType.NUM:
                raise Exception(f"Illegal construction in RANGE: '{expr.getText()}'")

        return GraphLangType.SET

    def visitEdge_expr(self, ctx: GraphParser.Edge_exprContext):
        edge_exprs = ctx.expr()

        left_num_check = self.visitExpr(edge_exprs[0]) == GraphLangType.NUM
        char_check = self.visitExpr(edge_exprs[1]) == GraphLangType.CHAR
        right_num_check = self.visitExpr(edge_exprs[2]) == GraphLangType.NUM

        edge_check = left_num_check and char_check and right_num_check

        if edge_check:
            return GraphLangType.EDGE
        else:
            raise Exception(f"Illegal EDGE construction: '{ctx.getText()}'")

    def __get_var_name(self, ctx: GraphParser.VarContext) -> str:
        return str(ctx.VAR_ID().getText())

    def visitRange(self, ctx: GraphParser.RangeContext) -> GraphLangType:
        return GraphLangType.RANGE

    def visitNum(self, ctx: GraphParser.NumContext) -> GraphLangType:
        return GraphLangType.NUM

    def visitChar(self, ctx: GraphParser.CharContext) -> GraphLangType:
        return GraphLangType.CHAR

    def visitVar(self, ctx: GraphParser.VarContext) -> GraphLangType:
        var_name = self.__get_var_name(ctx)
        if not self.__variables.contain_variable(var_name):
            raise Exception(f"Variable '{var_name}' doesn't exist.")

        return self.__variables.get_variable(var_name)
