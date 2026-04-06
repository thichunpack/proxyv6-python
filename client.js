const state = {
  adapters: [],
  selectedAdapter: "",
  ipv6Items: [],
  proxies: [],
  selectedIds: new Set(),
  lang: "vi",
  ws: null,
  wsConnected: false,
  wsRetryCount: 0,
  pending: new Map(),
  reconnectTimer: null,
  busy: {
    create: false,
    runAll: false,
    runIds: new Set(),
    stopIds: new Set(),
    stopPorts: new Set(),
    rotatePorts: new Set(),
    deleteIds: new Set(),
    removeIpv6Values: new Set(),
    opTokens: new Map(),
  },
};

const $ = (id) => document.getElementById(id);
const refs = {
  baseUrl: $("baseUrl"),
  langSelect: $("langSelect"),
  saveCfg: $("saveCfg"),
  checkBtn: $("checkBtn"),
  statusDot: $("statusDot"),
  statusText: $("statusText"),
  refreshAdapters: $("refreshAdapters"),
  loadIpv6: $("loadIpv6"),
  clearIpv6: $("clearIpv6"),
  adaptersBox: $("adaptersBox"),
  ipv6Box: $("ipv6Box"),
  createForm: $("createForm"),
  createBtn: $("createForm").querySelector('button[type="submit"]'),
  groupName: $("groupName"),
  ifaceSelect: $("ifaceSelect"),
  customIpv6: $("customIpv6"),
  notifyMode: $("notifyMode"),
  refreshProxies: $("refreshProxies"),
  runAll: $("runAll"),
  runSel: $("runSel"),
  stopSel: $("stopSel"),
  delSel: $("delSel"),
  portInput: $("portInput"),
  stopPort: $("stopPort"),
  rotatePort: $("rotatePort"),
  checkAll: $("checkAll"),
  proxyBody: $("proxyBody"),
  totalC: $("totalC"),
  runC: $("runC"),
  stopC: $("stopC"),
  logBox: $("logBox"),
  toastBox: $("toastBox"),
  donationBox: $("donationBox"),
};

