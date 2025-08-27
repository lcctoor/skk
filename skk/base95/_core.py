import math
from collections import deque


# get_unit
def get_unit(radix: int):
    assert 2 <= radix <= 95
    result = []
    for byte_unit_length in range(1, min(96, radix + 1)):  # 1 <= byte_unit_length <= 95
        char_unit_length = math.ceil( math.log(256 ** byte_unit_length, radix) )
        result.append((char_unit_length / byte_unit_length, char_unit_length, byte_unit_length))
    result.sort()
    ratio, char_unit_length, byte_unit_length = result[0]
    return char_unit_length, byte_unit_length, round(ratio, 10)

assert get_unit(50) == (61, 43, 1.4186046512)  # 校验


# global_chars
global_chars = r'''0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_~!#$%&@^?=*+-.:,;<>[]{}()|/`'"\ '''
char_indexes = dict(zip(global_chars, range(len(global_chars))))
assert len(global_chars) == len(set(global_chars)) == 95
assert set(global_chars.encode('utf8')) == set(range(32, 127))


# BaseEncoding
EncodingTypes = {}

class BaseEncoding:
    radix: int
    chars: str
    char_unit_length: int
    byte_unit_length: int

    def __new__(cls, radix: int):
        if self := EncodingTypes.get(radix):
            return self
        else:
            assert 2 <= radix <= 95
            self = object.__new__(cls)
            self.radix = radix
            self.chars = global_chars[:radix]
            self.char_unit_length, self.byte_unit_length, ratio = get_unit(radix)
            EncodingTypes[radix] = self
            return self
    
    def encode(self, bytestring: bytes) -> str:
        radix, chars, char_unit, byte_unit = self.radix, self.chars, self.char_unit_length, self.byte_unit_length
        group_count, remainder = divmod(len(bytestring), byte_unit)
        if remainder:
            padding_length = byte_unit - remainder
            bytestring = bytes([0] * padding_length) + bytestring
            group_count += 1
        else:
            padding_length = 0
        result_string = []
        for gi in range(group_count):
            xbytes = bytestring[byte_unit * gi: byte_unit * (gi + 1)]
            x_result = deque()
            num = int.from_bytes(xbytes, 'big')  # 转换字节为大整数
            for _ in range(char_unit):  # 确保每组都是 char_unit 个字符
                num, i = divmod(num, radix)
                x_result.appendleft(chars[i])
            result_string += x_result
        result_string.append( global_chars[padding_length] )
        return ''.join(result_string)

    def decode(self, encoded_text: str) -> bytes:
        radix, chars, char_unit, byte_unit = self.radix, self.chars, self.char_unit_length, self.byte_unit_length
        padding_length = char_indexes[encoded_text[-1]]
        encoded_text = encoded_text[:-1]
        result_bytes = bytearray()
        group_count = len(encoded_text) // char_unit
        for gi in range(group_count):
            group_text = encoded_text[char_unit * gi: char_unit * (gi + 1)]
            # 从字符转换回大整数
            num = 0
            for char in group_text:
                num = num * radix + char_indexes[char]
            group_bytes = num.to_bytes(byte_unit, 'big')  # 指定字节数为 byte_unit, 以避免缺失高位零
            result_bytes.extend(group_bytes)
        if padding_length:
            result_bytes = result_bytes[padding_length:]
        return bytes(result_bytes)


# 常用进制
base10 = BaseEncoding(10)  # 仅使用 `0~9` 这 10 个字符
base62 = BaseEncoding(62)  # 仅使用 `0~9、a~z、A~Z` 这 62 个字符
base90 = BaseEncoding(90)  # 使用除【单引号、双引号、反引号(`)、空格、反斜杠】这 5 个可能影响阅读体验的字符以外的 90 个字符
base95 = BaseEncoding(95)  # 使用了 ASCII 中的全部（95 个，含空格）可见字符