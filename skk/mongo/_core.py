from typing import Dict, Literal
from collections import deque
from copy import deepcopy
from pymongo import MongoClient  # 代码提示
from motor.motor_asyncio import AsyncIOMotorClient as motor_client  # 代码提示


class TRUE:
    def __bool__(self): return True

class FALSE:
    def __bool__(self): return False

uniset = TRUE()
empset = FALSE()
undefined = FALSE()

class Odm_Index_Error(IndexError):
    def __repr__(self):
        return 'Odm_Index_Error'


class ODM():
    
    def __init__(self):
        self._connpool = deque([], maxlen=1)
        self._aconnpool = deque([], maxlen=1)

    def mkconn(self):
        '''
        请在子类中覆盖此方法
        '''
        return MongoClient(host='localhost', port=27017)
    
    async def amkconn(self):  # 面向未来编程。虽然 motor_client 是同步方法，但为了未来的可扩展性，这里将 amkconn 定义为异步函数
        '''
        请在子类中覆盖此方法
        '''
        return motor_client(host='localhost', port=27017)
    
    def get_conn(self):
        class core():
            # 同步
            def __enter__(mSelf) -> MongoClient:
                if self._connpool:
                    mSelf.conn = self._connpool.popleft()
                else:
                    mSelf.conn = self.mkconn()
                return mSelf.conn
            def __exit__(mSelf, errType, errValue, traceback):
                if not errType:
                    self._connpool.append(mSelf.conn)
            # 异步
            async def __aenter__(mSelf) -> MongoClient:
                if self._aconnpool:
                    mSelf.conn = self._aconnpool.popleft()
                else:
                    mSelf.conn = await self.amkconn()
                return mSelf.conn
            async def __aexit__(mSelf, errType, errValue, traceback):
                if not errType:
                    self._aconnpool.append(mSelf.conn)
        return core()
    
    def get_db_names(self):
        ignore = ('admin', 'config', 'local')
        with self.get_conn() as conn:
            return [x for x in conn.list_database_names() if x not in ignore]

    async def aget_db_names(self):
        ignore = ('admin', 'config', 'local')
        async with self.get_conn() as conn:
            return [x for x in await conn.list_database_names() if x not in ignore]
    
    def len(self): return len(self.get_db_names())

    async def alen(self): return len(await self.aget_db_names())

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

    def __init__(self, parent: ODM, db_name: str):
        self.parent = parent
        self.db_name = db_name

    def delete_db(self):
        with self.parent.get_conn() as conn:
            return conn.drop_database(self.db_name)

    async def adelete_db(self, *names):
        async with self.parent.get_conn() as conn:
            return await conn.drop_database(self.db_name)
        
    def __repr__(self):
        return f"skk.mongo.DB:<{self.db_name}>"
    
    __str__ = __repr__

    def get_sheet_names(self):
        with self.parent.get_conn() as conn:
            return conn[self.db_name].list_collection_names()
    
    async def aget_sheet_names(self):
        async with self.parent.get_conn() as conn:
            return await conn[self.db_name].list_collection_names()
    
    def len(self): return len(self.get_sheet_names())

    async def alen(self): return len(await self.aget_sheet_names())

    def __iter__(self):
        for x in self.get_sheet_names():
            yield Sheet(parent=self, sheet_name=x)

    async def __aiter__(self):
        for x in await self.aget_sheet_names():
            yield Sheet(parent=self, sheet_name=x)
    
    def __getitem__(self, sheet_name: str|tuple):
        if type(sheet_name) is str:
            return Sheet(parent=self, sheet_name=sheet_name)
        else:
            assert type(sheet_name) is tuple
            return [Sheet(parent=self, sheet_name=x) for x in sheet_name]


