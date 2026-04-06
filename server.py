import asyncio
import ipaddress
import sqlite3
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

import uvicorn
from fastapi import Body, FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from pydantic import BaseModel

from utils.db import init_ipv6_table, ipv6_address_path
from utils.generate_ipv6 import (
    add_ipv6_to_ethernet,
    ensure_admin_permission,
    generate_ipv6_addresses,
    get_adapters_ipv4,
    get_ipv6_by_card_name,
    remove_ipv6_address,
)
from utils.proxy import create_proxy, list_running_proxies, stop_proxy

app = FastAPI()
init_ipv6_table()
BASE_DIR = Path(__file__).resolve().parent


class SocketHub:
    def __init__(self):
        self._clients: set[WebSocket] = set()
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        async with self._lock:
            self._clients.add(websocket)

    async def disconnect(self, websocket: WebSocket):
        async with self._lock:
            self._clients.discard(websocket)

    async def broadcast(self, payload: Dict[str, Any]):
        async with self._lock:
            clients = list(self._clients)

        stale: List[WebSocket] = []
        for ws in clients:
            try:
                await ws.send_json(payload)
            except Exception:
                stale.append(ws)

        if stale:
            async with self._lock:
                for ws in stale:
                    self._clients.discard(ws)


socket_hub = SocketHub()


# =========================
# Helper
# =========================
def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def new_request_id() -> str:
    return uuid.uuid4().hex


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


def build_proxy_snapshot() -> List[Dict[str, Any]]:
    rows = get_all_proxies()
    running = set(list_running_proxies())
    data = []
    for item_id, ipv6, group, port, interface in rows:
        status = "running" if int(port) in running else "stopped"
        data.append(
            {
                "id": item_id,
                "port": int(port),
                "ipv6": ipv6,
                "group": group,
                "interface": interface,
                "status": status,
            }
        )
    return data


def get_next_port() -> int:
    used_ports = set()
    for row in get_all_proxies():
        try:
            used_ports.add(int(row[3]))
        except (TypeError, ValueError):
            continue

    port = 10000
    while port in used_ports:
        port += 1
    return port


def reserve_next_port_and_insert(ipv6: str, group_name: str, interface_name: str) -> int:
    """
    Reserve smallest available port from 10000 and insert in one SQLite transaction.
    This avoids duplicate ports under concurrent create requests.
    """
    conn = db_connect()
    try:
        conn.execute("BEGIN IMMEDIATE")
        cur = conn.cursor()
        cur.execute("SELECT port FROM ipv6_address")
        used_ports = set()
        for (port_value,) in cur.fetchall():
            try:
                used_ports.add(int(port_value))
            except (TypeError, ValueError):
                continue

        port = 10000
        while port in used_ports:
            port += 1

        cur.execute(
            "INSERT INTO ipv6_address (ipv6, group_name, port, interface_name) VALUES (?,?,?,?)",
            (ipv6, group_name, str(port), interface_name),
        )
        conn.commit()
        return port
    finally:
        conn.close()


async def emit_operation(
    op: str,
    status: str,
    message: str,
    request_id: str,
    data: Dict[str, Any] | None = None,
):
    await socket_hub.broadcast(
        {
            "type": "operation",
            "op": op,
            "status": status,
            "message": message,
            "request_id": request_id,
            "data": data or {},
            "ts": now_iso(),
        }
    )


async def emit_proxy_snapshot():
    await socket_hub.broadcast(
        {
            "type": "proxy_snapshot",
            "data": build_proxy_snapshot(),
            "ts": now_iso(),
        }
    )


# =========================
# API Models
# =========================
class ProxyCreate(BaseModel):
    group_name: str
    interface_name: str = "Ethernet"
    custom_ipv6: str | None = None


# =========================
# Services
# =========================
def _normalize_custom_ipv6(custom_ipv6: str | None) -> str | None:
    if not custom_ipv6:
        return None
    value = custom_ipv6.strip()
    if not value:
        return None
    try:
        ipaddress.IPv6Address(value)
    except ValueError:
        raise HTTPException(status_code=400, detail="custom_ipv6 must be a valid IPv6 address")
    return value


