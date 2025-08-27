import re
from inspect import getsource
from typing import Dict, Literal, List
from collections import deque
from re import search
from bson import ObjectId  # 代码提示
from pymongo import MongoClient  # 代码提示


class TRUE:
    def __bool__(self): return True

class FALSE:
    def __bool__(self): return False

def uniset(row): return True
def empset(row): return False

undefined = FALSE()
undefined_2 = FALSE()


class OOM():
    
    def __init__(self):
        self._connpool = deque([], maxlen=1)

    def mkconn(self):
        '''
        请在子类中覆盖此方法
        '''
        return MongoClient(host='localhost', port=27017)
    
    def get_conn(self):
        class core():
            def __enter__(mSelf) -> MongoClient:
                if self._connpool:
                    mSelf.conn = self._connpool.popleft()
                else:
                    mSelf.conn = self.mkconn()
                return mSelf.conn
            def __exit__(mSelf, errType, errValue, traceback):
                if not errType:
                    self._connpool.append(mSelf.conn)
        return core()
    
    def get_db_names(self):
        ignore = ('admin', 'config', 'local')
        with self.get_conn() as conn:
            return [x for x in conn.list_database_names() if x not in ignore]
    
    def len(self): return len(self.get_db_names())

    def __iter__(self):
        for x in self.get_db_names():
            yield DB(parent=self, db_name=x)
    
    def __getitem__(self, db_name: str|tuple):
        if type(db_name) is str:
            return DB(parent=self, db_name=db_name)
        else:
            assert type(db_name) is tuple
            return [DB(parent=self, db_name=x) for x in db_name]


class DB():

    def __init__(self, parent: OOM, db_name: str):
        self.parent = parent
        self.db_name = db_name

    def delete_db(self):
        with self.parent.get_conn() as conn:
            return conn.drop_database(self.db_name)
        
    def __repr__(self):
        return f"oodb.DB:<{self.db_name}>"
    
    __str__ = __repr__

    def get_sheet_names(self):
        with self.parent.get_conn() as conn:
            return conn[self.db_name].list_collection_names()
    
    def len(self): return len(self.get_sheet_names())

    def __iter__(self):
        for x in self.get_sheet_names():
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
        self._condition: Dict[Literal['where'], Factory|None] = _condition or {
            'where': Factory(uniset),
        }

    def _deepcopy(self, condition_key: str, value):
        return Sheet(
            parent = self.parent,
            sheet_name = self.sheet_name,
            _condition = {
                'where': self._condition['where'],
                condition_key: value,
            }
        )
    
    def len(self): return len( list(self.find()) )
    
    def delete_sheet(self):
        with self.parent.parent.get_conn() as conn:
            return conn[self.parent.db_name].drop_collection(self.sheet_name)

    def insert(self, *data: dict, bases: List[str|dict]=None):
        bases = [x['_id'] if type(x) is dict else x for x in (bases or [])]
        for x in data:
            x['__bases__'] = bases
        with self.parent.parent.get_conn() as conn:
            sheet = conn[self.parent.db_name][self.sheet_name]
            if len(data) == 1:
                return sheet.insert_one( data[0] )  # 分配到的 _id 为 str(r)
            else:
                return sheet.insert_many( data )  # r.acknowledged, r.inserted_ids

    def find(self, limit: int=0):
        limit = limit or float('inf')
        sheet = self.parent.parent.mkconn()[self.parent.db_name][self.sheet_name]
        res = sheet.find({}, {'_id': 1})
        _ids = [x['_id'] for x in list(res)]
        _read_cache = {}
        for _id in _ids:
            row = Row(parent=self, _id=_id)
            row._read_cache = _read_cache
            if self._condition['where'].where(row):
                del row._read_cache
                yield row
                if not (limit := limit - 1): break
    
    def update(self, data: dict=None, setOnInsert: dict=None, limit: int=0):
        data_ = {'$set':{}}
        for k, v in ( data or {} ).items():
            if isinstance(v, mo_base):
                data_.setdefault(v.name, {})[k] = v.value
            else:
                data_['$set'][k] = v
        assert '_id' not in data_['$set'], 'You should not modify the _id value of an object !'
        if setOnInsert is None:
            upsert = False
        else:
            upsert = True
            data_['$setOnInsert'] = setOnInsert
            # 当传递了setOnInsert时:
            # 当结果为更新时, setOnInsert不生效.
            # 注意: 当结果为插入时, data和setOnInsert都会生效, 但相同字段后者优先级更高, 即: {**data, **setOnInsert} .
        if _ids := [row._id for row in self.find(limit=limit)]:
            condition = {'_id': {'$in': _ids}}
            sheet = self.parent.parent.mkconn()[self.parent.db_name][self.sheet_name]
            return sheet.update_many(condition, data_, upsert=upsert)
        else:
            sheet = self.parent.parent.mkconn()[self.parent.db_name][self.sheet_name]
            return sheet.update_many({"$expr": {"$eq": [1, 0]}}, data_, upsert=upsert)
    
    def delete(self, limit: int=0):
        if _ids := [row._id for row in self.find(limit=limit)]:
            condition = {'_id': {'$in': _ids}}
            sheet = self.parent.parent.mkconn()[self.parent.db_name][self.sheet_name]
            return sheet.delete_many( condition )
        else:
            sheet = self.parent.parent.mkconn()[self.parent.db_name][self.sheet_name]
            return sheet.delete_many( {"$expr": {"$eq": [1, 0]}} )
    
    def __getitem__(self, key):
        if isinstance(key, Factory): return self._deepcopy('where', self._condition['where'] & key)
        raise TypeError(key)

    def __repr__(self):
        return f"oodb.Sheet<{self.parent.db_name}.{self.sheet_name}>"
    
    __str__ = __repr__


