from copy import deepcopy
from typing import Dict, Literal
from json import dumps

import asyncpg
from asyncpg.connection import Connection


class TRUE:
    def __bool__(self): return True

class FALSE:
    def __bool__(self): return False

uniset = TRUE()
empset = FALSE()
undefined = FALSE()

class RowIndexError(IndexError):
    def __repr__(self):
        return 'RowIndexError'

def dump_data(data):
    if type(data) is str:
        return f"'{data}'"
    else:
        return dumps(data, ensure_ascii=False)

class DB():    
    async def mkconn(self):
        ''' 请在子类中覆盖此方法 '''
        return await asyncpg.connect(
            user = 'postgres',
            password = '123456789',
            database = 'test',
            host = 'localhost',
            port = 5432
        )
    
    def get_conn(self):
        class core():
            async def __aenter__(mSelf) -> Connection:
                self.conn = await self.mkconn()
                return self.conn
            async def __aexit__(mSelf, errType, errValue, traceback):
                await self.conn.close()
        return core()
    
    async def get_sheet_names(self):
        async with self.get_conn() as conn:
            tables = await conn.fetch("select tablename from pg_catalog.pg_tables where schemaname = 'public'")
            table_names = [table['tablename'] for table in tables]
            return table_names
    
    async def len(self): return len(await self.get_sheet_names())

    async def __aiter__(self):  # sheets = [x async for x in self]
        for x in await self.get_sheet_names():
            yield Sheet(parent=self, sheet_name=x)
    
    def __getitem__(self, sheet_name: str|tuple):
        if type(sheet_name) is str:
            return Sheet(parent=self, sheet_name=sheet_name)
        else:
            assert type(sheet_name) is tuple
            return [Sheet(parent=self, sheet_name=x) for x in sheet_name]

    def __repr__(self):
        return f"skk.postgre.DB{object.__repr__(self)}"
    
    __str__ = __repr__


