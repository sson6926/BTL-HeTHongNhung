import { useState, useEffect, useCallback } from "react";
import {
  LineChart, Line, AreaChart, Area,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
} from "recharts";

const API = "/api";

async function apiFetch(path, opts = {}) {
  const res = await fetch(`${API}${path}`, opts);
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || res.statusText);
  }
  return res.json();
}

const api = {
  health:        ()                    => fetch(`${API}/health`).then(r => r.ok),
  listDevices:   ()                    => apiFetch("/devices/"),
  createDevice:  (payload)             => apiFetch("/devices/", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  }),
  updateDevice:  (deviceId, payload)   => apiFetch(`/devices/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ device_id: deviceId, type: "esp32", status: "OFF", ...payload }),
  }),
  deleteDevice:  (deviceId)            => fetch(`${API}/devices/${encodeURIComponent(deviceId)}`, {
    method: "DELETE",
  }).then(async res => {
    if (!res.ok) {
      const body = await res.json().catch(() => ({}));
      throw new Error(body.detail || res.statusText);
    }
  }),
  latestSensors: (deviceId)            => apiFetch(`/sensors/latest?device_id=${encodeURIComponent(deviceId)}`),
  sensorHistory: (metric, limit = 30)  => apiFetch(`/sensors/history?metric_type=${metric}&limit=${limit}`),
  aiForecast:    (deviceId, steps = 12) => apiFetch(`/sensors/predict?device_id=${encodeURIComponent(deviceId)}&steps=${steps}`),
  controlDevice: (deviceId, target, action) => apiFetch(`/devices/${encodeURIComponent(deviceId)}/control`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ target, action }),
  }),
  getThresholds: (deviceId)            => apiFetch(`/devices/${encodeURIComponent(deviceId)}/thresholds`),
  updateThreshold: (deviceId, metric, payload) => apiFetch(`/devices/${encodeURIComponent(deviceId)}/thresholds/${metric}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  }),
};

// ── Pond types ────────────────────────────────────────────────────
const POND_TYPES = {
  generic:   { label: "Chung (mặc định)", icon: "🐟", desc: "Ngưỡng an toàn chung cho các loại thủy sản phổ biến." },
  ca_tra:    { label: "Cá tra / basa",    icon: "🐠", desc: "Cá tra cần O₂ ≥ 3 mg/L, pH 6.5–8, nhiệt độ 26–32°C. Chịu được môi trường khắc nghiệt hơn các loài khác." },
  tom_su:    { label: "Tôm sú",           icon: "🦐", desc: "Tôm sú rất nhạy với NH₃ và pH. Cần O₂ ≥ 5 mg/L, pH 7.5–8.5, độ mặn ổn định." },
  ca_ro_phi: { label: "Cá rô phi",        icon: "🐡", desc: "Cá rô phi chịu được pH rộng (6–9) và nhiệt độ cao. Phù hợp nuôi mật độ dày." },
  ca_chep:   { label: "Cá chép",          icon: "🎏", desc: "Cá chép cần O₂ ≥ 4 mg/L, pH 7–8.5, nhiệt độ lý tưởng 20–28°C." },
};

// ── Sensor metadata ───────────────────────────────────────────────
const METRICS = {
  o2:          { icon: "💧", label: "Oxy hòa tan (O₂)", unit: "mg/L", lo: 5,   hi: 9   },
  ph:          { icon: "⚗️",  label: "Độ pH",            unit: "pH",   lo: 6.5, hi: 8.5 },
  nh3:         { icon: "☣️",  label: "Amoniac (NH₃)",    unit: "mg/L", lo: 0,   hi: 0.5 },
  temperature: { icon: "🌡️", label: "Nhiệt độ nước",    unit: "°C",   lo: 24,  hi: 32  },
  tds:         { icon: "🧪", label: "TDS chất rắn",      unit: "ppm",  lo: 200, hi: 500 },
  turbidity:   { icon: "🌊", label: "Độ đục",            unit: "NTU",  lo: 0,   hi: 20  },
};
const SENSOR_ORDER = ["o2", "ph", "nh3", "temperature", "tds", "turbidity"];
const CONTROL_TARGETS = [
  { target: "oxygen",     name: "Máy sục oxy",   type: "relay", icon: "💨", bg: "#E1F5EE" },
  { target: "pump_fill",  name: "Bơm cấp nước",  type: "pump",  icon: "⬆️", bg: "#E6F1FB" },
  { target: "pump_drain", name: "Bơm xả nước",   type: "pump",  icon: "🚿", bg: "#FAEEDA" },
];
const FEEDER_TARGET = { target: "feeder", name: "Hệ thống cho ăn", type: "feeder", icon: "🐠", bg: "#E6F1FB" };

const PONDS_STORAGE_KEY = "aqua-dashboard-ponds";
const DEFAULT_PONDS = [
  { id: "pond-1", name: "Ao nuoi so 1", esp32Id: "esp32_1", pond_type: "generic" },
];

function normalizePond(raw, index = 0) {
  const name = String(raw?.name ?? "").trim();
  const esp32Id = String(raw?.esp32Id ?? raw?.deviceId ?? "").trim();
  if (!name || !esp32Id) return null;
  // migrate old pond_type keys
  const legacyMap = { catfish: "ca_tra", shrimp: "tom_su", tilapia: "ca_ro_phi", carp: "ca_chep", pangasius: "ca_tra" };
  const rawType = raw?.pond_type || "generic";
  const pond_type = legacyMap[rawType] || rawType;
  return {
    id: String(raw?.id ?? `${esp32Id}-${index}-${Date.now()}`),
    name,
    esp32Id,
    pond_type,
  };
}

function loadPonds() {
  try {
    const parsed = JSON.parse(localStorage.getItem(PONDS_STORAGE_KEY) || "[]");
    const ponds = Array.isArray(parsed)
      ? parsed.map(normalizePond).filter(Boolean)
      : [];
    return ponds.length ? ponds : DEFAULT_PONDS;
  } catch {
    return DEFAULT_PONDS;
  }
}

function deviceDisplay(device) {
  if (device.icon && device.bg)
    return { icon: device.icon, bg: device.bg };
  const n = (device.name || "").toLowerCase();
  if (device.type === "feeder")
    return { icon: "🐠", bg: "#E6F1FB" };
  if (n.includes("suc") || n.includes("oxy") || n.includes("aerator") || n.includes("air") || device.type === "relay")
    return { icon: "💨", bg: "#E1F5EE" };
  if (n.includes("xa") || n.includes("drain") || n.includes("thoat"))
    return { icon: "🚿", bg: "#FAEEDA" };
  if (n.includes("cap") || n.includes("fill") || n.includes("supply"))
    return { icon: "⬆️", bg: "#E6F1FB" };
  return { icon: "🔄", bg: "#E6F1FB" };
}

function statusOf(val, lo, hi) {
  if (val == null || isNaN(val)) return "ok";
  if (val < lo || val > hi) return "danger";
  const margin = (hi - lo) * 0.12;
  if (val < lo + margin || val > hi - margin) return "warning";
  return "ok";
}

// water level: distance (cm) to percent. 3cm=75%, 10cm=0%
function waterLevelPct(distanceCm) {
  if (distanceCm == null) return null;
  const pct = (1 - (distanceCm - 3) / (10 - 3)) * 75;
  return Math.max(0, Math.min(100, pct));
}

