# 描述

设置环境名称。

有时候，对于某些功能，我们也许希望在不同的环境上采用不同的方案。以访问数据库为例：当程序在外网运行时，须通过数据库公网 ip 访问；而当程序在内网运行时，为了提高性能，我们可以通过数据库内网 ip 访问。

[源码](https://github.com/lcctoor/skk/tree/main/skk/envname)

# 安装

```
pip install skk
```

# 教程

创建环境名称：

```python
from skk import envname

envname.set_environment_name('aliyun_hongkong_1')
```

查询环境名称：

```python
from skk import envname

print( envname.read_environment_name() )  # >>> 'aliyun_hongkong_1'
```

应用示例：

```python
import pymysql
from skk import envname


if envname.read_environment_name() == 'aliyun_hongkong_1':
    host = '192.168.0.127'
else:
    host = '112.47.203.101'


conn = pymysql.connect(host=host, port=3306, user='root', password='123456789')
```
