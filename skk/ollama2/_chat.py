from json import dumps as jsonDumps
from json import loads as jsonLoads
from pathlib import Path
from typing import List, Dict, Literal, Iterable
from base64 import b64encode, b64decode

import ollama

from ._chat_models import chat_models


class MsgBase:
    role_name: str
    text: str

    def __init__(self, text: str):
        self.text = text

    def __str__(self):
        return self.text

    def __iter__(self):
        yield "role", self.role_name
        yield "content", self.text


system_msg = type("system_msg", (MsgBase,), {"role_name": "system"})
user_msg = type("user_msg", (MsgBase,), {"role_name": "user"})
assistant_msg = type("assistant_msg", (MsgBase,), {"role_name": "assistant"})


class Temque:
    """ 一个先进先出, 可设置最大容量, 可固定元素的队列 """

    def __init__(self, maxlen: int = None):
        self.core: List[dict] = []
        self.maxlen = maxlen or float("inf")

    def _trim(self):
        core = self.core
        if len(core) > self.maxlen:
            dc = len(core) - self.maxlen
            indexes = []
            for i, x in enumerate(core):
                if not x["pin"]:
                    indexes.append(i)
                if len(indexes) == dc:
                    break
            for i in indexes[::-1]:
                core.pop(i)

    def add_many(self, *objs):
        for x in objs:
            self.core.append({"obj": x, "pin": False})
        self._trim()

    def __iter__(self):
        for x in self.core:
            yield x["obj"]

    def pin(self, *indexes):
        for i in indexes:
            self.core[i]["pin"] = True

    def unpin(self, *indexes):
        for i in indexes:
            self.core[i]["pin"] = False

    def copy(self):
        que = self.__class__(maxlen=self.maxlen)
        que.core = self.core.copy()
        return que

    def deepcopy(self):
        ...  # 创建这个方法是为了以代码提示的方式提醒用户: copy 方法是浅拷贝

    def __add__(self, obj: 'list|Temque'):
        que = self.copy()
        if isinstance(obj, self.__class__):
            que.core += obj.core
            que._trim()
        else:
            que.add_many(*obj)
        return que


class Chat:

    def __init__(
            self,
            model: chat_models,
            **chat_kwargs
    ):
        chat_kwargs['model'] = model
        msg_max_count = chat_kwargs.pop('msg_max_count', None)

        self._chat_kwargs = chat_kwargs
        self._messages = Temque(maxlen=msg_max_count)

    def request(self, content: str, **chat_kwargs):
        messages = [{"role": "user", "content": content}]
        response = ollama.chat(
            **{**self._chat_kwargs, **chat_kwargs, 'stream': False},
            messages = list(self._messages + messages)
        )
        assistant_content = response['message']['content']
        self._messages.add_many(*messages, {"role": "assistant", "content": assistant_content})
        return assistant_content

    def stream_request(self, content: str, **chat_kwargs):
        messages = [{"role": "user", "content": content}]
        response = ollama.chat(
            **{**self._chat_kwargs, **chat_kwargs, 'stream': True},
            messages = list(self._messages + messages)
        )
        assistant_content = []
        for chunk in response:
            chunk = (chunk.get('message') or {}).get('content')
            if chunk:
                yield chunk
                assistant_content.append(chunk)
        assistant_content = ''.join(assistant_content)
        self._messages.add_many(*messages, {"role": "assistant", "content": assistant_content})

    def fetch_messages(self):
        return list(self._messages)