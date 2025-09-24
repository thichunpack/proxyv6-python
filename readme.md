# Proxy IPv6 Manager 🚀

Một REST API viết bằng **FastAPI** cho phép:

- Tạo và quản lý proxy dựa trên địa chỉ IPv6.
- Tự động gán địa chỉ IPv6 vào card mạng (interface).
- Quản lý lifecycle của proxy: **run, stop, rotate, delete**.
- Liệt kê card mạng và lấy IPv4/IPv6 đang cấu hình.

---

## 📦 Yêu cầu hệ thống

- Python 3.9+
- Windows (cần quyền Administrator để thêm/xoá IPv6)
- Các thư viện Python:

  ```bash
  pip install fastapi uvicorn pydantic
  ```

---

## ⚙️ Cấu trúc thư mục

```
project/
├── server.py              # FastAPI server (API endpoints)
├── utils/
│   ├── generate_ipv6.py   # Hàm tạo/xoá/gán IPv6 vào card mạng
│   ├── db.py              # Quản lý SQLite database
│   └── proxy.py           # Logic chạy/stopp proxy TCP
└── data/
    └── ipv6_address.db    # SQLite database lưu proxy
```

---

## 🚀 Chạy server

```bash
uvicorn server:app --reload --host 0.0.0.0 --port 9002
```

API sẽ sẵn sàng tại: [http://localhost:9002](http://localhost:9002)

---

## 🔑 API Endpoints

### Proxy Management

- `POST /proxy/create` → Tạo mới proxy với IPv6 random.
- `POST /proxy/run_all` → Chạy toàn bộ proxy trong DB.
- `POST /proxy/run_by_ids` → Chạy proxy theo danh sách id trong DB.
- `POST /proxy/stop_by_ids` → Dừng proxy theo danh sách id.
- `POST /proxy/stop/{port}` → Dừng proxy theo port.
- `POST /proxy/rotate/{port}` → Xoay IP (remove IPv6 cũ, add IPv6 mới, giữ nguyên port).
- `DELETE /proxy/{id}` → Xoá proxy (nếu không chạy).
- `GET /proxy` → Liệt kê toàn bộ proxy với trạng thái running/stopped.

### Network Info

- `GET /network/adapters` → Lấy danh sách card mạng và IPv4.
- `GET /network/adapters/{card_name}/ipv6` → Lấy IPv6 của card mạng chỉ định.

---

## 📋 Ví dụ cURL

### Tạo proxy mới

```bash
curl --location 'http://localhost:9002/proxy/create' \
--header 'Content-Type: application/json' \
--data '{
  "group_name": "group1",
  "interface_name": "Ethernet"
}'
```

### Xem danh sách proxy

```bash
curl -X GET "http://localhost:9002/proxy"
```

### Chạy tất cả

```bash
curl --location --request POST 'http://localhost:9002/proxy/run_all'
```

### lấy danh sách

```bash
curl --location 'http://localhost:9002/proxy'
```

### Dừng bằng port

```bash
curl --location --request POST 'http://localhost:9002/proxy/stop/10000'
```

### Xoay ipv6 bằng port

```bash
curl --location --request POST 'http://localhost:9002/proxy/rotate/10005'
```

### Xóa proxy

```bash
curl --location --request DELETE 'http://localhost:9002/proxy/4'
```

### chạy bằng ids

```bash
http://localhost:9002/proxy/run_by_ids
```

### Dừng bằng ids

```bash
http://localhost:9002/proxy/stop_by_ids
```

### Danh sách card mạng:

```bash
http://localhost:9002/network/adapters
```

### Danh sách ipv6 có trong máy

```bash
curl --location 'http://localhost:9002/network/adapters/Ethernet/ipv6'
```

## Xóa trực tiếp ipv6 trong máy

```bash
curl --location --request DELETE 'http://localhost:9002/network/adapters/Ethernet/ipv6/2402:800:6344:86b:57d6:4ead:8312:9703'
```

---

## ⚠️ Lưu ý

- Cần chạy bằng **Administrator** để thêm hoặc xoá IPv6 vào interface.
- Nếu máy không có kết nối IPv6 public, proxy sẽ không hoạt động.
- Database SQLite lưu trong thư mục `data/ipv6_address.db`.

### Build:

```bash
python setup.py build_ext
```

### Build exe

```bash
pyinstaller --onefile --name server2 --icon=solumate_icon.ico --add-data "utils_ext;utils_ext" .\server.py
```