class Sheet():
    
    _pk = ''

    def __init__(self, parent: DB, sheet_name: str, _condition: dict=None):
        self.parent = parent
        self.sheet_name = sheet_name
        self._condition: Dict[Literal['where', 'columns', 'order', 'slice'], Factory|str|tuple|dict|list|None] = _condition or {
            'where': Factory(uniset),
            'columns': '*',  # str|tuple|'*', '*'表示不限定字段
            'order': {},  # {A:True, B:False, C:1, D:0}, bool(value) == True --> 升序, bool(value) == False --> 降序
            'slice': slice(None, None, None)
        }

    def __repr__(self):
        return f"skk.postgre.Sheet{object.__repr__(self)}"
    
    __str__ = __repr__

    def _deepcopy(self, condition_key: str, value):
        return Sheet(
            parent = self.parent,
            sheet_name = self.sheet_name,
            _condition = {
                'where': self._condition['where'],
                'columns': deepcopy(self._condition['columns']),
                'order': deepcopy(self._condition['order']),
                'slice': self._condition['slice'],
                condition_key: value,
            }
        )
    
    def __getitem__(self, key):
        if type(key) in (int, slice): return self._deepcopy('slice', key)
        if isinstance(key, str|tuple): return self._deepcopy('columns', key)  # 输入多个字符串, 用逗号隔开, Python会自动打包成tuple
        if isinstance(key, Factory): return self._deepcopy('where', self._condition['where'] & key)
        raise TypeError(key)

    def order(self, **rule): return self._deepcopy('order', rule)

    async def execute(self, sql:str, data=None, commit=False):
        async with self.parent.get_conn() as conn:
            data = data or []
            if sql.strip().lower().startswith("select"):
                rows = await conn.fetch(sql, *data)
                return [dict(row) for row in rows]
            elif commit:
                async with conn.transaction():  # 开启事务
                    return await conn.execute(sql, *data)
            else:
                return await conn.execute(sql, *data)
    
    def _parse_order(self):
        if order := self._condition['order']:
            return ' order by ' + ', '.join([k if v else f"{k} desc" for k,v in order.items()])
        return ''
    
    def _parse_columns(self):
        if type(columns := self._condition['columns']) is str:
            return columns
        return ', '.join(columns)
    
    def _parse_where(self): return str(self._condition['where'])
    
    def _parse_slice(self):
        key: int|slice = self._condition['slice']
        if type(key) is int:
            return key
        else:
            return [key.start, key.stop, key.step]

    async def insert(self, *rows: dict):
        cols = set()
        for x in rows: cols |= set(x)
        cols_sql = ', '.join(f'"{x}"' for x in cols)
        values_sql = ', '.join(f'${i+1}' for i, x in enumerate(cols))
        sql = f'insert into "{self.sheet_name}" ({cols_sql}) values ({values_sql})'
        data = [tuple(x.get(k) for k in cols) for x in rows]
        async with self.parent.get_conn() as conn:
            return await conn.executemany(sql, data)
        
    async def len(self):
        async with self.parent.get_conn() as conn:
            sql = f"select count(*) from {self.sheet_name}{self._parse_where()}"
            return await conn.fetchval(sql)
    
    async def select(self):
        key = self._parse_slice()
        if isinstance(key, int):
            assert key >= 1
            parse_offset = f" offset {key - 1} limit 1"
            sql = f"select {self._parse_columns()} from {self.sheet_name}{self._parse_where()}{self._parse_order()}{parse_offset}"
            r = await self.execute(sql, commit=False)
            if r:
                return r[0]
            else:
                raise RowIndexError(f"index({key}) out of range")  # 没有的话引发RowIndexError错误. 已被self.update和self.delete调用
        else:
            L, R, S = key[0], key[1], key[2] or 1
            assert {type(L), type(R), type(S)} <= {int, type(None)} and '-' not in f"{L}{R}{S}"  # -是负号
            sliceSort = True  # 正序
            if type(L) is type(R) is int and R < L:
                L, R = R, L
                sliceSort = False  # 逆序
            offset = max(1, L or 1) - 1  # 把L转化成offset
            if R is None: R = float('inf')
            size = R - offset
            if size > 0:
                offset = f" offset {offset}" if offset else ''
                if size == float('inf'):
                    parse_offset = f"{offset}"
                else:
                    parse_offset = f"{offset} limit {size}"
                sql = f"select {self._parse_columns()} from {self.sheet_name}{self._parse_where()}{self._parse_order()}{parse_offset}"
                r = await self.execute(sql, commit=False)
                if sliceSort:
                    if S == 1:
                        return r
                    else:
                        return r[::S]
                else:
                    return r[::-S]
            else:
                return []

    async def update(self, data: dict):
        key = self._parse_slice()
        data = ', '.join([f"{k}={v.field}" if isinstance(v,Filter) else f"{k}={dump_data(v)}" for k,v in data.items()])
        # [::]
        if isinstance(key, list):
            L, R, S = key[0], key[1], key[2] or 1
            assert {type(L), type(R), type(S)} <= {int, type(None)} and '-' not in f"{L}{R}{S}"  # -是负号
            if S == 1:
                if (L, R) in [(None, None), (1, None)]:
                    return await self.execute(f"update {self.sheet_name} set {data}{self._parse_where()}")
        # 其它情况
        pk = await self.get_pk()
        try:
            pks = await self[pk][self._condition['slice']].select()
        except RowIndexError:
            return await self.execute(f"update {self.sheet_name} set {data} where 1 = 2")
        else:
            if isinstance(pks, list):
                if pks:
                    pks = [x[pk] for x in pks]
                    return await self.execute(f"update {self.sheet_name} set {data}{mc[pk].isin(*pks)}")
                else:
                    return await self.execute(f"update {self.sheet_name} set {data} where 1 = 2 limit 1")
            else:
                return await self.execute(f"update {self.sheet_name} set {data}{mc[pk] == pks[pk]} limit 1")
    
    async def delete(self):
        key = self._parse_slice()
        # [::]
        if isinstance(key, list):
            L, R, S = key[0], key[1], key[2] or 1
            assert {type(L), type(R), type(S)} <= {int, type(None)} and '-' not in f"{L}{R}{S}"  # -是负号
            if S == 1:
                if (L, R) in [(None, None), (1, None)]:
                    return await self.execute(f"delete from {self.sheet_name}{self._parse_where()}")
        # 其它情况
        pk = await self.get_pk()
        try:
            pks = await self[pk][self._condition['slice']].select()
        except RowIndexError:
            return await self.execute(f"delete from {self.sheet_name} where 1 = 2")
        else:
            if isinstance(pks, list):
                if pks:
                    pks = [x[pk] for x in pks]
                    return await self.execute(f"delete from {self.sheet_name}{mc[pk].isin(*pks)}")
                else:
                    return await self.execute(f"delete from {self.sheet_name} where 1 = 2")
            else:
                return await self.execute(f"delete from {self.sheet_name}{mc[pk] == pks[pk]}")

    async def get_pk(self):
        if not self._pk:
            async with self.parent.get_conn() as conn:
                sql = f"select a.attname as column_name from pg_index i join pg_attribute a on a.attrelid = i.indrelid and a.attnum = any(i.indkey) where i.indrelid = '{self.sheet_name}'::regclass and i.indisprimary limit 1"
                row = await conn.fetchrow(sql)
                _pk = row["column_name"]
                object.__setattr__(self, '_pk', _pk)
        return self._pk
    
    def _select_native(self): return f"select {self._parse_columns()} from {self.sheet_name}{self._parse_where()}{self._parse_order()}"
    def _delete_native(self): return f"delete from {self.sheet_name}{self._parse_where()}"
    def _update_native(self, data:dict={}):
        data = ', '.join([f"{k}={v}" for k,v in data.items()])
        return f"update {self.sheet_name} set {data}{self._parse_where()}"


