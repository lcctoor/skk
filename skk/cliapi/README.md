# 描述

Cliapi 是一个专为 Python 初学者设计的 WEB 包，目的是让学者能够以非常简单的方式搭建一个 WEB 服务，进而提高对 Python 的兴趣，步入 Python 世界。

[源码](https://github.com/lcctoor/skk/tree/main/skk/cliapi)

# 安装

在命令行执行：

```
pip install skk
```

# 教程

## 运行一个服务

```python
import asyncio
from skk.cliapi import server, Request


async def get_1(request: Request):
    return 'Hi, Cliapi GET request successful!'  # get_1函数返回什么，客户端就会接收到什么


async def main():
    app1 = server(get=get_1, port=8887)  # port填多少，即代表让服务监听哪个端口
    await asyncio.Event().wait()

asyncio.run(main())
```

此时，你可以在浏览器中访问 [http://localhost:8887/](http://localhost:8887/) ，并看到页面上显示【Hi, Cliapi GET request successful!】。

说明：对于初学者，只需要理解：1、`get_1` 函数返回什么，客户端就会接收到什么。2、`port` 填多少，即代表让服务监听哪个端口。而并不需要明白其余的代码为什么要这样写，把它们视为固定用法即可。

### 参数说明

`request` 参数的常用属性及其描述：

| 方法和属性             | 描述                                                | 备注               |
| ---------------------- | --------------------------------------------------- | ------------------ |
| request.full_url()     | 完整的请求URL，包括协议、主机名和查询字符串         |                    |
| request.uri            | 请求的URI路径，包含查询字符串                       |                    |
| request.path.asstr()   | 请求的路径部分，不包括查询字符串                    | 下文的实战中需用到 |
| request.arguments      | 查询字符串参数的字典，键是参数名，值是参数值的列表  |                    |
| request.body           | 请求体的原始字节数据                                |                    |
| request.body_arguments | 请求体中的参数字典，键是参数名，值是参数值的列表    |                    |
| request.cookies        | 请求中的所有 cookie，键是 cookie 名，值是 cookie 值 |                    |
| request.headers        | 请求头的字典，键是头的名称，值是头的值              |                    |
| request.host           | 请求的主机名和端口                                  |                    |
| request.host_name      | 请求的主机名，不包含端口                            |                    |
| request.files          | 上传的文件字典，键是文件名，值是文件对象的列表      |                    |

`request.handler` 参数的常用属性及其描述：

| 方法和属性                        | 描述                          | 备注 |
| --------------------------------- | ----------------------------- | ---- |
| request.handler                   | 与该 request 对应的 handler |      |
| request.handler.redirect          | 重定向请求到指定的 URL        |      |
| request.handler.set_cookie        | 设置一个新的 cookie           |      |
| request.handler.clear_cookie      | 清除指定名称的 cookie         |      |
| request.handler.clear_all_cookies | 清除所有的 cookies            |      |
| request.handler.cookies           | 以字典形式获取所有的 cookies  |      |
| request.handler.set_header        | 设置一个 HTTP 响应头          |      |
| request.handler.add_header        | 添加一个 HTTP 响应头          |      |
| request.handler.clear_header      | 清除指定的 HTTP 响应头        |      |
| request.handler.set_status        | 设置 HTTP 响应状态码          |      |

## 完成《在线阅读四大名著》网站

当你能够正确部署一个服务后，可以尝试做一个《在线阅读四大名著》网站。在此计划中，你须要重新设计 `get_1` 函数的内容，并完成以下事项：

* 掌握 if 条件判断的语法。
* 收集四大名著（西游记、三国演义、水浒传、红楼梦）每部小说的前 2 章。
* 学会使用 pathlib.Path（Python标准库中的模块） 读取本地文本。
* 学会使用 request.path.asstr() 获取客户端（比如浏览器）请求的路径。
* 根据 request.path.asstr() 的值，利用任何有效的语法（比如 if 结构），使服务按照 `/{book}/pages/{n}` 的路径返回各小说的章节，例如：当访问 [http://localhost:8887/xiyouji/pages/1](http://localhost:8887/xiyouji/pages/1) 时，返回《西游记》的第一章。然后在浏览器上体验该网站。
* （可选）注册一个域名，购买一个云服务器，将服务部署在云端，然后在本地设备上体验云网站。

## 在浏览器上显示一张图片

我们已经知道了要返回一段文本的方式为：

```python
async def get_1(request: Request):
    return 'Hi, Cliapi GET request successful!'
```

那么如何返回一张 jpeg 图片呢？可能有学者【猜想】可以使用下面这种方式：

```python
from pathlib import Path

async def get_1(request: Request):
    return Path('_ig_.jpeg').read_bytes()
```

那么，这种方式究竟是否可行呢？

答案是：这种方式可行的概率非常低，因为浏览器一般不会自动根据内容推断类型（但具体情况取决于浏览器的特性，不排除极少数浏览器具备了根据内容推断类型的特性），我们需要告诉浏览器【该数据是一张图片】。

为了告诉浏览器【该数据是一张图片】，可以采取以下两种方式中的任意一种：

### 方式一

将 URL 的后缀设置为 `.jpeg` ，比如，设定当访问 [http://localhost:8887/xiyouji/cover.jpeg](http://localhost:8887/xiyouji/cover.jpeg) 时，返回一张图片。代码示例：

```python
from pathlib import Path

async def get_1(request: Request):
    urlpath = request.path.asstr()
  
    if urlpath == '/xiyouji/cover.jpeg':
        return Path('_ig_1.jpeg').read_bytes()
  
    if urlpath == '/shuihuzhuan/cover.jpeg':
        return Path('_ig_2.jpeg').read_bytes()
  
    return 'Hi, Cliapi GET request successful!'
```

### 方式二

`return` 时，返回两个值，其中第二个值将被用来告诉浏览器数据类型，代码示例：

```python
from pathlib import Path

async def get_1(request: Request):
    urlpath = request.path.asstr()

    if urlpath == '/xiyouji/cover':
        return Path('_ig_1.jpeg').read_bytes(), 'jpeg'
  
    if urlpath == '/shuihuzhuan/cover':
        return Path('_ig_2.jpeg').read_bytes(), 'jpeg'
  
    return 'Hi, Cliapi GET request successful!'
```

### 说明

1、以上两种方式适用于任何 MIME 数据类型，比如：jpeg、jpg、png、mp3、flac、mp4、avi、txt、html、js、css、json、zip、rar。

2、由于浏览器主要是用来处理 html 的，因此当你未指定数据类型时，大多数情况下浏览器会将数据视为 html 处理。由于这个原因，以下两种写法对于浏览器是等价的：

```python
async def get_1(request: Request):
    return 'Hi, Cliapi GET request successful!'
```

```python
async def get_1(request: Request):
    return 'Hi, Cliapi GET request successful!', 'html'
```

3、当指定数据类型为 `bytes` 时，浏览器会把该文件下载到本地。

## 为《在线阅读四大名著》网站添加含封面的目录

在此计划中，你须要完成以下事项：

* 学会使用 pathlib.Path 读取本地二进制文件，用来读取图片。
* 理解：在 html 中超链接的写法是 `<a href="{url}" target="_blank">{desc}</a>` ，例如 `<a href="http://localhost:8887/xiyouji/pages/1" target="_blank">西游记·第一章</a>` 。
* 理解：在 html 中图片的写法是 `<img src="{url}" style="width: 25rem;">` ，例如 `<img src="http://localhost:8887/xiyouji/cover.jpeg" style="width: 25rem;">` 。
* 学会 `'\n'.join(['a', 'b'])` 形式的字符串拼接方法，并将图片标签与章节超链接标签拼接成一个文本。
* 根据 request.path.asstr() 的值判断客户端想请求的是哪个资源。
* 使服务按照 /{book}/ 的路径返回各小说的目录，例如：当访问 [http://localhost:8887/xiyouji/](http://localhost:8887/xiyouji/) 时，返回《西游记》的目录。

## POST 方法示例

```python
import asyncio
from skk.cliapi import server, Request


async def get_1(request: Request):
    return 'Hi, Cliapi GET request successful!'

async def post_1(request: Request):
    return 'Hi, Cliapi POST request successful!'


async def main():
    app1 = server(get=get_1, post=post_1, port=8887)
    await asyncio.Event().wait()

asyncio.run(main())
```
