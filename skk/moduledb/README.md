# 描述

为 Python 模块提供数据持久化支持。

# 安装

```
pip install skk
```

# 导入

```python
from os.path import abspath
from skk import moduledb
```

# 为当前模块持久化数据

```python
db = moduledb.DB(abspath(__file__), depth=3)

city = db['泉州市']  # 第 1 层
school = city['希望小学']  # 第 2 层
wang = school['小王']  # 第 depth 层

wang['age'] = 18
wang['name'] = '小王'
wang.setdefault('性别', '男')

print(wang['name'])  # >>> '小王'
```
