## 1. Cấu hình và Khởi chạy hệ thống

**Bước 1: Cài đặt môi trường**
```bash
pip install -r requirements.txt
```

**Bước 2: Thiết lập thông số kết nối**
Khởi tạo tệp `.env` tại thư mục gốc của dự án. Điền link cơ sở dữ liệu và API ChatGPT nếu có, không thì mặc định là ollama.

```env
DB_URL=sqlite:///my_sample.db
MODEL_PROVIDER=ollama
MODEL_NAME=llama3.1
```

**Bước 3: Khởi chạy giao diện**
Sử dụng Chainlit để tạo giao diện chat:

```bash
python -m chainlit run app.py
```

Địa chỉ kích hoạt là: `http://localhost:8000`.

## 2. Phương thức tương tác

Hệ thống tiếp cận 2 loại người dùng.
- **User 1:** Người dùng đã biết lệnh SQL thì sử dụng lệnh, sẽ cho kết quả tức thì.
- **User 2:** Người dùng chưa biết lệnh thì đặt yêu cầu tương tác với cơ sở dữ liệu qua ngôn ngữ tự nhiên

### 2.1. Tương tác qua ngôn ngữ tự nhiên

Phương thức này cho phép người dùng nhập yêu cầu bằng văn bản thông thường. AI sẽ đảm nhiệm việc phân tích ngữ nghĩa, chuyển đổi thành truy vấn SQL, thực thi và diễn giải kết quả.

* **Ví dụ truy xuất:** "Hiển thị danh sách nhân viên thuộc bộ phận IT trong bảng employees."
* **Ví dụ hiệu chỉnh:** "Cập nhật tên của nhân viên Nguyen Van A thành Nguyen Van B trong bảng employees."

### 2.2. Tương tác qua các khối lệnh trực tiếp (Direct Commands)

Phương thức này bỏ qua quá trình suy luận của LLM, cho phép người dùng thực thi trực tiếp các câu lệnh SQL nhằm tối ưu hóa thời gian xử lý và tài nguyên hệ thống.

* **Lệnh `/run <câu_lệnh_SQL>`:** Thực thi truy vấn và trả về kết quả dưới định dạng JSON có cấu trúc tĩnh, bao gồm dữ liệu và các siêu dữ liệu liên quan.
* **Lệnh `/raw <câu_lệnh_SQL>`:** Thực thi truy vấn và kết xuất dữ liệu thô dưới dạng bảng Markdown.
* **Lệnh `/summary <câu_lệnh_SQL>`:** Thực thi truy vấn và trích xuất thông tin thống kê của tập kết quả (số lượng bản ghi, danh sách trường dữ liệu).

*Ví dụ:* `/raw SELECT * FROM employees;`

## 3. Khắc phục sự cố cơ bản

* **Lỗi không tìm thấy cấu trúc bảng (Table not found):** Xảy ra khi LLM nội suy sai cấu trúc cơ sở dữ liệu. Khắc phục bằng cách cung cấp yêu cầu tường minh hơn (đính kèm tên bảng cụ thể) hoặc yêu cầu hệ thống tra cứu cấu trúc (`sqlite_master`, `information_schema`) trước khi truy vấn.
* **Lỗi quá tải yêu cầu:** Trong trường hợp lỗi phát sinh do LLM phản hồi quá giới hạn bộ nhớ ngữ cảnh, người dùng cần chia nhỏ các yêu cầu truy vấn.


## 4. Test mẫu

### Phần 1: Test bằng Ngôn ngữ tự nhiên (Chat với AI)

**1. Kiểm tra đọc dữ liệu cơ bản (SELECT)**

* *"Trong cơ sở dữ liệu hiện tại có những bảng nào?"*
* *"Hiển thị danh sách nhân viên phòng IT trong bảng employees."*

**2. Kiểm tra tính toán và thống kê (GROUP BY, ORDER BY, AVG, MAX)**

* *"Ai là người có mức lương cao nhất trong bảng employees?"*
* *"Hãy thống kê số lượng nhân viên và mức lương trung bình theo từng phòng ban."*

**3. Kiểm tra thay đổi dữ liệu (INSERT, UPDATE, DELETE)**

* *"Tăng lương cho 'Nguyen Van A' trong bảng employees lên thành 2000.0"*
*(Mục đích: Test lệnh `UPDATE`).*
* *"Thêm một nhân viên mới tên là 'Nguyễn Bảo Vệ', phòng 'Bảo vệ', lương 900.0 vào bảng employees."*
*(Mục đích: Test lệnh `INSERT`).*
* *"Hãy xóa nhân viên tên 'Trần Thị B' khỏi cơ sở dữ liệu."*
*(Mục đích: Test lệnh `DELETE`).*

**4. Thử thách chống "ảo giác" (Hallucination Test)**

* *"Hãy cho tôi xem danh sách khách hàng."*
*(Mục đích: CSDL của không có bảng khách hàng. AI chuẩn sẽ phải từ chối hoặc báo lỗi "Không tìm thấy bảng khách hàng", để xem AI có bịa ra hay không).*

---

### Phần 2: Test bằng Lệnh Trực tiếp (Bỏ qua AI)

**1. Lệnh `/raw` (Test hiển thị bảng Markdown sạch)**

```sql
/raw SELECT department, COUNT(id) as total_staff, SUM(salary) as total_salary FROM employees GROUP BY department;
```

*(Mục đích: Hệ thống phải trả ra ngay 1 cái bảng thống kê).*

**2. Lệnh `/summary` (Test tóm tắt cấu trúc)**

```sql
/summary SELECT * FROM employees;
```

*(Mục đích: Hệ thống không in ra danh sách nhân viên, mà chỉ báo: "Trả về X hàng dữ liệu. Cột gồm: id, name, department, salary").*

**3. Lệnh `/run` (Test đầu ra JSON chuẩn của Hệ thống)**

```sql
/run SELECT name, salary FROM employees WHERE salary > 1300;
```

*(Mục đích: Test file `raw_sql_executor.py`. Hệ thống phải trả về dữ liệu có format đầy đủ gồm Thought, SQL Query, Result (dạng bảng), và Explanation).*