class Factory:
    
    _variable = True

    def __init__(self, where):
        if where is not empset:
            where = where or uniset
        self.where = where
        self._variable = False

    def __setattr__(self, name, value):
        assert self._variable
        object.__setattr__(self, name, value)

    def __and__(self, obj: 'Factory'):
        a = self.where
        b = obj.where
        if a is uniset: return Factory(b)
        if b is uniset: return Factory(a)
        if a and b: return Factory(f"({a}) and ({b})")
        return Factory(empset)

    def __or__(self, obj: 'Factory'):
        a = self.where
        b = obj.where
        if a is empset: return Factory(b)
        if b is empset: return Factory(a)
        if a is uniset or b is uniset: return Factory(uniset)
        return Factory(f"({a}) or ({b})")

    def __invert__(self):
        w = self.where
        if w is uniset: return Factory(empset)
        if w is empset: return Factory(uniset)
        return Factory(f"not ({w})")

    def __sub__(self, obj): return self & (~ obj)
    
    def __str__(self):
        w = self.where
        if w is uniset: return ''
        if w is empset: return ' where 1 = 2'
        return f" where {w}"


class Filter():

    def __init__(self, field):
        self.field = field

    def __eq__(self, obj):
        if obj is None:
            return Factory(f"{self.field} is null")
        return Factory(f"{self.field} = {dump_data(obj)}")

    def __ne__(self, obj):
        if obj is None:
            return Factory(f"{self.field} is not null")
        return Factory(f"{self.field} != {dump_data(obj)}")

    def __lt__(self, obj): return Factory(f"{self.field} < {dump_data(obj)}")
    def __le__(self, obj): return Factory(f"{self.field} <= {dump_data(obj)}")
    def __gt__(self, obj): return Factory(f"{self.field} > {dump_data(obj)}")
    def __ge__(self, obj): return Factory(f"{self.field} >= {dump_data(obj)}")
    def re(self, pattern, case=True):
        if case:
            return Factory(f"{self.field} ~ {dump_data(pattern or '')}")
        else:
            return Factory(f"{self.field} ~* {dump_data(pattern or '')}")
    
    def isin(self, *lis):
        if not lis: return Factory(empset)
        if len(lis) == 1: return self == lis[0]
        null = False
        type_item = {str:set(), int:set(), float:set()}
        for i, x in enumerate(lis):
            if x is None:
                null = True
            else:
                type_item[type(x)].add(x)
        sumlis = []
        for lis in type_item.values():
            if len(lis) == 1:
                sumlis.append(f"{self.field} = {dump_data(list(lis)[0])}")
            elif len(lis) > 1:
                sumlis.append(f"{self.field} in ({', '.join(dump_data(x) for x in lis)})")
        if null:
            sumlis.append(f"{self.field} is null")
        if len(sumlis) == 1:
            return Factory(sumlis[0])
        else:
            return Factory(' or '.join(f"({x})" for x in sumlis))

    def notin(self, *lis):
        if not lis: return Factory(uniset)
        if len(lis) == 1: return self != lis[0]
        null = False
        type_item = {str:set(), int:set(), float:set()}
        for i, x in enumerate(lis):
            if x is None:
                null = True
            else:
                type_item[type(x)].add(x)
        sumlis = []
        for lis in type_item.values():
            if len(lis) == 1:
                sumlis.append(f"{self.field} != {dump_data(list(lis)[0])}")
            elif len(lis) > 1:
                sumlis.append(f"{self.field} not in ({', '.join(dump_data(x) for x in lis)})")
        if null:
            sumlis.append(f"{self.field} is not null")
            sumlis = sumlis[0] if len(sumlis) == 1 else ' and '.join(f"({x})" for x in sumlis)
        else:
            sumlis = sumlis[0] if len(sumlis) == 1 else ' and '.join(f"({x})" for x in sumlis)
            sumlis = f"({sumlis}) or ({self.field} is null)"
        return Factory(sumlis)


def creat_Filter(cls, field) -> Filter:
    return Filter(field=field)

class McType(type):
    __getattribute__ = creat_Filter
    __getitem__ = creat_Filter

class mc(object, metaclass=McType):
    id = None  # 预设字段提示