const I18N = {
  vi: {
    "brand.title": "Proxy IPv6 Control Center",
    "donation.kicker": "Ung ho du an",
    "donation.title": "Donation cho tac gia",
    "donation.desc": "Neu du an huu ich, ban co the ung ho de duy tri va phat trien them tinh nang.",
    "donation.momo": "MoMo",
    "donation.bank": "VietinBank",
    "donation.owner": "Chu tai khoan",
    "donation.ownerName": "Doan Thanh Luc",
    "donation.quickCopy": "Sao chep nhanh",
    "status.connected": "Da ket noi realtime",
    "status.disconnected": "Mat ket noi",
    "label.apiBase": "API Base URL",
    "label.groupName": "Ten nhom",
    "label.interface": "Card mang",
    "label.customIpv6": "IPv6 tuy chon (khong bat buoc)",
    "label.notifyMode": "Che do thong bao",
    "notify.quiet": "An",
    "notify.normal": "Day du",
    "section.adapters": "Card mang",
    "section.create": "Tao Proxy",
    "section.fleet": "Danh Sach Proxy",
    "section.activity": "Nhat ky hoat dong",
    "note.interfaceSync": "Danh sach card mang dong bo tu muc adapters.",
    "stat.total": "Tong",
    "stat.running": "Dang chay",
    "stat.stopped": "Da dung",
    "table.id": "ID",
    "table.port": "Port",
    "table.ipv6": "IPv6",
    "table.group": "Nhom",
    "table.interface": "Card",
    "table.status": "Trang thai",
    "table.actions": "Thao tac",
    "btn.save": "Luu cau hinh",
    "btn.check": "Kiem tra ket noi",
    "btn.refreshAdapters": "Tai lai adapters",
    "btn.loadIpv6": "Tai IPv6",
    "btn.clearView": "Xoa view",
    "btn.create": "Tao proxy",
    "btn.refreshList": "Tai lai danh sach",
    "btn.runAll": "Chay tat ca",
    "btn.runSelected": "Chay ID da chon",
    "btn.stopSelected": "Dung ID da chon",
    "btn.deleteSelected": "Xoa da chon",
    "btn.stopByPort": "Dung theo port",
    "btn.rotateByPort": "Xoay theo port",
    "btn.run": "Chay",
    "btn.stop": "Dung",
    "btn.rotate": "Xoay",
    "btn.delete": "Xoa",
    "btn.remove": "Xoa",
    "btn.copy": "Copy",
    "loading.creating": "Dang tao...",
    "loading.running": "Dang chay...",
    "loading.stopping": "Dang dung...",
    "loading.deleting": "Dang xoa...",
    "loading.working": "Dang xu ly...",
    "loading.rotating": "Dang xoay...",
    "loading.removing": "Dang xoa...",
    "empty.noAdapters": "Khong co adapter",
    "empty.noInterface": "Khong co card",
    "empty.selectAdapter": "Chon card mang truoc",
    "empty.noIpv6On": "Khong co IPv6 tren {name}",
    "empty.noProxies": "Chua co proxy",
    "misc.ipv4": "IPv4",
    "misc.ipv6": "IPv6",
    "misc.connected": "Da ket noi",
    "misc.disconnected": "Mat ket noi",
    "misc.invalidPort": "Port khong hop le",
    "status.running": "dang chay",
    "status.stopped": "da dung",
    "msg.configSaved": "Da luu cau hinh",
    "msg.copyDone": "Da sao chep {label}",
    "msg.copyFail": "Khong the sao chep. Vui long copy thu cong",
    "msg.socketConnected": "Socket realtime da ket noi",
    "msg.socketDisconnected": "Socket realtime da ngat ket noi",
    "msg.socketError": "Socket loi",
    "msg.socketInitFailed": "Khoi tao socket loi: {error}",
    "msg.connectionOk": "Kenh lenh realtime hoat dong",
    "msg.connectionFail": "Ket noi that bai: {error}",
    "msg.loadAdaptersOk": "Da tai {count} adapter",
    "msg.loadAdaptersFail": "Tai adapters loi: {error}",
    "msg.selectAdapterFirst": "Vui long chon card mang truoc",
    "msg.loadIpv6Ok": "Da tai IPv6 cho {name}",
    "msg.noIpv6On": "Khong co IPv6 tren {name}",
    "msg.loadIpv6Fail": "Tai IPv6 loi: {error}",
    "msg.removeIpv6Confirm": "Xoa {ipv6} khoi {card_name}?",
    "msg.removeIpv6Fail": "Xoa IPv6 loi: {error}",
    "msg.groupRequired": "Vui long nhap group name",
    "msg.interfaceRequired": "Vui long chon card mang",
    "msg.invalidIpv6": "IPv6 khong hop le",
    "msg.prefillIpv6FromAdapter": "Da dien IPv6 tu card {name}",
    "msg.createProxyFail": "Tao proxy loi: {error}",
    "msg.loadProxyFail": "Tai danh sach proxy loi: {error}",
    "msg.runAllStarted": "Run all da chay {count} port",
    "msg.runAllFail": "Run all loi: {error}",
    "msg.noIdsSelected": "Chua chon ID",
    "msg.runByIdsFail": "Run by IDs loi: {error}",
    "msg.stopByIdsFail": "Stop by IDs loi: {error}",
    "msg.portPositive": "Port phai > 0",
    "msg.stopByPortFail": "Stop theo port loi: {error}",
    "msg.rotateFail": "Rotate loi: {error}",
    "msg.deleteByIdFail": "Xoa ID {id} loi: {error}",
    "msg.deleteSelectedConfirm": "Xoa cac proxy da chon: {ids} ?",
    "msg.deleteDone": "Xoa xong: ok={ok}, fail={fail}",
    "msg.deleteLog": "Xoa da chon: ok={ok}, fail={fail}",
    "msg.deleteProxyConfirm": "Xoa proxy ID {id}?",
    "msg.operationFail": "Thao tac that bai",
    "msg.commandTimeout": "Socket command timeout: {action}",
    "msg.socketNotConnected": "Socket chua ket noi",
    "msg.unknownSocketError": "Loi socket khong xac dinh",
    "op.proxy.create": "Tao proxy",
    "op.proxy.run_all": "Run all",
    "op.proxy.run_by_ids": "Run by IDs",
    "op.proxy.stop_by_ids": "Stop by IDs",
    "op.proxy.stop": "Stop",
    "op.proxy.rotate": "Rotate",
    "op.proxy.delete": "Xoa proxy",
    "op.network.remove_ipv6": "Xoa IPv6",
    "opstatus.started": "bat dau",
    "opstatus.success": "thanh cong",
    "opstatus.error": "loi",
    "opmsg.proxy.create.started": "Dang tao proxy tren card {interface_name}",
    "opmsg.proxy.create.success": "Da tao proxy cong {port}",
    "opmsg.proxy.run_all.started": "Dang chay tat ca proxy da dung",
    "opmsg.proxy.run_all.success": "Da chay {count} proxy",
    "opmsg.proxy.run_by_ids.started": "Dang chay proxy theo IDs",
    "opmsg.proxy.run_by_ids.success": "Chay theo IDs hoan tat",
    "opmsg.proxy.stop_by_ids.started": "Dang dung proxy theo IDs",
    "opmsg.proxy.stop_by_ids.success": "Dung theo IDs hoan tat",
    "opmsg.proxy.stop.started": "Dang dung port {port}",
    "opmsg.proxy.stop.success": "Da dung port {port}",
    "opmsg.proxy.rotate.started": "Dang xoay IP port {port}",
    "opmsg.proxy.rotate.success": "Da xoay IP port {port}",
    "opmsg.proxy.delete.started": "Dang xoa proxy ID {id}",
    "opmsg.proxy.delete.success": "Da xoa proxy ID {id}",
    "opmsg.network.remove_ipv6.started": "Dang xoa IPv6 khoi {card_name}",
    "opmsg.network.remove_ipv6.success": "Da xoa IPv6 khoi {from}",
  },
  en: {
    "brand.title": "Proxy IPv6 Control Center",
    "donation.kicker": "Support project",
    "donation.title": "Donation for the author",
    "donation.desc": "If this project helps you, consider supporting maintenance and future features.",
    "donation.momo": "MoMo",
    "donation.bank": "VietinBank",
    "donation.owner": "Account name",
    "donation.ownerName": "Doan Thanh Luc",
    "donation.quickCopy": "Quick copy",
    "status.connected": "Realtime connected",
    "status.disconnected": "Disconnected",
    "label.apiBase": "API Base URL",
    "label.groupName": "Group name",
    "label.interface": "Interface",
    "label.customIpv6": "Custom IPv6 (optional)",
    "label.notifyMode": "Notification mode",
    "notify.quiet": "Quiet",
    "notify.normal": "Normal",
    "section.adapters": "Network Adapters",
    "section.create": "Create Proxy",
    "section.fleet": "Proxy Fleet",
    "section.activity": "Activity Log",
    "note.interfaceSync": "Interface list syncs from adapters.",
    "stat.total": "Total",
    "stat.running": "Running",
    "stat.stopped": "Stopped",
    "table.id": "ID",
    "table.port": "Port",
    "table.ipv6": "IPv6",
    "table.group": "Group",
    "table.interface": "Interface",
    "table.status": "Status",
    "table.actions": "Actions",
    "btn.save": "Save Config",
    "btn.check": "Check Connection",
    "btn.refreshAdapters": "Refresh adapters",
    "btn.loadIpv6": "Load IPv6",
    "btn.clearView": "Clear view",
    "btn.create": "Create proxy",
    "btn.refreshList": "Refresh list",
    "btn.runAll": "Run all",
    "btn.runSelected": "Run selected IDs",
    "btn.stopSelected": "Stop selected IDs",
    "btn.deleteSelected": "Delete selected",
    "btn.stopByPort": "Stop by port",
    "btn.rotateByPort": "Rotate by port",
    "btn.run": "Run",
    "btn.stop": "Stop",
    "btn.rotate": "Rotate",
    "btn.delete": "Delete",
    "btn.remove": "Remove",
    "btn.copy": "Copy",
    "loading.creating": "Creating...",
    "loading.running": "Running...",
    "loading.stopping": "Stopping...",
    "loading.deleting": "Deleting...",
    "loading.working": "Working...",
    "loading.rotating": "Rotating...",
    "loading.removing": "Removing...",
    "empty.noAdapters": "No adapters found",
    "empty.noInterface": "No interface",
    "empty.selectAdapter": "Select adapter first",
    "empty.noIpv6On": "No IPv6 found on {name}",
    "empty.noProxies": "No proxy data",
    "misc.ipv4": "IPv4",
    "misc.ipv6": "IPv6",
    "misc.connected": "Connected",
    "misc.disconnected": "Disconnected",
    "misc.invalidPort": "Invalid port",
    "status.running": "running",
    "status.stopped": "stopped",
    "msg.configSaved": "Config saved",
    "msg.copyDone": "Copied {label}",
    "msg.copyFail": "Cannot copy automatically. Please copy manually",
    "msg.socketConnected": "Realtime socket connected",
    "msg.socketDisconnected": "Realtime socket disconnected",
    "msg.socketError": "Socket error",
    "msg.socketInitFailed": "Socket init failed: {error}",
    "msg.connectionOk": "Realtime command channel reachable",
    "msg.connectionFail": "Connection failed: {error}",
    "msg.loadAdaptersOk": "Loaded {count} adapters",
    "msg.loadAdaptersFail": "Load adapters failed: {error}",
    "msg.selectAdapterFirst": "Select adapter first",
    "msg.loadIpv6Ok": "Loaded IPv6 for {name}",
    "msg.noIpv6On": "No IPv6 on {name}",
    "msg.loadIpv6Fail": "Load IPv6 failed: {error}",
    "msg.removeIpv6Confirm": "Remove {ipv6} from {card_name}?",
    "msg.removeIpv6Fail": "Remove IPv6 failed: {error}",
    "msg.groupRequired": "Group name is required",
    "msg.interfaceRequired": "Interface is required",
    "msg.invalidIpv6": "Invalid IPv6 format",
    "msg.prefillIpv6FromAdapter": "Prefilled IPv6 from adapter {name}",
    "msg.createProxyFail": "Create proxy failed: {error}",
    "msg.loadProxyFail": "Load proxies failed: {error}",
    "msg.runAllStarted": "Run all started {count} ports",
    "msg.runAllFail": "Run all failed: {error}",
    "msg.noIdsSelected": "No IDs selected",
    "msg.runByIdsFail": "Run by IDs failed: {error}",
    "msg.stopByIdsFail": "Stop by IDs failed: {error}",
    "msg.portPositive": "Port must be positive",
    "msg.stopByPortFail": "Stop by port failed: {error}",
    "msg.rotateFail": "Rotate failed: {error}",
    "msg.deleteByIdFail": "Delete ID {id} failed: {error}",
    "msg.deleteSelectedConfirm": "Delete selected proxies: {ids} ?",
    "msg.deleteDone": "Delete done: ok={ok}, fail={fail}",
    "msg.deleteLog": "Delete selected done: ok={ok}, fail={fail}",
    "msg.deleteProxyConfirm": "Delete proxy ID {id}?",
    "msg.operationFail": "Operation failed",
    "msg.commandTimeout": "Socket command timeout: {action}",
    "msg.socketNotConnected": "Socket is not connected",
    "msg.unknownSocketError": "Unknown socket command error",
    "op.proxy.create": "Create proxy",
    "op.proxy.run_all": "Run all",
    "op.proxy.run_by_ids": "Run by IDs",
    "op.proxy.stop_by_ids": "Stop by IDs",
    "op.proxy.stop": "Stop",
    "op.proxy.rotate": "Rotate",
    "op.proxy.delete": "Delete proxy",
    "op.network.remove_ipv6": "Remove IPv6",
    "opstatus.started": "started",
    "opstatus.success": "success",
    "opstatus.error": "error",
    "opmsg.proxy.create.started": "Creating proxy on {interface_name}",
    "opmsg.proxy.create.success": "Created proxy at port {port}",
    "opmsg.proxy.run_all.started": "Starting all stopped proxies",
    "opmsg.proxy.run_all.success": "Started {count} proxies",
    "opmsg.proxy.run_by_ids.started": "Running proxies by IDs",
    "opmsg.proxy.run_by_ids.success": "Run by IDs completed",
    "opmsg.proxy.stop_by_ids.started": "Stopping proxies by IDs",
    "opmsg.proxy.stop_by_ids.success": "Stop by IDs completed",
    "opmsg.proxy.stop.started": "Stopping port {port}",
    "opmsg.proxy.stop.success": "Stopped port {port}",
    "opmsg.proxy.rotate.started": "Rotating port {port}",
    "opmsg.proxy.rotate.success": "Rotated port {port}",
    "opmsg.proxy.delete.started": "Deleting proxy ID {id}",
    "opmsg.proxy.delete.success": "Deleted proxy ID {id}",
    "opmsg.network.remove_ipv6.started": "Removing IPv6 from {card_name}",
    "opmsg.network.remove_ipv6.success": "Removed IPv6 from {from}",
  },
};

