import re
import socket
import subprocess
import threading
import traceback

from utils.generate_ipv6 import (
    add_ipv6_to_ethernet_sync,
    generate_ipv6_from_base,
    remove_ipv6_address_sync,
)

# running proxy cache: port -> {"thread": t, "stop": bool, "server_socket": sock}
_running_proxies = {}
lock = threading.Lock()


def create_proxy(data):
    """Start a simple proxy on port=data['port'] and bind outgoing source to data['ip']."""
    listen_port = data["port"]
    source_ipv6 = data["ip"]
    source_address = (source_ipv6, 0)
    interface_name = data.get("interface_name", "Ethernet")
    auto_rotate_ipv6 = bool(data.get("auto_rotate_ipv6", False))

    max_conn = 10000
    buffer_size = 8192

    try:
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind(("", listen_port))
        server_socket.listen(max_conn)
    except Exception:
        return

    with lock:
        _running_proxies[listen_port] = {
            "thread": threading.current_thread(),
            "stop": False,
            "server_socket": server_socket,
        }

    try:
        while True:
            if _running_proxies[listen_port]["stop"]:
                break
            try:
                server_socket.settimeout(1.0)
                conn, _ = server_socket.accept()
                data = conn.recv(buffer_size)
                if not data:
                    conn.close()
                    continue

                if auto_rotate_ipv6:
                    rotated = rotate_source_ipv6(source_ipv6, interface_name)
                    if rotated:
                        source_ipv6 = rotated
                        source_address = (source_ipv6, 0)

                threading.Thread(
                    target=handle_client,
                    args=(conn, data, source_address, buffer_size),
                    daemon=True,
                ).start()
            except socket.timeout:
                continue
            except Exception:
                traceback.print_exc()
    finally:
        server_socket.close()
        with lock:
            if listen_port in _running_proxies:
                del _running_proxies[listen_port]


def handle_client(conn, data, source_address, buffer_size):
    try:
        first_line = data.decode("latin-1", errors="ignore").split("\n")[0]
        if "CONNECT" in first_line:
            target_host, target_port = first_line.split(" ")[1].split(":")
            target_port = int(target_port)
            try:
                with socket.create_connection(
                    (target_host, target_port), source_address=source_address
                ) as remote_socket:
                    conn.sendall(b"HTTP/1.1 200 Connection established\r\n\r\n")
                    threading.Thread(
                        target=forward,
                        args=(conn, remote_socket, buffer_size),
                        daemon=True,
                    ).start()
                    forward(remote_socket, conn, buffer_size)
            except socket.gaierror:
                conn.sendall(b"HTTP/1.1 502 Bad Gateway\r\n\r\n")
        else:
            parts = first_line.split(" ")
            if len(parts) > 1:
                _ = parts[1]
    except Exception:
        traceback.print_exc()
    finally:
        conn.close()


def forward(source, destination, buffer_size):
    try:
        while True:
            data = source.recv(buffer_size)
            if not data:
                break
            destination.sendall(data)
    except Exception:
        pass
    finally:
        source.close()
        destination.close()


def rotate_source_ipv6(current_ipv6: str, interface_name: str) -> str | None:
    generated = generate_ipv6_from_base(current_ipv6, 1)
    if not generated:
        return None

    new_ipv6 = generated[0]
    if new_ipv6 == current_ipv6:
        return current_ipv6

    try:
        add_ipv6_to_ethernet_sync(new_ipv6, interface_name)
        remove_ipv6_address_sync(current_ipv6, interface_name)
        return new_ipv6
    except Exception:
        return None


def get_ipv6_addresses():
    """Extract IPv6 list from ipconfig."""
    result = subprocess.run(
        ["ipconfig"], capture_output=True, text=True, encoding="utf-8", errors="ignore"
    )
    output = result.stdout
    lines = [line.strip() for line in output.splitlines() if "IPv6 Address" in line]
    ipv6_pattern = r"([a-fA-F0-9:]+:[a-fA-F0-9:]+)"
    ipv6_addresses = [
        re.search(ipv6_pattern, line).group(1)
        for line in lines
        if re.search(ipv6_pattern, line)
    ]
    return ipv6_addresses


def start_multi_proxy(list_run_thread):
    """Start multiple proxies."""
    for data in list_run_thread:
        t = threading.Thread(target=create_proxy, args=(data,), daemon=True)
        t.start()


def stop_proxy(port: int):
    """Stop one proxy by port."""
    with lock:
        if port in _running_proxies:
            _running_proxies[port]["stop"] = True
            return True
    return False


def list_running_proxies():
    """Return running proxy ports."""
    with lock:
        # Treat proxies marked for stop as not-running so UI can update
        # immediately after a stop command, without waiting for thread teardown.
        return [
            port
            for port, meta in _running_proxies.items()
            if not bool(meta.get("stop"))
        ]


def runProxy():
    with open("ip6.txt", "r") as file_obj:
        list_ip = file_obj.readlines()
    ipv6_list = [ip.strip() for ip in list_ip]
    filtered_ipv6_list = [ip for ip in ipv6_list if "::" not in ip]
    start_port = 10000
    list_run_thread = [
        {"port": start_port + i, "ip": ipv6}
        for i, ipv6 in enumerate(filtered_ipv6_list)
    ]
    start_multi_proxy(list_run_thread)
