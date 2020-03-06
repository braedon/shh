from enum import Enum


class Comparator(Enum):
    eq = '='
    ne = '!='
    gt = '>'
    ge = '>='
    lt = '<'
    le = '<='


class Combinators(Enum):
    and_ = 'AND'
    or_ = 'OR'


class JoinTypes(Enum):
    inner = 'INNER JOIN'
    outer = 'OUTER JOIN'


class Table:

    def __init__(self, name, alias=None, columns=None):
        self.name = name
        self.alias = alias
        self.columns = columns

    def copy(self, **kwargs):
        return Table(**{'name': self.name,
                        'alias': self.alias,
                        'columns': self.columns,
                        **kwargs})

    def as_alias(self, alias):
        assert self.alias is None
        return self.copy(alias=alias)

    def all(self):
        return TableWildcard(self)

    def on(self, clause):
        return JoinClause(self, clause)

    def aliased_name(self):
        return self.name if self.alias is None else self.alias

    def __getitem__(self, key):
        # Raw column names
        if isinstance(key, str):
            if self.columns is not None and key not in self.columns:
                raise KeyError(f'Column {key} not in specified columns')
            return BasicColumn(self, key)

        # Indexes into the columns proeprty
        elif isinstance(key, int):
            # Handle unspecified (None) columns
            if self.columns is None:
                raise TypeError('Can\'t use column indices when columns aren\'t specified')
            return BasicColumn(self, self.columns[key])

        else:
            raise TypeError('Expected column name or index')


class WildcardType:
    __instance = None

    def __new__(cls):
        if cls.__instance is None:
            cls.__instance = object.__new__(cls)
        return cls.__instance


Wildcard = WildcardType()


class TableWildcard:

    def __init__(self, table):
        self.table = table


class Value:
    pass


class Column(Value):

    def __eq__(self, other):
        return BasicClause(self, Comparator.eq, other)

    def __ne__(self, other):
        return BasicClause(self, Comparator.ne, other)

    def __gt__(self, other):
        return BasicClause(self, Comparator.gt, other)

    def __ge__(self, other):
        return BasicClause(self, Comparator.ge, other)

    def __lt__(self, other):
        return BasicClause(self, Comparator.lt, other)

    def __le__(self, other):
        return BasicClause(self, Comparator.le, other)

    def in_clause(self, values, prefix, inverted=False):
        return InClause(self, values, prefix, inverted=inverted)


class BasicColumn(Column):

    def __init__(self, table, name, alias=None):
        self.table = table
        self.name = name
        self.alias = alias

    def copy(self, **kwargs):
        return BasicColumn(**{'table': self.table,
                              'name': self.name,
                              'alias': self.alias,
                              **kwargs})

    def as_alias(self, alias):
        assert self.alias is None
        return self.copy(alias=alias)


class ColumnAlias(Column):

    def __init__(self, alias):
        self.alias = alias


class Param(Value):

    def __init__(self, name):
        self.name = name


class Clause:

    def __and__(self, other):
        self_comb = isinstance(self, CombinedClause)
        other_comb = isinstance(other, CombinedClause)

        if self_comb and other_comb and self.op == other.op == Combinators.and_:
            return self.copy(clauses=[*self.clauses, *other.clauses])

        elif self_comb and self.op == Combinators.and_:
            return self.copy(clauses=[*self.clauses, other])

        elif other_comb and other.op == Combinators.and_:
            return other.copy([self, *other.clauses])

        else:
            return CombinedClause(Combinators.and_, [self, other])

    def __or__(self, other):
        self_comb = isinstance(self, CombinedClause)
        other_comb = isinstance(other, CombinedClause)

        if self_comb and other_comb and self.op == other.op == Combinators.or_:
            return self.copy(clauses=[*self.clauses, *other.clauses])

        elif self_comb and self.op == Combinators.or_:
            return self.copy(clauses=[*self.clauses, other])

        elif other_comb and other.op == Combinators.or_:
            return other.copy([self, *other.clauses])

        else:
            return CombinedClause(Combinators.or_, [self, other])

    def __invert__(self):
        return NegatedClause(self)


