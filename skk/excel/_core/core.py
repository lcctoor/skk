from datetime import datetime as datetime2
from typing import Any, Dict
from pathlib import Path as lpath

import numpy as np
import pandas as pd
from pandas import Series, DataFrame


class Excel_Meta(type):
    def __truediv__(cls, path):
        return File(path=path)


class Excel(object, metaclass=Excel_Meta):
    ...


class File:
    def __init__(self, path):
        self.path = str(path)
        self._sheets = {}
        lfile = lpath(self.path)
        self.name = lfile.name
        self.out_dir = lfile.parent
        self._file_name_indexes = {}
    
    def __truediv__(self, sheet_name: str|int):
        assert type(sheet_name) in (str, int)
        if type(sheet_name) is int:
            assert sheet_name > 0
            sheet_name -= 1  # 转化为从 1 开始的索引
        sh = self._sheets.get(sheet_name)
        if sh is None:
            df = pd.read_excel(self.path, sheet_name=sheet_name)
            sh = self._sheets[sheet_name] = Sheet(file=self, df=df)
        return sh


class Groups:
    def __init__(self, core: Dict[tuple, 'Sheet']):
        self.core = core
    
    def __str__(self): return self.core.__str__()
    def __repr__(self): return self.core.__repr__()

    def __getitem__(self, key):
        if type(key) is not tuple:
            key = (key,)
        return self.core[key]
    
    @property
    def 组名列表(self):
        return list(self.core)


class Sheet:
    def __init__(self, file: File, df: DataFrame):
        self.file = file
        self.df = df
        self.列 = Columns(sheet=self)
    
    def __str__(self): return self.df.__str__()
    def __repr__(self): return self.df.__repr__()
    
    def __getattr__(self, name):
        return object.__getattribute__(self, name)
    
    def 另存(self, 文件名: str|None=''):
        if not (文件名 or '').endswith('.xlsx'):
            indexes = self.file._file_name_indexes
            t = datetime2.now().strftime(r" _%m%d _%H%M%S")
            if t in indexes:
                indexes[t] += 1
                文件名 = f"{self.file.name}{t} _{indexes[t]}.xlsx"
            else:
                indexes[t] = 1
                文件名 = f"{self.file.name}{t}.xlsx"
        path = f"{self.file.out_dir}/{文件名}"
        self.df.to_excel(path, index=False)
        print(f"已另存到 {文件名}")
    
    def 分组(self, *列名):
        core = {}
        for key, df in self.df.groupby(list(列名)):
            key = tuple(np.array([k]).tolist()[0] for k in key)
            df = self.__class__(file=self.file, df=df.copy(deep=True))
            core[key] = df
        return Groups(core=core)


oget = object.__getattribute__
oset = object.__setattr__


def get_column_core(obj):
    if isinstance(obj, Column):
        return obj.core
    else:
        return obj


class Column:
    def __init__(self, sheet: Sheet, core: Series):
        self.sheet = sheet
        self.core = core
    
    def __str__(self): return self.core.__str__()
    def __repr__(self): return self.core.__repr__()

    def __add__(self, other): return self.__class__(self.sheet, self.core + get_column_core(other))  # 加
    def __sub__(self, other): return self.__class__(self.sheet, self.core - get_column_core(other))  # 减
    def __mul__(self, other): return self.__class__(self.sheet, self.core * get_column_core(other))  # 乘
    def __truediv__(self, other): return self.__class__(self.sheet, self.core / get_column_core(other))  # 除
    def __pow__(self, other): return self.__class__(self.sheet, self.core ** get_column_core(other))  # 乘方

    def __gt__(self, other): return self.__class__(self.sheet, self.core > get_column_core(other))  # 大于
    def __ge__(self, other): return self.__class__(self.sheet, self.core >= get_column_core(other))  # 大于等于
    def __lt__(self, other): return self.__class__(self.sheet, self.core < get_column_core(other))  # 小于
    def __le__(self, other): return self.__class__(self.sheet, self.core <= get_column_core(other))  # 小于等于
    def __eq__(self, other): return self.__class__(self.sheet, self.core == get_column_core(other))  # 等于
    def __ne__(self, other): return self.__class__(self.sheet, self.core != get_column_core(other))  # 不等于

    def __and__(self, other): return self.__class__(self.sheet, self.core & get_column_core(other))  # 交集
    def __or__(self, other): return self.__class__(self.sheet, self.core | get_column_core(other))  # 并集
    def __invert__(self): return self.__class__(self.sheet, ~ self.core)  # 补集

    def 应用(self, 函数):
        core = self.core.apply(函数)
        return self.__class__(self.sheet, core)


def 求和(self: Column):
    return np.array([self.core.sum()]).tolist()[0]

def 筛选(self: Column):
    sheet = self.sheet
    df = sheet.df[self.core].copy(deep=True)
    return Sheet(file=sheet.file, df=df)
    
def 判断(self: Column, 真值, 假值):
    return self.应用(lambda x: 真值 if x else 假值)


class Columns:
    sheet: Sheet

    def __init__(self, sheet: Sheet):
        oset(self, 'sheet', sheet)
    
    def __getattribute__(self, column_name: str):
        assert type(column_name) is str
        sheet: Sheet = oget(self, 'sheet')
        return Column(sheet, sheet.df[column_name])
    
    def __setattr__(self, column_name: str, value):
        assert type(column_name) is str
        sheet: Sheet = oget(self, 'sheet')
        sheet.df[column_name] = get_column_core(value)
    
    __getitem__ = __getattribute__
    __setitem__ = __setattr__
