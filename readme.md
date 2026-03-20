# Solumate Project

🌐 Language / Ngôn ngữ:

- Tiếng Việt
- English

This repository provides Vietnamese and English guides for beginners.

## Đóng góp / Donation
Nếu bạn thấy dự án hữu ích và muốn ủng hộ tác giả duy trì/hoàn thiện dự án, bạn có thể donation theo thông tin dưới đây:

- MoMo: 0799640848
- VietinBank: 0799640848 — Đoàn Thanh Lực

Xin cảm ơn bạn đã ủng hộ! 🙏

## Donation
If you find this project useful and would like to support continued development/maintenance:

- MoMo: 0799640848
- VietinBank: 0799640848 — Đoàn Thanh Lực

Thank you for your support! 🙏

---
# Proxy IPv6 Manager ðŸš€

Má»™t REST API viáº¿t báº±ng **FastAPI** cho phÃ©p:

- Táº¡o vÃ  quáº£n lÃ½ proxy dá»±a trÃªn Ä‘á»‹a chá»‰ IPv6.
- Tá»± Ä‘á»™ng gÃ¡n Ä‘á»‹a chá»‰ IPv6 vÃ o card máº¡ng (interface).
- Quáº£n lÃ½ lifecycle cá»§a proxy: **run, stop, rotate, delete**.
- Liá»‡t kÃª card máº¡ng vÃ  láº¥y IPv4/IPv6 Ä‘ang cáº¥u hÃ¬nh.

---

## ðŸ“¦ YÃªu cáº§u há»‡ thá»‘ng

- Python 3.9+
- Windows (cáº§n quyá»n Administrator Ä‘á»ƒ thÃªm/xoÃ¡ IPv6)
- CÃ¡c thÆ° viá»‡n Python:

  ```bash
  pip install fastapi uvicorn pydantic
  ```

---

## âš™ï¸ Cáº¥u trÃºc thÆ° má»¥c

```
project/
â”œâ”€â”€ server.py              # FastAPI server (API endpoints)
â”œâ”€â”€ utils/
â”‚   â”œâ”€â”€ generate_ipv6.py   # HÃ m táº¡o/xoÃ¡/gÃ¡n IPv6 vÃ o card máº¡ng
â”‚   â”œâ”€â”€ db.py              # Quáº£n lÃ½ SQLite database
â”‚   â””â”€â”€ proxy.py           # Logic cháº¡y/stopp proxy TCP
â””â”€â”€ data/
    â””â”€â”€ ipv6_address.db    # SQLite database lÆ°u proxy
```

---

## ðŸš€ Cháº¡y server

```bash
uvicorn server:app --reload --host 0.0.0.0 --port 9002
```

API sáº½ sáºµn sÃ ng táº¡i: [http://localhost:9002](http://localhost:9002)

---

## ðŸ”‘ API Endpoints

### Proxy Management

- `POST /proxy/create` â†’ Táº¡o má»›i proxy vá»›i IPv6 random.
- `POST /proxy/run_all` â†’ Cháº¡y toÃ n bá»™ proxy trong DB.
- `POST /proxy/run_by_ids` â†’ Cháº¡y proxy theo danh sÃ¡ch id trong DB.
- `POST /proxy/stop_by_ids` â†’ Dá»«ng proxy theo danh sÃ¡ch id.
- `POST /proxy/stop/{port}` â†’ Dá»«ng proxy theo port.
- `POST /proxy/rotate/{port}` â†’ Xoay IP (remove IPv6 cÅ©, add IPv6 má»›i, giá»¯ nguyÃªn port).
- `DELETE /proxy/{id}` â†’ XoÃ¡ proxy (náº¿u khÃ´ng cháº¡y).
- `GET /proxy` â†’ Liá»‡t kÃª toÃ n bá»™ proxy vá»›i tráº¡ng thÃ¡i running/stopped.

### Network Info

- `GET /network/adapters` â†’ Láº¥y danh sÃ¡ch card máº¡ng vÃ  IPv4.
- `GET /network/adapters/{card_name}/ipv6` â†’ Láº¥y IPv6 cá»§a card máº¡ng chá»‰ Ä‘á»‹nh.

---

## ðŸ“‹ VÃ­ dá»¥ cURL

### Táº¡o proxy má»›i

```bash
curl --location 'http://localhost:9002/proxy/create' \
--header 'Content-Type: application/json' \
--data '{
  "group_name": "group1",
  "interface_name": "Ethernet"
}'
```

### Xem danh sÃ¡ch proxy

```bash
curl -X GET "http://localhost:9002/proxy"
```

### Cháº¡y táº¥t cáº£

```bash
curl --location --request POST 'http://localhost:9002/proxy/run_all'
```

### láº¥y danh sÃ¡ch

```bash
curl --location 'http://localhost:9002/proxy'
```

### Dá»«ng báº±ng port

```bash
curl --location --request POST 'http://localhost:9002/proxy/stop/10000'
```

### Xoay ipv6 báº±ng port

```bash
curl --location --request POST 'http://localhost:9002/proxy/rotate/10005'
```

### XÃ³a proxy

```bash
curl --location --request DELETE 'http://localhost:9002/proxy/4'
```

### cháº¡y báº±ng ids

```bash
http://localhost:9002/proxy/run_by_ids
```

### Dá»«ng báº±ng ids

```bash
http://localhost:9002/proxy/stop_by_ids
```

### Danh sÃ¡ch card máº¡ng:

```bash
http://localhost:9002/network/adapters
```

### Danh sÃ¡ch ipv6 cÃ³ trong mÃ¡y

```bash
curl --location 'http://localhost:9002/network/adapters/Ethernet/ipv6'
```

## XÃ³a trá»±c tiáº¿p ipv6 trong mÃ¡y

```bash
curl --location --request DELETE 'http://localhost:9002/network/adapters/Ethernet/ipv6/2402:800:6344:86b:57d6:4ead:8312:9703'
```

---

## âš ï¸ LÆ°u Ã½

- Cáº§n cháº¡y báº±ng **Administrator** Ä‘á»ƒ thÃªm hoáº·c xoÃ¡ IPv6 vÃ o interface.
- Náº¿u mÃ¡y khÃ´ng cÃ³ káº¿t ná»‘i IPv6 public, proxy sáº½ khÃ´ng hoáº¡t Ä‘á»™ng.
- Database SQLite lÆ°u trong thÆ° má»¥c `data/ipv6_address.db`.

### Build:

```bash
python setup.py build_ext
```

### Build exe

```bash
pyinstaller --onefile --name server2 --icon=solumate_icon.ico --add-data "utils_ext;utils_ext" .\server.py
```

python -m pip install -r requirements.txt
