import socket
import threading
import traceback
import subprocess
import re

# Cache quản lý proxy đang chạy: port -> {"thread": t, "stop": False, "server_socket": sock}
_running_proxies = {}
lock = threading.Lock()


def create_proxy(authorization, data):
    """
    Khởi chạy 1 proxy đơn giản, bind IPv6/IPv4 theo data["ip"], port=data["port"]
    """
    listen_port = data["port"]
    source_address = (data["ip"], 0)

    max_conn = 10000
    buffer_size = 8192

    try:
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind(("", listen_port))
        server_socket.listen(max_conn)
    except Exception as e:
        pass
        # print(f"[❌] Lỗi tạo socket trên port {listen_port}: {e}")
        return

    with lock:
        _running_proxies[listen_port] = {
            "thread": threading.current_thread(),
            "stop": False,
            "server_socket": server_socket,
        }

    pass
    # print(f"[✅] Proxy listen on port {listen_port} (ip {data['ip']})")

    try:
        while True:
            # check stop flag
            if _running_proxies[listen_port]["stop"]:
                break
            try:
                server_socket.settimeout(1.0)  # tránh block vĩnh viễn
                conn, addr = server_socket.accept()
                data = conn.recv(buffer_size)
                if not data:
                    conn.close()
                    continue
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
        pass
        # print(f"[⏹] Proxy on port {listen_port} stopped.")


def handle_client(conn, data, source_address, buffer_size):
    try:
        first_line = data.decode("latin-1", errors="ignore").split("\n")[0]
        if "CONNECT" in first_line:
            # HTTPS CONNECT request
            target_host, target_port = first_line.split(" ")[1].split(":")
            target_port = int(target_port)
            pass
            # print(f"[🔗] CONNECT {target_host}:{target_port}")
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
            except socket.gaierror as e:
                pass
                # print(f"[❌] DNS error {target_host}:{target_port} - {e}")
                conn.sendall(b"HTTP/1.1 502 Bad Gateway\r\n\r\n")
        else:
            # HTTP request
            parts = first_line.split(" ")
            if len(parts) > 1:
                url = parts[1]
                pass
                # print(f"[🌐] HTTP request for: {url}")
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
    except Exception as e:
        pass
        # print(f"[⚠️] Forward error: {e}")
    finally:
        source.close()
        destination.close()


def get_ipv6_addresses():
    """Trích xuất danh sách IPv6 từ ipconfig"""
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
    """Khởi chạy nhiều proxy cùng lúc"""
    for data in list_run_thread:
        t = threading.Thread(target=create_proxy, args=(data,), daemon=True)
        t.start()


def stop_proxy(authorization, port: int):
    """Dừng 1 proxy theo port"""
    with lock:
        if port in _running_proxies:
            _running_proxies[port]["stop"] = True
            return True
    return False


def list_running_proxies(authorization):
    """Trả về danh sách proxy đang chạy"""
    with lock:
        return list(_running_proxies.keys())


def runProxy():
    with open("ip6.txt", "r") as f:
        list_ip = f.readlines()
    ipv6_list = [ip.strip() for ip in list_ip]
    filtered_ipv6_list = [ip for ip in ipv6_list if "::" not in ip]
    start_port = 10000
    list_run_thread = [
        {"port": start_port + i, "ip": ipv6}
        for i, ipv6 in enumerate(filtered_ipv6_list)
    ]
    pass
    # print(list_run_thread)
    start_multi_proxy(list_run_thread)
