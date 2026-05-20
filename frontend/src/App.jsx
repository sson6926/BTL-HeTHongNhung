import { useState, useEffect, useCallback } from "react";
import {
  LineChart, Line, AreaChart, Area,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
} from "recharts";

// ── API base: dùng proxy Vite (/api → http://localhost:8000) ──────
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
  latestSensors: (deviceId)            => apiFetch(`/sensors/latest?device_id=${encodeURIComponent(deviceId)}`),
  sensorHistory: (metric, limit = 30)  => apiFetch(`/sensors/history?metric_type=${metric}&limit=${limit}`),
  controlDevice: (deviceId, action)    => apiFetch(`/devices/${encodeURIComponent(deviceId)}/control`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ action }),
  }),
};

// ── Sensor metadata ───────────────────────────────────────────────
const METRICS = {
  o2:          { icon: "💧", label: "Oxy hòa tan (O₂)", unit: "mg/L", lo: 5,   hi: 9   },
  ph:          { icon: "⚗️",  label: "Độ pH",             unit: "pH",   lo: 6.5, hi: 8.5 },
  nh3:         { icon: "☣️",  label: "Amoniac (NH₃)",    unit: "mg/L", lo: 0,   hi: 0.5 },
  temperature: { icon: "🌡️", label: "Nhiệt độ nước",    unit: "°C",   lo: 24,  hi: 32  },
  tds:         { icon: "🧪", label: "TDS chất rắn",       unit: "ppm",  lo: 200, hi: 500 },
  turbidity:   { icon: "🌊", label: "Độ đục",             unit: "NTU",  lo: 0,   hi: 20  },
};
const SENSOR_ORDER = ["o2", "ph", "nh3", "temperature", "tds", "turbidity"];

// ── Device display helper ─────────────────────────────────────────
function deviceDisplay(device) {
  const n = (device.name || "").toLowerCase();
  if (device.type === "feeder")
    return { icon: "🐠", bg: "#E6F1FB" };
  if (n.includes("sục") || n.includes("oxy") || n.includes("aerator") || n.includes("air") || device.type === "relay")
    return { icon: "💨", bg: "#E1F5EE" };
  if (n.includes("xả") || n.includes("drain") || n.includes("thoat"))
    return { icon: "🚿", bg: "#FAEEDA" };
  if (n.includes("cấp") || n.includes("fill") || n.includes("cap") || n.includes("supply"))
    return { icon: "⬆️", bg: "#E6F1FB" };
  return { icon: "🔄", bg: "#E6F1FB" };
}

// ── Threshold helper ──────────────────────────────────────────────
function statusOf(val, lo, hi) {
  if (val == null || isNaN(val)) return "ok";
  if (val < lo || val > hi) return "danger";
  const margin = (hi - lo) * 0.12;
  if (val < lo + margin || val > hi - margin) return "warning";
  return "ok";
}

