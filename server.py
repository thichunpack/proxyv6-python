import threading
import sqlite3
import uvicorn

from fastapi import FastAPI, HTTPException, Header, Body
from pydantic import BaseModel
from typing import Optional, List, Dict
from utils.generate_ipv6 import (
    generate_ipv6_addresses,
    add_ipv6_to_ethernet,
    remove_ipv6_address,
    get_adapters_ipv4,
    get_ipv6_by_card_name,
)
from utils_ext.db import ipv6_address_path, init_ipv6_table
from utils.proxy import create_proxy, stop_proxy, list_running_proxies

app = FastAPI()
init_ipv6_table()


# =========================
# Helper DB
# =========================
def db_connect():
    return sqlite3.connect(ipv6_address_path)


def get_all_proxies():
    conn = db_connect()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, ipv6, group_name, port, interface_name FROM ipv6_address ORDER BY port"
    )
    rows = cur.fetchall()
    conn.close()
    return rows


def get_next_port():
    rows = [int(r[3]) for r in get_all_proxies()]
    if not rows:
        return 10000
    rows = sorted(rows)
    # tìm lỗ trống nhỏ nhất
    for i in range(rows[0], rows[-1] + 2):
        if i not in rows:
            return i
    return max(rows) + 1


# =========================
# API Models
# =========================
class ProxyCreate(BaseModel):
    group_name: str
    interface_name: str = "Ethernet"


# =========================
# API Controllers
# =========================


@app.post("/proxy/create")
async def create_proxy_v6(
    data: ProxyCreate, authorization: Optional[str] = Header(None)
):
    port = get_next_port()
    ipv6 = generate_ipv6_addresses(authorization, 1)[0]
    group = data.group_name
    interface = data.interface_name

    # add ipv6 vào card mạng
    await add_ipv6_to_ethernet(authorization, ipv6, interface)

    conn = db_connect()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO ipv6_address (ipv6, group_name, port, interface_name) VALUES (?,?,?,?)",
        (ipv6, group, str(port), interface),
    )
    conn.commit()
    conn.close()

    # run proxy
    t = threading.Thread(
        target=create_proxy,
        args=(
            authorization,
            {"port": port, "ip": ipv6},
        ),
        daemon=True,
    )
    t.start()

    return {"port": port, "ipv6": ipv6, "status": "running"}


@app.post("/proxy/run_all")
def run_all_proxy(authorization: Optional[str] = Header(None)):
    proxies = get_all_proxies()
    started = []
    for row in proxies:
        id_, ipv6, group, port, interface = row
        port = int(port)
        if port not in list_running_proxies(authorization):
            t = threading.Thread(
                target=create_proxy,
                args=(
                    authorization,
                    {"port": port, "ip": ipv6},
                ),
                daemon=True,
            )
            t.start()
            started.append(port)
    return {"started": started}


@app.post("/proxy/run_by_ids")
def run_proxies_by_ids(
    ids: List[int] = Body(...), authorization: Optional[str] = Header(None)
):
    """
    Run proxies theo danh sách DB id.
    Body: [1, 2, 3]
    Returns per-id status.
    """
    if not ids:
        return {"detail": "No ids provided", "results": []}

    conn = db_connect()
    cur = conn.cursor()

    results: List[Dict] = []

    # fetch rows cho các id được chỉ định
    placeholders = ",".join(["?"] * len(ids))
    cur.execute(
        f"SELECT id, ipv6, group_name, port, interface_name FROM ipv6_address WHERE id IN ({placeholders})",
        tuple(ids),
    )
    rows = cur.fetchall()
    conn.close()

    found_ids = {row[0] for row in rows}
    for i in ids:
        if i not in found_ids:
            results.append({"id": i, "status": "not_found"})

    running_ports = list_running_proxies(authorization)

    for id_, ipv6, group, port, interface in rows:
        port = int(port)
        if port in running_ports:
            results.append({"id": id_, "port": port, "status": "already_running"})
        else:
            try:
                t = threading.Thread(
                    target=create_proxy,
                    args=(
                        authorization,
                        {"port": port, "ip": ipv6},
                    ),
                    daemon=True,
                )
                t.start()
                results.append({"id": id_, "port": port, "status": "started"})
            except Exception as e:
                results.append(
                    {"id": id_, "port": port, "status": "error", "error": str(e)}
                )

    return {"results": results}


@app.post("/proxy/stop_by_ids")
def stop_proxies_by_ids(
    ids: List[int] = Body(...), authorization: Optional[str] = Header(None)
):
    """
    Stop proxies by a list of DB ids.
    Body: [1, 2, 3]
    Returns per-id status.
    """
    if not ids:
        return {"detail": "No ids provided", "results": []}

    conn = db_connect()
    cur = conn.cursor()

    results: List[Dict] = []

    # fetch rows for provided ids: id, port
    placeholders = ",".join(["?"] * len(ids))
    cur.execute(
        f"SELECT id, port FROM ipv6_address WHERE id IN ({placeholders})", tuple(ids)
    )
    rows = cur.fetchall()
    id_to_port = {row[0]: int(row[1]) for row in rows}

    # For ids not found in DB
    found_ids = set(id_to_port.keys())
    for i in ids:
        if i not in found_ids:
            results.append({"id": i, "status": "not_found"})

    # Try to stop proxies for found ids
    running_ports = list_running_proxies(
        authorization
    )  # get current running ports from proxy module

    for id_, port in id_to_port.items():
        try:
            if port in running_ports:
                ok = stop_proxy(authorization, port)  # trả về True nếu đã đánh dấu stop
                if ok:
                    results.append({"id": id_, "port": port, "status": "stopped"})
                else:
                    # stop_proxy returned False mặc dù port có trong running_ports (hiếm)
                    results.append({"id": id_, "port": port, "status": "stop_failed"})
            else:
                results.append({"id": id_, "port": port, "status": "not_running"})
        except Exception as e:
            results.append(
                {"id": id_, "port": port, "status": "error", "error": str(e)}
            )

    conn.close()
    return {"results": results}