function t(key, vars = {}) {
  const dict = I18N[state.lang] || I18N.en;
  const fallback = I18N.en;
  let text = dict[key] ?? fallback[key] ?? key;
  if (typeof text !== "string") {
    return String(text);
  }
  return text.replace(/\{(\w+)\}/g, (_, name) => String(vars[name] ?? `{${name}}`));
}

function applyI18n() {
  document.documentElement.lang = state.lang;
  document.querySelectorAll("[data-i18n]").forEach((node) => {
    const key = node.getAttribute("data-i18n");
    if (!key) {
      return;
    }
    node.textContent = t(key);
  });
  refs.portInput.placeholder = t("table.port");
  syncBulk();
  applyBusyUI();
}

function localizeOperationMessage(msg) {
  const op = msg?.op || "";
  const status = msg?.status || "";
  const data = msg?.data || {};
  const key = `opmsg.${op}.${status}`;

  if ((I18N[state.lang] && I18N[state.lang][key]) || (I18N.en && I18N.en[key])) {
    const vars = {
      interface_name: data.interface_name || "",
      port: data.port ?? data.stopped ?? "",
      id: data.id ?? data.deleted ?? "",
      card_name: data.card_name || "",
      from: data.from || data.card_name || "",
      count: Array.isArray(data.started)
        ? data.started.length
        : Array.isArray(data.results)
          ? data.results.length
          : "",
    };
    return t(key, vars);
  }

  return msg?.message || "";
}

function setLanguage(lang) {
  const normalized = lang === "en" ? "en" : "vi";
  if (state.lang === normalized) {
    return;
  }
  state.lang = normalized;
  localStorage.setItem("proxy_ui_lang", state.lang);
  if (refs.langSelect) {
    refs.langSelect.value = state.lang;
  }
  applyI18n();
  renderAdapters();
  renderIpv6();
  renderProxies();
}