// ── CSS ───────────────────────────────────────────────────────────
const CSS = `
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;600&display=swap');

  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

  :root {
    --blue-50:  #E6F1FB;
    --blue-100: #B5D4F4;
    --blue-200: #85B7EB;
    --blue-400: #378ADD;
    --blue-600: #185FA5;
    --blue-800: #0C447C;
    --blue-900: #042C53;

    --teal-50:  #E1F5EE;
    --teal-400: #1D9E75;

    --bg:        #F0F6FD;
    --card:      #FFFFFF;
    --border:    rgba(55,138,221,.15);
    --border-md: rgba(55,138,221,.25);
    --text:      #042C53;
    --text-sec:  #185FA5;
    --text-dim:  #378ADD;
    --muted:     #B5D4F4;

    --ok:        #1D9E75;
    --ok-bg:     #E1F5EE;
    --warn:      #BA7517;
    --warn-bg:   #FAEEDA;
    --danger:    #A32D2D;
    --danger-bg: #FCEBEB;

    --shadow-sm: 0 1px 4px rgba(4,44,83,.07);
    --shadow:    0 2px 12px rgba(4,44,83,.09);

    --font-ui:   'Inter', sans-serif;
    --font-mono: 'JetBrains Mono', monospace;
    --radius:    12px;
    --radius-sm: 8px;
  }

  body { background: var(--bg); color: var(--text); font-family: var(--font-ui); font-size: 14px; }

  ::-webkit-scrollbar { width: 4px; }
  ::-webkit-scrollbar-track { background: var(--bg); }
  ::-webkit-scrollbar-thumb { background: var(--blue-100); border-radius: 4px; }

  .app { display: flex; height: 100vh; overflow: hidden; }

  /* Sidebar */
  .sidebar {
    width: 64px; background: var(--blue-900);
    display: flex; flex-direction: column; align-items: center;
    padding: 16px 0; gap: 4px; flex-shrink: 0;
  }
  .logo {
    width: 38px; height: 38px; background: var(--blue-400);
    border-radius: 10px; display: flex; align-items: center;
    justify-content: center; font-size: 18px; margin-bottom: 20px;
  }
  .nav-btn {
    width: 42px; height: 42px; border-radius: 10px;
    background: transparent; border: none; color: var(--blue-200);
    cursor: pointer; font-size: 17px;
    display: flex; align-items: center; justify-content: center;
    transition: background .18s, color .18s; position: relative;
  }
  .nav-btn:hover { background: rgba(255,255,255,.1); color: #fff; }
  .nav-btn.active { background: var(--blue-600); color: #fff; }
  .nav-btn.active::after {
    content:''; position:absolute; right:0; top:50%;
    transform:translateY(-50%); width:3px; height:22px;
    background:var(--blue-200); border-radius:3px 0 0 3px;
  }
  .sidebar-bottom { margin-top: auto; }

  /* Main */
  .main { flex: 1; overflow-y: auto; display: flex; flex-direction: column; }

  /* Topbar */
  .topbar {
    display: flex; align-items: center; justify-content: space-between;
    padding: 14px 24px; background: var(--blue-900);
    border-bottom: 1px solid rgba(255,255,255,.08);
    position: sticky; top: 0; z-index: 5; flex-shrink: 0;
  }
  .topbar h1 { font-size: 16px; font-weight: 700; color: #fff; letter-spacing: -.2px; }
  .topbar p  { font-size: 11px; color: var(--blue-200); font-family: var(--font-mono); margin-top: 2px; }
  .topbar-right { display: flex; gap: 10px; align-items: center; }
  .live-pill {
    display: flex; align-items: center; gap: 6px;
    padding: 5px 12px; border-radius: 20px;
    background: rgba(255,255,255,.1); border: 1px solid rgba(255,255,255,.15);
    font-size: 11px; color: #fff; font-family: var(--font-mono); font-weight: 600;
  }
  .live-dot {
    width: 7px; height: 7px; border-radius: 50%;
    box-shadow: 0 0 6px currentColor; animation: blink 1.6s infinite;
  }
  @keyframes blink { 0%,100%{opacity:1} 50%{opacity:.4} }
  .sys-badge {
    padding: 5px 12px; border-radius: 20px; font-size: 11px;
    font-family: var(--font-mono); font-weight: 700;
  }
  .sys-ok   { background:rgba(29,158,117,.2);  color:#6ee7c4; border:1px solid rgba(29,158,117,.3); }
  .sys-warn { background:rgba(186,117,23,.2);  color:#fcd07a; border:1px solid rgba(186,117,23,.3); }
  .sys-err  { background:rgba(163,45,45,.2);   color:#fca5a5; border:1px solid rgba(163,45,45,.3); }

  /* Content */
  .content { padding: 22px 24px; display: flex; flex-direction: column; gap: 22px; }

  /* Section header */
  .sec-head { display:flex; align-items:center; justify-content:space-between; margin-bottom:12px; }
  .sec-title {
    font-size:11px; font-weight:700; text-transform:uppercase;
    letter-spacing:1.5px; color:var(--text-sec);
    display:flex; align-items:center; gap:8px;
  }
  .sec-title::before { content:''; width:12px; height:2px; background:var(--blue-400); display:block; border-radius:2px; }
  .sec-note { font-size:11px; color:var(--text-dim); font-family:var(--font-mono); }

  /* Sensor grid */
  .sensor-grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(175px,1fr)); gap:12px; }

  .s-card {
    background:var(--card); border:1px solid var(--border);
    border-radius:var(--radius); padding:16px 18px;
    box-shadow:var(--shadow-sm); position:relative; overflow:hidden;
    transition:box-shadow .2s, border-color .2s, transform .2s;
  }
  .s-card:hover { box-shadow:var(--shadow); border-color:var(--border-md); transform:translateY(-1px); }
  .s-card::before {
    content:''; position:absolute; top:0; left:0; right:0; height:3px;
    background:var(--c,var(--blue-400)); border-radius:var(--radius) var(--radius) 0 0;
  }
  .s-card.ok      { --c:var(--ok); }
  .s-card.warning { --c:var(--warn); border-color:rgba(186,117,23,.25); }
  .s-card.danger  { --c:var(--danger); border-color:rgba(163,45,45,.25); animation:d-glow 1.8s infinite; }
  @keyframes d-glow { 0%,100%{box-shadow:var(--shadow-sm)} 50%{box-shadow:0 0 0 3px rgba(163,45,45,.12),var(--shadow)} }

  .s-icon  { font-size:20px; margin-bottom:8px; }
  .s-label { font-size:10px; color:var(--text-dim); font-family:var(--font-mono); text-transform:uppercase; letter-spacing:1px; }
  .s-value { font-size:28px; font-weight:700; color:var(--text); font-family:var(--font-mono); line-height:1; margin:5px 0 4px; }
  .s-value em { font-size:12px; font-weight:400; color:var(--text-dim); font-style:normal; }
  .s-status {
    display:inline-flex; align-items:center; gap:5px;
    font-size:10px; font-weight:700; font-family:var(--font-mono);
    padding:3px 8px; border-radius:20px; margin-top:6px;
  }
  .s-status::before { content:''; width:5px; height:5px; border-radius:50%; background:currentColor; }
  .st-ok   { background:var(--ok-bg);     color:var(--ok);     }
  .st-warn { background:var(--warn-bg);   color:var(--warn);   }
  .st-err  { background:var(--danger-bg); color:var(--danger); }
  .s-spark { height:34px; margin-top:10px; }

  /* Chart cards */
  .two-col { display:grid; grid-template-columns:1fr 1fr; gap:16px; }
  @media (max-width:860px) { .two-col { grid-template-columns:1fr; } }

  .chart-card {
    background:var(--card); border:1px solid var(--border);
    border-radius:var(--radius); padding:18px 20px; box-shadow:var(--shadow-sm);
  }
  .chart-card h3 { font-size:13px; font-weight:600; color:var(--text); margin-bottom:4px; }
  .chart-card p  { font-size:10px; color:var(--text-dim); font-family:var(--font-mono); margin-bottom:14px; }

  /* Tooltip */
  .tt { background:var(--blue-900); border:1px solid var(--blue-600); border-radius:8px; padding:8px 12px; }
  .tt-l { font-size:10px; color:var(--blue-200); font-family:var(--font-mono); margin-bottom:2px; }
  .tt-v { font-size:13px; font-weight:600; color:#fff; font-family:var(--font-mono); }

  /* Device cards */
  .device-grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(200px,1fr)); gap:12px; }
  .d-card {
    background:var(--card); border:1px solid var(--border);
    border-radius:var(--radius); padding:16px 18px;
    box-shadow:var(--shadow-sm); display:flex; flex-direction:column; gap:12px;
  }
  .d-top { display:flex; align-items:center; gap:12px; }
  .d-icon {
    width:42px; height:42px; border-radius:10px;
    display:flex; align-items:center; justify-content:center;
    font-size:19px; flex-shrink:0;
  }
  .d-name  { font-size:14px; font-weight:600; color:var(--text); }
  .d-state { font-size:11px; color:var(--text-dim); font-family:var(--font-mono); margin-top:2px; }
  .d-note  {
    font-size:11px; color:var(--text-sec); font-family:var(--font-mono);
    background:var(--blue-50); border-radius:var(--radius-sm);
    padding:6px 10px; border:1px solid var(--border);
  }
  .d-id { font-size:9px; color:var(--muted); font-family:var(--font-mono); margin-top:2px; }
  .toggle-row { display:flex; align-items:center; justify-content:space-between; }
  .toggle-label { font-size:11px; color:var(--text-dim); font-family:var(--font-mono); }
  .toggle {
    width:44px; height:24px; border-radius:12px;
    background:var(--muted); border:none; cursor:pointer;
    position:relative; transition:background .22s;
  }
  .toggle:disabled { opacity:.5; cursor:not-allowed; }
  .toggle.on { background:var(--blue-400); }
  .toggle::after {
    content:''; position:absolute; width:18px; height:18px; border-radius:50%;
    background:#fff; top:3px; left:3px; transition:transform .22s;
    box-shadow:0 1px 3px rgba(0,0,0,.2);
  }
  .toggle.on::after { transform:translateX(20px); }

  /* Feed button */
  .feed-btn {
    width:100%; padding:10px; background:var(--blue-600);
    border:none; border-radius:var(--radius-sm); color:#fff;
    font-weight:700; font-size:13px; font-family:var(--font-ui);
    cursor:pointer; transition:background .18s, transform .12s;
  }
  .feed-btn:hover   { background:var(--blue-800); }
  .feed-btn:active  { transform:scale(.98); }
  .feed-btn:disabled{ background:var(--muted); color:var(--blue-100); cursor:not-allowed; }

  /* Stats */
  .stats-row { display:flex; gap:10px; flex-wrap:wrap; }
  .stat-box {
    flex:1; min-width:80px; background:var(--blue-50);
    border:1px solid var(--border); border-radius:var(--radius-sm);
    padding:10px 12px; text-align:center;
  }
  .stat-box .v { font-size:18px; font-weight:700; font-family:var(--font-mono); color:var(--blue-800); }
  .stat-box .l { font-size:9px; color:var(--text-dim); font-family:var(--font-mono); text-transform:uppercase; letter-spacing:1px; margin-top:2px; }

  /* Water tank */
  .water-card {
    background:var(--card); border:1px solid var(--border);
    border-radius:var(--radius); padding:18px 20px;
    box-shadow:var(--shadow-sm); display:flex; flex-direction:column; gap:16px;
  }
  .tank-wrap { display:flex; justify-content:center; }
  .tank {
    width:90px; height:150px;
    border:2px solid var(--border-md); border-radius:var(--radius-sm);
    position:relative; overflow:hidden; background:var(--blue-50);
  }
  .tank-fill {
    position:absolute; bottom:0; left:0; right:0;
    background:linear-gradient(180deg,var(--blue-200) 0%,var(--blue-400) 100%);
    transition:height 1s cubic-bezier(.4,0,.2,1);
  }
  .tank-fill::after {
    content:''; position:absolute; top:0; left:0; right:0; height:2px;
    background:var(--blue-100); animation:wave 2s ease-in-out infinite;
  }
  @keyframes wave { 0%,100%{opacity:1} 50%{opacity:.5} }
  .tank-pct {
    position:absolute; top:50%; left:50%; transform:translate(-50%,-50%);
    font-size:17px; font-weight:700; font-family:var(--font-mono);
    color:var(--blue-900); z-index:1; text-shadow:0 0 8px rgba(255,255,255,.8);
  }
  .wl-badge { text-align:center; }
  .badge {
    display:inline-block; padding:4px 12px; border-radius:20px;
    font-size:10px; font-weight:700; font-family:var(--font-mono);
  }
  .b-ok   { background:var(--ok-bg);     color:var(--ok);     }
  .b-warn { background:var(--warn-bg);   color:var(--warn);   }
  .b-err  { background:var(--danger-bg); color:var(--danger); }

  /* Alerts */
  .alerts-card {
    background:var(--card); border:1px solid var(--border);
    border-radius:var(--radius); overflow:hidden; box-shadow:var(--shadow-sm);
  }
  .alert-row {
    display:flex; align-items:flex-start; gap:10px;
    padding:10px 16px; border-bottom:1px solid var(--border);
    transition:background .15s; animation:fadein .3s ease;
  }
  @keyframes fadein { from{opacity:0;transform:translateY(-4px)} to{opacity:1;transform:translateY(0)} }
  .alert-row:hover { background:var(--blue-50); }
  .alert-row:last-child { border-bottom:none; }
  .a-dot { width:7px; height:7px; border-radius:50%; flex-shrink:0; margin-top:4px; }
  .a-msg  { font-size:12px; color:var(--text); }
  .a-time { font-size:10px; color:var(--text-dim); font-family:var(--font-mono); margin-top:2px; }

  /* Today card */
  .today-card {
    background:var(--card); border:1px solid var(--border);
    border-radius:var(--radius); padding:16px 18px; box-shadow:var(--shadow-sm);
  }
  .today-row {
    display:flex; justify-content:space-between; align-items:center;
    padding:7px 0; border-bottom:1px solid var(--border);
  }
  .today-row:last-child { border-bottom:none; }
  .today-lbl { font-size:11px; color:var(--text-dim); font-family:var(--font-mono); }
  .today-val { font-size:14px; font-weight:700; font-family:var(--font-mono); color:var(--blue-800); }

  /* Connection banner */
  .conn-banner {
    margin: 0 24px; padding: 10px 14px; border-radius:var(--radius-sm);
    font-size:12px; font-family:var(--font-mono);
    background:var(--danger-bg); color:var(--danger);
    border:1px solid rgba(163,45,45,.25);
    display:flex; align-items:center; gap:8px;
  }

  /* Footer */
  .footer {
    text-align:center; padding:14px 0;
    border-top:1px solid var(--border);
    font-size:10px; color:var(--text-dim); font-family:var(--font-mono);
  }
`;