@app.delete("/proxy/{id}")
async def remove_proxy(id: int, authorization: Optional[str] = Header(None)):
    conn = db_connect()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, ipv6, port, interface_name FROM ipv6_address WHERE id=?", (id,)
    )
    row = cur.fetchone()
    if not row:
        raise HTTPException(404, "Not found")

    _, ipv6, port, interface = row
    port = int(port)

    if port in list_running_proxies(authorization):
        raise HTTPException(400, "Proxy đang chạy, không thể xóa!")

    cur.execute("DELETE FROM ipv6_address WHERE id=?", (id,))
    await remove_ipv6_address(authorization, ipv6, interface)
    conn.commit()
    conn.close()

    return {"deleted": id}


@app.post("/proxy/stop/{port}")
def stop_proxy_api(port: int, authorization: Optional[str] = Header(None)):
    if not stop_proxy(authorization, port):
        raise HTTPException(404, "Proxy not running")
    return {"stopped": port}


@app.post("/proxy/rotate/{port}")
async def rotate_proxy(port: int, authorization: Optional[str] = Header(None)):
    conn = db_connect()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, ipv6, group_name, port, interface_name FROM ipv6_address WHERE port=?",
        (str(port),),
    )
    row = cur.fetchone()
    if not row:
        raise HTTPException(404, "Not found")

    id_, old_ipv6, group, port, interface = row
    port = int(port)
    # Dừng proxy củ
    stop_proxy(authorization, port)
    # remove ipv6 cũ
    await remove_ipv6_address(authorization, old_ipv6, interface)

    # tạo ipv6 mới
    new_ipv6 = generate_ipv6_addresses(1)[0]
    await add_ipv6_to_ethernet(authorization, new_ipv6, interface)

    # update DB
    cur.execute("UPDATE ipv6_address SET ipv6=? WHERE id=?", (new_ipv6, id_))
    conn.commit()
    conn.close()

    # stop cũ, start lại
    t = threading.Thread(
        target=create_proxy,
        args=(
            authorization,
            {"port": port, "ip": new_ipv6},
        ),
        daemon=True,
    )
    t.start()

    return {"port": port, "ipv6": new_ipv6}


@app.get("/proxy")
async def list_proxies(authorization: Optional[str] = Header(None)):
    rows = get_all_proxies()
    running = list_running_proxies(authorization)
    data = []
    for id_, ipv6, group, port, interface in rows:
        status = "running" if int(port) in running else "stopped"
        data.append(
            {
                "id": id_,
                "port": int(port),
                "ipv6": ipv6,
                "group": group,
                "interface": interface,
                "status": status,
            }
        )
    return data


@app.get("/network/adapters")
async def list_network_adapters(authorization: Optional[str] = Header(None)):
    """
    Trả về danh sách card mạng và IPv4 address.
    """
    try:
        adapters = get_adapters_ipv4(authorization)
        return {"count": len(adapters), "adapters": adapters}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting adapters: {e}")


@app.get("/network/adapters/{card_name}/ipv6")
def get_ipv6_for_card(card_name: str, authorization: Optional[str] = Header(None)):
    """
    Trả về IPv6 của 1 card mạng cụ thể theo card_name
    """
    adapter = get_ipv6_by_card_name(authorization, card_name)
    if not adapter:
        raise HTTPException(
            status_code=404,
            detail=f"Adapter '{card_name}' not found or no IPv6 assigned",
        )
    return adapter


@app.delete("/network/adapters/{card_name}/ipv6/{ipv6_address}")
async def get_ipv6_for_card(
    card_name: str, ipv6_address: str, authorization: Optional[str] = Header(None)
):
    """
    Trả về IPv6 của 1 card mạng cụ thể theo card_name
    """
    try:
        adapter = get_ipv6_by_card_name(authorization, card_name)
        if not adapter:
            raise HTTPException(
                status_code=404,
                detail=f"Adapter '{card_name}' not found or no IPv6 assigned",
            )
        await remove_ipv6_address(authorization, ipv6_address, card_name)

        return {"removed": ipv6_address, "from": card_name}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error removing IPv6: {e}")


def _main():
    uvicorn.run(
        app,
        host="127.0.0.1",  # chỉ localhost -> không popup firewall & chỉ NestJS local gọi được
        port=9002,
        reload=False,
        log_level="info",
        access_log=False,
    )


if __name__ == "__main__":
    _main()