async def svc_create_proxy(
    group_name: str, interface_name: str, request_id: str, custom_ipv6: str | None = None
):
    await emit_operation(
        "proxy.create",
        "started",
        f"Creating proxy on interface {interface_name}",
        request_id,
        {"group_name": group_name, "interface_name": interface_name},
    )

    normalized_custom_ipv6 = _normalize_custom_ipv6(custom_ipv6)
    if normalized_custom_ipv6:
        ipv6 = normalized_custom_ipv6
    else:
        generated = generate_ipv6_addresses(1)
        if not generated:
            msg = "Cannot generate IPv6 address"
            await emit_operation("proxy.create", "error", msg, request_id)
            raise HTTPException(status_code=500, detail=msg)
        ipv6 = generated[0]

    try:
        await add_ipv6_to_ethernet(ipv6, interface_name)
        port = reserve_next_port_and_insert(ipv6, group_name, interface_name)

        t = threading.Thread(
            target=create_proxy,
            args=(
                {
                    "port": port,
                    "ip": ipv6,
                    "interface_name": interface_name,
                    "auto_rotate_ipv6": True,
                },
            ),
            daemon=True,
        )
        t.start()

        result = {"port": port, "ipv6": ipv6, "status": "running"}
        await emit_operation(
            "proxy.create",
            "success",
            f"Created proxy at port {port}",
            request_id,
            result,
        )
        await emit_proxy_snapshot()
        return result
    except HTTPException:
        raise
    except Exception as exc:
        await emit_operation("proxy.create", "error", str(exc), request_id)
        raise HTTPException(status_code=500, detail=str(exc))


async def svc_run_all(request_id: str):
    await emit_operation("proxy.run_all", "started", "Starting all stopped proxies", request_id)

    try:
        await ensure_admin_permission()
    except RuntimeError as exc:
        await emit_operation("proxy.run_all", "error", str(exc), request_id)
        raise HTTPException(status_code=403, detail=str(exc))

    proxies = get_all_proxies()
    started = []
    running_ports = set(list_running_proxies())

    for _, ipv6, _, port, interface_name in proxies:
        port = int(port)
        if port not in running_ports:
            t = threading.Thread(
                target=create_proxy,
                args=(
                    {
                        "port": port,
                        "ip": ipv6,
                        "interface_name": interface_name,
                        "auto_rotate_ipv6": True,
                    },
                ),
                daemon=True,
            )
            t.start()
            started.append(port)

    result = {"started": started}
    await emit_operation(
        "proxy.run_all",
        "success",
        f"Started {len(started)} proxy",
        request_id,
        result,
    )
    await emit_proxy_snapshot()
    return result


async def svc_run_by_ids(ids: List[int], request_id: str):
    await emit_operation(
        "proxy.run_by_ids", "started", f"Run proxies by IDs: {ids}", request_id, {"ids": ids}
    )

    if not ids:
        result = {"detail": "No ids provided", "results": []}
        await emit_operation("proxy.run_by_ids", "success", "No ids provided", request_id, result)
        return result

    try:
        await ensure_admin_permission()
    except RuntimeError as exc:
        await emit_operation("proxy.run_by_ids", "error", str(exc), request_id, {"ids": ids})
        raise HTTPException(status_code=403, detail=str(exc))

    conn = db_connect()
    cur = conn.cursor()

    results: List[Dict[str, Any]] = []
    placeholders = ",".join(["?"] * len(ids))
    cur.execute(
        f"SELECT id, ipv6, group_name, port, interface_name FROM ipv6_address WHERE id IN ({placeholders})",
        tuple(ids),
    )
    rows = cur.fetchall()
    conn.close()

    found_ids = {row[0] for row in rows}
    for item_id in ids:
        if item_id not in found_ids:
            results.append({"id": item_id, "status": "not_found"})

    running_ports = set(list_running_proxies())

    for item_id, ipv6, _, port, interface_name in rows:
        port = int(port)
        if port in running_ports:
            results.append({"id": item_id, "port": port, "status": "already_running"})
        else:
            try:
                t = threading.Thread(
                    target=create_proxy,
                    args=(
                        {
                            "port": port,
                            "ip": ipv6,
                            "interface_name": interface_name,
                            "auto_rotate_ipv6": True,
                        },
                    ),
                    daemon=True,
                )
                t.start()
                results.append({"id": item_id, "port": port, "status": "started"})
            except Exception as exc:
                results.append(
                    {"id": item_id, "port": port, "status": "error", "error": str(exc)}
                )

    result = {"results": results}
    await emit_operation("proxy.run_by_ids", "success", "Run by IDs completed", request_id, result)
    await emit_proxy_snapshot()
    return result


