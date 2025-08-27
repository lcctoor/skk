import asyncio
from pathlib import Path
from skk.miumapp import App, allow_callpy


html = (Path(__file__).parent / 'demo.html').read_text('utf8')


class Introduce(App):
    async def main(self):
        # 创建一个窗口
        await self.create_window(html=html)

    @allow_callpy
    async def ComputeDays(self, year, month):
        ''' 接收年份和月份，返回当月天数 '''
        year, month = int(year), int(month)
        if (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0):  # 判断是否为闰年
            days = {1:31, 2:29, 3:31, 4:30, 5:31, 6:30, 7:31, 8:31, 9:30, 10:31, 11:30, 12:31}
        else:
            days = {1:31, 2:28, 3:31, 4:30, 5:31, 6:30, 7:31, 8:31, 9:30, 10:31, 11:30, 12:31}
        num = days[month]
        return str(num)

    @allow_callpy
    async def CreatTempWindow_8_seconds(self):
        ''' 创建 1 个新窗口，并于 8 秒后自动关闭 '''
        window = await self.create_window(html=html)
        await asyncio.sleep(8)  # 8秒后自动关闭
        await window.close()

    @allow_callpy
    async def CreatTempWindow(self):
        ''' 创建 1 个新窗口，不自动关闭 '''
        await self.create_window(html=html)