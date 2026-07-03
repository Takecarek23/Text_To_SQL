# raw_sql_executor.py

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from typing import Optional, List, Dict

class RawSQLExecutor:
    def __init__(self, db_url: str):
        self.engine = create_engine(db_url)
        self.Session = sessionmaker(bind=self.engine)

    def run_query(self, sql: str, limit: Optional[int] = None) -> Dict:
        """Execute raw SQL and return structured result or error."""
        try:
            with self.Session() as session, session.begin():
                result = session.execute(text(sql))
                try:
                    if result.returns_rows:
                        if limit:
                            rows = result.fetchmany(limit)
                        else:
                            rows = result.fetchall()
                        return {
                            "sql": sql,
                            "result": [row._asdict() for row in rows],
                            "explanation": "Raw query executed successfully without model assistance."
                        }
                    else:
                        # Xử lý cho INSERT/UPDATE/DELETE
                        return {
                            "sql": sql,
                            "result": [{"status": "Thành công", "rows_affected": result.rowcount}],
                            "explanation": f"Lệnh thay đổi dữ liệu đã chạy thành công. {result.rowcount} hàng bị ảnh hưởng."
                        }
                except Exception as parse_error:
                    return {
                        "sql": sql,
                        "error": f"Query executed but could not parse result: {parse_error}",
                        "explanation": "Query ran but result formatting failed."
                    }
        except Exception as exec_error:
            return {
                "sql": sql,
                "error": str(exec_error),
                "explanation": "Query failed during execution."
            }
