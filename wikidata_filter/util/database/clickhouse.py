"""ClickHouse数据库操作封装"""
import time
import json
import traceback

try:
    from clickhouse_driver import Client
except:
    print('install clickhouse_driver first!')
    raise "clickhouse_driver not installed"

from .rdb_base import RDBBase


class CK(RDBBase):
    def __init__(self, host: str = 'localhost',
                 tcp_port: int = 9000,
                 username: str = 'default',
                 password: str = '',
                 database: str = 'default',
                 **kwargs):
        super().__init__(database=database, **kwargs)
        self.connect_params = dict(host=host,
                                   port=tcp_port,
                                   database=database,
                                   user=username,
                                   password=password,
                                   send_receive_timeout=20)
        self.client = Client(**self.connect_params)

    def make_gen(self, it):
        cols = None
        for row in it:
            if cols is None:
                cols = row
                continue
            yield {cols[i][0]: row[i] for i in range(len(row))}

    def fetch_cursor(self, query: str):
        return self.make_gen(self.client.execute_iter(query, with_column_types=True))

    def fetchall(self, query: str, fmt="json"):
        return self.fetch_cursor(query)
        # return self.make_gen(self.client.execute(query, with_column_types=True))

    def list_tables(self, db: str = None):
        sql = f"show tables"
        if db:
            sql = f"show tables in `{db}`"
        return [row[0] for row in self.client.execute(sql)]

    def upsert(self, items: dict or list,
               write_mode: str = "upsert",
               table: str = None,
               cluster: str = None,
               retry_times: int = 3,
               ignore_error: bool = False,
               **kwargs):
        table = table or self.table
        if not isinstance(items, list):
            items = [items]

        cluster = f'on cluster {cluster}' if cluster else ''

        json_data = [json.dumps(row, ensure_ascii=False) for row in items]
        sql = f"insert into {table} {cluster} format JSONEachRow {','.join(json_data)}"
        try:
            self.client.execute(sql)
            return True
        except Exception as e:
            # 失败后等待、重试{retry_times}次
            traceback.print_exc()
            time.sleep(10)
            for i in range(retry_times):
                try:
                    self.client = Client(**self.connect_params)
                    self.client.execute(sql)
                    return True
                except Exception as e2:
                    pass
                    # print(e2)
                print('reconnect in 5 minutes')
                time.sleep(300)
            print('clickhouse operation failed for 3 times, giveing up')
            if ignore_error:
                return False
            raise e
