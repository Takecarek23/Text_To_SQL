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