class Sheet():

    def __init__(self, parent: DB, sheet_name: str, _condition: dict=None):
        self.parent = parent
        self.sheet_name = sheet_name
        self._condition: Dict[Literal['where', 'columns', 'order', 'slice'], Factory|str|tuple|dict|list|None] = _condition or {
            'where': Factory(uniset),
            'columns': None,  # str|tuple|None, None表示不限定字段
            'order': {},  # {A:True, B:False, C:1, D:0}, bool(value) == True --> 升序, bool(value) == False --> 降序
            'slice': slice(None, None, None)
        }

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
    
    def order(self, **rule): return self._deepcopy('order', rule)

    def _parse_slice(self):
        key: int|slice = self._condition['slice']
        if type(key) is int:
            return key
        else:
            return [key.start, key.stop, key.step]
    
    def _parse_where(self): return self._condition['where'].ParseWhere()

    def _parse_columns(self):
        columns = self._condition['columns']
        if columns is None: return None
        if isinstance(columns, tuple):
            columns = dict.fromkeys(columns, 1)
        else:
            columns = {columns: 1}
        columns.setdefault('_id', 0)
        return columns
    
    def _parse_order(self):
        return [(k, 1 if v else -1) for k,v in self._condition['order'].items()]
    
    def len(self):
        with self.parent.parent.get_conn() as conn:
            sheet = conn[self.parent.db_name][self.sheet_name]
            return sheet.count_documents(self._parse_where())
    
    async def alen(self):
        async with self.parent.parent.get_conn() as conn:
            sheet = conn[self.parent.db_name][self.sheet_name]
            return await sheet.count_documents(self._parse_where())
    
    def delete_sheet(self):
        with self.parent.parent.get_conn() as conn:
            return conn[self.parent.db_name].drop_collection(self.sheet_name)

    async def adelete_sheet(self):
        async with self.parent.parent.get_conn() as conn:
            return await conn[self.parent.db_name].drop_collection(self.sheet_name)

    def insert(self, *data: dict):
        with self.parent.parent.get_conn() as conn:
            sheet = conn[self.parent.db_name][self.sheet_name]
            if len(data) == 1:
                return sheet.insert_one( data[0] )  # 分配到的 _id 为 str(r)
            else:
                return sheet.insert_many( data )  # r.acknowledged, r.inserted_ids

    def _for_tip(self):
        x: 'motor_client'  # 查看代码提示是否生效

    async def ainsert(self, *data: dict):
        if self._for_tip(): return self.insert( *data )  # 引导 vscode 产生代码提示
        async with self.parent.parent.get_conn() as conn:
            sheet = conn[self.parent.db_name][self.sheet_name]
            if len(data) == 1:
                return await sheet.insert_one( data[0] )  # r.inserted_id
            else:
                return await sheet.insert_many( data )  # r.inserted_ids

    def find(self):
        key = self._parse_slice()
        if type(key) is int:
            index = key
            if index < 0: index = self.len() + index + 1  # R索引
            if index < 1: raise Odm_Index_Error(f"index({key}) out of range")
            skip = index - 1
            with self.parent.parent.get_conn() as conn:
                sheet = conn[self.parent.db_name][self.sheet_name]
                res = sheet.find(self._parse_where(), self._parse_columns())
                if sort:= self._parse_order():
                    res = res.sort(sort)
                if skip: res = res.skip(skip)
                if r := list(res.limit(1)):
                    return r[0]
                else:
                    raise Odm_Index_Error(f"index({key}) out of range")  # 没有的话引发Odm_Index_Error错误. 已被self.update和self.delete调用
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
                with self.parent.parent.get_conn() as conn:
                    sheet = conn[self.parent.db_name][self.sheet_name]
                    res = sheet.find(self._parse_where(), self._parse_columns())
                    if sort:= self._parse_order():
                        res = res.sort(sort)
                    if skip: res = res.skip(skip)
                    if type(size) is int: res = res.limit(size)
                    r = list(res)
                if sliceSort:
                    return r if S == 1 else r[::S]
                else:
                    return r[::-S]
            else:
                return []
    
    async def aget(self, default=None):
        try:
            return await self.afind()
        except Odm_Index_Error:
            return default

    async def afind(self):
        if self._for_tip(): return self.find()  # 引导 vscode 产生代码提示
        key = self._parse_slice()
        if type(key) is int:
            index = key
            if index < 0: index = await self.alen() + index + 1
            if index < 1: raise Odm_Index_Error(f"index({key}) out of range")
            skip = index - 1
            async with self.parent.parent.get_conn() as conn:
                sheet = conn[self.parent.db_name][self.sheet_name]
                res = sheet.find(self._parse_where(), self._parse_columns())
                if sort:= self._parse_order():
                    res = res.sort(sort)
                if skip: res = res.skip(skip)
                if r := await res.limit(1).to_list(1):
                    return r[0]
                else:
                    raise Odm_Index_Error(f"index({key}) out of range")
        else:
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
                async with self.parent.parent.get_conn() as conn:
                    sheet = conn[self.parent.db_name][self.sheet_name]
                    res = sheet.find(self._parse_where(), self._parse_columns())
                    if sort:= self._parse_order():
                        res = res.sort(sort)
                    if skip: res = res.skip(skip)
                    if type(size) is int: res = res.limit(size)
                    r = [x async for x in res]
                if sliceSort:
                    return r if S == 1 else r[::S]
                else:
                    return r[::-S]
            else:
                return []

    def update(self, data: dict=None, setOnInsert: dict=None):
        data_ = {'$set':{}}
        for k, v in ( data or {} ).items():
            if isinstance(v, mo_base):
                data_.setdefault(v.name, {})[k] = v.value
            else:
                data_['$set'][k] = v
        if setOnInsert is None:
            upsert = False
        else:
            upsert = True
            data_['$setOnInsert'] = setOnInsert
            # 当传递了setOnInsert时:
            # 当结果为更新时, setOnInsert不生效.
            # 注意: 当结果为插入时, data和setOnInsert都会生效, 但相同字段后者优先级更高, 即: {**data, **setOnInsert} .
        empsetCondi = Factory(empset).ParseWhere()
        key = self._parse_slice()
        with self.parent.parent.get_conn() as conn:
            sheet = conn[self.parent.db_name][self.sheet_name]
            # [::]
            if isinstance(key, list):
                L, R, S = key[0], key[1], key[2] or 1
                if S in [None, 1]:
                    if (L in [None, 1] and R in [None, -1]) or (L == -1 and R == 1):
                        return sheet.update_many(self._parse_where(), data_, upsert=upsert)
                        # r.acknowledged, r.matched_count
                        # matched_count 与 modified_count 的区别:
                        # matched_count 表示匹配到的数目, 如果是update_one, 则 matched_count in [0, 1]
                        # modified_count 表示数据有变化的数目
                        # 如果一条数据修改前和修改后一致(例如:把3修改成3), 则不会被统计到modified_count中
            # [1]且无排序
            if key == 1 and not self._parse_order():
                return sheet.update_one(self._parse_where(), data_, upsert=upsert)  # r.acknowledged, r.matched_count
            # 其它情况
            try:
                ids = self['_id'][self._condition['slice']].find()
            except Odm_Index_Error:  # 说明key是int而非切片，且找不到符合条件的
                return sheet.update_one(empsetCondi, data_, upsert=upsert)
            else:
                if isinstance(ids, list):
                    if ids:
                        ids = [x['_id'] for x in ids]
                        condition = (mc._id == mf.isin(*ids)).ParseWhere()
                        return sheet.update_many(condition, data_, upsert=upsert)
                    else:
                        return sheet.update_many(empsetCondi, data_, upsert=upsert)
                else:  # 说明key是int而非切片，且找到了符合条件的
                    condition = (mc._id == ids['_id']).ParseWhere()
                    return sheet.update_one(condition, data_, upsert=upsert)

    async def aupdate(self, data: dict=None, setOnInsert: dict=None):
        if self._for_tip(): return self.update(data=data, setOnInsert=setOnInsert)  # 引导 vscode 产生代码提示
        data_ = {'$set':{}}
        for k, v in ( data or {} ).items():
            if isinstance(v, mo_base):
                data_.setdefault(v.name, {})[k] = v.value
            else:
                data_['$set'][k] = v
        if setOnInsert is None:
            upsert = False
        else:
            upsert = True
            data_['$setOnInsert'] = setOnInsert
            # 当传递了setOnInsert时:
            # 当结果为更新时, setOnInsert不生效.
            # 注意: 当结果为插入时, data和setOnInsert都会生效, 但相同字段后者优先级更高, 即: {**data, **setOnInsert} .
        empsetCondi = Factory(empset).ParseWhere()
        key = self._parse_slice()
        async with self.parent.parent.get_conn() as conn:
            sheet = conn[self.parent.db_name][self.sheet_name]
            # [::]
            if isinstance(key, list):
                L, R, S = key[0], key[1], key[2] or 1
                if S in [None, 1]:
                    if (L in [None, 1] and R in [None, -1]) or (L == -1 and R == 1):
                        return await sheet.update_many(self._parse_where(), data_, upsert=upsert)
            # [1]且无排序
            if key == 1 and not self._parse_order():
                return await sheet.update_one(self._parse_where(), data_, upsert=upsert)  # r.acknowledged, r.matched_count
            # 其它情况
            try:
                ids = await self['_id'][self._condition['slice']].afind()
            except Odm_Index_Error:
                return await sheet.update_one(empsetCondi, data_, upsert=upsert)
            else:
                if isinstance(ids, list):
                    if ids:
                        ids = [x['_id'] for x in ids]
                        condition = (mc._id == mf.isin(*ids)).ParseWhere()
                        return await sheet.update_many(condition, data_, upsert=upsert)
                    else:
                        return await sheet.update_many(empsetCondi, data_, upsert=upsert)
                else:
                    condition = (mc._id == ids['_id']).ParseWhere()
                    return await sheet.update_one(condition, data_, upsert=upsert)

    def delete(self):
        key = self._parse_slice()
        with self.parent.parent.get_conn() as conn:
            sheet = conn[self.parent.db_name][self.sheet_name]
            # [::]
            if isinstance(key, list):
                L, R, S = key[0], key[1], key[2] or 1
                if S in [None, 1]:
                    if (L in [None, 1] and R in [None, -1]) or (L == -1 and R == 1):
                        return sheet.delete_many(self._parse_where())  # r.acknowledged, r.deleted_count
            # [1]且无排序
            if key == 1 and not self._parse_order():
                return sheet.delete_one(self._parse_where())  # r.acknowledged, r.deleted_count
            # 其它索引
            try:
                ids = self['_id'][self._condition['slice']].find()
            except Odm_Index_Error:  # 说明key是int而非切片，且找不到符合条件的
                return sheet.delete_one( Factory(empset).ParseWhere() )
            else:
                if isinstance(ids, list):
                    return sheet.delete_many( (mc._id == mf.isin(*ids)).ParseWhere() )
                else:
                    return sheet.delete_one( (mc._id == ids['_id']).ParseWhere() )
    
    async def adelete(self):
        if self._for_tip(): return self.delete()  # 引导 vscode 产生代码提示
        key = self._parse_slice()
        async with self.parent.parent.get_conn() as conn:
            sheet = conn[self.parent.db_name][self.sheet_name]
            # [::]
            if isinstance(key, list):
                L, R, S = key[0], key[1], key[2] or 1
                if S in [None, 1]:
                    if (L in [None, 1] and R in [None, -1]) or (L == -1 and R == 1):
                        return await sheet.delete_many(self._parse_where())  # r.acknowledged, r.deleted_count
            # [1]且无排序
            if key == 1 and not self._parse_order():
                return await sheet.delete_one(self._parse_where())  # r.acknowledged, r.deleted_count
            # 其它索引
            try:
                ids = await self['_id'][self._condition['slice']].afind()
            except Odm_Index_Error:  # 说明key是int而非切片，且找不到符合条件的
                return await sheet.delete_one( Factory(empset).ParseWhere() )
            else:
                if isinstance(ids, list):
                    return await sheet.delete_many( (mc._id == mf.isin(*ids)).ParseWhere() )
                else:
                    return await sheet.delete_one( (mc._id == ids['_id']).ParseWhere() )

    def __getitem__(self, key):
        if type(key) in (int, slice): return self._deepcopy('slice', key)
        if isinstance(key, str|tuple): return self._deepcopy('columns', key)  # 输入多个字符串, 用逗号隔开, Python会自动打包成tuple
        if key is None: return self._deepcopy('columns', None)  # None表示不限定字段
        if isinstance(key, Factory): return self._deepcopy('where', self._condition['where'] & key)
        raise TypeError(key)

    def __repr__(self):
        return f"skk.mongo.Sheet<{self.parent.db_name}.{self.sheet_name}>"
    
    __str__ = __repr__


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
    
    def __bool__(self): return True

    def _deepcopy(self, obj):
        if obj in (uniset, empset):
            return obj
        return deepcopy(obj)

    def __and__(self, obj: 'Factory'):  # 交集 &
        a = self._deepcopy(self.where)
        b = self._deepcopy(obj.where)
        if a is uniset: return Factory(b)
        if b is uniset: return Factory(a)
        if a and b:  # a 和 b 有可能是 empset
            if set(a) & set(b):
                return Factory({'$and': [a, b]})
            return Factory({**a, **b})
        return Factory(empset)
    
    def __or__(self, obj: 'Factory'):  # 并集 |
        a = self._deepcopy(self.where)
        b = self._deepcopy(obj.where)
        if a is empset: return Factory(b)
        if b is empset: return Factory(a)
        if a is uniset or b is uniset:
            return Factory(uniset)
        return Factory({'$or': [a, b]})

    def __invert__(self):  # 补集 ~
        w = self.where
        if w is uniset: return Factory(empset)
        if w is empset: return Factory(uniset)
        return Factory({'$nor': [w]})
    
    def __sub__(self, obj): return self & (~ obj)  # 差集 -

    def ParseWhere(self) -> dict:
        where  = self._deepcopy(self.where)
        if where is uniset: return {}
        if where is empset: return {"$expr": {"$eq": [1, 0]}}
        return where