function initCfg() {
  refs.baseUrl.value = localStorage.getItem("proxy_api_base_url") || "http://127.0.0.1:9002";
  refs.groupName.value = localStorage.getItem("proxy_group_name") || "group-main";
  refs.notifyMode.value = localStorage.getItem("proxy_notify_mode") || "quiet";
  const storedLang = (localStorage.getItem("proxy_ui_lang") || "vi").toLowerCase();
  state.lang = storedLang === "en" ? "en" : "vi";
  if (refs.langSelect) {
    refs.langSelect.value = state.lang;
  }
  applyI18n();
}

function saveCfg() {
  localStorage.setItem("proxy_api_base_url", refs.baseUrl.value.trim());
  localStorage.setItem("proxy_group_name", refs.groupName.value.trim());
  localStorage.setItem("proxy_notify_mode", refs.notifyMode.value || "quiet");
  localStorage.setItem("proxy_ui_lang", state.lang);
  toast(t("msg.configSaved"), "ok");
  connectSocket(true);
}

async function copyText(text) {
  if (!text) {
    throw new Error("empty");
  }
  if (navigator.clipboard && typeof navigator.clipboard.writeText === "function") {
    await navigator.clipboard.writeText(text);
    return;
  }
  const ta = document.createElement("textarea");
  ta.value = text;
  ta.setAttribute("readonly", "");
  ta.style.position = "fixed";
  ta.style.top = "-9999px";
  ta.style.opacity = "0";
  document.body.appendChild(ta);
  ta.focus();
  ta.select();
  let ok = false;
  try {
    ok = document.execCommand("copy");
  } catch (e) {
    ok = false;
  } finally {
    ta.remove();
  }
  if (!ok) {
    throw new Error("copy_failed");
  }
}

const base = () => refs.baseUrl.value.trim().replace(/\/+$/, "");

function wsUrl() {
  const baseUrl = new URL(base());
  baseUrl.protocol = baseUrl.protocol === "https:" ? "wss:" : "ws:";
  baseUrl.pathname = "/ws/events";
  baseUrl.search = "";
  baseUrl.hash = "";
  return baseUrl.toString();
}

function conn(ok, txt) {
  refs.statusDot.classList.toggle("ok", ok);
  refs.statusText.textContent = txt;
}

function log(msg, level = "ok") {
  const n = document.createElement("div");
  n.className = `log ${level}`;
  n.textContent = `[${new Date().toLocaleTimeString()}] ${msg}`;
  refs.logBox.prepend(n);
  while (refs.logBox.children.length > 50) {
    refs.logBox.removeChild(refs.logBox.lastChild);
  }
}

function toast(msg, type = "ok") {
  if (refs.notifyMode?.value === "quiet" && type !== "err") {
    return;
  }
  const n = document.createElement("div");
  n.className = `toast ${type}`;
  n.textContent = msg;
  refs.toastBox.appendChild(n);
  setTimeout(() => n.remove(), 3200);
}

const esc = (v) =>
  String(v)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");

function toInt(value) {
  const n = Number(value);
  return Number.isInteger(n) ? n : null;
}

function isValidIpv6(value) {
  if (!value) {
    return false;
  }
  return /^[0-9a-fA-F:]+$/.test(value) && value.includes(":");
}

function addToSet(setObj, value, active) {
  if (value === null || value === undefined) {
    return;
  }
  if (active) {
    setObj.add(value);
  } else {
    setObj.delete(value);
  }
}

function addManyToSet(setObj, values, active) {
  for (const value of values) {
    addToSet(setObj, value, active);
  }
}

function portByProxyId(id) {
  const item = state.proxies.find((p) => p.id === id);
  return item ? item.port : null;
}

function clearBusyState() {
  state.busy.create = false;
  state.busy.runAll = false;
  state.busy.runIds.clear();
  state.busy.stopIds.clear();
  state.busy.stopPorts.clear();
  state.busy.rotatePorts.clear();
  state.busy.deleteIds.clear();
  state.busy.removeIpv6Values.clear();
  state.busy.opTokens.clear();
  applyBusyUI();
}

function syncCreateFormFromAdapter(autoFillIpv6 = false) {
  if (!state.selectedAdapter) {
    return;
  }
  refs.ifaceSelect.value = state.selectedAdapter;
  if (!autoFillIpv6 || !refs.customIpv6) {
    return;
  }
  if (refs.customIpv6.value.trim()) {
    return;
  }
  const firstIpv6 = (state.ipv6Items || []).find((x) => x?.value)?.value;
  if (!firstIpv6) {
    return;
  }
  refs.customIpv6.value = firstIpv6;
  log(t("msg.prefillIpv6FromAdapter", { name: state.selectedAdapter }), "ok");
}

function setButtonLoading(button, loading, loadingText) {
  if (!button) {
    return;
  }
  if (loading) {
    button.classList.add("is-loading");
    button.textContent = loadingText || `${button.textContent}...`;
  } else {
    button.classList.remove("is-loading");
    const key = button.getAttribute("data-i18n");
    if (key) {
      button.textContent = t(key);
    }
  }
}

function buildBusyToken(msg) {
  const op = msg?.op;
  const data = msg?.data || {};

  if (op === "proxy.create") {
    return { type: "create" };
  }
  if (op === "proxy.run_all") {
    return { type: "run_all" };
  }
  if (op === "proxy.run_by_ids") {
    const ids = new Set();
    if (Array.isArray(data.ids)) {
      for (const raw of data.ids) {
        const id = toInt(raw);
        if (id !== null) {
          ids.add(id);
        }
      }
    }
    if (Array.isArray(data.results)) {
      for (const row of data.results) {
        const id = toInt(row?.id);
        if (id !== null) {
          ids.add(id);
        }
      }
    }
    return { type: "run_by_ids", ids: [...ids] };
  }
  if (op === "proxy.stop_by_ids") {
    const ids = new Set();
    const ports = new Set();
    if (Array.isArray(data.ids)) {
      for (const raw of data.ids) {
        const id = toInt(raw);
        if (id !== null) {
          ids.add(id);
          const port = portByProxyId(id);
          if (port !== null) {
            ports.add(port);
          }
        }
      }
    }
    if (Array.isArray(data.results)) {
      for (const row of data.results) {
        const id = toInt(row?.id);
        if (id !== null) {
          ids.add(id);
        }
        const port = toInt(row?.port);
        if (port !== null) {
          ports.add(port);
        }
      }
    }
    return { type: "stop_by_ids", ids: [...ids], ports: [...ports] };
  }
  if (op === "proxy.stop") {
    const port = toInt(data.port ?? data.stopped);
    return { type: "stop_port", ports: port === null ? [] : [port] };
  }
  if (op === "proxy.rotate") {
    const port = toInt(data.port);
    return { type: "rotate_port", ports: port === null ? [] : [port] };
  }
  if (op === "proxy.delete") {
    const id = toInt(data.id ?? data.deleted);
    return { type: "delete", ids: id === null ? [] : [id] };
  }
  if (op === "network.remove_ipv6") {
    const value = (data.ipv6_address || data.removed || "").toString().trim();
    return { type: "remove_ipv6", values: value ? [value] : [] };
  }
  return null;
}

