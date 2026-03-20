import base64
import asyncio
import ctypes
import random
import re
import subprocess
import time

import httpx

_CACHE_DURATION = 100

_cached_ip = None
_cached_time = 0


def is_admin():
    """Check if the script is running with administrator privileges."""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except Exception:
        return False


def _ps_escape(value: str) -> str:
    return str(value).replace("'", "''")


def _run_powershell(command: str):
    result = subprocess.run(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", command],
        text=True,
        capture_output=True,
    )
    if result.returncode != 0:
        output = (result.stderr or result.stdout or "Unknown error").strip()
        raise RuntimeError(output)


def _run_powershell_with_uac(command: str):
    encoded = base64.b64encode(command.encode("utf-16le")).decode("ascii")
    launcher_script = (
        f"$arg='-NoProfile -ExecutionPolicy Bypass -EncodedCommand {encoded}'; "
        "$p = Start-Process -FilePath 'powershell' -Verb RunAs -ArgumentList $arg -Wait -PassThru; "
        "exit $p.ExitCode"
    )
    result = subprocess.run(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", launcher_script],
        text=True,
        capture_output=True,
    )
    if result.returncode != 0:
        output = (result.stderr or result.stdout or "Unknown error").strip()
        lowered = output.lower()
        if "canceled" in lowered or "cancelled" in lowered or "1223" in lowered:
            raise PermissionError("Administrator permission was canceled by user.")
        raise RuntimeError(output)


def _run_with_optional_uac(command: str):
    if is_admin():
        _run_powershell(command)
    else:
        _run_powershell_with_uac(command)


async def ensure_admin_permission():
    if is_admin():
        return

    command = "Write-Output 'admin-check' | Out-Null"
    try:
        await asyncio.to_thread(_run_powershell_with_uac, command)
    except PermissionError:
        raise RuntimeError("UAC was canceled. Please allow Administrator permission.")
    except RuntimeError as exc:
        raise RuntimeError(f"Administrator check failed: {exc}")


def generate_ipv6_addresses(count=1):
    base_ipv6 = get_ethernet_ipv6_addresses()
    if not base_ipv6:
        return []

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
        return _cached_ip

    try:
        with httpx.Client(timeout=5) as client:
            response = client.get("https://api64.ipify.org/?format=json")
            response.raise_for_status()
            ip = response.json().get("ip")
            if ip:
                _cached_ip = ip
                _cached_time = time.time()
                return ip
    except Exception:
        pass

    return None


async def add_ipv6_to_ethernet(ipv6_address, interface_name="Ethernet"):
    interface = _ps_escape(interface_name)
    ipv6 = _ps_escape(ipv6_address)

    command = (
        f"New-NetIPAddress -InterfaceAlias '{interface}' -IPAddress '{ipv6}' -AddressFamily IPv6 -ErrorAction Stop; "
        f"Set-DnsClientServerAddress -InterfaceAlias '{interface}' -ServerAddresses @('2001:4860:4860::8888','2001:4860:4860::8844') -ErrorAction Stop"
    )

    try:
        await asyncio.to_thread(_run_with_optional_uac, command)
    except PermissionError:
        raise RuntimeError("UAC was canceled. Please allow Administrator permission.")
    except RuntimeError as exc:
        raise RuntimeError(f"Add IPv6 failed: {exc}")


async def remove_ipv6_address(ipv6_address, interface_name="Ethernet"):
    interface = _ps_escape(interface_name)
    ipv6 = _ps_escape(ipv6_address)

    command = (
        f"Remove-NetIPAddress -InterfaceAlias '{interface}' -IPAddress '{ipv6}' "
        "-AddressFamily IPv6 -Confirm:$false -ErrorAction Stop"
    )

    try:
        await asyncio.to_thread(_run_with_optional_uac, command)
    except PermissionError:
        raise RuntimeError("UAC was canceled. Please allow Administrator permission.")
    except RuntimeError as exc:
        lowered = str(exc).lower()
        if "no matching msft_netipaddress" in lowered:
            return
        raise RuntimeError(f"Remove IPv6 failed: {exc}")


def get_adapters_ipv4():
    result = subprocess.run(
        ["ipconfig"], capture_output=True, text=True, encoding="utf-8", errors="ignore"
    )
    lines = result.stdout.splitlines()

    adapters = []
    current_adapter = None
    adapter_info = {}

    for line in lines:
        adapter_match = re.match(r"^\s*([^\r\n:]+ adapter .+):", line)
        if adapter_match:
            if current_adapter and "ipv4" in adapter_info:
                adapters.append(adapter_info)

            current_adapter = adapter_match.group(1).split("adapter ")[-1].strip()
            adapter_info = {"card_name": current_adapter}

        ipv4_match = re.search(r"IPv4 Address[\s.]*: ([^\s]+)", line)
        if ipv4_match:
            adapter_info["ipv4"] = ipv4_match.group(1)

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
                parts = line.split(":", 1)
                if debug:
                    print(f"--> Split parts (limit=1): {parts}")
                if len(parts) == 2:
                    addr = parts[1].strip()
                    addr = addr.split("%")[0]
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
    """Return all IPv6 Address and Temporary IPv6 Address by card name."""
    adapters = get_adapters_ipv6()
    for adapter in adapters:
        if adapter["card_name"].lower() == card_name.lower():
            return adapter
    return None
