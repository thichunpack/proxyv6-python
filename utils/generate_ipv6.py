import random
import time
import httpx
import asyncio
import subprocess
import re
import ctypes

_CACHE_DURATION = 100

# Khai báo biến cache toàn cục trước
_cached_ip = None
_cached_time = 0


def is_admin():
    """Check if the script is running with administrator privileges."""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False


def generate_ipv6_addresses(count=1):
    base_ipv6 = get_ethernet_ipv6_addresses()
    if not base_ipv6:
        return []  # Trả về rỗng nếu không lấy được IPv6 gốc

    components = base_ipv6.split(":")
    generated = []
    for _ in range(count):
        new = components.copy()
        new[4] = f"{random.randint(0x1000, 0xFFFF):x}"
        new[5] = f"{random.randint(0x1000, 0xFFFF):x}"
        new[-1] = f"{random.randint(0x1, 0xFFFF):x}"
        generated.append(":".join(new))
    return generated


def get_ethernet_ipv6_addresses() -> str:
    global _cached_ip, _cached_time

    now = time.time()
    if _cached_ip and (now - _cached_time) < _CACHE_DURATION:
        return _cached_ip  # ✅ Trả từ cache nếu còn hiệu lực

    try:
        with httpx.Client(timeout=5) as client:
            response = client.get("https://api64.ipify.org/?format=json")
            response.raise_for_status()
            ip = response.json().get("ip")
            if ip:
                _cached_ip = ip  # ✅ Cache IP
                _cached_time = time.time()
                return ip
    except Exception as e:
        pass
        # print(f"[❌] Lỗi khi lấy IP public v6: {e}")

    return None


async def add_ipv6_to_ethernet(ipv6_address, interface_name="Ethernet"):
    if not is_admin():
        return "Bạn phải chạy script với quyền Administrator!"

    # Add IPv6 address
    add_ip_cmd = [
        "powershell",
        "-Command",
        f"New-NetIPAddress -InterfaceAlias '{interface_name}' -IPAddress {ipv6_address} -AddressFamily IPv6",
    ]

    # Set IPv6 DNS server (Google DNS)
    set_dns_cmd = [
        "powershell",
        "-Command",
        f"Set-DnsClientServerAddress -InterfaceAlias '{interface_name}' -ServerAddresses @('2001:4860:4860::8888','2001:4860:4860::8844')",
    ]

    try:
        await asyncio.to_thread(
            subprocess.run, add_ip_cmd, check=True, text=True, capture_output=True
        )
        await asyncio.to_thread(
            subprocess.run, set_dns_cmd, check=True, text=True, capture_output=True
        )
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Add IPv6 failed: {e.stderr or e.stdout}")


async def remove_ipv6_address(ipv6_address, interface_name="Ethernet"):
    if not is_admin():
        return "Bạn phải chạy script với quyền Administrator!"
    command = [
        "powershell",
        "-Command",
        f"Remove-NetIPAddress -InterfaceAlias '{interface_name}' -IPAddress {ipv6_address} -AddressFamily IPv6 -Confirm:$false",
    ]

    try:
        await asyncio.to_thread(
            subprocess.run, command, check=True, text=True, capture_output=True
        )
    except subprocess.CalledProcessError as e:
        pass
        # print(f"⚠️ Remove IPv6 failed: {e.stderr or e.stdout or str(e)}")


def get_adapters_ipv4():
    # chạy ipconfig và lấy output
    result = subprocess.run(
        ["ipconfig"], capture_output=True, text=True, encoding="utf-8", errors="ignore"
    )
    lines = result.stdout.splitlines()

    adapters = []
    current_adapter = None
    adapter_info = {}

    for line in lines:
        # Nhận diện adapter mới (dạng: "Ethernet adapter Ethernet:" hoặc "Wireless LAN adapter Wi-Fi:")
        adapter_match = re.match(r"^\s*([^\r\n:]+ adapter .+):", line)
        if adapter_match:
            # lưu lại adapter cũ (nếu có IPv4)
            if current_adapter and "ipv4" in adapter_info:
                adapters.append(adapter_info)

            # tạo adapter mới
            current_adapter = adapter_match.group(1).split("adapter ")[-1].strip()
            adapter_info = {"card_name": current_adapter}

        # Kiểm tra IPv4
        ipv4_match = re.search(r"IPv4 Address[\s.]*: ([^\s]+)", line)
        if ipv4_match:
            adapter_info["ipv4"] = ipv4_match.group(1)

    # check adapter cuối cùng
    if current_adapter and "ipv4" in adapter_info:
        adapters.append(adapter_info)

    return adapters


def get_adapters_ipv6(debug: bool = False):
    result = subprocess.run(
        ["ipconfig"], capture_output=True, text=True, encoding="utf-8", errors="ignore"
    )
    lines = result.stdout.splitlines()

    adapters = []
    current_adapter = None
    adapter_info = {}
    ipv6_list = []

    for line in lines:
        if debug:
            print(f"[LINE] {line}")

        # Nhận diện adapter mới
        adapter_match = re.match(r"^\s*([^\r\n:]+ adapter .+):", line)
        if adapter_match:
            if current_adapter and ipv6_list:
                adapter_info["ipv6"] = ipv6_list
                adapters.append(adapter_info)

            current_adapter = adapter_match.group(1).split("adapter ")[-1].strip()
            adapter_info = {"card_name": current_adapter}
            ipv6_list = []
            if debug:
                print(f"--> Found adapter: {current_adapter}")
            continue

        if current_adapter:
            if not line.strip():
                continue

            if "IPv6 Address" in line or "Temporary IPv6 Address" in line:
                # chỉ tách 1 lần đầu tiên
                parts = line.split(":", 1)
                if debug:
                    print(f"--> Split parts (limit=1): {parts}")
                if len(parts) == 2:
                    addr = parts[1].strip()
                    addr = addr.split("%")[0]  # bỏ %index
                    addr_type = (
                        "Temporary IPv6 Address"
                        if "Temporary" in line
                        else "IPv6 Address"
                    )
                    if debug:
                        print(f"--> Detected {addr_type}: {addr}")
                    ipv6_list.append({"type": addr_type, "value": addr})

    if current_adapter and ipv6_list:
        adapter_info["ipv6"] = ipv6_list
        adapters.append(adapter_info)

    return adapters
def get_ipv6_by_card_name(card_name: str):
    """
    Trả về tất cả IPv6 Address và Temporary IPv6 Address của card_name
    """
    adapters = get_adapters_ipv6()
    for adapter in adapters:
        if adapter["card_name"].lower() == card_name.lower():
            return adapter
    return None