function applyBusyToken(token, active) {
  if (!token) {
    return;
  }

  switch (token.type) {
    case "create":
      state.busy.create = active;
      break;
    case "run_all":
      state.busy.runAll = active;
      break;
    case "run_by_ids":
      addManyToSet(state.busy.runIds, token.ids || [], active);
      break;
    case "stop_by_ids":
      addManyToSet(state.busy.stopIds, token.ids || [], active);
      addManyToSet(state.busy.stopPorts, token.ports || [], active);
      break;
    case "stop_port":
      addManyToSet(state.busy.stopPorts, token.ports || [], active);
      break;
    case "rotate_port":
      addManyToSet(state.busy.rotatePorts, token.ports || [], active);
      break;
    case "delete":
      addManyToSet(state.busy.deleteIds, token.ids || [], active);
      break;
    case "remove_ipv6":
      addManyToSet(state.busy.removeIpv6Values, token.values || [], active);
      break;
    default:
      break;
  }
  applyBusyUI();
}

function applyBusyUI() {
  setButtonLoading(refs.createBtn, state.busy.create, t("loading.creating"));
  setButtonLoading(refs.runAll, state.busy.runAll, t("loading.running"));
  setButtonLoading(refs.runSel, state.busy.runIds.size > 0, t("loading.running"));
  setButtonLoading(
    refs.stopSel,
    state.busy.stopIds.size > 0 || state.busy.stopPorts.size > 0,
    t("loading.stopping"),
  );
  setButtonLoading(refs.delSel, state.busy.deleteIds.size > 0, t("loading.deleting"));
  setButtonLoading(
    refs.loadIpv6,
    state.busy.removeIpv6Values.size > 0,
    t("loading.working"),
  );
  renderProxies();
  renderIpv6();
}

function renderAdapters() {
  if (!state.adapters.length) {
    refs.adaptersBox.innerHTML = `<div class="empty">${t("empty.noAdapters")}</div>`;
    refs.ifaceSelect.innerHTML = `<option value="">${t("empty.noInterface")}</option>`;
    return;
  }

  refs.adaptersBox.innerHTML = state.adapters
    .map((a) => {
      const active = a.card_name === state.selectedAdapter ? "active" : "";
      return `<div class="adapter ${active}" data-adapter="${esc(a.card_name)}"><div class="aname">${esc(
        a.card_name,
      )}</div><div class="muted">${t("misc.ipv4")}: ${esc(a.ipv4 || "n/a")}</div></div>`;
    })
    .join("");

  refs.ifaceSelect.innerHTML = state.adapters
    .map((a) => {
      const sel = a.card_name === state.selectedAdapter ? "selected" : "";
      return `<option value="${esc(a.card_name)}" ${sel}>${esc(a.card_name)}</option>`;
    })
    .join("");
  syncCreateFormFromAdapter(false);
}

function renderIpv6() {
  if (!state.selectedAdapter) {
    refs.ipv6Box.innerHTML = `<div class="empty">${t("empty.selectAdapter")}</div>`;
    return;
  }

  if (!state.ipv6Items.length) {
    refs.ipv6Box.innerHTML = `<div class="empty">${t("empty.noIpv6On", { name: esc(
      state.selectedAdapter,
    ) })}</div>`;
    return;
  }

  refs.ipv6Box.innerHTML = state.ipv6Items
    .map(
      (x) => `
        <div class="ipv6">
          <div class="ipv6top"><strong>${esc(x.type || t("misc.ipv6"))}</strong><button class="tiny d rm-ip ${
            state.busy.removeIpv6Values.has(x.value) ? "is-loading" : ""
          }" data-ipv6="${esc(x.value)}" ${
            state.busy.removeIpv6Values.has(x.value) ? "disabled" : ""
          }>${state.busy.removeIpv6Values.has(x.value) ? t("loading.removing") : t("btn.remove")}</button></div>
          <div class="mono" data-fill-ipv6="${esc(x.value)}">${esc(x.value)}</div>
        </div>
      `,
    )
    .join("");
}

function renderProxies() {
  const running = state.proxies.filter((p) => p.status === "running").length;
  refs.totalC.textContent = String(state.proxies.length);
  refs.runC.textContent = String(running);
  refs.stopC.textContent = String(state.proxies.length - running);

  if (!state.proxies.length) {
    refs.proxyBody.innerHTML = `<tr><td colspan="8"><div class="empty">${t("empty.noProxies")}</div></td></tr>`;
    refs.checkAll.checked = false;
    syncBulk();
    return;
  }

  refs.proxyBody.innerHTML = state.proxies
    .map((p) => {
      const chk = state.selectedIds.has(p.id) ? "checked" : "";
      const badge = p.status === "running" ? "running" : "stopped";
      const statusText = t(`status.${p.status}`);
      const runBusy = state.busy.runAll || state.busy.runIds.has(p.id);
      const stopBusy = state.busy.stopIds.has(p.id) || state.busy.stopPorts.has(p.port);
      const rotateBusy = state.busy.rotatePorts.has(p.port);
      const deleteBusy = state.busy.deleteIds.has(p.id);
      const rowBusy = runBusy || stopBusy || rotateBusy || deleteBusy;
      return `
          <tr class="${rowBusy ? "row-busy" : ""}">
            <td><input type="checkbox" class="row-check" data-id="${p.id}" ${chk} /></td>
            <td>${p.id}</td>
            <td>${p.port}</td>
            <td class="mono">${esc(p.ipv6)}</td>
            <td>${esc(p.group || "")}</td>
            <td>${esc(p.interface || "")}</td>
            <td><span class="badge ${badge}">${esc(statusText)}</span></td>
            <td>
              <div class="acts">
                <button class="tiny g act-run ${runBusy ? "is-loading" : ""}" data-id="${p.id}" ${
                  rowBusy ? "disabled" : ""
                }>${runBusy ? t("loading.running") : t("btn.run")}</button>
                <button class="tiny w act-stop ${stopBusy ? "is-loading" : ""}" data-port="${p.port}" ${
                  rowBusy ? "disabled" : ""
                }>${stopBusy ? t("loading.stopping") : t("btn.stop")}</button>
                <button class="tiny p act-rotate ${rotateBusy ? "is-loading" : ""}" data-port="${p.port}" ${
                  rowBusy ? "disabled" : ""
                }>${rotateBusy ? t("loading.rotating") : t("btn.rotate")}</button>
                <button class="tiny d act-del ${deleteBusy ? "is-loading" : ""}" data-id="${p.id}" ${
                  rowBusy ? "disabled" : ""
                }>${deleteBusy ? t("loading.deleting") : t("btn.delete")}</button>
              </div>
            </td>
          </tr>
        `;
    })
    .join("");

  refs.checkAll.checked =
    state.proxies.length > 0 && state.proxies.every((p) => state.selectedIds.has(p.id));
  syncBulk();
}

