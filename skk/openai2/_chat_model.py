from typing import Literal


if 0 == 1:
    from openai.types.chat_model import ChatModel  # 用途：点击跳转


chat_models = Literal[
    "o1",
    "o1-mini",
    "gpt-4o",
    "gpt-4o-mini",
    "gpt-4-turbo",
    "gpt-4",
    "gpt-4-32k",
    "gpt-3.5-turbo",
    "gpt-3.5-turbo-16k",
    "dall-e-3",
    "dall-e-2",
]