// ── Tooltip component ─────────────────────────────────────────────
const ChartTT = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="tt">
      <div className="tt-l">{label}</div>
      <div className="tt-v">{typeof payload[0].value === "number" ? payload[0].value.toFixed(2) : payload[0].value}</div>
    </div>
  );
};

// ── SCard: sensor display card ────────────────────────────────────
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

// ── DCard: pump / relay toggle card ──────────────────────────────
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
        <div className="stat-box"><div className="v">3</div><div className="l">Lần/ngày</div></div>
        <div className="stat-box"><div className="v">08:00</div><div className="l">Lần tới</div></div>
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

// ── App ───────────────────────────────────────────────────────────
export default function App() {
  const [devices,       setDevices]      = useState([]);
  const [sensorHistory, setSensorHistory] = useState({});
  const [latest,        setLatest]        = useState({});
  const [connected,     setConnected]     = useState(null);   // null=loading
  const [lastPoll,      setLastPoll]      = useState(null);
  const [busy,          setBusy]          = useState({});     // deviceId → bool
  const [alerts,        setAlerts]        = useState([
    { id: 1, level: "ok", msg: "Frontend khởi động, đang kết nối backend…", time: new Date().toLocaleTimeString("vi-VN") },
  ]);
  const [clock, setClock] = useState(new Date());
  const [nav,   setNav]   = useState(0);

  // Find ESP32 sensor device (type="esp32"), fallback to "esp32_1"
  const esp32Id = devices.find(d => d.type === "esp32")?.device_id ?? "esp32_1";

  // ── Clock ────────────────────────────────────────────────────
  useEffect(() => {
    const id = setInterval(() => setClock(new Date()), 1000);
    return () => clearInterval(id);
  }, []);

  // ── Push alert (deduplicate within 10 s) ─────────────────────
  const pushAlert = useCallback((level, msg) => {
    setAlerts(prev => {
      const now = Date.now();
      if (prev[0]?.msg === msg && now - prev[0]?.id < 10000) return prev;
      return [{ id: now, level, msg, time: new Date().toLocaleTimeString("vi-VN") }, ...prev].slice(0, 20);
    });
  }, []);

  // ── Load devices once ─────────────────────────────────────────
  useEffect(() => {
    api.listDevices()
      .then(devs => {
        setDevices(devs);
        pushAlert("ok", `Đã tải ${devs.length} thiết bị từ backend`);
      })
      .catch(e => pushAlert("error", `Không thể tải thiết bị: ${e.message}`));
  }, []);

  // ── Load historical data for each metric on mount ─────────────
  useEffect(() => {
    Object.keys(METRICS).concat(["water_level"]).forEach(metric => {
      api.sensorHistory(metric, 30)
        .then(data => {
          const pts = [...data].reverse().map(d => ({
            t: new Date(d.created_at).toLocaleTimeString("vi-VN", { hour: "2-digit", minute: "2-digit" }),
            v: d.value,
          }));
          setSensorHistory(h => ({ ...h, [metric]: pts }));
        })
        .catch(() => {});
    });
  }, []);

  // ── Poll latest sensors every 5 s ────────────────────────────
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

        // Append new points to rolling history
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

        // Threshold alerts
        const { o2, nh3, temperature, ph } = newLatest;
        if (o2  != null && o2  < 4)   pushAlert("error", `O₂ nguy hiểm: ${(+o2).toFixed(2)} mg/L`);
        if (nh3 != null && nh3 > 0.6) pushAlert("warn",  `NH₃ vượt ngưỡng: ${(+nh3).toFixed(2)} mg/L`);
        if (temperature != null && (temperature < 20 || temperature > 34))
          pushAlert("warn", `Nhiệt độ bất thường: ${(+temperature).toFixed(1)} °C`);
        if (ph != null && (ph < 6 || ph > 9))
          pushAlert("warn", `pH bất thường: ${(+ph).toFixed(2)}`);
      } catch {
        setConnected(false);
      }
    };

    poll();
    const id = setInterval(poll, 5000);
    return () => clearInterval(id);
  }, [esp32Id, pushAlert]);

  // ── Control device ────────────────────────────────────────────
  const handleControl = useCallback(async (deviceId, action) => {
    setBusy(b => ({ ...b, [deviceId]: true }));
    try {
      await api.controlDevice(deviceId, action);
      pushAlert("ok", `${deviceId}: lệnh ${action} thành công`);
      // Refresh device list to get updated status
      const devs = await api.listDevices();
      setDevices(devs);
    } catch (e) {
      pushAlert("error", `${deviceId}: lỗi – ${e.message}`);
    } finally {
      setBusy(b => ({ ...b, [deviceId]: false }));
    }
  }, [pushAlert]);

  // ── Derived state ─────────────────────────────────────────────
  const wl = latest.water_level ?? null;
  const controllable = devices.filter(d => d.type !== "esp32");
  const feeder       = controllable.find(d => d.type === "feeder");
  const actuators    = controllable.filter(d => d.type !== "feeder");

  const critSts = ["o2", "ph", "nh3"].map(m => statusOf(latest[m], METRICS[m].lo, METRICS[m].hi));
  const sys     = critSts.some(s => s === "danger") ? "err"
                : critSts.some(s => s === "warning") ? "warn"
                : "ok";
  const sysLabel = { ok: "HỆ THỐNG ỔN ĐỊNH", warn: "CÓ CẢNH BÁO", err: "NGUY HIỂM" }[sys];

  // Chart data: align o2, nh3, ph, temperature by index
  const chartLen  = Math.max(
    (sensorHistory.o2 ?? []).length,
    (sensorHistory.ph ?? []).length,
    (sensorHistory.nh3 ?? []).length,
    (sensorHistory.temperature ?? []).length,
  );
  const chartData = Array.from({ length: chartLen }, (_, i) => ({
    t:   sensorHistory.o2?.[i]?.t ?? sensorHistory.ph?.[i]?.t ?? "",
    o2:  sensorHistory.o2?.[i]?.v,
    nh3: sensorHistory.nh3?.[i]?.v,
    ph:  sensorHistory.ph?.[i]?.v,
    tmp: sensorHistory.temperature?.[i]?.v,
  }));

  const navIcons = ["⬡", "📊", "🔧", "🔔", "⚙️"];

  return (
    <>
      <style>{CSS}</style>
      <div className="app">

        {/* Sidebar */}
        <nav className="sidebar">
          <div className="logo">🐟</div>
          {navIcons.map((ic, i) => (
            <button key={i} className={`nav-btn ${nav === i ? "active" : ""}`} onClick={() => setNav(i)}>{ic}</button>
          ))}
          <div className="sidebar-bottom">
            <button className="nav-btn">👤</button>
          </div>
        </nav>

        <div className="main">

          {/* Topbar */}
          <header className="topbar">
            <div>
              <h1>Hệ Thống Giám Sát Nuôi Trồng Thủy Sản</h1>
              <p>{clock.toLocaleString("vi-VN")} · {esp32Id} · MQTT · MySQL</p>
            </div>
            <div className="topbar-right">
              <div className="live-pill">
                <div
                  className="live-dot"
                  style={{
                    background: connected === false ? "#f87171" : "#4ade80",
                    color:      connected === false ? "#f87171" : "#4ade80",
                  }}
                />
                {connected === null ? "KẾT NỐI…" : connected ? "LIVE" : "MẤT KẾT NỐI"}
              </div>
              <span className={`sys-badge sys-${sys}`}>{sysLabel}</span>
            </div>
          </header>

          {/* Offline banner */}
          {connected === false && (
            <div className="conn-banner">
              ⚠ Không thể kết nối backend (http://localhost:8000). Kiểm tra FastAPI và thử lại.
            </div>
          )}

          <div className="content">

            {/* ── Sensors ── */}
            <div>
              <div className="sec-head">
                <div className="sec-title">Thông số môi trường</div>
                <span className="sec-note">
                  {lastPoll
                    ? `Cập nhật lúc ${lastPoll.toLocaleTimeString("vi-VN")} · mỗi 5s`
                    : "Đang tải dữ liệu…"}
                </span>
              </div>
              <div className="sensor-grid">
                {SENSOR_ORDER.map(m => {
                  const cfg = METRICS[m];
                  return (
                    <SCard
                      key={m}
                      icon={cfg.icon}
                      label={cfg.label}
                      value={latest[m]}
                      unit={cfg.unit}
                      lo={cfg.lo}
                      hi={cfg.hi}
                      history={sensorHistory[m]}
                    />
                  );
                })}
              </div>
            </div>

            {/* ── Charts ── */}
            <div className="two-col">
              <div className="chart-card">
                <h3>O₂ & NH₃ theo thời gian</h3>
                <p>{esp32Id} · {chartData.length} mẫu gần nhất</p>
                <ResponsiveContainer width="100%" height={150}>
                  <AreaChart data={chartData}>
                    <defs>
                      <linearGradient id="go2" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%"  stopColor="#378ADD" stopOpacity={.25} />
                        <stop offset="95%" stopColor="#378ADD" stopOpacity={0} />
                      </linearGradient>
                      <linearGradient id="gnh3" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%"  stopColor="#BA7517" stopOpacity={.2} />
                        <stop offset="95%" stopColor="#BA7517" stopOpacity={0} />
                      </linearGradient>
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
                <h3>pH & Nhiệt độ</h3>
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

            {/* ── Devices + Water ── */}
            <div style={{ display: "grid", gridTemplateColumns: "1fr 190px", gap: 16 }}>
              <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>

                {/* Device controls */}
                <div>
                  <div className="sec-head">
                    <div className="sec-title">Điều khiển thiết bị</div>
                    <span className="sec-note">{controllable.length} thiết bị</span>
                  </div>

                  {controllable.length === 0 ? (
                    <div style={{ color: "var(--text-dim)", fontSize: 12, fontFamily: "var(--font-mono)", padding: "12px 0" }}>
                      {connected === false
                        ? "Backend offline – không tải được thiết bị"
                        : "Đang tải thiết bị…"}
                    </div>
                  ) : (
                    <div className="device-grid">
                      {actuators.map(dev => {
                        const n = dev.name.toLowerCase();
                        const note =
                          n.includes("sục") || n.includes("oxy") || n.includes("aerator") || dev.type === "relay"
                            ? `O₂: ${latest.o2 != null ? (+latest.o2).toFixed(2) : "--"} mg/L · Bật khi <5.5`
                            : n.includes("xả") || n.includes("drain")
                            ? `NH₃: ${latest.nh3 != null ? (+latest.nh3).toFixed(2) : "--"} mg/L · Bật khi >0.5`
                            : `Mực nước: ${wl != null ? (+wl).toFixed(0) : "--"}% · Bật khi <40%`;
                        return (
                          <DCard
                            key={dev.device_id}
                            device={dev}
                            sensorNote={note}
                            onControl={handleControl}
                            busy={!!busy[dev.device_id]}
                          />
                        );
                      })}

                      {feeder ? (
                        <FeederCard
                          device={feeder}
                          onControl={handleControl}
                          busy={!!busy[feeder.device_id]}
                        />
                      ) : (
                        <div className="d-card">
                          <div className="d-top">
                            <div className="d-icon" style={{ background: "#E6F1FB" }}>🐠</div>
                            <div>
                              <div className="d-name">Hệ thống cho ăn</div>
                              <div className="d-state" style={{ color: "var(--text-dim)" }}>Chưa đăng ký</div>
                            </div>
                          </div>
                          <div className="d-note">Thiết bị feeder chưa được thêm vào DB</div>
                        </div>
                      )}
                    </div>
                  )}
                </div>

                {/* Alert log */}
                <div>
                  <div className="sec-head">
                    <div className="sec-title">Nhật ký cảnh báo</div>
                    <button
                      onClick={() => setAlerts([])}
                      style={{ fontSize: 11, background: "none", border: "none", color: "var(--text-dim)", cursor: "pointer", fontFamily: "var(--font-mono)" }}
                    >
                      Xóa tất cả
                    </button>
                  </div>
                  <div className="alerts-card">
                    {alerts.length === 0
                      ? <div style={{ padding: 20, textAlign: "center", color: "var(--text-dim)", fontSize: 12, fontFamily: "var(--font-mono)" }}>Không có cảnh báo</div>
                      : alerts.map(a => <AlertRow key={a.id} {...a} />)
                    }
                  </div>
                </div>
              </div>

              {/* Right column */}
              <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>

                {/* Water level tank */}
                <div>
                  <div className="sec-head" style={{ marginBottom: 10 }}>
                    <div className="sec-title" style={{ fontSize: 10 }}>Mực nước</div>
                  </div>
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
                      <div style={{ fontSize: 20, fontWeight: 700, fontFamily: "var(--font-mono)", color: "var(--blue-800)", textAlign: "center" }}>
                        {wl != null ? (+wl).toFixed(1) : "--"}%
                      </div>
                      <div style={{ fontSize: 10, color: "var(--text-dim)", fontFamily: "var(--font-mono)", textAlign: "center", marginTop: 2 }}>HC-SR04</div>
                      <div style={{ textAlign: "center", marginTop: 8 }}>
                        <span className={`badge ${wl == null ? "b-ok" : wl < 30 ? "b-err" : wl < 50 ? "b-warn" : "b-ok"}`}>
                          {wl == null ? "--" : wl < 30 ? "THẤP" : wl < 50 ? "TRUNG BÌNH" : "ỔN ĐỊNH"}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Today summary */}
                <div className="today-card">
                  <div style={{ fontSize: 11, fontWeight: 700, textTransform: "uppercase", letterSpacing: "1.2px", color: "var(--text-sec)", marginBottom: 10, display: "flex", alignItems: "center", gap: 6 }}>
                    <span style={{ display: "block", width: 10, height: 2, background: "var(--blue-400)", borderRadius: 2 }} />
                    Tình trạng
                  </div>
                  {[
                    { l: "Thiết bị",  v: `${devices.length} máy` },
                    { l: "Backend",   v: connected === null ? "…" : connected ? "Online" : "Offline" },
                    { l: "Cảnh báo", v: `${alerts.filter(a => a.level !== "ok").length} mục` },
                    { l: "Cập nhật", v: lastPoll ? lastPoll.toLocaleTimeString("vi-VN", { hour: "2-digit", minute: "2-digit", second: "2-digit" }) : "--" },
                  ].map(s => (
                    <div key={s.l} className="today-row">
                      <span className="today-lbl">{s.l}</span>
                      <span className="today-val">{s.v}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            <div className="footer">PTIT · Nhóm 06 · Hệ Thống Nhúng 2025 · ESP32 + MQTT + ReactJS + FastAPI + MySQL</div>
          </div>
        </div>
      </div>
    </>
  );
}
