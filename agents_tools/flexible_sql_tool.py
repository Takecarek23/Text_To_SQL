# flexible_sql_tool.py
import json
from typing import Optional

from phi.tools import Toolkit
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker


class FlexibleSQLTool(Toolkit):
    def __init__(self, db_url: str):
        super().__init__(name="flexible_sql_tool")

        self.db_url = db_url
        self.engine = create_engine(db_url)
        self.Session = sessionmaker(bind=self.engine)

        # Đăng ký hàm này làm công cụ cho AI
        self.register(self.use)

    # Sử dụng kiểu str cho biến limit để bộ tạo Schema của Phi Data không bị lỗi 'type'
    def use(self, sql: str, format: str = "table", limit: Optional[str] = None) -> str:
        """
        Executes an SQL query and returns the result as a table or a brief summary.
        :param sql: SQL query
        :param format: 'table' | 'summary'
        :param limit: row limit
        :return: string containing the result
        """
        # SỬA LỖI 1: Xử lý trường hợp AI truyền vào chuỗi rỗng '' thay vì số nguyên
        parsed_limit = None
        if limit and str(limit).strip():
            try:
                parsed_limit = int(limit)
            except (ValueError, TypeError):
                parsed_limit = None

        try:
            with self.Session() as session, session.begin():
                result = session.execute(text(sql))
                try:
                    # SỬA LỖI 2: Phân biệt lệnh SELECT (có dữ liệu) và lệnh UPDATE/INSERT (không có dữ liệu)
                    if result.returns_rows:
                        rows = result.fetchmany(parsed_limit) if parsed_limit else result.fetchall()
                        parsed = [row._asdict() for row in rows]
                        if format == "summary":
                            return self._summarise(parsed)
                        return self._render_table(parsed)
                    else:
                        return f"[✅] Lệnh thực thi thành công. Đã thay đổi {result.rowcount} hàng dữ liệu."
                except Exception as parse_error:
                    return f"[⚠] Lệnh chạy thành công, nhưng lỗi đọc kết quả: {parse_error}"
        except Exception as exec_error:
            return f"[❌] Lệnh thất bại: {exec_error}"

    def _render_table(self, rows: list[dict]) -> str:
        if not rows:
            return "[ℹ] Không có dữ liệu trả về."
        keys = list(rows[0].keys())
        header = "| " + " | ".join(keys) + " |"
        separator = "| " + " | ".join(["---"] * len(keys)) + " |"
        body = "\n".join("| " + " | ".join(str(row.get(k, "")) for k in keys) + " |" for row in rows)
        return "\n".join([header, separator, body])

    def _summarise(self, rows: list[dict]) -> str:
        if not rows:
            return "[ℹ] Không có dữ liệu để tóm tắt."
        summary_lines = [f"- Trả về {len(rows)} hàng dữ liệu."]
        fields = rows[0].keys() if rows else []
        summary_lines.append(f"- Các cột hiện có: {', '.join(fields)}")
        return "\n".join(summary_lines)