import os, platform, socket
from math import ceil
import hashlib
from hashlib import shake_256
from typing import Any, List, Union, Literal
import numpy as np
from pathlib import Path
from json import dumps as jsonDumps

class missing_arguments_error(Exception): ...

class undefined: ...

##################################################################################

class bidict:
    ''' 双向字典 '''
    def __init__(self):
        self.core = {}
    
    def __setitem__(self, key, value):
        self.pop(key, None)
        self.pop(value, None)
        self.core[key] = value
        self.core[value] = key
    
    def __getitem__(self, key):
        return self.core[key]

    def get(self, key, default=undefined):
        value = self.core.get(key, default)
        if value is undefined:
            raise missing_arguments_error('default')
        else:
            return value
    
    def pop(self, key, default=undefined):
        if key in self.core:
            value = self.core.pop(key)
            self.core.pop(value, 0)
            return value
        elif default is undefined:
            raise missing_arguments_error('default')
        else:
            return default

##################################################################################


class ztype():
    core: Any

    def __getattr__(self, name):
        return self.core.__getattr__(name)
    
    @classmethod
    def _GetZtypeCore(cls, obj):
        if isinstance(obj, ztype):
            return obj.core
        return obj
    
    def __str__(self): return str(self.core)
    def __int__(self): return int(self.core)
    def __float__(self): return float(self.core)
    def __bool__(self): return bool(self.core)
    def __bytes__(self): return bytes(self.core)

    def str(self): return str(self)
    def int(self): return int(self)
    def float(self): return float(self)
    def bool(self): return bool(self)
    def bytes(self): return bytes(self.core)

    def __len__(self): return len(self.core)

    # 默认用内核比较大小
    def __eq__(self, obj): return self.core == self._GetZtypeCore(obj)
    def __ne__(self, obj): return self.core != self._GetZtypeCore(obj)
    def __lt__(self, obj): return self.core < self._GetZtypeCore(obj)
    def __le__(self, obj): return self.core <= self._GetZtypeCore(obj)
    def __gt__(self, obj): return self.core > self._GetZtypeCore(obj)
    def __ge__(self, obj): return self.core >= self._GetZtypeCore(obj)

    # 加减乘除默认用内核操作
    def __add__(self, n): return self.__class__(self.core + self._GetZtypeCore(n))
    def __radd__(self, n): return self.__class__(self._GetZtypeCore(n) + self.core)
    def __iadd__(self, n):
        self.core += self._GetZtypeCore(n)
        return self
    
    def __sub__(self, n): return self.__class__(self.core - self._GetZtypeCore(n))
    def __rsub__(self, n): return self.__class__(self._GetZtypeCore(n) - self.core)
    def __isub__(self, n):
        self.core -= self._GetZtypeCore(n)
        return self.core

    def __mul__(self, n): return self.__class__(self.core * self._GetZtypeCore(n))
    def __rmul__(self, n): return self.__class__(self._GetZtypeCore(n) * self.core)
    def __imul__(self, n):
        self.core *= self._GetZtypeCore(n)
        return self

    def __truediv__(self, n): return self.__class__(self.core / self._GetZtypeCore(n))
    def __rtruediv__(self, n): return self.__class__(self._GetZtypeCore(n) / self.core)
    def __itruediv__(self, n):
        self.core /= self._GetZtypeCore(n)
        return self


##################################################################################

class vbytes(ztype):
    ''' 可变字节串 '''

    core: bytes

    def __bytes__(self): return self.core
    
    def __init__(self, *s, **kvs):
        self.core = bytes(*s, **kvs)

    def md5(self, rtype: Literal['str','bytes','vbytes']='str'):
        value = hashlib.md5(self.core)
        if rtype in (str, 'str'): return value.hexdigest()
        if rtype in (bytes, 'bytes'): return value.digest()
        if rtype in (vbytes, 'vbytes'): return vbytes(value.digest())
        raise ValueError(rtype)

    def shake256(self, rtype: Literal['str','bytes','vbytes']='str', rsize=32):
        value = shake_256(self.core)
        if rtype in (str, 'str'): return value.hexdigest(ceil(rsize/2))[:rsize]
        if rtype in (bytes, 'bytes'): return value.digest(rsize)
        if rtype in (vbytes, 'vbytes'): return vbytes(value.digest(rsize))
        raise ValueError(rtype)

##################################################################################

