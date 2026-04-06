# Solumate Project

## Language / Ngôn ngữ
- Tiếng Việt
- English

This repository provides Vietnamese and English guides for beginners.

## Đóng góp / Donation
Nếu bạn thấy dự án hữu ích và muốn ủng hộ tác giả duy trì/hoàn thiện dự án, bạn có thể donation theo thông tin dưới đây:

- MoMo: 0799640848
- VietinBank: 0799640848 - Đoàn Thanh Lực

Xin cảm ơn bạn đã ủng hộ.

## Donation
If you find this project useful and would like to support continued development/maintenance:

- MoMo: 0799640848
- VietinBank: 0799640848 - Đoàn Thanh Lực

Thank you for your support.

---

# Proxy IPv6 Manager

Một REST API viết bằng **FastAPI** cho phép:

- Tạo và quản lý proxy dựa trên địa chỉ IPv6.
- Tự động gán địa chỉ IPv6 vào card mạng (interface).
- Quản lý vòng đời proxy: **run, stop, rotate, delete**.
- Tự động xoay IPv6 theo từng kết nối mới để tăng độ ẩn danh.
- Liệt kê card mạng và lấy IPv4/IPv6 đang cấu hình.
- Hỗ trợ realtime bằng WebSocket để cập nhật trạng thái.

---

## Yêu cầu hệ thống

- Python 3.9+
- Windows (cần quyền Administrator để thêm/xóa IPv6)
- Các thư viện Python (xem `requirements.txt`)

Cài đặt:

```bash
python -m pip install -r requirements.txt
```

---

## Cấu trúc thư mục

```text
project/
|-- server.py              # FastAPI server (API endpoints + websocket)
|-- client.html            # UI dashboard
|-- client.js              # UI logic + realtime socket
|-- utils/
|   |-- generate_ipv6.py   # Tạo/xóa/gán IPv6 vào card mạng
|   |-- db.py              # Quản lý SQLite database
|   |-- proxy.py           # Logic chạy/stop proxy TCP
|-- data/
|   |-- ipv6_address.db    # SQLite database lưu proxy
|-- requirements.txt
|-- LICENSE
```

---

## Chạy server

```bash
python server.py
```

hoặc

```bash
uvicorn server:app --host 0.0.0.0 --port 9002
```

- Web UI: `http://127.0.0.1:9002`
- API base: `http://127.0.0.1:9002`
- WebSocket realtime: `ws://127.0.0.1:9002/ws/events`

---

## API Endpoints

### Proxy Management

- `POST /proxy/create` -> Tạo mới proxy với IPv6 random
- `POST /proxy/run_all` -> Chạy toàn bộ proxy trong DB
- `POST /proxy/run_by_ids` -> Chạy proxy theo danh sách id
- `POST /proxy/stop_by_ids` -> Dừng proxy theo danh sách id
- `POST /proxy/stop/{port}` -> Dừng proxy theo port
- `POST /proxy/rotate/{port}` -> Xoay IP (remove IPv6 cũ, add IPv6 mới, giữ nguyên port)
- `DELETE /proxy/{id}` -> Xóa proxy (nếu không đang chạy)
- `GET /proxy` -> Liệt kê toàn bộ proxy với trạng thái running/stopped

### Network

- `GET /network/adapters` -> Lấy danh sách card mạng và IPv4
- `GET /network/adapters/{card_name}/ipv6` -> Lấy IPv6 của card mạng chỉ định
- `DELETE /network/adapters/{card_name}/ipv6/{ipv6_address}` -> Xóa 1 IPv6 cụ thể khỏi card mạng

### Realtime

- `WS /ws/events`
- Server phát các event `operation` và `proxy_snapshot` để cập nhật UI theo thời gian thực.

---

## Ví dụ cURL

### Tạo proxy mới

```bash
curl --location 'http://127.0.0.1:9002/proxy/create' \
--header 'Content-Type: application/json' \
--data '{
  "group_name": "group1",
  "interface_name": "Ethernet"
}'
```

### Xem danh sách proxy

```bash
curl -X GET "http://127.0.0.1:9002/proxy"
```

### Chạy tất cả proxy

```bash
curl --location --request POST 'http://127.0.0.1:9002/proxy/run_all'
```

### Chạy theo IDs

```bash
curl --location --request POST 'http://127.0.0.1:9002/proxy/run_by_ids' \
--header 'Content-Type: application/json' \
--data '[1,2,3]'
```

### Dừng theo IDs

```bash
curl --location --request POST 'http://127.0.0.1:9002/proxy/stop_by_ids' \
--header 'Content-Type: application/json' \
--data '[1,2,3]'
```

### Dừng theo port

```bash
curl --location --request POST 'http://127.0.0.1:9002/proxy/stop/10000'
```

### Xoay IPv6 theo port

```bash
curl --location --request POST 'http://127.0.0.1:9002/proxy/rotate/10005'
```

### Xóa proxy

```bash
curl --location --request DELETE 'http://127.0.0.1:9002/proxy/4'
```

### Danh sách card mạng

```bash
curl --location 'http://127.0.0.1:9002/network/adapters'
```

### Danh sách IPv6 theo card

```bash
curl --location 'http://127.0.0.1:9002/network/adapters/Ethernet/ipv6'
```

### Xóa trực tiếp 1 IPv6 trong máy

```bash
curl --location --request DELETE 'http://127.0.0.1:9002/network/adapters/Ethernet/ipv6/2402:800:6344:86b:57d6:4ead:8312:9703'
```

---

## Lưu ý

- Cần chạy bằng **Administrator** để thêm hoặc xóa IPv6 vào interface.
- Nếu máy không có kết nối IPv6 public, proxy có thể không hoạt động đúng.
- Database SQLite lưu trong thư mục `data/ipv6_address.db`.

---

## Build (tùy chọn)

```bash
python setup.py build_ext
```

```bash
pyinstaller --onefile --name server2 --icon=solumate_icon.ico --add-data "utils_ext;utils_ext" .\server.py
```