function syncBulk() {
  const dis = state.selectedIds.size === 0;
  refs.runSel.disabled = dis || state.busy.runAll || state.busy.runIds.size > 0;
  refs.stopSel.disabled =
    dis || state.busy.stopIds.size > 0 || state.busy.stopPorts.size > 0;
  refs.delSel.disabled = dis || state.busy.deleteIds.size > 0;
  refs.runAll.disabled = state.busy.runAll;
  refs.createBtn.disabled = state.busy.create;
}

function newCommandId() {
  if (typeof crypto !== "undefined" && crypto.randomUUID) {
    return crypto.randomUUID();
  }
  return `${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

function clearPending(reason) {
  for (const [id, pending] of state.pending.entries()) {
    clearTimeout(pending.timer);
    pending.reject(new Error(reason));
    state.pending.delete(id);
  }
}

function connectSocket(force = false) {
  if (force && state.ws) {
    try {
      state.ws.close();
    } catch {
      // noop
    }
  }

  if (state.ws && state.ws.readyState === WebSocket.OPEN) {
    return;
  }
  if (state.ws && state.ws.readyState === WebSocket.CONNECTING) {
    return;
  }

  try {
    const socket = new WebSocket(wsUrl());
    state.ws = socket;

    socket.onopen = () => {
      state.wsConnected = true;
      state.wsRetryCount = 0;
      conn(true, t("status.connected"));
      log(t("msg.socketConnected"), "ok");
      if (state.reconnectTimer) {
        clearTimeout(state.reconnectTimer);
        state.reconnectTimer = null;
      }
      socket.send(JSON.stringify({ type: "ping" }));
    };

    socket.onmessage = (event) => {
      handleSocketMessage(event.data);
    };

    socket.onclose = () => {
      state.wsConnected = false;
      conn(false, t("status.disconnected"));
      log(t("msg.socketDisconnected"), "warn");
      clearPending(t("msg.socketDisconnected"));
      clearBusyState();
      scheduleReconnect();
    };

    socket.onerror = () => {
      log(t("msg.socketError"), "err");
    };
  } catch (e) {
    state.wsConnected = false;
    conn(false, t("status.disconnected"));
    log(t("msg.socketInitFailed", { error: e.message }), "err");
    scheduleReconnect();
  }
}

function scheduleReconnect() {
  if (state.reconnectTimer) {
    return;
  }
  state.wsRetryCount += 1;
  const waitMs = Math.min(6000, 1000 + state.wsRetryCount * 800);
  state.reconnectTimer = setTimeout(() => {
    state.reconnectTimer = null;
    connectSocket();
  }, waitMs);
}

function ensureSocketReady(timeoutMs = 6000) {
  if (state.ws && state.ws.readyState === WebSocket.OPEN) {
    return Promise.resolve();
  }

  connectSocket();

  return new Promise((resolve, reject) => {
    const started = Date.now();
    const timer = setInterval(() => {
      if (state.ws && state.ws.readyState === WebSocket.OPEN) {
        clearInterval(timer);
        resolve();
        return;
      }

      if (Date.now() - started > timeoutMs) {
        clearInterval(timer);
        reject(new Error(t("msg.socketNotConnected")));
      }
    }, 120);
  });
}

function handleSocketMessage(raw) {
  let msg = null;
  try {
    msg = JSON.parse(raw);
  } catch {
    return;
  }

  if (msg.type === "pong") {
    return;
  }

  if (msg.type === "socket_status") {
    log(msg.message || t("msg.socketConnected"), "ok");
    return;
  }

  if (msg.type === "command_result") {
    const pending = state.pending.get(msg.id);
    if (!pending) {
      return;
    }
    clearTimeout(pending.timer);
    state.pending.delete(msg.id);

    if (msg.ok) {
      pending.resolve(msg.data);
    } else {
      const detail = msg.error?.detail || t("msg.unknownSocketError");
      pending.reject(new Error(`${msg.error?.status_code || 500}: ${detail}`));
    }
    return;
  }

  if (msg.type === "operation") {
    const status = msg.status || "info";
    const opToken = buildBusyToken(msg);

    if (status === "started") {
      if (msg.request_id) {
        state.busy.opTokens.set(msg.request_id, opToken);
      }
      applyBusyToken(opToken, true);
    } else if (status === "success" || status === "error") {
      const trackedToken = msg.request_id ? state.busy.opTokens.get(msg.request_id) : null;
      if (msg.request_id) {
        state.busy.opTokens.delete(msg.request_id);
      }
      applyBusyToken(trackedToken || opToken, false);
    }

    const level = status === "error" ? "err" : status === "started" ? "warn" : "ok";
    const opLabel = t(`op.${msg.op}`);
    const statusLabel = t(`opstatus.${status}`);
    const localizedMsg = localizeOperationMessage(msg);
    const detailMsg = localizedMsg || msg.message || "";
    const text = detailMsg
      ? `[${opLabel}] ${statusLabel} - ${detailMsg}`
      : `[${opLabel}] ${statusLabel}`;
    log(text, level);

    if (status === "success") {
      toast(detailMsg || opLabel, "ok");
    }
    if (status === "error") {
      toast(detailMsg || t("msg.operationFail"), "err");
    }

    if (msg.op === "network.remove_ipv6" && status === "success") {
      loadIpv6().catch(() => {});
    }

    return;
  }

  if (msg.type === "proxy_snapshot") {
    state.proxies = Array.isArray(msg.data) ? msg.data : [];
    const ids = new Set(state.proxies.map((p) => p.id));
    [...state.selectedIds].forEach((id) => {
      if (!ids.has(id)) {
        state.selectedIds.delete(id);
      }
    });
    renderProxies();
  }
}

async function socketCommand(action, payload = {}, timeoutMs = 15000) {
  await ensureSocketReady();

  const id = newCommandId();
  const command = { type: "command", id, action, payload };

  return new Promise((resolve, reject) => {
    const timer = setTimeout(() => {
      state.pending.delete(id);
      reject(new Error(t("msg.commandTimeout", { action })));
    }, timeoutMs);

    state.pending.set(id, { resolve, reject, timer });
    state.ws.send(JSON.stringify(command));
  });
}

async function checkConnection() {
  try {
    connectSocket();
    const data = await socketCommand("proxy.list", {});
    state.proxies = Array.isArray(data) ? data : [];
    renderProxies();
    conn(true, t("status.connected"));
    log(t("msg.connectionOk"), "ok");
    toast(t("misc.connected"), "ok");
  } catch (e) {
    conn(false, t("status.disconnected"));
    log(t("msg.connectionFail", { error: e.message }), "err");
    toast(t("msg.connectionFail", { error: e.message }), "err");
  }
}

async function refreshAdapters() {
  try {
    const d = await socketCommand("network.adapters", {});
    state.adapters = Array.isArray(d.adapters) ? d.adapters : [];

    if (!state.adapters.length) {
      state.selectedAdapter = "";
    } else if (!state.adapters.some((a) => a.card_name === state.selectedAdapter)) {
      state.selectedAdapter = state.adapters[0].card_name;
    }

    renderAdapters();
    renderIpv6();
    log(t("msg.loadAdaptersOk", { count: state.adapters.length }), "ok");
  } catch (e) {
    toast(t("msg.loadAdaptersFail", { error: e.message }), "err");
    log(t("msg.loadAdaptersFail", { error: e.message }), "err");
  }
}

async function loadIpv6() {
  if (!state.selectedAdapter) {
    toast(t("msg.selectAdapterFirst"), "warn");
    return;
  }

  try {
    const d = await socketCommand("network.adapter_ipv6", {
      card_name: state.selectedAdapter,
    });
    state.ipv6Items = Array.isArray(d.ipv6) ? d.ipv6 : [];
    renderIpv6();
    syncCreateFormFromAdapter(true);
    log(t("msg.loadIpv6Ok", { name: state.selectedAdapter }), "ok");
  } catch (e) {
    if (String(e.message).startsWith("404")) {
      state.ipv6Items = [];
      renderIpv6();
      log(t("msg.noIpv6On", { name: state.selectedAdapter }), "warn");
      return;
    }
    toast(t("msg.loadIpv6Fail", { error: e.message }), "err");
    log(t("msg.loadIpv6Fail", { error: e.message }), "err");
  }
}

async function removeIpv6(ip) {
  if (!state.selectedAdapter) {
    return;
  }
  if (!window.confirm(t("msg.removeIpv6Confirm", { ipv6: ip, card_name: state.selectedAdapter }))) {
    return;
  }

  try {
    await socketCommand("network.remove_ipv6", {
      card_name: state.selectedAdapter,
      ipv6_address: ip,
    });
  } catch (e) {
    toast(t("msg.removeIpv6Fail", { error: e.message }), "err");
    log(t("msg.removeIpv6Fail", { error: e.message }), "err");
  }
}

async function createProxy(ev) {
  ev.preventDefault();
  const group = refs.groupName.value.trim();
  const iface = refs.ifaceSelect.value.trim();
  const customIpv6 = refs.customIpv6.value.trim();
  if (!group) {
    toast(t("msg.groupRequired"), "warn");
    return;
  }
  if (!iface) {
    toast(t("msg.interfaceRequired"), "warn");
    return;
  }
  if (customIpv6 && !isValidIpv6(customIpv6)) {
    toast(t("msg.invalidIpv6"), "warn");
    return;
  }

  try {
    const payload = {
      group_name: group,
      interface_name: iface,
    };
    if (customIpv6) {
      payload.custom_ipv6 = customIpv6;
    }
    await socketCommand("proxy.create", payload);
  } catch (e) {
    toast(t("msg.createProxyFail", { error: e.message }), "err");
    log(t("msg.createProxyFail", { error: e.message }), "err");
  }
}
async function refreshProxies() {
  try {
    const d = await socketCommand("proxy.list", {});
    state.proxies = Array.isArray(d) ? d : [];

    const ids = new Set(state.proxies.map((p) => p.id));
    [...state.selectedIds].forEach((id) => {
      if (!ids.has(id)) {
        state.selectedIds.delete(id);
      }
    });

    renderProxies();
  } catch (e) {
    toast(t("msg.loadProxyFail", { error: e.message }), "err");
    log(t("msg.loadProxyFail", { error: e.message }), "err");
  }
}

async function runAll() {
  try {
    const r = await socketCommand("proxy.run_all", {});
    const count = Array.isArray(r.started) ? r.started.length : 0;
    log(t("msg.runAllStarted", { count }), "ok");
  } catch (e) {
    toast(t("msg.runAllFail", { error: e.message }), "err");
    log(t("msg.runAllFail", { error: e.message }), "err");
  }
}

async function runByIds(ids) {
  if (!ids.length) {
    toast(t("msg.noIdsSelected"), "warn");
    return;
  }
  try {
    await socketCommand("proxy.run_by_ids", { ids });
  } catch (e) {
    toast(t("msg.runByIdsFail", { error: e.message }), "err");
    log(t("msg.runByIdsFail", { error: e.message }), "err");
  }
}

async function stopByIds(ids) {
  if (!ids.length) {
    toast(t("msg.noIdsSelected"), "warn");
    return;
  }
  try {
    await socketCommand("proxy.stop_by_ids", { ids });
  } catch (e) {
    toast(t("msg.stopByIdsFail", { error: e.message }), "err");
    log(t("msg.stopByIdsFail", { error: e.message }), "err");
  }
}

async function stopByPort(port) {
  if (!port || port <= 0) {
    toast(t("msg.portPositive"), "warn");
    return;
  }
  try {
    await socketCommand("proxy.stop_port", { port });
  } catch (e) {
    toast(t("msg.stopByPortFail", { error: e.message }), "err");
    log(t("msg.stopByPortFail", { error: e.message }), "err");
  }
}

async function rotateByPort(port) {
  if (!port || port <= 0) {
    toast(t("msg.portPositive"), "warn");
    return;
  }
  try {
    await socketCommand("proxy.rotate_port", { port });
    await loadIpv6();
  } catch (e) {
    toast(t("msg.rotateFail", { error: e.message }), "err");
    log(t("msg.rotateFail", { error: e.message }), "err");
  }
}

async function delById(id, silent = false) {
  try {
    await socketCommand("proxy.delete", { id });
    if (!silent) {
      log(t("op.proxy.delete") + ` #${id}`, "ok");
    }
    return true;
  } catch (e) {
    if (!silent) {
      toast(t("msg.deleteByIdFail", { id, error: e.message }), "err");
      log(t("msg.deleteByIdFail", { id, error: e.message }), "err");
    }
    return false;
  }
}