async def svc_stop_by_ids(ids: List[int], request_id: str):
    await emit_operation(
        "proxy.stop_by_ids",
        "started",
        f"Stopping proxies by IDs: {ids}",
        request_id,
        {"ids": ids},
    )

    if not ids:
        result = {"detail": "No ids provided", "results": []}
        await emit_operation("proxy.stop_by_ids", "success", "No ids provided", request_id, result)
        return result

    conn = db_connect()
    cur = conn.cursor()

    results: List[Dict[str, Any]] = []
    placeholders = ",".join(["?"] * len(ids))
    cur.execute(f"SELECT id, port FROM ipv6_address WHERE id IN ({placeholders})", tuple(ids))
    rows = cur.fetchall()
    id_to_port = {row[0]: int(row[1]) for row in rows}

    found_ids = set(id_to_port.keys())
    for item_id in ids:
        if item_id not in found_ids:
            results.append({"id": item_id, "status": "not_found"})

    running_ports = set(list_running_proxies())

    for item_id, port in id_to_port.items():
        try:
            if port in running_ports:
                ok = stop_proxy(port)
                if ok:
                    results.append({"id": item_id, "port": port, "status": "stopped"})
                else:
                    results.append({"id": item_id, "port": port, "status": "stop_failed"})
            else:
                results.append({"id": item_id, "port": port, "status": "not_running"})
        except Exception as exc:
            results.append(
                {"id": item_id, "port": port, "status": "error", "error": str(exc)}
            )

    conn.close()
    result = {"results": results}

    await emit_operation("proxy.stop_by_ids", "success", "Stop by IDs completed", request_id, result)
    await emit_proxy_snapshot()
    return result


async def svc_delete_proxy(id_value: int, request_id: str):
    await emit_operation(
        "proxy.delete",
        "started",
        f"Deleting proxy ID {id_value}",
        request_id,
        {"id": id_value},
    )

    conn = db_connect()
    cur = conn.cursor()
    cur.execute("SELECT id, ipv6, port, interface_name FROM ipv6_address WHERE id=?", (id_value,))
    row = cur.fetchone()
    if not row:
        conn.close()
        await emit_operation("proxy.delete", "error", "Not found", request_id, {"id": id_value})
        raise HTTPException(404, "Not found")

    _, ipv6, port, interface = row
    port = int(port)

    if port in list_running_proxies():
        conn.close()
        msg = "Proxy dang chay, khong the xoa"
        await emit_operation("proxy.delete", "error", msg, request_id, {"id": id_value, "port": port})
        raise HTTPException(400, msg)

    cur.execute("DELETE FROM ipv6_address WHERE id=?", (id_value,))
    await remove_ipv6_address(ipv6, interface)
    conn.commit()
    conn.close()

    result = {"deleted": id_value}
    await emit_operation("proxy.delete", "success", f"Deleted proxy ID {id_value}", request_id, result)
    await emit_proxy_snapshot()
    return result


