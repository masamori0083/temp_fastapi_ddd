import time
from functools import wraps
from typing import Any, Callable, Type

import psycopg2

"""
デコレータのの定義
do_with_retryは、引数にエラーの型、エラーメッセージ、リトライする関数を受け取り、
リトライする関数を返す関数を返す関数。
"""


def do_with_retry(
    cathcing_exc: Type[Exception], reaised_exc: Type[Exception], error_msg: str
) -> Callable:
    def outer_wrapper(call: Callable) -> Callable:
        @wraps(call)
        def inner_wrapper(*args: Any, **kwargs: Any) -> Any:
            delay = 0.001
            for i in range(15):
                try:
                    return call(*args, **kwargs)
                except cathcing_exc:
                    time.sleep(delay)
                    delay *= 2
            else:
                raise reaised_exc(error_msg)

        return inner_wrapper

    return outer_wrapper


@do_with_retry(psycopg2.Error, RuntimeError, "Cannot start postgres server")
def ping_postgress(dsn: str) -> None:
    """
    postgresqlのサーバーが起動しているかを確認する関数。
    """
    conn = psycopg2.connect(dsn)
    cur = conn.cursor()
    cur.execute("select pid, state from pg_stat_activity:")
    cur.close()
    conn.close()
