from copy import deepcopy
from typing import Dict, List, Literal
from json import dumps
from pymysql import connect  # 代码提示
from aiomysql import connect as async_connect  # 代码提示
from pymysql.cursors import DictCursor
from aiomysql.cursors import DictCursor as async_DictCursor


class TRUE:
    def __bool__(self): return True

class FALSE:
    def __bool__(self): return False

uniset = TRUE()
empset = FALSE()
undefined = FALSE()

class ORMIndexError(IndexError):
    def __repr__(self):
        return 'ORMIndexError'

def dump_data(data): return dumps(data, ensure_ascii=False)


class ORM():
    def mkconn(self):
        '''
        请在子类中覆盖此方法
        '''
        return connect(
            host = 'localhost',
            port = 3306,
            user = 'root',
            password = '123456789'
        )
    
    async def amkconn(self):
        '''
        请在子类中覆盖此方法
        '''
        return await async_connect(
            host = 'localhost',
            port = 3306,
            user = 'root',
            password = '123456789'
        )
    
    def get_conn(self, db_name: str=''):
        class core():
            # 同步
            def __enter__(mSelf) -> List[connect|DictCursor]:
                conn = self.mkconn()
                cursor = conn.cursor(cursor=DictCursor)
                if db_name: cursor.execute(f'use {db_name}')
                return conn, cursor
            def __exit__(mSelf, errType, errValue, traceback):
                ...
            # 异步
            async def __aenter__(mSelf) -> List[connect|async_DictCursor]:  # async_connect是个函数而非类, 因此用connect代替代码提示
                conn = await self.amkconn()
                cursor = await conn.cursor(async_DictCursor)
                if db_name: await cursor.execute(f'use {db_name}')
                return conn, cursor
            async def __aexit__(mSelf, errType, errValue, traceback):
                ...
        return core()
    
    def get_db_names(self):
        ignore = ('mysql', 'information_schema', 'performance_schema', 'sys')
        with self.get_conn() as (conn, cursor):
            cursor.execute("show databases")  # 非本地操作, 需要连接到数据库
            dbs = [x['Database'] for x in cursor.fetchall()]
            return [x for x in dbs if x not in ignore]
    
    async def aget_db_names(self):
        ignore = ('mysql', 'information_schema', 'performance_schema', 'sys')
        async with self.get_conn() as (conn, cursor):
            await cursor.execute("show databases")  # 非本地操作, 需要连接到数据库
            dbs = [x['Database'] for x in await cursor.fetchall()]
            return [x for x in dbs if x not in ignore]
    
    def len(self): return len(self.get_db_names())
    
    async def alen(self): return len(await self.aget_db_names())

    def get_dbs(self): return [DB(parent=self, db_name=x) for x in self.get_db_names()]
    
    async def aget_dbs(self): return [DB(parent=self, db_name=x) for x in await self.aget_db_names()]

    def __iter__(self):
        for x in self.get_db_names():
            yield DB(parent=self, db_name=x)

    async def __aiter__(self):
        for x in await self.aget_db_names():
            yield DB(parent=self, db_name=x)
    
    def __getitem__(self, db_name: str|tuple):
        if type(db_name) is str:
            return DB(parent=self, db_name=db_name)
        else:
            assert type(db_name) is tuple
            return [DB(parent=self, db_name=x) for x in db_name]