class Row:
    _read_cache: dict|FALSE = undefined
    
    def __init__(self, parent: Sheet, _id: ObjectId):
        self.parent = parent
        self._id = _id

    def __repr__(self):
        return f"oodb.Row<{self.parent.parent.db_name}.{self.parent.sheet_name}.{self._id}>"
    
    __str__ = __repr__
    
    def _search_key(self, data: dict, key: str, _read_cache: dict):
        value_1 = data.get(key, undefined)
        if value_1 is undefined:
            sheet = self.parent.parent.parent.mkconn()[self.parent.parent.db_name][self.parent.sheet_name]
            for _id in data['__bases__']:
                value_2 = _read_cache.get(direct_key := (_id, key), undefined_2)
                if value_2 is undefined_2:
                    if res := list( sheet.find({'_id': _id}, {key: 1, '__bases__': 1}).limit(1) ):
                        _read_cache[direct_key] = value_2 = self._search_key(res[0], key, _read_cache)
                    else:
                        _read_cache[direct_key] = value_2 = undefined
                if value_2 is not undefined:
                    return value_2
        return value_1
    
    def get(self, key: str|tuple, default=None):
        if type(key) is not tuple: key = (key,)
        _read_cache = {} if self._read_cache is undefined else self._read_cache
        value = self._search_key({'__bases__': [self._id]}, key[0], _read_cache)
        value = parse_oodb_key(self, value)
        while key := key[1:]:
            if type(value) is dict:
                value = value.get(key[0], undefined)
                value = parse_oodb_key(self, value)
            else:  # dict 以外的其它类型，例如：list、str、int、float, undefined
                value = undefined
                break
        return default if value is undefined else value
    
    def __getitem__(self, key: str|tuple):
        value = self.get(key, default=undefined)
        if value is undefined:
            raise KeyError(key)
        return value
    
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
        sheet = self.parent.parent.parent.mkconn()[self.parent.parent.db_name][self.parent.sheet_name]
        return sheet.update_one({'_id': self._id}, data_, upsert=upsert)
    
    def delete(self):
        sheet = self.parent.parent.parent.mkconn()[self.parent.parent.db_name][self.parent.sheet_name]
        return sheet.delete_one( {'_id': self._id} )


class mpy:
    def _serialize_func(func):
        func_string = getsource(func)
        indent = len( re.search(r'''( *)@''', func_string).group(1) )
        defined, func_name = re.search(rf'''\n( {{{indent}}}def +([^\s\(]+)\(.+)''', func_string, re.S).group(1, 2)
        return indent, defined, func_name
    
    @classmethod
    def method(cls, func):
        indent, defined, func_name = cls._serialize_func(func)
        return {'__oodb__': [ dict(pipeline='method', indent=indent, defined=defined, func_name=func_name) ]}
    
    @classmethod
    def dynamic(cls, *args, **kwargs):
        def core(func):
            indent, defined, func_name = cls._serialize_func(func)
            return {'__oodb__': [ dict(pipeline='dynamic', indent=indent, defined=defined, func_name=func_name, args=args, kwargs=kwargs) ]}
        return core

def creat_method(func, self: Row):
    def value(*args, **kwargs):
        return func(self, *args, **kwargs)
    return value

def parse_oodb_key(row: Row, value):
    if type(value) is dict and '__oodb__' in value:
        for pipeline in value['__oodb__']:
            match pipeline['pipeline']:
                case 'method':
                    indent, defined, func_name = [pipeline[x] for x in ('indent', 'defined', 'func_name')]
                    if indent:
                        defined = f"if True:\n{defined}"
                    exec(defined, {},  l := {})
                    value = creat_method(l[func_name], row)
                case 'dynamic':
                    indent, defined, func_name, args, kwargs = [pipeline[x] for x in ('indent', 'defined', 'func_name', 'args', 'kwargs')]
                    if indent:
                        defined = f"if True:\n{defined}"
                    exec(defined, {},  l := {})
                    value = l[func_name](row, *args, **kwargs)
    return value