// ── CSS ───────────────────────────────────────────────────────────
const CSS = `
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;600&display=swap');
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
  :root {
    --blue-50:#E6F1FB; --blue-100:#B5D4F4; --blue-200:#85B7EB;
    --blue-400:#378ADD; --blue-600:#185FA5; --blue-800:#0C447C; --blue-900:#042C53;
    --teal-50:#E1F5EE; --teal-400:#1D9E75;
    --bg:#F0F6FD; --card:#FFFFFF; --border:rgba(55,138,221,.15); --border-md:rgba(55,138,221,.25);
    --text:#042C53; --text-sec:#185FA5; --text-dim:#378ADD; --muted:#B5D4F4;
    --ok:#1D9E75; --ok-bg:#E1F5EE; --warn:#BA7517; --warn-bg:#FAEEDA;
    --danger:#A32D2D; --danger-bg:#FCEBEB;
    --shadow-sm:0 1px 4px rgba(4,44,83,.07); --shadow:0 2px 12px rgba(4,44,83,.09);
    --font-ui:'Inter',sans-serif; --font-mono:'JetBrains Mono',monospace;
    --radius:12px; --radius-sm:8px;
  }
  body { background:var(--bg); color:var(--text); font-family:var(--font-ui); font-size:14px; }
  ::-webkit-scrollbar{width:4px} ::-webkit-scrollbar-track{background:var(--bg)}
  ::-webkit-scrollbar-thumb{background:var(--blue-100);border-radius:4px}
  .app{display:flex;height:100vh;overflow:hidden}
  .sidebar{width:64px;background:var(--blue-900);display:flex;flex-direction:column;align-items:center;padding:16px 0;gap:4px;flex-shrink:0}
  .logo{width:38px;height:38px;background:var(--blue-400);border-radius:10px;display:flex;align-items:center;justify-content:center;font-size:18px;margin-bottom:20px}
  .nav-btn{width:42px;height:42px;border-radius:10px;background:transparent;border:none;color:var(--blue-200);cursor:pointer;font-size:17px;display:flex;align-items:center;justify-content:center;transition:background .18s,color .18s;position:relative;title:attr(title)}
  .nav-btn:hover{background:rgba(255,255,255,.1);color:#fff}
  .nav-btn.active{background:var(--blue-600);color:#fff}
  .nav-btn.active::after{content:'';position:absolute;right:0;top:50%;transform:translateY(-50%);width:3px;height:22px;background:var(--blue-200);border-radius:3px 0 0 3px}
  .sidebar-bottom{margin-top:auto}
  .main{flex:1;overflow-y:auto;display:flex;flex-direction:column}
  .topbar{display:flex;align-items:center;justify-content:space-between;padding:14px 24px;background:var(--blue-900);border-bottom:1px solid rgba(255,255,255,.08);position:sticky;top:0;z-index:5;flex-shrink:0}
  .topbar h1{font-size:16px;font-weight:700;color:#fff;letter-spacing:-.2px}
  .topbar p{font-size:11px;color:var(--blue-200);font-family:var(--font-mono);margin-top:2px}
  .topbar-right{display:flex;gap:10px;align-items:center}
  .live-pill{display:flex;align-items:center;gap:6px;padding:5px 12px;border-radius:20px;background:rgba(255,255,255,.1);border:1px solid rgba(255,255,255,.15);font-size:11px;color:#fff;font-family:var(--font-mono);font-weight:600}
  .live-dot{width:7px;height:7px;border-radius:50%;box-shadow:0 0 6px currentColor;animation:blink 1.6s infinite}
  @keyframes blink{0%,100%{opacity:1}50%{opacity:.4}}
  .sys-badge{padding:5px 12px;border-radius:20px;font-size:11px;font-family:var(--font-mono);font-weight:700}
  .sys-ok{background:rgba(29,158,117,.2);color:#6ee7c4;border:1px solid rgba(29,158,117,.3)}
  .sys-warn{background:rgba(186,117,23,.2);color:#fcd07a;border:1px solid rgba(186,117,23,.3)}
  .sys-err{background:rgba(163,45,45,.2);color:#fca5a5;border:1px solid rgba(163,45,45,.3)}
  .content{padding:22px 24px;display:flex;flex-direction:column;gap:22px}
  .sec-head{display:flex;align-items:center;justify-content:space-between;margin-bottom:12px}
  .sec-title{font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:1.5px;color:var(--text-sec);display:flex;align-items:center;gap:8px}
  .sec-title::before{content:'';width:12px;height:2px;background:var(--blue-400);display:block;border-radius:2px}
  .sec-note{font-size:11px;color:var(--text-dim);font-family:var(--font-mono)}
  .sensor-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(175px,1fr));gap:12px}
  .s-card{background:var(--card);border:1px solid var(--border);border-radius:var(--radius);padding:16px 18px;box-shadow:var(--shadow-sm);position:relative;overflow:hidden;transition:box-shadow .2s,border-color .2s,transform .2s}
  .s-card:hover{box-shadow:var(--shadow);border-color:var(--border-md);transform:translateY(-1px)}
  .s-card::before{content:'';position:absolute;top:0;left:0;right:0;height:3px;background:var(--c,var(--blue-400));border-radius:var(--radius) var(--radius) 0 0}
  .s-card.ok{--c:var(--ok)} .s-card.warning{--c:var(--warn);border-color:rgba(186,117,23,.25)}
  .s-card.danger{--c:var(--danger);border-color:rgba(163,45,45,.25);animation:d-glow 1.8s infinite}
  @keyframes d-glow{0%,100%{box-shadow:var(--shadow-sm)}50%{box-shadow:0 0 0 3px rgba(163,45,45,.12),var(--shadow)}}
  .s-icon{font-size:20px;margin-bottom:8px}
  .s-label{font-size:10px;color:var(--text-dim);font-family:var(--font-mono);text-transform:uppercase;letter-spacing:1px}
  .s-value{font-size:28px;font-weight:700;color:var(--text);font-family:var(--font-mono);line-height:1;margin:5px 0 4px}
  .s-value em{font-size:12px;font-weight:400;color:var(--text-dim);font-style:normal}
  .s-status{display:inline-flex;align-items:center;gap:5px;font-size:10px;font-weight:700;font-family:var(--font-mono);padding:3px 8px;border-radius:20px;margin-top:6px}
  .s-status::before{content:'';width:5px;height:5px;border-radius:50%;background:currentColor}
  .st-ok{background:var(--ok-bg);color:var(--ok)} .st-warn{background:var(--warn-bg);color:var(--warn)} .st-err{background:var(--danger-bg);color:var(--danger)}
  .s-spark{height:34px;margin-top:10px}
  .two-col{display:grid;grid-template-columns:1fr 1fr;gap:16px}
  @media(max-width:860px){.two-col{grid-template-columns:1fr}}
  .chart-card{background:var(--card);border:1px solid var(--border);border-radius:var(--radius);padding:18px 20px;box-shadow:var(--shadow-sm)}
  .chart-card h3{font-size:13px;font-weight:600;color:var(--text);margin-bottom:4px}
  .chart-card p{font-size:10px;color:var(--text-dim);font-family:var(--font-mono);margin-bottom:14px}
  .tt{background:var(--blue-900);border:1px solid var(--blue-600);border-radius:8px;padding:8px 12px}
  .tt-l{font-size:10px;color:var(--blue-200);font-family:var(--font-mono);margin-bottom:2px}
  .tt-v{font-size:13px;font-weight:600;color:#fff;font-family:var(--font-mono)}
  .device-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:12px}
  .d-card{background:var(--card);border:1px solid var(--border);border-radius:var(--radius);padding:16px 18px;box-shadow:var(--shadow-sm);display:flex;flex-direction:column;gap:12px}
  .d-top{display:flex;align-items:center;gap:12px}
  .d-icon{width:42px;height:42px;border-radius:10px;display:flex;align-items:center;justify-content:center;font-size:19px;flex-shrink:0}
  .d-name{font-size:14px;font-weight:600;color:var(--text)}
  .d-state{font-size:11px;color:var(--text-dim);font-family:var(--font-mono);margin-top:2px}
  .d-note{font-size:11px;color:var(--text-sec);font-family:var(--font-mono);background:var(--blue-50);border-radius:var(--radius-sm);padding:6px 10px;border:1px solid var(--border)}
  .d-id{font-size:9px;color:var(--muted);font-family:var(--font-mono);margin-top:2px}
  .toggle-row{display:flex;align-items:center;justify-content:space-between}
  .toggle-label{font-size:11px;color:var(--text-dim);font-family:var(--font-mono)}
  .toggle{width:44px;height:24px;border-radius:12px;background:var(--muted);border:none;cursor:pointer;position:relative;transition:background .22s}
  .toggle:disabled{opacity:.5;cursor:not-allowed}
  .toggle.on{background:var(--blue-400)}
  .toggle::after{content:'';position:absolute;width:18px;height:18px;border-radius:50%;background:#fff;top:3px;left:3px;transition:transform .22s;box-shadow:0 1px 3px rgba(0,0,0,.2)}
  .toggle.on::after{transform:translateX(20px)}
  .feed-btn{width:100%;padding:10px;background:var(--blue-600);border:none;border-radius:var(--radius-sm);color:#fff;font-weight:700;font-size:13px;font-family:var(--font-ui);cursor:pointer;transition:background .18s,transform .12s}
  .feed-btn:hover{background:var(--blue-800)} .feed-btn:active{transform:scale(.98)} .feed-btn:disabled{background:var(--muted);color:var(--blue-100);cursor:not-allowed}
  .stats-row{display:flex;gap:10px;flex-wrap:wrap}
  .stat-box{flex:1;min-width:80px;background:var(--blue-50);border:1px solid var(--border);border-radius:var(--radius-sm);padding:10px 12px;text-align:center}
  .stat-box .v{font-size:18px;font-weight:700;font-family:var(--font-mono);color:var(--blue-800)}
  .stat-box .l{font-size:9px;color:var(--text-dim);font-family:var(--font-mono);text-transform:uppercase;letter-spacing:1px;margin-top:2px}
  .water-card{background:var(--card);border:1px solid var(--border);border-radius:var(--radius);padding:18px 20px;box-shadow:var(--shadow-sm);display:flex;flex-direction:column;gap:16px}
  .tank-wrap{display:flex;justify-content:center}
  .tank{width:90px;height:150px;border:2px solid var(--border-md);border-radius:var(--radius-sm);position:relative;overflow:hidden;background:var(--blue-50)}
  .tank-fill{position:absolute;bottom:0;left:0;right:0;background:linear-gradient(180deg,var(--blue-200) 0%,var(--blue-400) 100%);transition:height 1s cubic-bezier(.4,0,.2,1)}
  .tank-fill::after{content:'';position:absolute;top:0;left:0;right:0;height:2px;background:var(--blue-100);animation:wave 2s ease-in-out infinite}
  @keyframes wave{0%,100%{opacity:1}50%{opacity:.5}}
  .tank-pct{position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);font-size:17px;font-weight:700;font-family:var(--font-mono);color:var(--blue-900);z-index:1;text-shadow:0 0 8px rgba(255,255,255,.8)}
  .wl-badge{text-align:center}
  .badge{display:inline-block;padding:4px 12px;border-radius:20px;font-size:10px;font-weight:700;font-family:var(--font-mono)}
  .b-ok{background:var(--ok-bg);color:var(--ok)} .b-warn{background:var(--warn-bg);color:var(--warn)} .b-err{background:var(--danger-bg);color:var(--danger)}
  .alerts-card{background:var(--card);border:1px solid var(--border);border-radius:var(--radius);overflow:hidden;box-shadow:var(--shadow-sm)}
  .alert-row{display:flex;align-items:flex-start;gap:10px;padding:10px 16px;border-bottom:1px solid var(--border);transition:background .15s;animation:fadein .3s ease}
  @keyframes fadein{from{opacity:0;transform:translateY(-4px)}to{opacity:1;transform:translateY(0)}}
  .alert-row:hover{background:var(--blue-50)} .alert-row:last-child{border-bottom:none}
  .a-dot{width:7px;height:7px;border-radius:50%;flex-shrink:0;margin-top:4px}
  .a-msg{font-size:12px;color:var(--text)} .a-time{font-size:10px;color:var(--text-dim);font-family:var(--font-mono);margin-top:2px}
  .today-card{background:var(--card);border:1px solid var(--border);border-radius:var(--radius);padding:16px 18px;box-shadow:var(--shadow-sm)}
  .today-row{display:flex;justify-content:space-between;align-items:center;padding:7px 0;border-bottom:1px solid var(--border)}
  .today-row:last-child{border-bottom:none}
  .today-lbl{font-size:11px;color:var(--text-dim);font-family:var(--font-mono)}
  .today-val{font-size:14px;font-weight:700;font-family:var(--font-mono);color:var(--blue-800)}
  .conn-banner{margin:0 24px;padding:10px 14px;border-radius:var(--radius-sm);font-size:12px;font-family:var(--font-mono);background:var(--danger-bg);color:var(--danger);border:1px solid rgba(163,45,45,.25);display:flex;align-items:center;gap:8px}
  .overview-shell{min-height:100vh;background:var(--bg)}
  .overview-main{max-width:1180px;margin:0 auto;padding:26px 24px 34px}
  .overview-hero{background:linear-gradient(135deg,var(--blue-900),var(--blue-600));border-radius:18px;padding:24px 28px;color:#fff;display:flex;justify-content:space-between;gap:20px;box-shadow:var(--shadow)}
  .overview-hero h1{font-size:24px;line-height:1.2;letter-spacing:-.4px;margin-bottom:8px}
  .overview-hero p{color:var(--blue-100);font-size:13px;max-width:620px}
  .overview-stats{display:flex;gap:10px;align-items:flex-start;flex-wrap:wrap}
  .overview-stat{min-width:112px;padding:12px 14px;border-radius:14px;background:rgba(255,255,255,.1);border:1px solid rgba(255,255,255,.15)}
  .overview-stat strong{display:block;font-size:22px;font-family:var(--font-mono)}
  .overview-stat span{font-size:10px;color:var(--blue-100);font-family:var(--font-mono);text-transform:uppercase}
  .overview-layout{display:grid;grid-template-columns:1fr 320px;gap:18px;margin-top:20px;align-items:start}
  .pond-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:14px}
  .pond-card{background:var(--card);border:1px solid var(--border);border-radius:var(--radius);padding:18px;box-shadow:var(--shadow-sm);display:flex;flex-direction:column;gap:14px}
  .pond-card:hover{box-shadow:var(--shadow);border-color:var(--border-md);transform:translateY(-1px);transition:.18s}
  .pond-top{display:flex;gap:12px;align-items:center}
  .pond-icon{width:46px;height:46px;border-radius:14px;background:var(--blue-50);display:flex;align-items:center;justify-content:center;font-size:22px}
  .pond-name{font-size:16px;font-weight:700;color:var(--text)}
  .pond-meta{font-size:11px;color:var(--text-dim);font-family:var(--font-mono);margin-top:3px}
  .pond-info{display:grid;grid-template-columns:1fr 1fr;gap:8px;padding:10px;border-radius:var(--radius-sm);background:var(--blue-50);border:1px solid var(--border)}
  .pond-info span{font-size:10px;color:var(--text-dim);font-family:var(--font-mono)}
  .pond-info strong{display:block;margin-top:3px;color:var(--blue-800);font-family:var(--font-mono);font-size:12px}
  .pond-actions{display:flex;gap:8px;margin-top:auto}
  .primary-btn,.ghost-btn,.danger-btn,.back-btn,.save-btn{border:none;border-radius:10px;padding:9px 12px;font-family:var(--font-mono);font-size:11px;font-weight:700;cursor:pointer;transition:.18s}
  .primary-btn{background:var(--blue-600);color:#fff;flex:1}
  .primary-btn:hover{background:var(--blue-800)}
  .ghost-btn{background:var(--blue-50);color:var(--blue-800);border:1px solid var(--border)}
  .ghost-btn:hover{border-color:var(--border-md);background:#fff}
  .danger-btn{background:var(--danger-bg);color:var(--danger)}
  .back-btn{background:rgba(255,255,255,.1);color:#fff;border:1px solid rgba(255,255,255,.18)}
  .back-btn:hover{background:rgba(255,255,255,.18)}
  .save-btn{background:var(--teal-400);color:#fff;padding:10px 20px}
  .save-btn:hover{opacity:.9}
  .save-btn:disabled{opacity:.5;cursor:not-allowed}
  .pond-form-card{background:var(--card);border:1px solid var(--border);border-radius:var(--radius);padding:18px;box-shadow:var(--shadow-sm)}
  .pond-form-card h3{font-size:14px;margin-bottom:4px}
  .pond-form-card p{font-size:11px;color:var(--text-dim);font-family:var(--font-mono);margin-bottom:14px}
  .form-field{display:flex;flex-direction:column;gap:6px;margin-bottom:12px}
  .form-field label{font-size:10px;font-weight:700;color:var(--text-sec);text-transform:uppercase;letter-spacing:1px}
  .form-field input,.form-field select{border:1px solid var(--border);border-radius:10px;padding:10px 12px;font-family:var(--font-mono);color:var(--text);outline:none;background:#fff}
  .form-field input:focus,.form-field select:focus{border-color:var(--blue-400);box-shadow:0 0 0 3px rgba(55,138,221,.12)}
  .form-field input[readonly]{background:var(--blue-50);color:var(--text-dim);cursor:default}
  .form-error{font-size:11px;color:var(--danger);font-family:var(--font-mono);margin-bottom:10px}
  .save-msg{font-size:11px;font-family:var(--font-mono);margin-top:8px;padding:6px 10px;border-radius:8px;background:var(--ok-bg);color:var(--ok)}
  .save-msg.err{background:var(--danger-bg);color:var(--danger)}
  .empty-pond{background:var(--card);border:1px dashed var(--border-md);border-radius:var(--radius);padding:28px;color:var(--text-dim);font-family:var(--font-mono);text-align:center}
  .thresh-table{width:100%;border-collapse:collapse;font-size:12px}
  .thresh-table th{text-align:left;padding:8px 10px;font-size:10px;color:var(--text-sec);text-transform:uppercase;letter-spacing:1px;border-bottom:2px solid var(--border);font-family:var(--font-mono)}
  .thresh-table td{padding:8px 10px;border-bottom:1px solid var(--border);vertical-align:middle}
  .thresh-table tr:hover td{background:var(--blue-50)}
  .thresh-input{width:70px;border:1px solid var(--border);border-radius:6px;padding:5px 8px;font-family:var(--font-mono);font-size:12px;outline:none;text-align:center}
  .thresh-input:focus{border-color:var(--blue-400)}
  .pond-desc{background:var(--blue-50);border:1px solid var(--border);border-radius:var(--radius-sm);padding:12px 14px;font-size:12px;color:var(--text-sec);margin-bottom:16px;font-family:var(--font-mono)}
  @media(max-width:900px){.overview-layout{display:flex;flex-direction:column}.pond-form-card{width:100%}}
  .footer{text-align:center;padding:14px 0;border-top:1px solid var(--border);font-size:10px;color:var(--text-dim);font-family:var(--font-mono)}
`;

