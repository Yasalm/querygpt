from functools import wraps
from typing import Callable
from querygpt.core._database import InternalDatabase
from datetime import datetime


class Memory:
    """
    Usage:
        @Memory(internal_db=InternalDatabase())
        def chat_completion(messages=messages): ...
    """

    def __init__(
        self,
        internal_db: InternalDatabase = None,
    ):
        self.internal_db = internal_db

    def __call__(self, func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                response = func(*args, **kwargs)
                # print(
                #     {
                #         "response": response,
                #         "inputs": [{"name": str(i), "value": arg} for i, arg in enumerate(args)]
                #         + [
                #             {"name": str(k), "value": v} for k, v in kwargs.items()
                #         ],
                #         "error": "",
                #         "timestamp": datetime.now().isoformat(),
                #     }
                # )
                return response
            except Exception as e:
                raise e

        return wrapper