def GetFiField(obj: 'Filter'):
    return object.__getattribute__(obj, 'field')


class Filter():
    _variable = True

    def __init__(self, field:str):
        self.field = field
        self._variable = False
    
    def __setattr__(self, name, value):
        assert object.__getattribute__(self, '_variable')
        object.__setattr__(self, name, value)
    
    def __getattribute__(self, field): return Filter(f"{GetFiField(self)}.{field}")
    
    __getitem__ = __getattribute__

    def __lt__(self, obj): return Factory({GetFiField(self): {'$lt': obj}})  # <
    def __le__(self, obj): return Factory({GetFiField(self): {'$lte': obj}})  # <=
    def __gt__(self, obj): return Factory({GetFiField(self): {'$gt': obj}})  # >
    def __ge__(self, obj): return Factory({GetFiField(self): {'$gte': obj}})  # >=
    def __ne__(self, obj): return Factory({GetFiField(self): {'$ne': obj}})  # !=

    def __eq__(self, obj) -> Factory:
        if isinstance(obj, mf.contain_all):
            lis = obj.lis
            if len(lis) == 1: return Factory({GetFiField(self): {'$elemMatch':{'$eq':lis[0]}}})
            if len(lis) > 1: return Factory({'$and': [{GetFiField(self): {'$elemMatch':{'$eq':x}}} for x in set(lis)]})
            return Factory(uniset)
        
        elif isinstance(obj, mf.contain_any):
            lis = obj.lis
            if len(lis) == 1: return Factory({GetFiField(self): {'$elemMatch':{'$eq':lis[0]}}})
            if len(lis) > 1: return Factory({'$or': [{GetFiField(self): {'$elemMatch':{'$eq':x}}} for x in set(lis)]})
            return Factory(empset)
        
        elif isinstance(obj, mf.contain_none):
            if lis := obj.lis:
                return Factory({'$nor': [{GetFiField(self): {'$elemMatch':{'$eq':x}}} for x in set(lis)]})
            return Factory(uniset)
        
        elif isinstance(obj, mf.isin):
            lis = obj.lis
            if not lis: return Factory(empset)
            if len(lis) == 1: return Factory({GetFiField(self): lis[0]})
            return Factory({GetFiField(self): {'$in': lis}})
        
        elif isinstance(obj, mf.notin):
            lis = obj.lis
            if not lis: return Factory(uniset)
            if len(lis) == 1: return Factory({GetFiField(self): {'$ne': lis[0]}})
            return Factory({GetFiField(self): {'$nin': lis}})
        
        else:
            return Factory({GetFiField(self): obj})


