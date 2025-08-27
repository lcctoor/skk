# 有颜色版

### 效果

<h1 align="center"><img src="有颜色版.png" width="44.72%"></h1>

### 代码

```python
next = input('''游戏规则:
根据棋盘上的数字提示，输入落棋坐标，按“Enter”键确认。
玩家棋子以 O 表示，苏轼棋子以 X 表示。
玩家先落子，先在棋盘上连成连续的五颗棋子者为胜。
>>>''')
next = input("按“Enter”键开始游戏\n>>>")

#  游戏代码
count = []
z = range(119,456)
u = list(range(1,553))
s = [20] * 552
x, a, b, c, d, k = [[1] * 552 for i in range(6)]
while max(a+b+c+d) < 24300000:
    #  电脑落棋
    for i in z:
        s[i] = ( a[i]+a[i-1]+a[i-2]+a[i-3]+a[i-4] + b[i]+b[i-23]+b[i-46]+b[i-69]+b[i-92] +
                 c[i]+c[i-22]+c[i-44]+c[i-66]+c[i-88] + d[i]+d[i-24]+d[i-48]+d[i-72]+d[i-96] )
    for f in range(0,552): k[f] = s[f]
    for h in count: k[h] = 0
    x[k.index(max(k))] = 0
    u[k.index(max(k))] = "\033[32;1m X \033[0m"
    count.append(k.index(max(k)))
    #  打印棋盘
    print(''.join("  ".join(str(u[23*w+v]) for v in range(4,19)) + "\n\n" for w in range(5,20)))
    #  玩家落棋
    user = int(input("请选择：")) - 1
    x[user] = 30
    u[user] = "\033[33;1m O \033[0m"
    count.append(user)
    for j in z:
        a[j] = x[j] * x[j+1] * x[j+2] * x[j+3] * x[j+4]
        b[j] = x[j] * x[j+23] * x[j+46] * x[j+69] * x[j+92]
        c[j] = x[j] * x[j+22] * x[j+44] * x[j+66] * x[j+88]
        d[j] = x[j] * x[j+24] * x[j+48] * x[j+72] * x[j+96]
print(''.join("  ".join(str(u[23*w+v]) for v in range(4,19)) + "\n\n" for w in range(5,20)))
print(f"恭喜，您已取得胜利！总共下了{len(count)//2}步.\n\n")
```

# 无颜色版

若有颜色版的棋盘乱码，可使用无颜色版。

### 效果

<h1 align="center"><img src="无颜色版.png" width="44.72%"></h1>

### 代码

```python
next = input('''游戏规则:
根据棋盘上的数字提示，输入落棋坐标，按“Enter”键确认。
玩家棋子以 O 表示，苏轼棋子以 X 表示。
玩家先落子，先在棋盘上连成连续的五颗棋子者为胜。
>>>''')
next = input("按“Enter”键开始游戏\n>>>")

#  游戏代码
count = []
z = range(119,456)
u = list(range(1,553))
s = [20] * 552
x, a, b, c, d, k = [[1] * 552 for i in range(6)]
while max(a+b+c+d) < 24300000:
    #  电脑落棋
    for i in z:
        s[i] = ( a[i]+a[i-1]+a[i-2]+a[i-3]+a[i-4] + b[i]+b[i-23]+b[i-46]+b[i-69]+b[i-92] +
                 c[i]+c[i-22]+c[i-44]+c[i-66]+c[i-88] + d[i]+d[i-24]+d[i-48]+d[i-72]+d[i-96] )
    for f in range(0,552): k[f] = s[f]
    for h in count: k[h] = 0
    x[k.index(max(k))] = 0
    u[k.index(max(k))] = " X "
    count.append(k.index(max(k)))
    #  打印棋盘
    print(''.join("  ".join(str(u[23*w+v]) for v in range(4,19)) + "\n\n" for w in range(5,20)))
    #  玩家落棋
    user = int(input("请选择：")) - 1
    x[user] = 30
    u[user] = " O "
    count.append(user)
    for j in z:
        a[j] = x[j] * x[j+1] * x[j+2] * x[j+3] * x[j+4]
        b[j] = x[j] * x[j+23] * x[j+46] * x[j+69] * x[j+92]
        c[j] = x[j] * x[j+22] * x[j+44] * x[j+66] * x[j+88]
        d[j] = x[j] * x[j+24] * x[j+48] * x[j+72] * x[j+96]
print(''.join("  ".join(str(u[23*w+v]) for v in range(4,19)) + "\n\n" for w in range(5,20)))
print(f"恭喜，您已取得胜利！总共下了{len(count)//2}步.\n\n")
```
