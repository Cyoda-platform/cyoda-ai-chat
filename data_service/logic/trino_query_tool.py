from langchain.tools import Tool

class TrinoQueryTool(Tool):
    def __init__(self, trino_conn):
        super().__init__(
            name="Trino Query Tool",
            description="Executes SQL queries on Trino and returns results.",
            func=self.run_query,
            metadata={"trino_conn": trino_conn},
        )

    def run_query(self, query: str):
        conn = self.metadata["trino_conn"]
        cursor = conn.cursor()
        cursor.execute(query)
        return cursor.fetchall()
