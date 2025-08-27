# 描述

一个优雅的 mysql ORM ，无须做模型映射。

[源码](https://github.com/lcctoor/skk/tree/main/skk/mysql)

# 教程

本文将以简洁的方式向你介绍核心知识，而不会让你被繁琐的术语所淹没。

## 安装

```bash
pip install skk
```

## 导入

```python
import pymysql, aiomysql
from skk.mysql import ORM, mc
```

## 创建ORM

```python
class ORM_2(ORM):

    def mkconn(self):  # 定义同步连接器
        return pymysql.connect(
            host = 'localhost',
            port = 3306,
            user = 'root',
            password = '123456789'
        )
  
    async def amkconn(self):  # 定义异步连接器
        return await aiomysql.connect(
            host = 'localhost',
            port = 3306,
            user = 'root',
            password = '123456789'
        )

orm = ORM_2()          # 账户ORM
db = orm['泉州市']      # 库ORM
sheet = db['希望小学']  # 表ORM
```

## 基础功能 —— 增、查、改、删

【增、查、改、删】的同步方法名称分别为：insert、select、update、delete 。

对应的异步方法名称为各同步方法名前加 `a` ，即：ainsert、aselect、aupdate、adelete 。

### 示例

```python
row1 = {'姓名': '小一', '年龄': 11, '性别': '男', '视力': 4.5, '签到日期': '2023-01-11'}
row2 = {'姓名': '小二', '年龄': 12, '性别': '男', '视力': 4.6, '签到日期': '2023-01-12'}
row3 = {'姓名': '小三', '年龄': 13, '性别': '女', '视力': 4.7, '签到日期': '2023-01-13'}
row4 = {'姓名': '小四', '年龄': 14, '性别': '女', '视力': 4.8, '签到日期': '2023-01-14'}
row5 = {'姓名': '小五', '年龄': 15, '性别': '男', '视力': 4.9, '签到日期': '2023-01-15'}
row6 = {'姓名': '小六', '年龄': 16, '性别': '女', '视力': 5.0, '签到日期': '2023-01-16'}
```

|            | 同步方式                      | 异步方式                                                 |
| :---------: | ----------------------------- | -------------------------------------------------------- |
| 增（1 条） | sheet.insert( row1 )          | await sheet.ainsert( row2 )          |
| 增（批量） | sheet.insert( row3, row4 )    | await sheet.ainsert( row5, row6 )    |
|     查     | sheet.select( )               | await sheet.aselect( )               |
|     改     | sheet.update( {'年龄': 100} ) | await sheet.aupdate( {'年龄': 200} ) |
|     删     | sheet.delete( )               | await sheet.adelete( )               |

### 新增时，查看分配到的主键：

```python
r1 = sheet.insert( row1 )
r2 = await sheet.ainsert( row2 )

r1.lastrowid
r2.lastrowid
```

## 注：下文中所有示例都同时支持同步方式和异步方式，将同步示例中的 insert、delete、update、select 替换为 ainsert、adelete、aupdate、aselect 即为异步方式，当然，须加上 await 前缀。

## 条件筛选

### 示例一：理解条件筛选的基本范式

筛选【年龄>13，且视力≧4.6，且性别为女】的数据，并进行查改删：

**查询**：`sheet[mc.年龄 > 13][mc.视力 >= 4.6][mc.性别 == '女'].select( )`

**修改**：`sheet[mc.年龄 > 13][mc.视力 >= 4.6][mc.性别 == '女'].update( {'年级':'初一', '爱好':'画画,跳绳'} )`

**删除**：`sheet[mc.年龄 > 13][mc.视力 >= 4.6][mc.性别 == '女'].delete( )`

### 筛选操作清单

| **代码**                                                                 | **解释**                   |
| ------------------------------------------------------------------------------ | -------------------------------- |
| mc.年龄 > 10                                                                   | 大于                             |
| mc.年龄 >= 10                                                                  | 大于或等于                       |
| mc.年龄 < 10                                                                   | 小于                             |
| mc.年龄 <= 10                                                                  | 小于或等于                       |
| mc.年龄 == 10                                                                  | 等于                             |
| mc.年龄 != 10                                                                  | 不等于                           |
| mc.年级.isin( '初三', '高二' )                                                 | 若字段值是传入值的成员，则符合   |
| mc.年龄.notin( 10, 30, 45 )                                                    | 若字段值不是传入值的成员，则符合 |
| mc.姓名.re( '小' )                                                             | 正则匹配                         |
| \[mc.年龄 > 3\][mc.年龄 < 100]                                                 | 交集（方式一）                   |
| [ (mc.年龄 > 3) & (mc.年龄 < 100) ]                                            | 交集（方式二）                   |
| [(mc.年龄<30)&#124; (mc.年龄>30) &#124; (mc.年龄==30) &#124; (mc.年龄==None)] | 并集                             |
| [ (mc.年龄 > 3) - (mc.年龄 > 100) ]                                            | 差集                             |
| [ ~(mc.年龄 > 100) ]                                                           | 补集                             |

注：

1、isin、notin 的传入值都不必是同类型的数据，以 isin 为例：可以这样使用：mc.tag.isin( 3, 3.5, '学生', None )  ，传入值含有 int、float、str、NoneType 等多种类型。

2、成员运算符未传入任何值时的处理方式：

| **代码**   | **处理方式** |
| ---------------- | ------------------ |
| mc.年级.isin( )  | 所有数据都 不符合  |
| mc.年级.notin( ) | 所有数据都 符合    |

3、四种集合运算可以相互嵌套，且可以无限嵌套。

### 示例二：理解并集、交集、差集的使用

筛选【年龄>13或视力≧4.6、且姓名含有‘小’、且喜欢足球但不喜欢画画】的数据：

**查询**：`sheet[(mc.年龄>13) | (mc.视力>=4.6)][mc.姓名.re('小')][mc.爱好.re('足球') - mc.爱好.re('画画')].select( )`

**修改**：`sheet[(mc.年龄>13) | (mc.视力>=4.6)][mc.姓名.re('小')][mc.爱好.re('足球') - mc.爱好.re('画画')].update( {'年级':'初三'} )`

**删除**：`sheet[(mc.年龄>13) | (mc.视力>=4.6)][mc.姓名.re('小')][mc.爱好.re('足球') - mc.爱好.re('画画')].delete( )`

## 特殊字段名的表示方法

MySQL 支持各种特殊的字段名，如：数字、符号、emoji 表情，这些字符在 Python 中不是合法变量名，因此使用  mc.1、mc.+  等格式会报错，可用  mc['1']、mc['+']、mc['👈']  这种格式代替。

## 切片

1、切片格式为  [start: stop: step]  ，start 表示从哪条开始，stop 表示到哪条停止，step 表示步长。

2、start 和 stop

* 当为正值时，表示正序第 x 条，例如：1 表示第 1 条、2 表示第 2 条。
* 当为负值时，表示倒数第 x 条，例如：-1 表示倒数第 1 条、-2 表示倒数第 2 条。
* 不可为 0 。

3、step

* 须为正整数。
* 当 step ≧ 2  时表示间隔式切片。
* 当 step = 1 时可省略 `: step` ，即：[start: stop] 等价于 [start: stop: 1] 。

### 示例

```python
sheet[过滤器]...[过滤器][:].select()                    # 查询符合条件的全部数据
sheet[过滤器]...[过滤器][:].delete()                    # 删除符合条件的全部数据
sheet[过滤器]...[过滤器][:].update({'年级':'初一'})      # 修改符合条件的全部数据

sheet[过滤器]...[过滤器][1].select()                    # 查询符合条件的第1条
sheet[过滤器]...[过滤器][1].delete()                    # 删除符合条件的第1条
sheet[过滤器]...[过滤器][1].update({'年级':'初一'})      # 修改符合条件的第1条

sheet[过滤器]...[过滤器][3:7].select()                  # 查询符合条件的第3~7条
sheet[过滤器]...[过滤器][3:7].delete()                  # 删除符合条件的第3~7条
sheet[过滤器]...[过滤器][3:7].update({'年级':'初一'})    # 修改符合条件的第3~7条

sheet[过滤器]...[过滤器][3:7:2].select()                # 查询符合条件的第3、5、7条
sheet[过滤器]...[过滤器][3:7:2].delete()                # 删除符合条件的第3、5、7条
sheet[过滤器]...[过滤器][3:7:2].update({'年级':'初一'})  # 修改符合条件的第3、5、7条
```

值得注意的地方：  [3: 8: 2]  操作第  3、5、7  条，而  [8: 3: 2]  操作第  8、6、4  条。

更多示例：

```python
[:]           # 所有数据
[1:-1]        # 所有数据
[-1:1]        # 所有数据（逆序）
[1:]          # 所有数据
[:1000]       # 第1条 ~ 第1000条
[:-1000]      # 第1条 ~ 倒数第1000条
[100:200]     # 第100条 ~ 第200条
[200:100]     # 第200条 ~ 第100条
[-300:-2]     # 倒数第300条 ~ 倒数第2条
[50:-2]       # 第50条 ~ 倒数第2条
[250:]        # 第250条 ~ 最后1条
[-250:]       # 倒数第250条 ~ 最后1条
[1]           # 第1条
[-1]          # 最后1条
[::3]         # 以3为间距, 间隔操作所有数据
[100:200:4]   # 以4为间距, 间隔操作第100条 ~ 第200条
```

## 字段提示

变量 mc 无字段提示功能，输入‘mc.’后，编辑器不会提示可选字段。

为了获得字段提示功能，可自建一个‘mc2’：

```python
class mc2(mc):
    姓名 = 年龄 = 签到日期 = 年级 = 爱好 = None

await sheet[mc.姓名 == '小王'][mc2.年龄 > 10].aselect()
```

注：

1、mc2 与 mc 用法完全一致，可混用。

2、mc2 设置字段提示后，仅具备提示效果，而不产生任何实际约束。

## 排序

对所有年级为“高一”的数据，优先按年龄降序，其次按姓名升序，排序后返回第 2\~4 条数据：

```python
sheet[mc.年级=='高一'].order(年龄=False, 姓名=True)[2:4].select()
```

有趣的，以下两行代码的返回结果相同：

```python
sheet[mc.年级=='高一'].order(年龄=True)[1:-1].select()

sheet[mc.年级=='高一'].order(年龄=False)[-1:1].select()
```

解释：order(年龄=False) 表示按年龄降序，[-1:1] 表示逆序切片，产生了类似‘负负得正’的效果。

注：

1、筛选器、切片器、排序器、限定字段器的位置可任意，位置不影响其效果。当然，它们都应该在 sheet 之后，且在 select/update/delete 之前。

2、可反复排序，select/update/delete 时是根据最后一次指定的顺序提取数据。以下代码最终是按年龄降序后提取数据：

```python
sheet.order(年龄=True, 姓名=False).order(年龄=False).select()
```

3、若想取消排序，则再次调用 order 方法，但不传入任何值。

```python
sheet.order(年龄=True, 姓名=False).order().select()
```

## 限定字段

只返回姓名、年龄这两个字段：

```python
sheet[mc.年级=='高一']['姓名','年龄'].select()
```

注：

1、限定字段只对 select 有作用，对 update/delete 无作用但不会报错。

2、筛选器、切片器、排序器、限定字段器的位置可任意，位置不影响其效果。当然，它们都应该在 sheet 之后，且在 select/update/delete 之前。

3、可反复限定字段，查询时是根据最后一次指定的字段提取数据。以下代码返回结果中只有‘年龄’字段：

```python
sheet[mc.年级=='高一']['姓名']['年龄'].select()
```

4、若想恢复提取全部字段，则限定字段为 `'*'` ，`'*'` 即代表“全部字段”。

```python
sheet[mc.年级=='高一']['姓名']['*'].select()
```

## 统计

|                        | 同步方式                    | 异步方式                                               |
| ---------------------- | --------------------------- | ------------------------------------------------------ |
| 统计库的数量           | orm.len( )                  | await orm.alen( )                  |
| 统计表的数量           | db.len( )                   | await db.alen( )                   |
| 统计行的数量           | sheet.len( )                | await sheet.alen( )                |
| 统计符合条件的行的数量 | sheet[ mc.age > 8 ].len( ) | await sheet[ mc.age > 8 ].alen( ) |
| 获取库名清单           | orm.get_db_names( )         | await orm.aget_db_names( )         |
| 获取表名清单           | db.get_sheet_names( )       | await db.aget_sheet_names( )       |
| 获取主键               | sheet.get_pk( )             | await sheet.aget_pk( )             |

## 迭代所有 库ORM 和 表ORM

```python
# 同步方式迭代
for db in orm:
    for sheet in db:
        print(sheet.sheet_name)

# 异步方式迭代
async for db in orm:
    async for sheet in db:
        print(sheet.sheet_name)
```

## 执行原生 SQL 语句

```python
data, cursor = sheet.execute('select 姓名 from 希望小学 limit 1')
data  # >>> [{'姓名': '小一'}]

data, cursor = sheet.execute('update 希望小学 set 爱好="编程" limit 3')
cursor.rowcount  # >>> 3

data, cursor = sheet.execute("delete from 希望小学 limit 2")
cursor.rowcount  # >>> 2

data, cursor = sheet.executemany( 'insert into 希望小学(姓名, 年龄) values (%s, %s)', [('小七', 17), ('小八', 18)] )
cursor.lastrowid  # >>> 8
```

## 按主键修改

```python
data = {
    2: {'姓名':'xiao二', '年龄':20},
    3: {'年级':'三年级'},
    4: {'id':400, '视力':4.0}
}

sheet.update_by_pk(data)
```

## 用自定义函数修改

```python
def handler(row: dict):
    row['年龄'] += 1  # 年龄统一加1岁
    if row['爱好'] == '打篮球':
        row['身高'] = 180
    elif row['爱好'] == '玩手机':
        row['视力'] = 1.8
    row['姓名'] = row['姓名'].replace('小', 'xiao')

sheet[mc.年龄>11][:].apply(handler)  # 修改符合条件的所有数据
sheet[mc.年龄>11][2:-2].apply(handler)  # 修改符合条件的第2条~倒数第2条
sheet[mc.年龄>11][2].apply(handler)  # 修改符合条件的第2条数据
```

注：

1、传递给 apply 方法的函数必须接收且仅接收 1 个参数，参数名可以不是‘row’。

2、可只提取需要的字段以提升性能。比如在上例中，handler 函数只使用到年龄、爱好、姓名这3个字段，可改为 `sheet[mc.年龄>11]['年龄', '爱好', '姓名'][:].apply(handler)` 以提高性能。

3、ORM 会自动对比修改前与修改后的数据差异，只提交差异部分到数据库。

## 调用 MySQL 函数

### 示例一

在查询、删除、修改的筛选条件中调用 year 函数

```python
from skk.mysql import mf

sheet[mf.year('签到日期') == 2023][:].select()
sheet[mf.year('签到日期') == 2029][:].delete()
sheet[mf.year('签到日期') == 2023][:].update({'性别':'女'})
```

### 示例二

在修改中作为新值

```python
sheet[:].update({'备注': '签到日期'}) # 修改为'签到日期'这个字符串
sheet[:].update({'备注': mc.签到日期}) # 修改为各自的'签到日期'字段的值
sheet[:].update({'备注': mf.year('签到日期')}) # 修改为各自的'签到日期'字段的值经year处理后的值
```

使用该语法可调用mysql的任意函数。

### MySQL 函数名提示

ORM 已添加了（20几个）mysql 常用函数的函数名提示，输入‘mf.’后，编辑器会提示可选函数名。如有需要，可添加更多提示：

```python
class mf2(mf):
    reverse = length = lower = upper = None

sheet[mf2.reverse('姓名') == '二小'][:].select()
```

注：

1、mf2 与 mf 用法完全一致，可混用。

2、mf2 设置函数名提示后，仅具备提示效果，而不产生任何实际约束。
