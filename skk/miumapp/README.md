# 描述

一个使用 Python + HTML 开发桌面 GUI 应用的框架，支持 Windows、Mac、Linux 平台。

功能：

* 可在 HTML 中调用后端的 Python 函数。
* 可在 Python 上下文中调用窗口内的 JavaScript 对象。
* 可在 Python 上下文中对窗口发送操纵指令，执行包括但不限于：URL跳转、关闭窗口、JS注入、最大化等操作。
* 可开启多个窗口。
* 由于每个窗口可与 Python 双向调用，因此不同窗口之间可通过【窗口A → Python → 窗口B】的途径相互调用。
* 可指定窗口标题。
* 可指定窗口图标。
* 可通过传递 URL 或 HTML 文本这两种数据之一来决定窗口内容。
* 可通过 Nuitka 打包成可移植二进制文件。

我们所采用的技术栈组合是经过深思熟虑的，通过结合 **Python** 与  **HTML** 这两种高效、灵活、易用的技术栈，意味着你正在选择一个能够大大减少开发时间、简化开发流程、拥有丰富的第三方扩展的解决方案。与其它工具相比，我们的优势在于对新技术的快速适应、更为强大的社区支持，以及持续的更新和改进。

[源码](https://github.com/lcctoor/skk/tree/main/skk/miumapp)

# 安装

```bash
pip install pyppeteer
pip install skk
```

# 检查是否安装成功

运行内置Demo：

```python
import asyncio
from miumapp.demo import Introduce

asyncio.run( Introduce().start() )
```

运行后，若显示出与图片 [效果图](static/DemoUI.png) 所示一致的效果，则说明安装成功。

# 教程

本文将以简洁的方式向你介绍核心知识，而不会让你被繁琐的术语所淹没。

## 导入

```python
import asyncio
from skk.miumapp import App, allow_callpy
```

## 创建 APP

```python
class my_app(App):
    async def main(self):
        ...

asyncio.run( my_app().start() )
```

由于我们在主任务 main 中未定义任何代码，因此这个 APP 是一个空 APP，运行后看不到任何效果。

## 创建窗口

```python
class my_app(App):
  
    async def main(self):
        html = 'Hello, miumapp !'
        await self.create_window(html=html)

asyncio.run( my_app().start() )
```

此时，我们将能看到屏幕上打开了一个窗口，其内容为“Hello, miumapp !”。

### 指定窗口内容源

可通过传递 HTML 文本或 URL 链接这两种数据之一来决定窗口内容，示例：

```python
await self.create_window(html='你好!')
```

```python
await self.create_window(url='https://www.baidu.com/')
```

### 指定窗口标题

```python
await self.create_window(html='你好!', title='第一个窗口')
```

## 关闭窗口

可通过对窗口对象执行 `await window.close()` 或者点击窗口右上角的 `×` 图标来关闭窗口。

## 在 HTML 中调用 Python 函数

使用 allow_callpy 装饰的 Python 异步函数将能够在 HTML 中被调用，例如：

```python
class my_app(App):
  
    async def main(self):
        html = 'Hello, miumapp !'
        await self.create_window(html=html)

    @allow_callpy
    async def addition(self, a, b):
        return a + b

    async def sub(self, a, b):
        return a - b

asyncio.run( my_app().start() )
```

在这个例子中，方法 sub 只能在 Python 层面被调用，而方法 addition 既能在 Python 层面被调用，也能在 HTML 中被调用。

在 HTML 中调用 addition 方法：

```JavaScript
async function sum() {
    let a = parseInt( document.getElementById('a').value )  // 30
    let b = parseInt( document.getElementById('b').value )  // 50
    let kwargs = {a:a, b:b}
    let result = await miumapp.callpy(method='addition', kwargs=kwargs)
    console.log(result)  // {"code":0, "msg":"", "data":80}
}
```

## 在 Python 中调用 JavaScript 对象

### 一些示例

执行 JavaScript 代码：

```python
await window.evaluate("document.title = '第一个APP'", force_expr=True)
```

```python
await window.evaluate("alert(1)", force_expr=True)
```

获取变量值：

```python
CityName = await window.evaluate("CityName")  # 假设窗口中有一个叫 CityName 的变量
print(CityName)  # >>> '北京市'
```

调用函数并获取返回值：

```python
city_name = await window.evaluate("get_city_name()", force_expr=True)  # 假设窗口中有一个叫 get_city_name 的函数
print(city_name)  # >>> '上海市'
```

由于 window 对象继承自 pyppeteer.page.Page，因此 window.evaluate 支持 pyppeteer.page.Page.evaluate 的所有用法。关于 window.evaluate 的更多用法，请参考 [pyppeteer.page.Page.evaluate](https://pyppeteer.github.io/pyppeteer/reference.html#pyppeteer.page.Page.evaluate) 。

## window 对象的更多方法

由于 window 对象继承自 pyppeteer.page.Page，因此 window 支持 pyppeteer.page.Page 的所有方法，例如页面跳转、点击按钮、输入等。关于 window 的更多方法，请参考 [pyppeteer.page.Page](https://pyppeteer.github.io/pyppeteer/reference.html#pyppeteer.page.Page) 。