class DB():

    def __init__(self, parent: ORM, db_name: str):
        self.parent = parent
        self.db_name = db_name

    def __repr__(self):
        return f"skk.mysql.DB:<{self.db_name}>"
    
    __str__ = __repr__

    def get_sheet_names(self):
        with self.parent.get_conn() as (conn, cursor):
            sql = f'select table_name as TName from information_schema.tables where table_schema = "{self.db_name}"'
            cursor.execute(sql)
            return [x['TName'] for x in list(cursor.fetchall())]
    
    async def aget_sheet_names(self):
        async with self.parent.get_conn() as (conn, cursor):
            sql = f'select table_name as TName from information_schema.tables where table_schema = "{self.db_name}"'
            await cursor.execute(sql)
            return [x['TName'] for x in list(await cursor.fetchall())]
        
    def len(self): return len(self.get_sheet_names())
    
    async def alen(self): return len(await self.aget_sheet_names())

    def get_sheets(self): return [Sheet(parent=self, sheet_name=x) for x in self.get_sheet_names()]
    
    async def aget_sheets(self): return [Sheet(parent=self, sheet_name=x) for x in await self.aget_sheet_names()]

    def __getitem__(self, sheet_name: str|tuple):
        if type(sheet_name) is str:
            return Sheet(parent=self, sheet_name=sheet_name)
        else:
            assert type(sheet_name) is tuple
            return [Sheet(parent=self, sheet_name=x) for x in sheet_name]

    def __iter__(self):
        for x in self.get_sheet_names():
            yield Sheet(parent=self, sheet_name=x)

    async def __aiter__(self):
        for x in await self.aget_sheet_names():
            yield Sheet(parent=self, sheet_name=x)


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
        return f"skk.mysql.Sheet<{self.parent.db_name}.{self.sheet_name}>"
    
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

    def execute(self, sql:str, data=None, commit=True):
        with self.parent.parent.get_conn(self.parent.db_name) as (conn, cursor):
            try:
                cursor.execute(sql, data)
                r = list(cursor.fetchall())
                if commit: conn.commit()
                return r, cursor
            except:
                conn.rollback()
                raise

    async def aexecute(self, sql:str, data=None, commit=True):
        async with self.parent.parent.get_conn(self.parent.db_name) as (conn, cursor):
            try:
                await cursor.execute(sql, data)
                r = list(await cursor.fetchall())
                if commit: await conn.commit()
                return r, cursor
            except:
                await conn.rollback()
                raise
    
    def executemany(self, sql:str, data):
        with self.parent.parent.get_conn(self.parent.db_name) as (conn, cursor):
            try:
                cursor.executemany(sql, data)
                r = list(cursor.fetchall())
                conn.commit()
                return r, cursor
            except:
                conn.rollback()
                raise

    async def aexecutemany(self, sql:str, data):
        async with self.parent.parent.get_conn(self.parent.db_name) as (conn, cursor):
            try:
                await cursor.executemany(sql, data)
                r = list(await cursor.fetchall())
                await conn.commit()
                return r, cursor
            except:
                await conn.rollback()
                raise
    
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
    
    def len(self):
        rdata, cursor = self.execute(f"select count(1) as total from {self.sheet_name}{self._parse_where()}", commit=False)
        return rdata[0]['total']

    async def alen(self):
        rdata, cursor = await self.aexecute(f"select count(1) as total from {self.sheet_name}{self._parse_where()}", commit=False)
        return rdata[0]['total']

    def insert(self, *data: dict) -> DictCursor:
        if len(data) == 1:
            data = data[0]
            cols = [f"{x}" for x in data]
            sql = f"insert into {self.sheet_name}({', '.join(cols)}) values ({', '.join(('%s',)*len(cols))})"
            rdata, cursor = self.execute(sql, tuple(data.values()))
            return cursor  # cursor.rowcount, cursor.lastrowid
        else:
            cols = set()
            for x in data: cols |= set(x)
            cols = [f"{x}" for x in cols]
            sql = f"insert into {self.sheet_name}({', '.join(cols)}) values ({', '.join(('%s',)*len(cols))})"
            data = tuple(tuple(x.get(k) for k in cols) for x in data)
            r, cursor = self.executemany(sql, data)
            return cursor

    async def ainsert(self, *data: dict) -> DictCursor:
        if len(data) == 1:
            data = data[0]
            cols = [f"{x}" for x in data]
            sql = f"insert into {self.sheet_name}({', '.join(cols)}) values ({', '.join(('%s',)*len(cols))})"
            rdata, cursor = await self.aexecute(sql, tuple(data.values()))
            return cursor  # cursor.rowcount, cursor.lastrowid
        else:
            cols = set()
            for x in data: cols |= set(x)
            cols = [f"{x}" for x in cols]
            sql = f"insert into {self.sheet_name}({', '.join(cols)}) values ({', '.join(('%s',)*len(cols))})"
            data = tuple(tuple(x.get(k) for k in cols) for x in data)
            r, cursor = await self.aexecutemany(sql, data)
            return cursor
    
    def select(self):
        key = self._parse_slice()
        if type(key) is int:
            index = key
            if index < 0: index = self.len() + index + 1  # R索引
            if index < 1: raise ORMIndexError(f"index({key}) out of range")
            skip = index - 1
            parseLimit = f" limit {skip}, 1"
            sql = f"select {self._parse_columns()} from {self.sheet_name}{self._parse_where()}{self._parse_order()}{parseLimit}"
            r, cursor = self.execute(sql, commit=False)
            if r:
                return r[0]
            else:
                raise ORMIndexError(f"index({key}) out of range")  # 没有的话引发ORMIndexError错误. 已被self.update和self.delete调用
        else:
            # 没有的话返回空列表, 但不要报错. 已被self.update和self.delete调用
            L, R, S = key[0], key[1], key[2] or 1
            tL, tR, tS = type(L), type(R), type(S)
            assert {tL, tR, tS} <= {int, type(None)}
            assert 0 not in (L, R)
            assert S > 0
            lenSheet = float('inf')
            if '-' in f"{L}{R}":  # -是负号
                lenSheet = self.len()
                if '-' in str(L): L = lenSheet + L + 1  # R索引
                if '-' in str(R): R = lenSheet + R + 1  # R索引
            sliceSort = True  # 正序
            if tL is tR is int and R < L:
                L, R = R, L
                sliceSort = False  # 逆序
            skip = max(1, L or 1) - 1  # 把L转化成skip
            if R is None: R = float('inf')
            size = R - skip
            if skip >= lenSheet: return []
            if size > 0:
                if size == float('inf'):
                    parseLimit = f" limit {skip}, 9999999999999"
                else:
                    parseLimit = f" limit {skip}, {size}"
                sql = f"select {self._parse_columns()} from {self.sheet_name}{self._parse_where()}{self._parse_order()}{parseLimit}"
                r, cursor = self.execute(sql, commit=False)
                if sliceSort:
                    return r if S == 1 else r[::S]
                else:
                    return r[::-S]
            else:
                return []

    async def aselect(self):
        key = self._parse_slice()
        if isinstance(key, int):
            index = key
            if index < 0: index = await self.alen() + index + 1  # R索引
            if index < 1: raise ORMIndexError(f"index({key}) out of range")
            skip = index - 1
            parseLimit = f" limit {skip}, 1"
            sql = f"select {self._parse_columns()} from {self.sheet_name}{self._parse_where()}{self._parse_order()}{parseLimit}"
            r, cursor = await self.aexecute(sql, commit=False)
            if r:
                return r[0]
            else:
                raise ORMIndexError(f"index({key}) out of range")  # 没有的话引发ORMIndexError错误. 已被self.update和self.delete调用
        else:
            # 没有的话返回空列表, 但不要报错. 已被self.update和self.delete调用
            L, R, S = key[0], key[1], key[2] or 1
            tL, tR, tS = type(L), type(R), type(S)
            assert {tL, tR, tS} <= {int, type(None)}
            assert 0 not in (L, R)
            assert S > 0
            lenSheet = float('inf')
            if '-' in f"{L}{R}":  # -是负号
                lenSheet = await self.alen()
                if '-' in str(L): L = lenSheet + L + 1  # R索引
                if '-' in str(R): R = lenSheet + R + 1  # R索引
            sliceSort = True  # 正序
            if tL is tR is int and R < L:
                L, R = R, L
                sliceSort = False  # 逆序
            skip = max(1, L or 1) - 1  # 把L转化成skip
            if R is None: R = float('inf')
            size = R - skip
            if skip >= lenSheet: return []
            if size > 0:
                if size == float('inf'):
                    parseLimit = f" limit {skip}, 9999999999999"
                else:
                    parseLimit = f" limit {skip}, {size}"
                sql = f"select {self._parse_columns()} from {self.sheet_name}{self._parse_where()}{self._parse_order()}{parseLimit}"
                r, cursor = await self.aexecute(sql, commit=False)
                if sliceSort:
                    if S == 1:
                        return r
                    else:
                        return r[::S]
                else:
                    return r[::-S]
            else:
                return []

    def update(self, data: dict):
        key = self._parse_slice()
        data = ', '.join([f"{k}={v.field}" if isinstance(v,Filter) else f"{k}={dump_data(v)}" for k,v in data.items()])
        # [::]
        if isinstance(key, list):
            L, R, S = key[0], key[1], key[2] or 1
            if S in [None, 1]:
                if (L in [None, 1] and R in [None, -1]) or (L == -1 and R == 1):
                    rdata, cursor = self.execute(f"update {self.sheet_name} set {data}{self._parse_where()}")  # 无须self._parse_order(), 因为更新和删除不需要顺序
                    return cursor
        # [1]且无排序
        if key == 1 and not self._parse_order():
            rdata, cursor = self.execute(f"update {self.sheet_name} set {data}{self._parse_where()} limit 1")
            return cursor
        # 其它情况
        pk = self.get_pk()
        try:
            pks = self[pk][self._condition['slice']].select()
        except ORMIndexError:
            rdata, cursor = self.execute(f"update {self.sheet_name} set {data} where 1 = 2 limit 1")
        else:
            if isinstance(pks, list):
                if pks:
                    pks = [x[pk] for x in pks]
                    rdata, cursor = self.execute(f"update {self.sheet_name} set {data}{mc[pk].isin(*pks)}")
                else:
                    rdata, cursor = self.execute(f"update {self.sheet_name} set {data} where 1 = 2")
            else:
                rdata, cursor = self.execute(f"update {self.sheet_name} set {data}{mc[pk] == pks[pk]} limit 1")
        return cursor

    async def aupdate(self, data: dict):
        key = self._parse_slice()
        data = ', '.join([f"{k}={v.field}" if isinstance(v,Filter) else f"{k}={dump_data(v)}" for k,v in data.items()])
        # [::]
        if isinstance(key, list):
            L, R, S = key[0], key[1], key[2] or 1
            if S in [None, 1]:
                if (L in [None, 1] and R in [None, -1]) or (L == -1 and R == 1):
                    rdata, cursor = await self.aexecute(f"update {self.sheet_name} set {data}{self._parse_where()}")
                    return cursor
        # [1]且无排序
        if key == 1 and not self._parse_order():
            rdata, cursor = await self.aexecute(f"update {self.sheet_name} set {data}{self._parse_where()} limit 1")
            return cursor
        # 其它情况
        pk = await self.aget_pk()
        try:
            pks = await self[pk][self._condition['slice']].aselect()
        except ORMIndexError:
            rdata, cursor = await self.aexecute(f"update {self.sheet_name} set {data} where 1 = 2 limit 1")
        else:
            if isinstance(pks, list):
                if pks:
                    pks = [x[pk] for x in pks]
                    rdata, cursor = await self.aexecute(f"update {self.sheet_name} set {data}{mc[pk].isin(*pks)}")
                else:
                    rdata, cursor = await self.aexecute(f"update {self.sheet_name} set {data} where 1 = 2")
            else:
                rdata, cursor = await self.aexecute(f"update {self.sheet_name} set {data}{mc[pk] == pks[pk]} limit 1")
        return cursor

    def delete(self):
        key = self._parse_slice()
        # [::]
        if isinstance(key, list):
            L, R, S = key[0], key[1], key[2] or 1
            if S in [None, 1]:
                if (L in [None, 1] and R in [None, -1]) or (L == -1 and R == 1):
                    rdata, cursor = self.execute(f"delete from {self.sheet_name}{self._parse_where()}")
                    return cursor
        # [1]且无排序
        if key == 1 and not self._parse_order():
            rdata, cursor = self.execute(f"delete from {self.sheet_name}{self._parse_where()} limit 1")
            return cursor
        # 其它索引
        pk = self.get_pk()
        try:
            pks = self[pk][self._condition['slice']].select()
        except ORMIndexError:
            rdata, cursor = self.execute(f"delete from {self.sheet_name} where 1 = 2 limit 1")
        else:
            if isinstance(pks, list):
                if pks:
                    pks = [x[pk] for x in pks]
                    rdata, cursor = self.execute(f"delete from {self.sheet_name}{mc[pk].isin(*pks)}")
                else:
                    rdata, cursor = self.execute(f"delete from {self.sheet_name} where 1 = 2")
            else:
                rdata, cursor = self.execute(f"delete from {self.sheet_name}{mc[pk] == pks[pk]} limit 1")
        return cursor
    
    async def adelete(self):
        key = self._parse_slice()
        # [::]
        if isinstance(key, list):
            L, R, S = key[0], key[1], key[2] or 1
            if S in [None, 1]:
                if (L in [None, 1] and R in [None, -1]) or (L == -1 and R == 1):
                    rdata, cursor = await self.aexecute(f"delete from {self.sheet_name}{self._parse_where()}")
                    return cursor
        # [1]且无排序
        if key == 1 and not self._parse_order():
            rdata, cursor = await self.aexecute(f"delete from {self.sheet_name}{self._parse_where()} limit 1")
            return cursor
        # 其它索引
        pk = await self.aget_pk()
        try:
            pks = await self[pk][self._condition['slice']].aselect()
        except ORMIndexError:
            rdata, cursor = await self.aexecute(f"delete from {self.sheet_name} where 1 = 2 limit 1")
        else:
            if isinstance(pks, list):
                if pks:
                    pks = [x[pk] for x in pks]
                    rdata, cursor = await self.aexecute(f"delete from {self.sheet_name}{mc[pk].isin(*pks)}")
                else:
                    rdata, cursor = await self.aexecute(f"delete from {self.sheet_name} where 1 = 2")
            else:
                rdata, cursor = await self.aexecute(f"delete from {self.sheet_name}{mc[pk] == pks[pk]} limit 1")
        return cursor

    def get_pk(self):
        if not self._pk:
            sql = f"select column_name as co_name from information_schema.columns where table_schema = '{self.parent.db_name}' and table_name = '{self.sheet_name}' and column_key='PRI' "
            rdata, cursor = self.execute(sql, commit=False)
            assert len(data := rdata[0]) == 1
            _pk = list(data.values())[0]
            object.__setattr__(self, '_pk', rdata[0]['co_name'])
        return self._pk
    
    async def aget_pk(self):
        if not self._pk:
            sql = f"select column_name as co_name from information_schema.columns where table_schema = '{self.parent.db_name}' and table_name = '{self.sheet_name}' and column_key='PRI' "
            rdata, cursor = await self.aexecute(sql, commit=False)
            assert len(data := rdata[0]) == 1
            _pk = list(data.values())[0]
            object.__setattr__(self, '_pk', rdata[0]['co_name'])
        return self._pk
    
    def get_columns(self, comment=True, type=True):
        need = ['column_name as name']
        if comment: need.append('column_comment as comment')
        if type: need.append('column_type as type')
        need = ', '.join(need)
        sql = f"select {need} from information_schema.columns where table_schema = '{self.parent.db_name}' and table_name = '{self.sheet_name}'"
        rdata, cursor = self.execute(sql, commit=False)
        return rdata
    
    async def aget_columns(self, comment=True, type=True):
        need = ['column_name as name']
        if comment: need.append('column_comment as comment')
        if type: need.append('column_type as type')
        need = ', '.join(need)
        sql = f"select {need} from information_schema.columns where table_schema = '{self.parent.db_name}' and table_name = '{self.sheet_name}'"
        rdata, cursor = await self.aexecute(sql, commit=False)
        return rdata

    def apply(self, handler):
        # 添加主键字段
        columns = deepcopy(self._condition['columns'])
        if isinstance(columns, str): columns = [columns]
        for x in columns:
            if x.strip() in ('*', pk := self.get_pk()):
                break
        else:
            columns = tuple(list(columns) + [pk])
        self = self._deepcopy('columns', columns)
        # 从数据库提取数据
        lines = self[ self._condition['slice'] ].select()
        if type(lines) is dict:
            lines = [lines]
            r_type = 'dict'
        else:
            r_type = 'list'
        # 处理数据
        records = {}
        for line in lines:
            key = line[pk]
            line2 = line.copy()
            handler(line)
            for k, v in line.items():
                if v != line2.get(k, undefined):
                    records.setdefault(k, {})[key] = v
        if r_type == 'dict':
            lines = lines[0]
        # 更新到数据库
        if records:
            blocks = []
            for field, kvs in records.items():
                s = [f"{field} = ", '    case']
                for k, v in kvs.items():
                    s.append(f"        when {pk} = {dump_data(k)} then {dump_data(v)}")
                s.append(f"else {field}")
                s.append('end')
                blocks.append('\n'.join(s))
            blocks = ' ,\n'.join(blocks)
            sql = f"update {self.sheet_name} set \n{blocks}"
            self.execute(sql=sql)
            return dict(data=lines)
        else:
            return dict(data=lines)

    async def aapply(self, handler):
        # 添加主键字段
        columns = deepcopy(self._condition['columns'])
        if isinstance(columns, str): columns = [columns]
        for x in columns:
            if x.strip() in ('*', pk := await self.aget_pk()):
                break
        else:
            columns = tuple(list(columns) + [pk])
        self = self._deepcopy('columns', columns)
        # 从数据库提取数据
        lines = await self[ self._condition['slice'] ].aselect()
        if type(lines) is dict:
            lines = [lines]
            r_type = 'dict'
        else:
            r_type = 'list'
        # 处理数据
        records = {}
        for line in lines:
            key = line[pk]
            line2 = line.copy()
            handler(line)
            for k, v in line.items():
                if v != line2.get(k, undefined):
                    records.setdefault(k, {})[key] = v
        if r_type == 'dict':
            lines = lines[0]
        # 更新到数据库
        if records:
            blocks = []
            for field, kvs in records.items():
                s = [f"{field} = ", '    case']
                for k, v in kvs.items():
                    s.append(f"        when {pk} = {dump_data(k)} then {dump_data(v)}")
                s.append(f"else {field}")
                s.append('end')
                blocks.append('\n'.join(s))
            blocks = ' ,\n'.join(blocks)
            sql = f"update {self.sheet_name} set \n{blocks}"
            await self.aexecute(sql=sql)
            return dict(data=lines)
        else:
            return dict(data=lines)
        
    def update_by_pk(self, data:dict):
        pk = self.get_pk()
        records = {}
        for key, line in data.items():
            for field, value in line.items():
                records.setdefault(field, {})[key] = value
        blocks = []
        for field, kvs in records.items():
            s = [f"{field} = ", '    case']
            for k, v in kvs.items():
                s.append(f"        when {pk} = {dump_data(k)} then {dump_data(v)}")
            s.append(f"else {field}")
            s.append('end')
            blocks.append('\n'.join(s))
        blocks = ' ,\n'.join(blocks)
        sql = f"update {self.sheet_name} set \n{blocks}"
        r, cursor = self.execute(sql=sql)
        return cursor
    
    async def aupdate_by_pk(self, data:dict):
        pk = await self.aget_pk()
        records = {}
        for key, line in data.items():
            for field, value in line.items():
                records.setdefault(field, {})[key] = value
        blocks = []
        for field, kvs in records.items():
            s = [f"{field} = ", '    case']
            for k, v in kvs.items():
                s.append(f"        when {pk} = {dump_data(k)} then {dump_data(v)}")
            s.append(f"else {field}")
            s.append('end')
            blocks.append('\n'.join(s))
        blocks = ' ,\n'.join(blocks)
        sql = f"update {self.sheet_name} set \n{blocks}"
        r, cursor = await self.aexecute(sql=sql)
        return cursor
    
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
    def re(self, pattern): return Factory(f"{self.field} regexp {dump_data(pattern or '')}")

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

def _builtFunc(cls, func):
    def builtFunc(*fields):
        return Filter(field=f"{func}({', '.join(fields)})")
    return builtFunc

class MfType(type):
    __getattribute__ = _builtFunc

class mf(object, metaclass=MfType):
    # 函数名提示
    year = day = month = week = hour = None
    md5 = None
    round = ceil = floor = abs = least = greatest = sign = pi = None
    curdate = curtime = utcdata = utctime = now = localtime = None