async def svc_stop_port(port: int, request_id: str):
    await emit_operation("proxy.stop", "started", f"Stopping port {port}", request_id, {"port": port})

    if not stop_proxy(port):
        msg = "Proxy not running"
        await emit_operation("proxy.stop", "error", msg, request_id, {"port": port})
        raise HTTPException(404, msg)

    result = {"stopped": port}
    await emit_operation("proxy.stop", "success", f"Stopped port {port}", request_id, result)
    await emit_proxy_snapshot()
    return result


async def svc_rotate_port(port: int, request_id: str):
    await emit_operation("proxy.rotate", "started", f"Rotating port {port}", request_id, {"port": port})

    conn = db_connect()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, ipv6, group_name, port, interface_name FROM ipv6_address WHERE port=?",
        (str(port),),
    )
    row = cur.fetchone()
    if not row:
        conn.close()
        await emit_operation("proxy.rotate", "error", "Not found", request_id, {"port": port})
        raise HTTPException(404, "Not found")

    item_id, old_ipv6, _, port, interface = row
    port = int(port)

    try:
        stop_proxy(port)
        await remove_ipv6_address(old_ipv6, interface)

        generated = generate_ipv6_addresses(1)
        if not generated:
            msg = "Cannot generate IPv6 address"
            await emit_operation("proxy.rotate", "error", msg, request_id, {"port": port})
            raise HTTPException(status_code=500, detail=msg)

        new_ipv6 = generated[0]
        await add_ipv6_to_ethernet(new_ipv6, interface)

        cur.execute("UPDATE ipv6_address SET ipv6=? WHERE id=?", (new_ipv6, item_id))
        conn.commit()

        t = threading.Thread(
            target=create_proxy,
            args=(
                {
                    "port": port,
                    "ip": new_ipv6,
                    "interface_name": interface,
                    "auto_rotate_ipv6": True,
                },
            ),
            daemon=True,
        )
        t.start()

        result = {"port": port, "ipv6": new_ipv6}
        await emit_operation("proxy.rotate", "success", f"Rotated port {port}", request_id, result)
        await emit_proxy_snapshot()
        return result
    except HTTPException:
        raise
    except Exception as exc:
        await emit_operation("proxy.rotate", "error", str(exc), request_id, {"port": port})
        raise HTTPException(status_code=500, detail=str(exc))
    finally:
        conn.close()


async def svc_network_adapters():
    adapters = get_adapters_ipv4()
    return {"count": len(adapters), "adapters": adapters}


async def svc_network_adapter_ipv6(card_name: str):
    adapter = get_ipv6_by_card_name(card_name)
    if not adapter:
        raise HTTPException(
            status_code=404,
            detail=f"Adapter '{card_name}' not found or no IPv6 assigned",
        )
    return adapter


async def svc_remove_ipv6(card_name: str, ipv6_address: str, request_id: str):
    await emit_operation(
        "network.remove_ipv6",
        "started",
        f"Removing IPv6 from {card_name}",
        request_id,
        {"card_name": card_name, "ipv6_address": ipv6_address},
    )

    adapter = get_ipv6_by_card_name(card_name)
    if not adapter:
        msg = f"Adapter '{card_name}' not found or no IPv6 assigned"
        await emit_operation("network.remove_ipv6", "error", msg, request_id)
        raise HTTPException(status_code=404, detail=msg)

    await remove_ipv6_address(ipv6_address, card_name)
    result = {"removed": ipv6_address, "from": card_name}

    await emit_operation(
        "network.remove_ipv6",
        "success",
        f"Removed IPv6 from {card_name}",
        request_id,
        result,
    )
    return result


# =========================
# HTTP API
# =========================
@app.post("/proxy/create")
async def create_proxy_v6(data: ProxyCreate):
    return await svc_create_proxy(
        data.group_name, data.interface_name, new_request_id(), data.custom_ipv6
    )


@app.post("/proxy/run_all")
async def run_all_proxy():
    return await svc_run_all(new_request_id())


@app.post("/proxy/run_by_ids")
async def run_proxies_by_ids(ids: List[int] = Body(...)):
    return await svc_run_by_ids(ids, new_request_id())