class mf_base:
    def __init__(self, *lis, **dic):
        self.lis = lis
        self.dic = dic

class mf:
    class contain_all(mf_base): ...
    class contain_any(mf_base): ...
    class contain_none(mf_base): ...
    class isin(mf_base): ...
    class notin(mf_base): ...
    def re(pattern, i=False):
        if i:
            return {'$regex': pattern, '$options': 'i'}
        return {'$regex': pattern}


class mo_base: ...

class mo:
    class push(mo_base):  # 添加
        name = '$push'
        def __init__(self, *vs):
            self.value = {"$each":list(vs)}
    
    class add(mo_base):  # 不存在时才添加
        name = '$addToSet'
        def __init__(self, *vs):
            self.value = {"$each":list(vs)}

    class inc(mo_base):  # 自增:inc(1), 自减:inc(-1)
        name = '$inc'
        def __init__(self, value):
            self.value = value

    class pull(mo_base):  # 从数组field内删除一个等于value值
        name = '$pull'
        def __init__(self, value):
            self.value = value

    class rename(mo_base):  # 修改字段名称
        name = '$rename'
        def __init__(self, value):
            self.value = value

    class _(mo_base):  # 删除键
        name = '$unset'
        value = 1
    unset = delete = _()

    class _(mo_base):
        name = '$pop'
        def __init__(self, value):
            self.value = value
    popfirst = _(-1)  # 删除数组第1个元素, 和Python相反, -1代表最前面
    poplast = _(1)  # 删除数组最后1个元素


def creat_Filter(cls, field) -> Filter:
    return Filter(field=field)

class McType(type):
    __getattribute__ = creat_Filter
    __getitem__ = creat_Filter

class mc(object, metaclass=McType):
    _id = None  # 预设字段提示