// ── Tooltip ───────────────────────────────────────────────────────
const ChartTT = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="tt">
      <div className="tt-l">{label}</div>
      <div className="tt-v">{typeof payload[0].value === "number" ? payload[0].value.toFixed(2) : payload[0].value}</div>
    </div>
  );
};

// ── SCard ─────────────────────────────────────────────────────────
function SCard({ icon, label, value, unit, lo, hi, history }) {
  const st = statusOf(value, lo, hi);
  const colors = { ok: "#1D9E75", warning: "#BA7517", danger: "#A32D2D" };
  const labels = { ok: "Bình thường", warning: "Cảnh báo", danger: "NGUY HIỂM" };
  const display = value != null ? (+value).toFixed(2) : "--";
  return (
    <div className={`s-card ${st}`}>
      <div className="s-icon">{icon}</div>
      <div className="s-label">{label}</div>
      <div className="s-value">{display}<em> {unit}</em></div>
      <div className={`s-status st-${st === "danger" ? "err" : st}`}>{labels[st]}</div>
      {history?.length > 1 && (
        <div className="s-spark">
          <ResponsiveContainer width="100%" height={34}>
            <LineChart data={history}>
              <Line type="monotone" dataKey="v" dot={false} strokeWidth={1.5} stroke={colors[st]} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
}

// ── DCard ─────────────────────────────────────────────────────────
function DCard({ device, sensorNote, onControl, busy }) {
  const disp = deviceDisplay(device);
  const isOn = device.status === "ON";
  return (
    <div className="d-card">
      <div className="d-top">
        <div className="d-icon" style={{ background: disp.bg }}>{disp.icon}</div>
        <div>
          <div className="d-name">{device.name}</div>
          <div className="d-state">{isOn ? "BẬT" : "TẮT"}{busy ? " · đang gửi…" : ""}</div>
          <div className="d-id">{device.device_id}</div>
        </div>
      </div>
      {sensorNote && <div className="d-note">{sensorNote}</div>}
      <div className="toggle-row">
        <span className="toggle-label">Trạng thái</span>
        <button
          className={`toggle ${isOn ? "on" : ""}`}
          onClick={() => onControl(device.device_id, isOn ? "OFF" : "ON")}
          disabled={busy}
        />
      </div>
    </div>
  );
}

// ── FeederCard ────────────────────────────────────────────────────
function FeederCard({ device, onControl, busy }) {
  return (
    <div className="d-card">
      <div className="d-top">
        <div className="d-icon" style={{ background: "#E6F1FB" }}>🐠</div>
        <div>
          <div className="d-name">{device.name}</div>
          <div className="d-state">{busy ? "Đang phân phối…" : "Sẵn sàng"}</div>
          <div className="d-id">{device.device_id}</div>
        </div>
      </div>
      <div className="stats-row">
        <div className="stat-box"><div className="v">3</div><div className="l">Lan/ngay</div></div>
        <div className="stat-box"><div className="v">08:00</div><div className="l">Lan toi</div></div>
      </div>
      <button className="feed-btn" onClick={() => onControl(device.device_id, "FEED")} disabled={busy}>
        {busy ? "⏳ Đang cho ăn…" : "🐟 Cho ăn ngay"}
      </button>
    </div>
  );
}

// ── AlertRow ──────────────────────────────────────────────────────
function AlertRow({ level, msg, time }) {
  const c = level === "error" ? "#A32D2D" : level === "warn" ? "#BA7517" : "#1D9E75";
  return (
    <div className="alert-row">
      <div className="a-dot" style={{ background: c }} />
      <div>
        <div className="a-msg">{msg}</div>
        <div className="a-time">{time}</div>
      </div>
    </div>
  );
}

// ── App root ──────────────────────────────────────────────────────
export default function App() {
  const [ponds, setPonds] = useState(loadPonds);
  const [selectedPondId, setSelectedPondId] = useState(null);

  useEffect(() => {
    localStorage.setItem(PONDS_STORAGE_KEY, JSON.stringify(ponds));
  }, [ponds]);

  const handleAddPond = useCallback(async (rawPond) => {
    const name = String(rawPond?.name ?? "").trim();
    const esp32Id = String(rawPond?.esp32Id ?? "").trim();
    const pond_type = rawPond?.pond_type || "generic";
    if (!name || !esp32Id) return "Vui long nhap du ten ao va ma ESP32.";
    if (ponds.some(p => p.esp32Id.toLowerCase() === esp32Id.toLowerCase()))
      return "Mã ESP32 nay da duoc gan cho mot ao khac.";
    await api.createDevice({ device_id: esp32Id, name: `ESP32 ${esp32Id}`, type: "esp32", status: "OFF", location: name, pond_type });
    setPonds(prev => [...prev, { id: `${esp32Id}-${Date.now()}`, name, esp32Id, pond_type }]);
    return "";
  }, [ponds]);

  const handleRemovePond = useCallback(async (pondId) => {
    const pond = ponds.find(p => p.id === pondId);
    if (pond?.esp32Id) await api.deleteDevice(pond.esp32Id);
    setPonds(prev => prev.filter(p => p.id !== pondId));
    setSelectedPondId(cur => cur === pondId ? null : cur);
    return "";
  }, [ponds]);

  const selectedPond = ponds.find(p => p.id === selectedPondId);
  if (selectedPond) {
    return <PondDetail key={selectedPond.id} pond={selectedPond} onBack={() => setSelectedPondId(null)} />;
  }
  return <PondOverview ponds={ponds} onAddPond={handleAddPond} onOpenPond={setSelectedPondId} onRemovePond={handleRemovePond} />;
}

// ── PondOverview ──────────────────────────────────────────────────
function PondOverview({ ponds, onAddPond, onOpenPond, onRemovePond }) {
  const [form, setForm] = useState({ name: "", esp32Id: "", pond_type: "generic" });  const [formError, setFormError] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [removing, setRemoving] = useState({});
  const [devices, setDevices] = useState([]);

  useEffect(() => {
    let mounted = true;
    api.listDevices().then(data => mounted && setDevices(data)).catch(() => mounted && setDevices([]));
    return () => { mounted = false; };
  }, []);

  const handleSubmit = async e => {
    e.preventDefault();
    setSubmitting(true);
    setFormError("");
    try {
      const error = await onAddPond(form);
      if (error) { setFormError(error); return; }
      const nextDevices = await api.listDevices();
      setDevices(nextDevices);
      setForm({ name: "", esp32Id: "", pond_type: "generic" });
    } catch (err) {
      setFormError(err.message || "Khong the them thiết bị.");
    } finally {
      setSubmitting(false);
    }
  };

  const handleRemove = async pondId => {
    setRemoving(prev => ({ ...prev, [pondId]: true }));
    try {
      await onRemovePond(pondId);
      const nextDevices = await api.listDevices();
      setDevices(nextDevices);
    } catch (err) {
      setFormError(err.message || "Khong the xoa.");
    } finally {
      setRemoving(prev => ({ ...prev, [pondId]: false }));
    }
  };

  const registeredCount = ponds.filter(p => devices.some(d => d.device_id === p.esp32Id)).length;

  return (
    <>
      <style>{CSS}</style>
      <div className="overview-shell">
        <div className="overview-main">
          <section className="overview-hero">
            <div>
              <h1>Hệ thống giám sát ao nuôi thủy sản</h1>
              <p>Theo dõi chất lượng nước theo thời gian thực, điều khiển thiết bị từ xa và nhận cảnh báo tự động khi thông số vượt ngưỡng an toàn.</p>
            </div>
            <div className="overview-stats">
              <div className="overview-stat"><strong>{ponds.length}</strong><span>Tổng ao</span></div>
              <div className="overview-stat"><strong>{registeredCount}</strong><span>Ao đang hoạt động</span></div>
            </div>
          </section>

          <div className="overview-layout">
            <section>
              <div className="sec-head">
                <div className="sec-title">Danh sách ao</div>
                <span className="sec-note">Chọn ao để xem chi tiết</span>
              </div>
              {ponds.length === 0 ? (
                <div className="empty-pond">Chưa có ao nào. Hãy thêm ao ở biểu mẫu bên phải.</div>
              ) : (
                <div className="pond-grid">
                  {ponds.map(pond => {
                    const device = devices.find(d => d.device_id === pond.esp32Id);
                    const legacyMap = { catfish: "ca_tra", shrimp: "tom_su", tilapia: "ca_ro_phi", carp: "ca_chep", pangasius: "ca_tra" };
                    // Ưu tiên pond_type từ DB (device API), sau đó localStorage, sau đó generic
                    const rawPt = device?.pond_type || pond.pond_type || "generic";
                    const pt = legacyMap[rawPt] || rawPt;
                    const ptInfo = POND_TYPES[pt] || POND_TYPES.generic;
                    return (
                      <article key={pond.id} className="pond-card">
                        <div className="pond-top">
                          <div className="pond-icon">{ptInfo.icon}</div>
                          <div>
                            <div className="pond-name">{pond.name}</div>
                            <div className="pond-meta">Mã ESP32 · {pond.esp32Id}</div>
                          </div>
                        </div>
                        <div className="pond-info">
                          <div><span>Loại nuôi trồng</span><strong>{ptInfo.label}</strong></div>
                          <div><span>Trạng thái</span><strong>{device ? device.status : "Chờ dữ liệu"}</strong></div>
                          <div><span>Mã thiết bị</span><strong>{pond.esp32Id}</strong></div>
                          <div><span>Cập nhật</span><strong>{device?.last_seen ? new Date(device.last_seen).toLocaleTimeString("vi-VN") : "--"}</strong></div>
                        </div>
                        <div className="pond-actions">
                          <button className="primary-btn" onClick={() => onOpenPond(pond.id)}>Chi tiết</button>
                          <button className="danger-btn" onClick={() => handleRemove(pond.id)} disabled={!!removing[pond.id]}>Xóa</button>
                        </div>
                      </article>
                    );
                  })}
                </div>
              )}
            </section>

            <aside className="pond-form-card">
              <h3>Thêm ao mới</h3>
              <p>Nhập tên ao, mã ESP32 và loại nuôi trồng.</p>
              <form onSubmit={handleSubmit}>
                <div className="form-field">
                  <label>Tên ao</label>
                  <input value={form.name} onChange={e => setForm(p => ({ ...p, name: e.target.value }))} placeholder="VD: Ao cá số 2" />
                </div>
                <div className="form-field">
                  <label>Mã ESP32</label>
                  <input value={form.esp32Id} onChange={e => setForm(p => ({ ...p, esp32Id: e.target.value }))} placeholder="VD: esp32_2" />
                </div>
                <div className="form-field">
                  <label>Loại nuôi trồng</label>
                  <select value={form.pond_type} onChange={e => setForm(p => ({ ...p, pond_type: e.target.value }))}>
                    {Object.entries(POND_TYPES).map(([k, v]) => (
                      <option key={k} value={k}>{v.icon} {v.label}</option>
                    ))}
                  </select>
                </div>
                {formError && <div className="form-error">{formError}</div>}
                <button className="primary-btn" type="submit" style={{ width: "100%" }} disabled={submitting}>
                  {submitting ? "Đang thêm..." : "Thêm ao"}
                </button>
              </form>
            </aside>
          </div>
        </div>
      </div>
    </>
  );
}

// ── PondDetail ────────────────────────────────────────────────────
function PondDetail({ pond, onBack }) {
  const [devices,       setDevices]      = useState([]);
  const [sensorHistory, setSensorHistory] = useState({});
  const [latest,        setLatest]        = useState({});
  const [aiForecast,    setAiForecast]    = useState(null);
  const [aiLoading,     setAiLoading]     = useState(false);
  const [aiError,       setAiError]       = useState("");
  const [connected,     setConnected]     = useState(null);
  const [lastPoll,      setLastPoll]      = useState(null);
  const [busy,          setBusy]          = useState({});
  const [targetStatus,  setTargetStatus]  = useState({});
  const [alerts,        setAlerts]        = useState([
    { id: 1, level: "ok", msg: "Frontend khởi động, đang kết nối backend...", time: new Date().toLocaleTimeString("vi-VN") },
  ]);
  const [clock,  setClock]  = useState(new Date());
  const [nav,    setNav]    = useState(0);

  // threshold tab state
  const [thresholds,     setThresholds]     = useState([]);
  const [threshEdits,    setThreshEdits]    = useState({});
  const [pondEdit,       setPondEdit]       = useState({ name: pond.name, device_id: pond.esp32Id, pond_type: pond.pond_type || "generic" });
  const [savingPond,     setSavingPond]     = useState(false);
  const [pondSaveMsg,    setPondSaveMsg]    = useState("");
  const [pondSaveErr,    setPondSaveErr]    = useState(false);
  const [savingThresh,   setSavingThresh]   = useState(false);
  const [threshSaveMsg,  setThreshSaveMsg]  = useState("");
  const [threshSaveErr,  setThreshSaveErr]  = useState(false);

  const esp32Id = pond?.esp32Id || "esp32_1";

  // ── Clock ─────────────────────────────────────────────────────
  useEffect(() => {
    const id = setInterval(() => setClock(new Date()), 1000);
    return () => clearInterval(id);
  }, []);

  const pushAlert = useCallback((level, msg) => {
    setAlerts(prev => {
      const now = Date.now();
      if (prev[0]?.msg === msg && now - prev[0]?.id < 10000) return prev;
      return [{ id: now, level, msg, time: new Date().toLocaleTimeString("vi-VN") }, ...prev].slice(0, 20);
    });
  }, []);

  // ── Load devices ──────────────────────────────────────────────
  useEffect(() => {
    api.listDevices()
      .then(devs => { setDevices(devs); pushAlert("ok", `Đã tải ${devs.length} thiết bị tu backend`); })
      .catch(e => pushAlert("error", `Khong the tai thiết bị: ${e.message}`));
  }, []);

  // ── Load thresholds when on nav 2 ─────────────────────────────
  useEffect(() => {
    if (nav !== 2) return;
    api.getThresholds(esp32Id)
      .then(data => {
        setThresholds(data);
        const edits = {};
        data.forEach(t => { edits[t.metric_type] = { min_value: t.min_value, max_value: t.max_value, auto_control: t.auto_control ?? false, auto_action: t.auto_action ?? "" }; });
        setThreshEdits(edits);
      })
      .catch(() => {});
  }, [nav, esp32Id]);

  // ── Sync pondEdit pond_type from device ───────────────────────
  useEffect(() => {
    if (devices.length === 0) return;
    const device = devices.find(d => d.device_id === esp32Id);
    if (device?.pond_type) {
      setPondEdit(prev => ({ ...prev, pond_type: device.pond_type }));
    }
  }, [devices, esp32Id]);

  // ── Sensor history ────────────────────────────────────────────
  useEffect(() => {
    setSensorHistory({});
    Object.keys(METRICS).concat(["water_level"]).forEach(metric => {
      api.sensorHistory(metric, 30)
        .then(data => {
          const pts = [...data].filter(d => d.device_id === esp32Id).reverse().map(d => ({
            t: new Date(d.created_at).toLocaleTimeString("vi-VN", { hour: "2-digit", minute: "2-digit" }),
            v: d.value,
          }));
          setSensorHistory(h => ({ ...h, [metric]: pts }));
        })
        .catch(() => {});
    });
  }, [esp32Id]);

  // ── AI forecast ───────────────────────────────────────────────
  useEffect(() => {
    let mounted = true;
    setAiLoading(true); setAiError(""); setAiForecast(null);
    api.aiForecast(esp32Id, 12)
      .then(data => { if (mounted) { setAiForecast(data); pushAlert("ok", `AI da du bao ${data.forecast_steps} giờ tiếp theo`); } })
      .catch(error => { if (mounted) setAiError(error.message || "Không thể tải dự báo AI"); })
      .finally(() => { if (mounted) setAiLoading(false); });
    return () => { mounted = false; };
  }, [esp32Id, pushAlert]);

  // ── Poll sensors every 5s ─────────────────────────────────────
  useEffect(() => {
    const poll = async () => {
      try {
        const data = await api.latestSensors(esp32Id);
        const now = new Date().toLocaleTimeString("vi-VN", { hour: "2-digit", minute: "2-digit" });
        const newLatest = {};
        data.forEach(d => { newLatest[d.metric_type] = d.value; });
        setLatest(newLatest);
        setConnected(true);
        setLastPoll(new Date());
        setSensorHistory(h => {
          const nh = { ...h };
          data.forEach(d => {
            const arr = nh[d.metric_type] ?? [];
            const last = arr[arr.length - 1];
            if (!last || last.v !== d.value) {
              nh[d.metric_type] = [...arr.slice(-29), { t: now, v: d.value }];
            }
          });
          return nh;
        });
        const { o2, nh3, temperature, ph } = newLatest;
        if (o2  != null && o2  < 4)   pushAlert("error", `O2 nguy hiem: ${(+o2).toFixed(2)} mg/L`);
        if (nh3 != null && nh3 > 0.6) pushAlert("warn",  `NH3 vuot nguong: ${(+nh3).toFixed(2)} mg/L`);
        if (temperature != null && (temperature < 20 || temperature > 34))
          pushAlert("warn", `Nhiet do bat thuong: ${(+temperature).toFixed(1)} C`);
        if (ph != null && (ph < 6 || ph > 9))
          pushAlert("warn", `pH bat thuong: ${(+ph).toFixed(2)}`);
      } catch {
        setConnected(false);
      }
    };
    poll();
    const id = setInterval(poll, 5000);
    return () => clearInterval(id);
  }, [esp32Id, pushAlert]);

  // ── Control device ────────────────────────────────────────────
  const handleControl = useCallback(async (target, action) => {
    setBusy(b => ({ ...b, [target]: true }));
    try {
      await api.controlDevice(esp32Id, target, action);
      if (action === "ON" || action === "OFF") {
        setTargetStatus(prev => {
          const next = { ...prev, [target]: action };
          // pump_fill and pump_drain are mutually exclusive
          if (action === "ON" && target === "pump_fill")  next["pump_drain"] = "OFF";
          if (action === "ON" && target === "pump_drain") next["pump_fill"]  = "OFF";
          return next;
        });
      }
      pushAlert("ok", `${target}: lenh ${action} thanh cong`);
      const devs = await api.listDevices();
      setDevices(devs);
    } catch (e) {
      pushAlert("error", `${target}: loi - ${e.message}`);
    } finally {
      setBusy(b => ({ ...b, [target]: false }));
    }
  }, [esp32Id, pushAlert]);

  // ── Save pond info ────────────────────────────────────────────
  const handleSavePond = async () => {
    setSavingPond(true); setPondSaveMsg(""); setPondSaveErr(false);
    try {
      // validate: mã ESP32 mới không được trùng ao khác (kiểm tra qua listDevices)
      if (pondEdit.device_id !== esp32Id) {
        const allDevices = await api.listDevices();
        if (allDevices.some(d => d.device_id === pondEdit.device_id)) {
          setPondSaveMsg("Lỗi: Mã ESP32 này đã được sử dụng bởi ao khác.");
          setPondSaveErr(true);
          setSavingPond(false);
          return;
        }
      }
      await api.updateDevice(pondEdit.device_id, { name: pondEdit.name, location: pondEdit.name, pond_type: pondEdit.pond_type });
      setPondSaveMsg("Lưu thông tin ao thành công!");
    } catch (e) {
      setPondSaveMsg("Lỗi: " + e.message);
      setPondSaveErr(true);
    } finally {
      setSavingPond(false);
      setTimeout(() => setPondSaveMsg(""), 3000);
    }
  };

  // ── Save thresholds ───────────────────────────────────────────
  const handleSaveThresholds = async () => {
    setSavingThresh(true); setThreshSaveMsg(""); setThreshSaveErr(false);
    try {
      await Promise.all(
        Object.entries(threshEdits).map(([metric, vals]) =>
          api.updateThreshold(esp32Id, metric, {
            min_value: parseFloat(vals.min_value),
            max_value: parseFloat(vals.max_value),
            auto_control: vals.auto_control,
            auto_action: vals.auto_action,
          })
        )
      );
      setThreshSaveMsg("Lưu ngưỡng cảnh báo thành công!");
    } catch (e) {
      setThreshSaveMsg("Lỗi: " + e.message);
      setThreshSaveErr(true);
    } finally {
      setSavingThresh(false);
      setTimeout(() => setThreshSaveMsg(""), 3000);
    }
  };

  // ── Derived ───────────────────────────────────────────────────
  const wlRaw = latest.water_level ?? null;
  const wl    = waterLevelPct(wlRaw);

  const actuators = CONTROL_TARGETS.map(t => ({ ...t, device_id: t.target, status: targetStatus[t.target] ?? "OFF" }));
  const feeder    = { ...FEEDER_TARGET, device_id: FEEDER_TARGET.target, status: targetStatus[FEEDER_TARGET.target] ?? "OFF" };
  const controllableCount = actuators.length + 1;

  const critSts = ["o2", "ph", "nh3"].map(m => statusOf(latest[m], METRICS[m].lo, METRICS[m].hi));
  const sys     = critSts.some(s => s === "danger") ? "err" : critSts.some(s => s === "warning") ? "warn" : "ok";
  const sysLabel = { ok: "HỆ THỐNG ỔN ĐỊNH", warn: "CÓ CẢNH BÁO", err: "NGUY HIỂM" }[sys];

  const chartLen  = Math.max((sensorHistory.o2 ?? []).length, (sensorHistory.ph ?? []).length, (sensorHistory.nh3 ?? []).length, (sensorHistory.temperature ?? []).length);
  const chartData = Array.from({ length: chartLen }, (_, i) => ({
    t:   sensorHistory.o2?.[i]?.t ?? sensorHistory.ph?.[i]?.t ?? "",
    o2:  sensorHistory.o2?.[i]?.v,
    nh3: sensorHistory.nh3?.[i]?.v,
    ph:  sensorHistory.ph?.[i]?.v,
    tmp: sensorHistory.temperature?.[i]?.v,
  }));

  const aiChartData = (aiForecast?.forecasts ?? []).map(point => ({
    t: new Date(point.forecast_time).toLocaleTimeString("vi-VN", { hour: "2-digit", minute: "2-digit" }),
    ph: point.water_pH, tds: point.TDS, tmp: point.water_temp,
  }));
  const aiLastPoint = aiChartData[aiChartData.length - 1];

  const navIcons = [
    { icon: "⬡", title: "Tổng quan" },
    { icon: "📊", title: "Phân tích & Chẩn đoán" },
    { icon: "⚙️", title: "Ngưỡng cảnh báo" },
    { icon: "📋", title: "Lịch sử" },
    { icon: "🤖", title: "Cơ chế tự động" },
  ];

  const currentPondType = pondEdit.pond_type || "generic";
  const ptDesc = POND_TYPES[currentPondType]?.desc || "";

  return (
    <>
      <style>{CSS}</style>
      <div className="app">
        <nav className="sidebar">
          <div className="logo">🐟</div>
          {navIcons.map((item, i) => (
            <button key={i} className={`nav-btn ${nav === i ? "active" : ""}`} onClick={() => setNav(i)} title={item.title}>{item.icon}</button>
          ))}
          <div className="sidebar-bottom">
            <button className="nav-btn" title="Quay lại" onClick={onBack}>←</button>
          </div>
        </nav>

        <div className="main">
          <header className="topbar">
            <div>
              <h1>Chi tiết {pond?.name || "ao nuôi"}</h1>
              <p>{clock.toLocaleString("vi-VN")} · {esp32Id} · MQTT · MySQL</p>
            </div>
            <div className="topbar-right">
              <button className="back-btn" onClick={onBack}>← Tổng quan</button>
              <div className="live-pill">
                <div className="live-dot" style={{ background: connected === false ? "#f87171" : "#4ade80", color: connected === false ? "#f87171" : "#4ade80" }} />
                {connected === null ? "KẾT NỐI…" : connected ? "LIVE" : "MẤT KẾT NỐI"}
              </div>
              <span className={`sys-badge sys-${sys}`}>{sysLabel}</span>
            </div>
          </header>

          {connected === false && (
            <div className="conn-banner">
              ⚠ Không thể kết nối backend (http://localhost:8000). Kiểm tra FastAPI và thử lại.
            </div>
          )}

          <div className="content">

            {/* ── NAV 0: Tổng quan ── */}
            {nav === 0 && <>
              <div>
                <div className="sec-head">
                  <div className="sec-title">Thông số môi trường</div>
                  <span className="sec-note">{lastPoll ? `Cập nhật luc ${lastPoll.toLocaleTimeString("vi-VN")} · mỗi 5s` : "Đang tải dữ liệu..."}</span>
                </div>
                <div className="sensor-grid">
                  {SENSOR_ORDER.map(m => {
                    const cfg = METRICS[m];
                    return <SCard key={m} icon={cfg.icon} label={cfg.label} value={latest[m]} unit={cfg.unit} lo={cfg.lo} hi={cfg.hi} history={sensorHistory[m]} />;
                  })}
                </div>
              </div>

              {/* Device controls */}
              <div>
                <div className="sec-head">
                  <div className="sec-title">Điều khiển thiết bị</div>
                  <span className="sec-note">{controllableCount} thiết bị</span>
                </div>
                <div className="device-grid">
                  {actuators.map(dev => {
                    const note = dev.target === "oxygen" ? `O2: ${latest.o2 != null ? (+latest.o2).toFixed(2) : "--"} mg/L` : dev.target === "pump_drain" ? `NH3: ${latest.nh3 != null ? (+latest.nh3).toFixed(2) : "--"} mg/L` : `Mực nước: ${wl != null ? (+wl).toFixed(0) : "--"}%`;
                    return <DCard key={dev.device_id} device={dev} sensorNote={note} onControl={handleControl} busy={!!busy[dev.device_id]} />;
                  })}
                  <FeederCard device={feeder} onControl={handleControl} busy={!!busy[feeder.device_id]} />
                </div>
              </div>

              {/* Water level + summary */}
              <div style={{ display: "grid", gridTemplateColumns: "1fr 190px", gap: 16 }}>
                <div>
                  <div className="sec-head"><div className="sec-title">Nhật ký cảnh báo</div>
                    <button onClick={() => setAlerts([])} style={{ fontSize: 11, background: "none", border: "none", color: "var(--text-dim)", cursor: "pointer", fontFamily: "var(--font-mono)" }}>Xóa tất cả</button>
                  </div>
                  <div className="alerts-card">
                    {alerts.length === 0
                      ? <div style={{ padding: 20, textAlign: "center", color: "var(--text-dim)", fontSize: 12, fontFamily: "var(--font-mono)" }}>Khong co cảnh báo</div>
                      : alerts.map(a => <AlertRow key={a.id} {...a} />)}
                  </div>
                </div>
                <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
                  <div>
                    <div className="sec-head" style={{ marginBottom: 10 }}><div className="sec-title" style={{ fontSize: 10 }}>Mực nước</div></div>
                    <div className="water-card">
                      <div className="tank-wrap">
                        <div style={{ position: "relative" }}>
                          {[75, 50, 25].map(m => (
                            <div key={m} style={{ position: "absolute", right: -28, bottom: `${m}%`, fontSize: 9, color: "var(--text-dim)", fontFamily: "var(--font-mono)", transform: "translateY(50%)" }}>{m}%</div>
                          ))}
                          <div className="tank">
                            <div className="tank-fill" style={{ height: `${wl ?? 0}%` }} />
                            <div className="tank-pct">{wl != null ? (+wl).toFixed(0) : "--"}%</div>
                          </div>
                        </div>
                      </div>
                      <div className="wl-badge">
                        <div style={{ fontSize: 20, fontWeight: 700, fontFamily: "var(--font-mono)", color: "var(--blue-800)", textAlign: "center" }}>{wl != null ? (+wl).toFixed(1) : "--"}%</div>
                        <div style={{ fontSize: 10, color: "var(--text-dim)", fontFamily: "var(--font-mono)", textAlign: "center", marginTop: 2 }}>HC-SR04</div>
                        <div style={{ textAlign: "center", marginTop: 8 }}>
                          <span className={`badge ${wl == null ? "b-ok" : wl < 30 ? "b-err" : wl < 50 ? "b-warn" : "b-ok"}`}>
                            {wl == null ? "--" : wl < 30 ? "THẤP" : wl < 50 ? "TRUNG BÌNH" : "ỔN ĐỊNH"}
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>
                  <div className="today-card">
                    <div style={{ fontSize: 11, fontWeight: 700, textTransform: "uppercase", letterSpacing: "1.2px", color: "var(--text-sec)", marginBottom: 10 }}>Tình trạng</div>
                    {[
                      { l: "Thiet bi",   v: `${controllableCount} target` },
                      { l: "Cảnh báo",   v: `${alerts.filter(a => a.level !== "ok").length} muc` },
                      { l: "Cập nhật",   v: lastPoll ? lastPoll.toLocaleTimeString("vi-VN", { hour: "2-digit", minute: "2-digit", second: "2-digit" }) : "--" },
                    ].map(s => (
                      <div key={s.l} className="today-row"><span className="today-lbl">{s.l}</span><span className="today-val">{s.v}</span></div>
                    ))}
                  </div>
                </div>
              </div>
            </>}

            {/* ── NAV 1: Phân tích & Chan doan ── */}
            {nav === 1 && <>
              <div className="two-col">
                <div className="chart-card">
                  <h3>O2 &amp; NH3 theo thoi gian</h3>
                  <p>{esp32Id} · {chartData.length} mẫu gần nhất</p>
                  <ResponsiveContainer width="100%" height={150}>
                    <AreaChart data={chartData}>
                      <defs>
                        <linearGradient id="go2" x1="0" y1="0" x2="0" y2="1"><stop offset="5%" stopColor="#378ADD" stopOpacity={.25} /><stop offset="95%" stopColor="#378ADD" stopOpacity={0} /></linearGradient>
                        <linearGradient id="gnh3" x1="0" y1="0" x2="0" y2="1"><stop offset="5%" stopColor="#BA7517" stopOpacity={.2} /><stop offset="95%" stopColor="#BA7517" stopOpacity={0} /></linearGradient>
                      </defs>
                      <CartesianGrid strokeDasharray="3 3" stroke="rgba(55,138,221,.12)" />
                      <XAxis dataKey="t" tick={{ fontSize: 9, fill: "#378ADD", fontFamily: "JetBrains Mono" }} interval={5} />
                      <YAxis tick={{ fontSize: 9, fill: "#378ADD", fontFamily: "JetBrains Mono" }} />
                      <Tooltip content={<ChartTT />} />
                      <Area type="monotone" dataKey="o2"  stroke="#185FA5" fill="url(#go2)"  strokeWidth={2} dot={false} />
                      <Area type="monotone" dataKey="nh3" stroke="#BA7517" fill="url(#gnh3)" strokeWidth={2} dot={false} />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>
                <div className="chart-card">
                  <h3>pH &amp; Nhiet do</h3>
                  <p>DS18B20 · {chartData.length} mẫu gần nhất</p>
                  <ResponsiveContainer width="100%" height={150}>
                    <LineChart data={chartData}>
                      <CartesianGrid strokeDasharray="3 3" stroke="rgba(55,138,221,.12)" />
                      <XAxis dataKey="t" tick={{ fontSize: 9, fill: "#378ADD", fontFamily: "JetBrains Mono" }} interval={5} />
                      <YAxis tick={{ fontSize: 9, fill: "#378ADD", fontFamily: "JetBrains Mono" }} />
                      <Tooltip content={<ChartTT />} />
                      <Line type="monotone" dataKey="ph"  stroke="#1D9E75" strokeWidth={2} dot={false} />
                      <Line type="monotone" dataKey="tmp" stroke="#A32D2D" strokeWidth={2} dot={false} />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              </div>

              <div className="chart-card">
                <div className="sec-head" style={{ marginBottom: 10 }}>
                  <div><div className="sec-title">Du bao AI (LSTM)</div>
                    <p style={{ margin: "4px 0 0" }}>Du bao pH, TDS va nhiet do nuoc trong 12 gio toi</p>
                  </div>
                  <span className="sec-note">{aiLoading ? "Đang chạy AI..." : aiForecast ? `${aiForecast.input_points} mẫu đầu vào` : "Chưa có dữ liệu"}</span>
                </div>
                {aiError ? (
                  <div style={{ color: "var(--danger)", fontSize: 12, fontFamily: "var(--font-mono)", padding: "10px 0" }}>{aiError}</div>
                ) : aiLoading ? (
                  <div style={{ color: "var(--text-dim)", fontSize: 12, fontFamily: "var(--font-mono)", padding: "10px 0" }}>Đang tải kết quả dự báo từ backend...</div>
                ) : aiChartData.length === 0 ? (
                  <div style={{ color: "var(--text-dim)", fontSize: 12, fontFamily: "var(--font-mono)", padding: "10px 0" }}>Chua du 24 diem du lieu pH, TDS va nhiet do de AI du bao.</div>
                ) : (
                  <>
                    <div className="pond-info" style={{ marginBottom: 14 }}>
                      <div><span>pH cuối kỳ</span><strong>{aiLastPoint?.ph?.toFixed(2) ?? "--"}</strong></div>
                      <div><span>TDS cuối kỳ</span><strong>{aiLastPoint?.tds?.toFixed(0) ?? "--"} ppm</strong></div>
                      <div><span>Nhiệt độ cuối kỳ</span><strong>{aiLastPoint?.tmp?.toFixed(1) ?? "--"} C</strong></div>
                      <div><span>Số bước</span><strong>{aiForecast?.forecast_steps ?? aiChartData.length} gio</strong></div>
                    </div>
                    <ResponsiveContainer width="100%" height={190}>
                      <LineChart data={aiChartData}>
                        <CartesianGrid strokeDasharray="3 3" stroke="rgba(55,138,221,.12)" />
                        <XAxis dataKey="t" tick={{ fontSize: 9, fill: "#378ADD", fontFamily: "JetBrains Mono" }} interval={1} />
                        <YAxis tick={{ fontSize: 9, fill: "#378ADD", fontFamily: "JetBrains Mono" }} />
                        <Tooltip content={<ChartTT />} />
                        <Line type="monotone" dataKey="ph"  name="pH du bao" stroke="#1D9E75" strokeWidth={2} dot={false} />
                        <Line type="monotone" dataKey="tds" name="TDS du bao" stroke="#BA7517" strokeWidth={2} dot={false} />
                        <Line type="monotone" dataKey="tmp" name="Nhiet do du bao" stroke="#A32D2D" strokeWidth={2} dot={false} />
                      </LineChart>
                    </ResponsiveContainer>
                  </>
                )}
              </div>
            </>}

            {/* ── NAV 2: Nguong cảnh báo ── */}
            {nav === 2 && <>
              {/* Pond info form */}
              <div className="chart-card">
                <div className="sec-head" style={{ marginBottom: 14 }}>
                  <div className="sec-title">Thông tin ao</div>
                </div>
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 12, marginBottom: 12 }}>
                  <div className="form-field" style={{ margin: 0 }}>
                    <label>Tên ao</label>
                    <input value={pondEdit.name} onChange={e => setPondEdit(p => ({ ...p, name: e.target.value }))} />
                  </div>
                  <div className="form-field" style={{ margin: 0 }}>
                    <label>Mã ESP32</label>
                    <input value={pondEdit.device_id} onChange={e => setPondEdit(p => ({ ...p, device_id: e.target.value }))} placeholder="VD: esp32_1" />
                  </div>
                  <div className="form-field" style={{ margin: 0 }}>
                    <label>Loại nuôi trồng</label>
                    <select value={pondEdit.pond_type} onChange={e => setPondEdit(p => ({ ...p, pond_type: e.target.value }))}>
                      {Object.entries(POND_TYPES).map(([k, v]) => (
                        <option key={k} value={k}>{v.icon} {v.label}</option>
                      ))}
                    </select>
                  </div>
                </div>
                {ptDesc && <div className="pond-desc">📋 {ptDesc}</div>}
                <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
                  <button className="save-btn" onClick={handleSavePond} disabled={savingPond}>
                    {savingPond ? "Đang lưu..." : "💾 Lưu thông tin ao"}
                  </button>
                  {pondSaveMsg && <span className={`save-msg ${pondSaveErr ? "err" : ""}`}>{pondSaveMsg}</span>}
                </div>
              </div>

              {/* Threshold table */}
              <div className="chart-card">
                <div className="sec-head" style={{ marginBottom: 14 }}>
                  <div className="sec-title">Nguong cảnh báo</div>
                  <span className="sec-note">Chỉnh sửa và lưu ngưỡng cho từng chỉ số</span>
                </div>
                <table className="thresh-table">
                  <thead>
                    <tr>
                      <th>Chỉ số</th>
                      <th>Min</th>
                      <th>Max</th>
                      <th>Đơn vị</th>
                      <th>Tự động</th>
                      <th>Hành động khi vượt ngưỡng</th>
                    </tr>
                  </thead>
                  <tbody>
                    {thresholds.length === 0 ? (
                      <tr><td colSpan={6} style={{ textAlign: "center", color: "var(--text-dim)", padding: 20, fontFamily: "var(--font-mono)", fontSize: 12 }}>Chưa có ngưỡng nào. Tạo ao với loại nuôi trồng để sinh ngưỡng mặc định.</td></tr>
                    ) : thresholds.map(t => {
                      const edit = threshEdits[t.metric_type] || {};
                      const m = METRICS[t.metric_type];
                      const actionLabels = { "": "Không làm gì", "FEED": "Cho ăn", "CHANGE_WATER": "Thay nước", "RESET": "Khởi động lại" };
                      return (
                        <tr key={t.metric_type}>
                          <td style={{ fontWeight: 600 }}>{m ? `${m.icon} ${m.label}` : t.metric_type}</td>
                          <td>
                            <input className="thresh-input" type="number" step="0.1" value={edit.min_value ?? t.min_value}
                              onChange={e => setThreshEdits(prev => ({ ...prev, [t.metric_type]: { ...prev[t.metric_type], min_value: e.target.value } }))} />
                          </td>
                          <td>
                            <input className="thresh-input" type="number" step="0.1" value={edit.max_value ?? t.max_value}
                              onChange={e => setThreshEdits(prev => ({ ...prev, [t.metric_type]: { ...prev[t.metric_type], max_value: e.target.value } }))} />
                          </td>
                          <td style={{ fontFamily: "var(--font-mono)", color: "var(--text-dim)" }}>{m?.unit ?? ""}</td>
                          <td>
                            <button className={`toggle ${edit.auto_control ? "on" : ""}`}
                              onClick={() => setThreshEdits(prev => ({ ...prev, [t.metric_type]: { ...prev[t.metric_type], auto_control: !prev[t.metric_type]?.auto_control } }))} />
                          </td>
                          <td>
                            <select style={{ border: "1px solid var(--border)", borderRadius: 6, padding: "4px 8px", fontFamily: "var(--font-mono)", fontSize: 11, outline: "none" }}
                              value={edit.auto_action ?? ""}
                              onChange={e => setThreshEdits(prev => ({ ...prev, [t.metric_type]: { ...prev[t.metric_type], auto_action: e.target.value } }))}>
                              {Object.entries(actionLabels).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
                            </select>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
                <div style={{ display: "flex", alignItems: "center", gap: 12, marginTop: 16 }}>
                  <button className="save-btn" onClick={handleSaveThresholds} disabled={savingThresh || thresholds.length === 0}>
                    {savingThresh ? "Đang lưu..." : "💾 Lưu ngưỡng cảnh báo"}
                  </button>
                  {threshSaveMsg && <span className={`save-msg ${threshSaveErr ? "err" : ""}`}>{threshSaveMsg}</span>}
                </div>
              </div>
            </>}

            {/* ── NAV 3: Lịch sử ── */}
            {nav === 3 && <>
              <div className="chart-card">
                <div className="sec-head"><div className="sec-title">Nhật ký lenh va cảnh báo</div></div>
                <div className="alerts-card">
                  {alerts.length === 0
                    ? <div style={{ padding: 20, textAlign: "center", color: "var(--text-dim)", fontSize: 12, fontFamily: "var(--font-mono)" }}>Không có lịch sử</div>
                    : alerts.map(a => <AlertRow key={a.id} {...a} />)}
                </div>
              </div>
            </>}

            {/* ── NAV 4: Cơ chế tự động ── */}
            {nav === 4 && <>
              <div className="chart-card">
                <div className="sec-head"><div className="sec-title">Cơ chế tự động</div></div>
                <div style={{ color: "var(--text-dim)", fontFamily: "var(--font-mono)", fontSize: 12, padding: "20px 0" }}>
                  🚧 Tính năng đang được phát triển. Cấu hình ngưỡng tự động ở tab "Nguong cảnh báo".
                </div>
              </div>
            </>}

            <div className="footer">PTIT · Nhóm 07 · Hệ Thống Nhúng 2026 </div>
          </div>
        </div>
      </div>
    </>
  );
}