@app.post("/proxy/stop_by_ids")
async def stop_proxies_by_ids(ids: List[int] = Body(...)):
    return await svc_stop_by_ids(ids, new_request_id())


@app.delete("/proxy/{id}")
async def remove_proxy(id: int):
    return await svc_delete_proxy(id, new_request_id())


@app.post("/proxy/stop/{port}")
async def stop_proxy_api(port: int):
    return await svc_stop_port(port, new_request_id())


@app.post("/proxy/rotate/{port}")
async def rotate_proxy(port: int):
    return await svc_rotate_port(port, new_request_id())


@app.get("/proxy")
async def list_proxies():
    return build_proxy_snapshot()


@app.get("/network/adapters")
async def list_network_adapters():
    try:
        return await svc_network_adapters()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Error getting adapters: {exc}")


@app.get("/network/adapters/{card_name}/ipv6")
async def get_ipv6_for_card(card_name: str):
    return await svc_network_adapter_ipv6(card_name)


@app.delete("/network/adapters/{card_name}/ipv6/{ipv6_address}")
async def remove_ipv6_for_card(card_name: str, ipv6_address: str):
    try:
        return await svc_remove_ipv6(card_name, ipv6_address, new_request_id())
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Error removing IPv6: {exc}")


# =========================
# WebSocket realtime + command
# =========================
async def execute_ws_command(action: str, payload: Dict[str, Any], request_id: str):
    if action == "proxy.create":
        group_name = (payload.get("group_name") or "").strip()
        interface_name = (payload.get("interface_name") or "Ethernet").strip() or "Ethernet"
        custom_ipv6 = payload.get("custom_ipv6")
        if not group_name:
            raise HTTPException(status_code=400, detail="group_name is required")
        return await svc_create_proxy(group_name, interface_name, request_id, custom_ipv6)

    if action == "proxy.run_all":
        return await svc_run_all(request_id)

    if action == "proxy.run_by_ids":
        ids = payload.get("ids") or []
        if not isinstance(ids, list):
            raise HTTPException(status_code=400, detail="ids must be a list")
        try:
            normalized_ids = [int(x) for x in ids]
        except (TypeError, ValueError):
            raise HTTPException(status_code=400, detail="ids must contain integers")
        return await svc_run_by_ids(normalized_ids, request_id)

    if action == "proxy.stop_by_ids":
        ids = payload.get("ids") or []
        if not isinstance(ids, list):
            raise HTTPException(status_code=400, detail="ids must be a list")
        try:
            normalized_ids = [int(x) for x in ids]
        except (TypeError, ValueError):
            raise HTTPException(status_code=400, detail="ids must contain integers")
        return await svc_stop_by_ids(normalized_ids, request_id)

    if action == "proxy.stop_port":
        try:
            port = int(payload.get("port"))
        except (TypeError, ValueError):
            raise HTTPException(status_code=400, detail="port must be an integer")
        return await svc_stop_port(port, request_id)

    if action == "proxy.rotate_port":
        try:
            port = int(payload.get("port"))
        except (TypeError, ValueError):
            raise HTTPException(status_code=400, detail="port must be an integer")
        return await svc_rotate_port(port, request_id)

    if action == "proxy.delete":
        try:
            id_value = int(payload.get("id"))
        except (TypeError, ValueError):
            raise HTTPException(status_code=400, detail="id must be an integer")
        return await svc_delete_proxy(id_value, request_id)

    if action == "proxy.list":
        return build_proxy_snapshot()

    if action == "network.adapters":
        return await svc_network_adapters()

    if action == "network.adapter_ipv6":
        card_name = (payload.get("card_name") or "").strip()
        if not card_name:
            raise HTTPException(status_code=400, detail="card_name is required")
        return await svc_network_adapter_ipv6(card_name)

    if action == "network.remove_ipv6":
        card_name = (payload.get("card_name") or "").strip()
        ipv6_address = (payload.get("ipv6_address") or "").strip()
        if not card_name or not ipv6_address:
            raise HTTPException(
                status_code=400,
                detail="card_name and ipv6_address are required",
            )
        return await svc_remove_ipv6(card_name, ipv6_address, request_id)

    raise HTTPException(status_code=400, detail=f"Unknown action: {action}")


