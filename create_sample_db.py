import sqlite3

# 1. Tạo và kết nối tới file cơ sở dữ liệu mới tên là 'my_sample.db'
conn = sqlite3.connect('my_sample.db')
cursor = conn.cursor()

# 2. Tạo một bảng mẫu (ví dụ: bảng nhân viên - employees)
cursor.execute('''
CREATE TABLE IF NOT EXISTS employees (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    department TEXT NOT NULL,
    salary REAL
)
''')

# 3. Chèn một số dữ liệu mẫu vào bảng
sample_data = [
    (1, 'Nguyen Van A', 'IT', 1500.0),
    (2, 'Tran Thi B', 'Nhan su', 1200.0),
    (3, 'Le Van C', 'IT', 1600.0),
    (4, 'Pham Thi D', 'Marketing', 1300.0),
    (5, 'Hoang Van E', 'Ke toan', 1400.0)
]

# Xóa dữ liệu cũ nếu chạy lại script để tránh trùng lặp
cursor.execute('DELETE FROM employees')

cursor.executemany('''
INSERT INTO employees (id, name, department, salary)
VALUES (?, ?, ?, ?)
''', sample_data)

# 4. Lưu thay đổi và đóng kết nối
conn.commit()
conn.close()

print("✅ Đã tạo thành công cơ sở dữ liệu mẫu: my_sample.db")