async function delSelected() {
  const ids = [...state.selectedIds];
  if (!ids.length) {
    toast(t("msg.noIdsSelected"), "warn");
    return;
  }
  if (!window.confirm(t("msg.deleteSelectedConfirm", { ids: ids.join(", ") }))) {
    return;
  }

  let ok = 0;
  let fail = 0;
  for (const id of ids) {
    const done = await delById(id, true);
    if (done) {
      ok += 1;
      state.selectedIds.delete(id);
    } else {
      fail += 1;
    }
  }
  toast(t("msg.deleteDone", { ok, fail }), fail ? "warn" : "ok");
  log(t("msg.deleteLog", { ok, fail }), fail ? "warn" : "ok");
}

function bindEvents() {
  refs.saveCfg.addEventListener("click", saveCfg);
  refs.checkBtn.addEventListener("click", checkConnection);
  refs.langSelect.addEventListener("change", (ev) => {
    setLanguage(ev.target.value);
  });

  refs.refreshAdapters.addEventListener("click", refreshAdapters);
  refs.loadIpv6.addEventListener("click", loadIpv6);
  refs.ifaceSelect.addEventListener("change", async () => {
    state.selectedAdapter = refs.ifaceSelect.value.trim();
    renderAdapters();
    renderIpv6();
    if (state.selectedAdapter) {
      await loadIpv6();
    }
  });
  refs.notifyMode.addEventListener("change", () => {
    localStorage.setItem("proxy_notify_mode", refs.notifyMode.value || "quiet");
  });
  refs.clearIpv6.addEventListener("click", () => {
    state.ipv6Items = [];
    renderIpv6();
  });

  if (refs.donationBox) {
    refs.donationBox.addEventListener("click", async (ev) => {
      const btn = ev.target.closest(".donation-copy");
      if (!btn) {
        return;
      }
      const value = (btn.getAttribute("data-copy") || "").trim();
      const labelKey = btn.getAttribute("data-copy-label") || "donation.kicker";
      if (!value) {
        return;
      }
      try {
        await copyText(value);
        toast(t("msg.copyDone", { label: t(labelKey) }), "ok");
      } catch (e) {
        toast(t("msg.copyFail"), "warn");
      }
    });
  }

  refs.createForm.addEventListener("submit", createProxy);

  refs.refreshProxies.addEventListener("click", refreshProxies);
  refs.runAll.addEventListener("click", runAll);
  refs.runSel.addEventListener("click", () => runByIds([...state.selectedIds]));
  refs.stopSel.addEventListener("click", () => stopByIds([...state.selectedIds]));
  refs.delSel.addEventListener("click", delSelected);

  refs.stopPort.addEventListener("click", () => {
    const p = Number(refs.portInput.value);
    if (!Number.isFinite(p)) {
      return toast(t("misc.invalidPort"), "warn");
    }
    stopByPort(p);
  });

  refs.rotatePort.addEventListener("click", () => {
    const p = Number(refs.portInput.value);
    if (!Number.isFinite(p)) {
      return toast(t("misc.invalidPort"), "warn");
    }
    rotateByPort(p);
  });

  refs.adaptersBox.addEventListener("click", async (ev) => {
    const card = ev.target.closest("[data-adapter]");
    if (!card) {
      return;
    }
    state.selectedAdapter = card.getAttribute("data-adapter");
    renderAdapters();
    renderIpv6();
    await loadIpv6();
  });

  refs.ipv6Box.addEventListener("click", (ev) => {
    const fill = ev.target.closest("[data-fill-ipv6]");
    if (fill && refs.customIpv6) {
      refs.customIpv6.value = fill.getAttribute("data-fill-ipv6") || "";
      return;
    }
    const btn = ev.target.closest(".rm-ip");
    if (!btn) {
      return;
    }
    removeIpv6(btn.getAttribute("data-ipv6"));
  });

  refs.proxyBody.addEventListener("click", (ev) => {
    const run = ev.target.closest(".act-run");
    const stop = ev.target.closest(".act-stop");
    const rot = ev.target.closest(".act-rotate");
    const del = ev.target.closest(".act-del");

    if (run) {
      return runByIds([Number(run.getAttribute("data-id"))]);
    }
    if (stop) {
      return stopByPort(Number(stop.getAttribute("data-port")));
    }
    if (rot) {
      return rotateByPort(Number(rot.getAttribute("data-port")));
    }
    if (del) {
      const id = Number(del.getAttribute("data-id"));
      if (window.confirm(t("msg.deleteProxyConfirm", { id }))) {
        delById(id).then(() => {});
      }
    }
  });

  refs.proxyBody.addEventListener("change", (ev) => {
    const cb = ev.target.closest(".row-check");
    if (!cb) {
      return;
    }
    const id = Number(cb.getAttribute("data-id"));
    if (cb.checked) {
      state.selectedIds.add(id);
    } else {
      state.selectedIds.delete(id);
    }
    syncBulk();
  });

  refs.checkAll.addEventListener("change", (ev) => {
    if (ev.target.checked) {
      state.proxies.forEach((p) => state.selectedIds.add(p.id));
    } else {
      state.selectedIds.clear();
    }
    renderProxies();
  });
}

async function boot() {
  initCfg();
  bindEvents();
  applyBusyUI();
  connectSocket();

  setTimeout(async () => {
    await checkConnection();
    await refreshAdapters();
    await loadIpv6();
    await refreshProxies();
  }, 300);
}

boot();