class BasicClause(Clause):

    def __init__(self,
                 left,
                 op,
                 right):

        self.left = left
        self.op = op
        self.right = right


class InClause(Clause):

    def __init__(self,
                 column,
                 values,
                 prefix,
                 inverted=False):

        self.column = column
        self.values = values
        self.prefix = prefix
        self.inverted = inverted

    def copy(self, **kwargs):
        return InClause(**{'column': self.column,
                           'values': self.values,
                           'prefix': self.prefix,
                           'inverted': self.inverted,
                           **kwargs})

    def build_params(self):
        return {f'{self.prefix}_{i}': v for i, v in enumerate(self.values)}

    def __invert__(self):
        return self.copy(inverted=not self.inverted)


class CombinedClause(Clause):

    def __init__(self,
                 op,
                 clauses):

        assert len(clauses) >= 2
        self.op = op
        self.clauses = clauses

    def copy(self, **kwargs):
        return CombinedClause(**{'op': self.op,
                                 'clauses': self.clauses,
                                 **kwargs})


class NegatedClause(Clause):

    def __init__(self, clause):
        self.clause = clause


class JoinClause:

    def __init__(self,
                 table,
                 clause):

        self.table = table
        self.clause = clause

    def copy(self, **kwargs):
        return JoinClause(**{'table': self.table,
                             'clause': self.clause,
                             **kwargs})

    def __and__(self, clause):
        assert self.clause is not None

        return self.copy(clause=self.clause.and_(clause))

    def __or__(self, clause):
        assert self.clause is not None

        return self.copy(clause=self.clause.or_(clause))


class Join:

    def __init__(self,
                 join_type,
                 table,
                 clause):

        self.join_type = join_type
        self.table = table
        self.clause = clause


