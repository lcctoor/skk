# 描述

Base95 是一种用 95 个可见的 ASCII 字符（含空格）表示任意二进制数据的编码方法。

该实现使用了从空格（ASCII 32）到波浪符（ASCII 126）这 95 个字符来编码二进制数据，编码后的信息密度高于 Base64 编码。

[源码](https://github.com/lcctoor/skk/tree/main/skk/base95)

# 安装

```bash
pip install skk
```

# 教程

本文将以简洁的方式向你介绍核心知识，而不会让你被繁琐的术语所淹没。

## 导入

```python
from skk.base95 import BaseEncoding
```

## 编码

```python
base95 = BaseEncoding(95)

bytestring: bytes = '黄河之水天上来'.encode('utf8')  # 建构一个字节串

encoded_text: str = base95.encode(bytestring)  # 编码成 Base95
```

## 解码

```python
decoded_bytes: bytes = base95.decode(encoded_text)  # 解码成字节串
```

## 任意进制编码

通过上面的例子，你可能会想：使用 `BaseEncoding(n)` 是不是可以创建其它进制的编码方法？答案是：是的。

你可以通过 `BaseEncoding(n)` 方式创建 2 ~ 95 进制的编码方法。例如：

```python
base2 = BaseEncoding(2)
base50 = BaseEncoding(50)
base80 = BaseEncoding(80)
```

## 直接导入常用的编码方法

对于一些具有特别意义的编码方法，我们提供了直接导入的方式，而无须使用 `BaseEncoding(n)` 方式创建。

这些编码方法是：

* base95：使用了 ASCII 中的全部（95 个，含空格）可见字符；
* base90：使用除【单引号、双引号、反引号(`)、空格、反斜杠】这 5 个可能影响阅读体验的字符以外的 90 个字符；
* base62：仅使用 `0~9、a~z、A~Z` 这 62 个字符；
* base10：仅使用 `0~9` 这 10 个字符。

你可以直接导入并使用这些编码方法，例如：

```python
from base95 import base90

base90.encode('黄河之水天上来'.encode('utf8'))
```

当然，你仍然可以通过 `BaseEncoding(90)` 这种方式使用这些编码方法，这两种方式是等价的。
