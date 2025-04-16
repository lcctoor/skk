# 描述

一个优雅的时间模块。

[源码](https://github.com/lcctoor/skk/tree/main/skk/cooltime)

# 安装

```
pip install skk
```

# 教程

## 导入

```python
from skk.cooltime import Cooltime
```

## 创建时间

```python
t1 = Cooltime()                                   # 创建1个当前时间
t2 = Cooltime.random()                            # 创建1个随机时间
t3 = Cooltime(1687271066.000028)                  # 从时间戳创建, 高精度
t4 = Cooltime(1687271066)                         # 从时间戳创建, 精确到秒
t5 = Cooltime(t3)                                 # 从 Cooltime 创建
t6 = Cooltime('2023-06-20 22:24:26.000028')       # 从字符串创建, 高精度
t7 = Cooltime('2023-06-20 22:24:26')              # 从字符串创建, 精确到秒
t8 = Cooltime('2023-06-20 22:24')                 # 从字符串创建, 精确到分
t9 = Cooltime('2023-06-20 22')                    # 从字符串创建, 精确到时
t10 = Cooltime('2023-06-20')                      # 从字符串创建, 精确到日
t11 = Cooltime([2023, 6, 20, 22, 24, 26.000028])  # 从其它类型创建, 如: list、tuple、datetime、time.localtime ……
```

注：

1、从字符串创建时，字符串的格式可任意，比如 `2023/06/20/22/24/26.000028` 、`2023_06_20_22_24_26.000028` 、`2023.06+20-22:24#26.000028` 。

2、从【时间戳、Cooltime、字符串】以外的其它类型创建时，创建器会先执行 `str(obj)` 将对象转化成字符串，然后按处理字符串的方式创建。

## 转化为其它类型

```python
t.date                            # '2023-06-20'
t.time                            # '22:24:26.000028'
t.datetime                        # '2023-06-20 22:24:26.000028'
float( t )                        # 1687271066.000028
int( t )                          # 1687271066
t.floor_time                      # '22:24:26'
t.floor_datetime                  # '2023-06-20 22:24:26'
t.strftime(r"%Y-%m-%d %H:%M:%S")  # '2023-06-20 22:24:26'
t.strftime(r"%Y_%m_%d %H_%M_%S")  # '2023_06_20 22_24_26'
```

## 比较大小

```python
# == 号
assert t3 == t5 == t6 == t11
assert t4 == t7

# > 号
assert t6 > t7 > t8 > t9 > t10

# < 号
assert t10 < t9 < t8 < t7 < t6

# >= 号
assert t3 >= t5 >= t6 >= t11
assert t4 >= t7
assert t6 >= t7 >= t8 >= t9 >= t10

# <= 号
assert t3 <= t5 <= t6 <= t11
assert t4 <= t7
assert t10 <= t9 <= t8 <= t7 <= t6
```

## 增量操作

```python
B = Cooltime('2023-06-20 22:24:26')
A = B.shift_copy(-3)  # 减3秒
C = B.shift_copy(3)   # 加3秒
print(A)              # '2023-06-20 22:24:23'
print(B)              # '2023-06-20 22:24:26'
print(C)              # '2023-06-20 22:24:29'
print(A < B < C)      # True
```