class Select:

    def __init__(self,
                 *select_columns,
                 from_tables=None,
                 joins=None,
                 where_clause=None,
                 order_by_columns=None):

        self.select_columns = select_columns
        self.from_tables = from_tables
        self.joins = joins
        self.where_clause = where_clause
        self.order_by_columns = order_by_columns

    def copy(self, *select_columns, **kwargs):
        if not select_columns:
            select_columns = self.select_columns
        return Select(*select_columns,
                      **{'from_tables': self.from_tables,
                         'joins': self.joins,
                         'where_clause': self.where_clause,
                         'order_by_columns': self.order_by_columns,
                         **kwargs})

    def from_table(self, *tables):
        from_tables = [] if self.from_tables is None else self.from_tables
        from_tables = [*from_tables, *tables]

        return self.copy(from_tables=from_tables)

    def inner_join(self, join_clause):
        join = Join(JoinTypes.inner, join_clause.table, join_clause.clause)
        joins = [join] if self.joins is None else [*self.joins, join]

        return self.copy(joins=joins)

    def outer_join(self, join_clause):
        join = Join(JoinTypes.outer, join_clause.table, join_clause.clause)
        joins = [join] if self.joins is None else [*self.joins, join]

        return self.copy(joins=joins)

    def where(self, clause):
        if self.where_clause is not None:
            clause = self.where_clause & clause

        return self.copy(where_clause=clause)

    def order_by(self, *columns):
        order_by_columns = [] if self.order_by_columns is None else self.order_by_columns
        order_by_columns = [*order_by_columns, *columns]

        return self.copy(order_by_columns=order_by_columns)

    def to_sql(self):

        def format_column(c):
            if isinstance(c, WildcardType):
                return '*'

            elif isinstance(c, TableWildcard):
                return f'`{c.table.aliased_name()}`.*'

            elif isinstance(c, BasicColumn):
                if c.alias is not None:
                    return f'`{c.table.aliased_name()}`.`{c.name}` AS `{c.alias}`'
                else:
                    return f'`{c.table.aliased_name()}`.`{c.name}`'

            else:
                raise NotImplementedError

        def format_table(t):
            if t.alias is not None:
                return f'`{t.name}` `{t.alias}`'

            else:
                return f'`{t.name}`'

        def format_value(v):
            if isinstance(v, ColumnAlias):
                return f'`{v.alias}`'

            elif isinstance(v, BasicColumn):
                if v.alias is not None:
                    return f'`{v.alias}`'
                else:
                    return f'`{v.table.aliased_name()}`.`{v.name}`'

            elif isinstance(v, Param):
                return f'%({v.name})s'

            else:
                raise NotImplementedError

        def format_clause(c, nested=False):
            if isinstance(c, BasicClause):
                left_stmt = format_value(c.left)
                right_stmt = format_value(c.right)
                stmt = f'{left_stmt} {c.op.value} {right_stmt}'

            elif isinstance(c, InClause):
                column_stmt = format_value(c.column)
                op_stmt = 'NOT IN' if c.inverted else 'IN'
                values_stmt = ', '.join(f'%({c.prefix}_{i})s'
                                        for i in range(len(c.values)))
                stmt = f'{column_stmt} {op_stmt} ({values_stmt})'

            elif isinstance(c, CombinedClause):
                sub_clauses = [format_clause(sc, nested=True)
                               for sc in c.clauses]
                stmt = f' {c.op.value} '.join(sub_clauses)
                if nested:
                    stmt = f'({stmt})'

            elif isinstance(c, NegatedClause):
                stmt = format_clause(c.clause, nested=True)
                stmt = f'NOT {stmt}'

            else:
                raise NotImplementedError

            return stmt

        def format_join(j):
            table_stmt = format_table(j.table)
            clause_stmt = format_clause(j.clause)
            return f'{j.join_type.value} {table_stmt} ON {clause_stmt}'

        assert self.from_tables

        columns_stmt = ', '.join(format_column(c) for c in self.select_columns)
        tables_stmt = ', '.join(format_table(t) for t in self.from_tables)
        sql = f'SELECT {columns_stmt} FROM {tables_stmt}'

        if self.joins:
            join_stmt = ' '.join(format_join(j) for j in self.joins)
            sql += f' {join_stmt}'

        if self.where_clause:
            where_stmt = format_clause(self.where_clause)
            sql += f' WHERE {where_stmt}'

        if self.order_by_columns:
            # NOTE: Strictly not values (will never be Params), but
            #       format_value() none the less provides the correct format.
            order_by_stmt = ','.join(format_value(c)
                                     for c in self.order_by_columns)
            sql += f' ORDER BY {order_by_stmt}'

        return sql + ';'


class Insert:

    def __init__(self,
                 into_table,
                 into_columns=None):

        self.into_table = into_table
        self.into_columns = into_columns

    def copy(self, into_table=None, **kwargs):
        if not into_table:
            into_table = self.into_table
        return Insert(into_table,
                      **{'into_columns': self.into_columns,
                         **kwargs})

    def columns(self, *columns):
        into_columns = [] if self.into_columns is None else self.into_columns
        into_columns = [*into_columns, *columns]

        return self.copy(into_columns=into_columns)

    def to_sql(self):

        def format_table(t):
            # NOTE: Aliases aren't used in INSERT stmts
            return f'`{t.name}`'

        def format_column(c):
            # NOTE: Table names, aliases, and wildcards aren't used in INSERT stmts
            if isinstance(c, BasicColumn):
                assert c.table == self.into_table
                return f'`{c.name}`'

            else:
                raise NotImplementedError

        def format_value(c):
            # Each column has a corresponding value parameter
            if isinstance(c, BasicColumn):
                assert c.table == self.into_table
                return f'%({c.name})s'

            else:
                raise NotImplementedError

        assert self.into_columns

        table_stmt = format_table(self.into_table)
        columns_stmt = ', '.join(format_column(c) for c in self.into_columns)
        values_stmt = ', '.join(format_value(c) for c in self.into_columns)
        sql = f'INSERT INTO {table_stmt} ({columns_stmt}) VALUES ({values_stmt});'

        return sql


# For convenience/clarity
InsertInto = Insert
