"""
リポジトリパターンの実装
特定のリソースに対しデータベース機能をカプセル化し、ロジックをアプリケーションから分離することができる。
リポジトリ パターンは、アプリケーションとデータストア（例えば、データベース）との間の抽象層を提供するデザインパターンのこと。
"""

from databases import Database


class BaseRepository:
    """
    データベースコネクションへの参照を保持する
    """

    def __init__(self, db: Database) -> None:
        self.db = db