def XpathGet(dic, i, keySize, keys):
    if i < keySize and type(dic) is dict:
        ikey = keys[i]
        for k, v in dic.items():
            if k == ikey:
                if i == keySize - 1:
                    return v
                value = XpathGet(v, i + 1, keySize, keys)
                if value is not undefined:
                    return value
            else:
                value = XpathGet(v, i, keySize, keys)
                if value is not undefined:
                    return value
    return undefined

def into_dict(*s, **kvs):
    if s and isinstance(s[0], vdict): return s[0].core.copy()
    return dict(*s, **kvs)

class vdict(ztype):
    core: dict

    def __init__(self, *s, **kvs):
        self.core = into_dict(*s, **kvs)

    def xpath(self, *keys):
        '''
            一个查找字典的子孙键的工具.
            使用场景: 当字典的结构具有不确定性, 或者要获取的键位于较深层的子孙层时, 可使用该函数进行取值.
        '''
        if not isinstance(keys, tuple):
            keys = (keys, )
        value = XpathGet(self.core, 0, len(keys), keys)
        if value is undefined:
            raise KeyError(keys)
        return value
    
    def deepGet(self, *keys, default=undefined):
        res = self.core
        try:
            for k in keys:
                res = res[k]
            return res
        except:
            if default is undefined:
                raise missing_arguments_error('default')
            else:
                return default


class _CoolQueue:
    ''' 一个先进先出, 可设置最大容量, 可固定元素的队列 '''

    def __init__(self, maxlen: int=None):
        self._core: List[dict] = []
        self.maxlen = maxlen or float('inf')

    def _trim(self):
        _core = self._core
        if len(_core) > self.maxlen:
            dc = len(_core) - self.maxlen
            indexes = []
            for i,x in enumerate(_core):
                if not x['pin']:
                    indexes.append(i)
                if len(indexes) == dc:
                    break
            for i in indexes[::-1]:
                _core.pop(i)

    def add_many(self, *objs):
        for x in objs:
            self._core.append({'obj':x, 'pin':False})
        self._trim()

    def __iter__(self):
        for x in self._core:
            yield x['obj']

    def pin(self, *indexes):
        for i in indexes:
            self._core[i]['pin'] = True

    def unpin(self, *indexes):
        for i in indexes:
            self._core[i]['pin'] = False

    def copy(self):
        que = self.__class__(maxlen=self.maxlen)
        que._core = self._core.copy()
        return que
    
    def deepcopy(self): ...  # 创建这个方法是为了提醒用户: copy 方法是浅拷贝

    def __add__(self, obj: Union[list, '_CoolQueue']):
        que = self.copy()
        if isinstance(obj, self.__class__):
            que._core += obj._core
            que._trim()
        else:
            que.add_many(*obj)
        return que

def group_data(data, group_size):
    return [data[group_size*(i-1): group_size*i] for i in range(1, ceil(len(data)/group_size)+1)]

def json_chinese(data, *, indent=None): return jsonDumps(data, ensure_ascii=False, indent=indent)

def repair_pathclash(path):
    ''' 解决命名冲突 '''
    while Path(path).exists():
        path += '_'
    return path

def uniform_put(total, site_count):
    ''' 均匀放球 '''
    baseCount, r = divmod(total, site_count)
    sites = [baseCount] * site_count
    if r:
        for x in np.linspace(0, site_count-1, r):
            sites[round(x)] += 1
    return sites

def limit_input(prompt='', limit: list=[]):
    while True:
        user = input(prompt)
        if user in limit: return user

def get_chrome_path():
    for chrome in [
        rf'C:\Program Files\Google\Chrome\Application\chrome.exe',  # Chrome [已校验]
        rf'C:\Users\{os.getlogin()}\AppData\Local\360ChromeX\Chrome\Application\360ChromeX.exe',  # 360极速浏览器X [已校验]
        rf'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe',  # Edge [已校验] 32位的, 置底
        rf'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',  # Mac Chrome
        rf'/usr/bin/chromium-browser',  # Linux chromium
        rf'/usr/bin/google-chrome',  # Linux Chrome
    ]:
        if Path(chrome).is_file():
            return chrome
    return None

platform_system: Literal['linux', 'windows', 'darwin', 'java'] = platform.system().lower()

def get_free_port():
    sock = socket.socket()
    sock.bind(('localhost', 0))
    port = sock.getsockname()[1]
    sock.close()
    return port