@app.websocket("/ws/events")
async def websocket_events(websocket: WebSocket):
    await socket_hub.connect(websocket)
    send_lock = asyncio.Lock()
    command_tasks: set[asyncio.Task] = set()

    async def safe_send(payload: Dict[str, Any]) -> bool:
        async with send_lock:
            try:
                await websocket.send_json(payload)
                return True
            except Exception:
                return False

    async def process_command(action: str, payload: Dict[str, Any], request_id: str):
        try:
            result = await execute_ws_command(action, payload, request_id)
            await safe_send(
                {
                    "type": "command_result",
                    "ok": True,
                    "id": request_id,
                    "action": action,
                    "data": result,
                    "ts": now_iso(),
                }
            )
        except HTTPException as exc:
            await safe_send(
                {
                    "type": "command_result",
                    "ok": False,
                    "id": request_id,
                    "action": action,
                    "error": {
                        "status_code": exc.status_code,
                        "detail": exc.detail,
                    },
                    "ts": now_iso(),
                }
            )
        except Exception as exc:
            await safe_send(
                {
                    "type": "command_result",
                    "ok": False,
                    "id": request_id,
                    "action": action,
                    "error": {
                        "status_code": 500,
                        "detail": str(exc),
                    },
                    "ts": now_iso(),
                }
            )

    try:
        await safe_send(
            {
                "type": "socket_status",
                "status": "connected",
                "message": "Realtime socket connected",
                "ts": now_iso(),
            }
        )
        await safe_send(
            {
                "type": "proxy_snapshot",
                "data": build_proxy_snapshot(),
                "ts": now_iso(),
            }
        )

        while True:
            message = await websocket.receive_json()
            msg_type = message.get("type")

            if msg_type == "ping":
                await safe_send({"type": "pong", "ts": now_iso()})
                continue

            if msg_type != "command":
                await safe_send(
                    {
                        "type": "command_result",
                        "ok": False,
                        "id": message.get("id"),
                        "error": {"status_code": 400, "detail": "Invalid message type"},
                        "ts": now_iso(),
                    }
                )
                continue

            action = (message.get("action") or "").strip()
            request_id = (message.get("id") or new_request_id()).strip()
            payload = message.get("payload") or {}
            task = asyncio.create_task(process_command(action, payload, request_id))
            command_tasks.add(task)
            def _on_done(done_task: asyncio.Task):
                command_tasks.discard(done_task)
                try:
                    done_task.exception()
                except asyncio.CancelledError:
                    pass
                except Exception:
                    pass
            task.add_done_callback(_on_done)
    except WebSocketDisconnect:
        pass
    finally:
        for task in list(command_tasks):
            task.cancel()
        if command_tasks:
            await asyncio.gather(*command_tasks, return_exceptions=True)
        await socket_hub.disconnect(websocket)


@app.get("/", include_in_schema=False)
def client_app():
    client_path = BASE_DIR / "client.html"
    if not client_path.exists():
        raise HTTPException(status_code=404, detail="client.html not found")
    return FileResponse(client_path)


@app.get("/logo", include_in_schema=False)
def client_logo():
    logo_path = BASE_DIR / "solumate_icon.ico"
    if not logo_path.exists():
        raise HTTPException(status_code=404, detail="logo not found")
    return FileResponse(logo_path, media_type="image/x-icon")


@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    return client_logo()


@app.get("/client.js", include_in_schema=False)
def client_script():
    client_js_path = BASE_DIR / "client.js"
    if not client_js_path.exists():
        raise HTTPException(status_code=404, detail="client.js not found")
    return FileResponse(client_js_path, media_type="application/javascript")


def _main():
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=9002,
        reload=False,
        log_level="info",
        access_log=False,
    )


if __name__ == "__main__":
    _main()