class Factory:

    def __init__(self, where):
        self.where = where

    def __bool__(self): return True

    def __and__(self, obj: 'Factory'):  # 交集 &
        return Factory( lambda row: bool(self.where(row) and obj.where(row)) )
    
    def __or__(self, obj: 'Factory'):  # 并集 |
        return Factory( lambda row: bool(self.where(row) or obj.where(row)) )

    def __invert__(self):  # 补集 ~
        return Factory( lambda row: not self.where(row) )
    
    def __sub__(self, obj: 'Factory'): return self & (~ obj)  # 差集 -


def GetFiField(obj: 'Filter'):
    return object.__getattribute__(obj, 'field')


class Filter():

    def __init__(self, field: str|tuple):
        self.field = field
    
    def __getattribute__(self, field):
        self_field = GetFiField(self)
        if type(self_field) is tuple:
            return Filter( self_field + (field,) )
        else:
            return Filter( (self_field, field) )
    
    __getitem__ = __getattribute__

    def _lt(self, obj):
        key = GetFiField(self)
        def func(row: Row):
            value = row.get(key, undefined)
            if value is not undefined:
                return value < obj
        return func
    def __lt__(self, obj): return Factory(object.__getattribute__(self, '_lt')(obj))  # <

    def _le(self, obj):
        key = GetFiField(self)
        def func(row: Row):
            value = row.get(key, undefined)
            if value is not undefined:
                return value <= obj
        return func
    def __le__(self, obj): return Factory(object.__getattribute__(self, '_le')(obj))  # <=

    def _gt(self, obj):
        key = GetFiField(self)
        def func(row: Row):
            value = row.get(key, undefined)
            if value is not undefined:
                return value > obj
        return func
    def __gt__(self, obj): return Factory(object.__getattribute__(self, '_gt')(obj))  # >

    def _ge(self, obj):
        key = GetFiField(self)
        def func(row: Row):
            value = row.get(key, undefined)
            if value is not undefined:
                return value >= obj
        return func
    def __ge__(self, obj): return Factory(object.__getattribute__(self, '_ge')(obj))  # >=

    def _ne(self, obj):
        key = GetFiField(self)
        def func(row: Row):
            value = row.get(key, undefined)
            if value is not undefined:
                return value != obj
        return func
    def __ne__(self, obj): return Factory(object.__getattribute__(self, '_ne')(obj))  # !=

    def _contain_all(self, obj: tuple):
        key = GetFiField(self)
        def func(row: Row):
            value = row.get(key, undefined)
            if type(value) is list:
                return not bool(set(obj) - set(value))
        return func
    
    def _contain_any(self, obj: tuple):
        key = GetFiField(self)
        def func(row: Row):
            value = row.get(key, undefined)
            if type(value) is list:
                return bool(set(value) & set(obj))
        return func
    
    def _contain_none(self, obj: tuple):
        key = GetFiField(self)
        def func(row: Row):
            value = row.get(key, undefined)
            if type(value) is list:
                return not bool(set(value) & set(obj))
        return func
    
    def _isin(self, obj: tuple):
        key = GetFiField(self)
        def func(row: Row):
            value = row.get(key, undefined)
            if value is not undefined:
                return value in obj
        return func
    
    def _notin(self, obj: tuple):
        key = GetFiField(self)
        def func(row: Row):
            value = row.get(key, undefined)
            if value is not undefined:
                return value not in obj
        return func
    
    def _re(self, pattern: str):
        key = GetFiField(self)
        def func(row: Row):
            value = row.get(key, undefined)
            if type(value) is str:
                return bool(search(pattern, value))
        return func
    
    def _eq(self, obj):
        key = GetFiField(self)
        def func(row: Row):
            value = row.get(key, undefined)
            if value is not undefined:
                return value == obj
        return func
    
    def __eq__(self, obj) -> Factory:
        if isinstance(obj, mf.contain_all):
            if lis := obj.lis:
                return Factory( object.__getattribute__(self, '_contain_all')(lis) )
            return Factory(uniset)
        
        elif isinstance(obj, mf.contain_any):
            if lis := obj.lis:
                return Factory( object.__getattribute__(self, '_contain_any')(lis) )
            return Factory(empset)
        
        elif isinstance(obj, mf.contain_none):
            if lis := obj.lis:
                return Factory( object.__getattribute__(self, '_contain_none')(lis) )
            return Factory(uniset)
        
        elif isinstance(obj, mf.isin):
            if lis := obj.lis:
                return Factory( object.__getattribute__(self, '_isin')(lis) )
            return Factory(empset)
        
        elif isinstance(obj, mf.notin):
            if lis := obj.lis:
                return Factory( object.__getattribute__(self, '_notin')(lis) )
            return Factory(uniset)
        
        elif isinstance(obj, mf.re):
            return Factory( object.__getattribute__(self, '_re')(obj.pattern) )
                
        else:
            return Factory(object.__getattribute__(self, '_eq')(obj))


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
    class re:
        def __init__(self, pattern):
            self.pattern = pattern


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