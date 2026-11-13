"""Dedicated 8-parameter interactive web pages for Earth Jukebox."""
from typing import Dict
from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse

router = APIRouter(tags=["Parameter Pages"])

CATEGORY_PAGES: Dict[str, Dict[str, str]] = {
    "temperature": {
        "title": "Temperature",
        "icon": "🌡️",
        "accent": "#ff9e44",
        "accent2": "#e85d3f",
        "bg_glow": "rgba(255, 130, 67, 0.20)",
        "subtitle": "Surface thermal dynamics mapped to warm analog sine harmonics.",
        "dataset": "NASA POWER Monthly Surface Temperature (T2M)",
        "synth_mode": "temperature",
    },
    "rain": {
        "title": "Rainfall",
        "icon": "🌧️",
        "accent": "#46c8f5",
        "accent2": "#2b7de9",
        "bg_glow": "rgba(70, 200, 245, 0.18)",
        "subtitle": "Precipitation patterns translated into hydro-acoustic droplet pulses.",
        "dataset": "NASA POWER / GPM Corrected Precipitation (PRECTOTCORR)",
        "synth_mode": "rain",
    },
    "wind": {
        "title": "Wind",
        "icon": "💨",
        "accent": "#9cd6ff",
        "accent2": "#4f86c6",
        "bg_glow": "rgba(156, 214, 255, 0.18)",
        "subtitle": "10-meter wind speed sculpted into resonant filtered noise swells.",
        "dataset": "NASA POWER 10-Meter Wind Speed (WS10M)",
        "synth_mode": "wind",
    },
    "fires": {
        "title": "Wildfires",
        "icon": "🔥",
        "accent": "#ff7354",
        "accent2": "#c93b2b",
        "bg_glow": "rgba(255, 115, 84, 0.20)",
        "subtitle": "Active thermal hotspots mapped to staccato FM pulses (observation only).",
        "dataset": "NASA FIRMS VIIRS 375m Active Fire Detections",
        "synth_mode": "fires",
    },
    "ocean": {
        "title": "Ocean",
        "icon": "🌊",
        "accent": "#3ad0e6",
        "accent2": "#1368aa",
        "bg_glow": "rgba(58, 208, 230, 0.18)",
        "subtitle": "Surface thermal proxy waves rendered as deep sub-bass oceanic pads.",
        "dataset": "NASA POWER TS Proxy (GHRSST MUR Granule Discovery)",
        "synth_mode": "ocean",
    },
    "ice": {
        "title": "Cryosphere",
        "icon": "❄️",
        "accent": "#bce6ff",
        "accent2": "#5c95cc",
        "bg_glow": "rgba(188, 230, 255, 0.20)",
        "subtitle": "Polar cryosphere signals (|lat| >= 60°) voiced as crystalline chimes.",
        "dataset": "NSIDC Sea Ice Index / Polar Cryosphere Proxy",
        "synth_mode": "ice",
    },
    "storms": {
        "title": "Storms",
        "icon": "🌀",
        "accent": "#b896ff",
        "accent2": "#6b4fd1",
        "bg_glow": "rgba(184, 150, 255, 0.20)",
        "subtitle": "Convective precipitation surges mapped to atmospheric rumbles (no track forecasting).",
        "dataset": "NASA GES DISC / POWER Storm Precipitation Proxy",
        "synth_mode": "storms",
    },
    "vegetation": {
        "title": "Vegetation",
        "icon": "🌿",
        "accent": "#66dc92",
        "accent2": "#288a5b",
        "bg_glow": "rgba(102, 220, 146, 0.18)",
        "subtitle": "Photosynthetically active flux translated into biophilic Lydian chords.",
        "dataset": "NASA LP DAAC MODIS / POWER PAR Biophysical Series",
        "synth_mode": "vegetation",
    },
}


def render_parameter_page(category: str) -> str:
    cfg = CATEGORY_PAGES[category]
    nav_links = "".join(
        f'<a class="pill {"active" if slug == category else ""}" href="/explore/{slug}">'
        f'{meta["icon"]} {meta["title"]}</a>'
        for slug, meta in CATEGORY_PAGES.items()
    )
    default_lat = "78.2232" if category == "ice" else "19.0760"
    default_lon = "15.6267" if category == "ice" else "72.8777"
    default_place = "Svalbard, Norway" if category == "ice" else "Mumbai, India"

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Earth Jukebox | {cfg["title"]}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Manrope:wght@400;600;700;800&display=swap" rel="stylesheet">
<style>
:root{{--accent:{cfg["accent"]};--accent2:{cfg["accent2"]};--bg:#060a14;--panel:#0d1527;--line:rgba(148,179,235,.18);--text:#edf3ff;--muted:#96a6c2;--green:#47d7a0;--red:#ff7187;--amber:#ffca70}}
*{{box-sizing:border-box;margin:0;padding:0}}
body{{min-height:100vh;background:radial-gradient(ellipse at 82% -8%,{cfg["bg_glow"]},transparent 40%),var(--bg);color:var(--text);font-family:Manrope,system-ui,sans-serif}}
.container{{width:min(1240px,92%);margin:auto}}
.navbar{{position:sticky;top:0;z-index:20;background:rgba(6,10,20,.9);backdrop-filter:blur(14px);border-bottom:1px solid var(--line);padding:12px 0}}
.nav-top{{display:flex;justify-content:space-between;align-items:center;gap:12px;flex-wrap:wrap}}
.brand{{display:flex;align-items:center;gap:10px;text-decoration:none;color:var(--text);font-weight:800}}
.brand-mark{{width:34px;height:34px;border-radius:10px;display:grid;place-items:center;background:linear-gradient(135deg,var(--accent2),var(--accent));color:#06101d}}
.param-nav{{display:flex;gap:7px;flex-wrap:wrap;margin-top:10px}}
.pill{{padding:6px 11px;border-radius:999px;border:1px solid var(--line);color:var(--muted);text-decoration:none;font-size:11px;font-weight:700;transition:.15s}}
.pill:hover,.pill.active{{border-color:var(--accent);color:#fff;background:rgba(255,255,255,.06)}}
.hero{{padding:38px 0 24px;display:grid;grid-template-columns:1.15fr .85fr;gap:28px;align-items:center}}
.kicker{{font:10px 'DM Mono',monospace;letter-spacing:1.6px;color:var(--accent);text-transform:uppercase;margin-bottom:10px}}
h1{{font-size:clamp(34px,5vw,56px);line-height:1.05;letter-spacing:-1.8px}}
h1 span{{background:linear-gradient(100deg,var(--accent),#ffffff);-webkit-background-clip:text;background-clip:text;color:transparent}}
.hero p{{color:var(--muted);font-size:14px;line-height:1.75;margin:14px 0}}
.earth-box{{position:relative;height:285px;display:grid;place-items:center}}
#earth3d{{width:265px;height:265px;cursor:grab;filter:drop-shadow(0 0 26px {cfg["bg_glow"]})}}
#earth3d:active{{cursor:grabbing}}
.earth-hint{{font:10px 'DM Mono',monospace;color:var(--muted);margin-top:6px}}
.panel{{background:linear-gradient(145deg,rgba(15,24,44,.96),rgba(9,15,29,.96));border:1px solid var(--line);border-radius:16px;padding:20px;margin-bottom:18px}}
.panel-head{{display:flex;justify-content:space-between;align-items:center;gap:10px;flex-wrap:wrap;margin-bottom:14px}}
.panel-head span{{font:10px 'DM Mono',monospace;color:var(--accent)}}
.loc-bar{{display:grid;grid-template-columns:1.5fr auto auto;gap:10px;align-items:end}}
.field{{display:flex;flex-direction:column;gap:6px}}
.field label{{font-size:10px;font-weight:800;color:var(--muted)}}
.field input,.field select{{background:#080f20;border:1px solid var(--line);border-radius:9px;padding:10px 12px;color:var(--text);font-size:12px}}
.btn{{border:0;border-radius:9px;padding:10px 15px;font-weight:800;font-size:12px;cursor:pointer;transition:.15s}}
.btn-primary{{background:linear-gradient(110deg,var(--accent2),var(--accent));color:#07101d}}
.btn-secondary{{background:#111c33;border:1px solid var(--line);color:var(--text)}}
.btn:disabled{{opacity:.5;cursor:not-allowed}}
.chips{{display:flex;gap:7px;flex-wrap:wrap;margin-top:10px}}
.chip{{background:#0b152a;border:1px solid var(--line);color:var(--muted);padding:5px 10px;border-radius:999px;font-size:11px;cursor:pointer}}
.chip:hover{{border-color:var(--accent);color:#fff}}
.loc-meta{{margin-top:10px;display:flex;justify-content:space-between;flex-wrap:wrap;gap:10px;font:11px 'DM Mono',monospace;color:var(--muted)}}
.grid-2{{display:grid;grid-template-columns:1.4fr .6fr;gap:16px;align-items:start}}
.chart-wrap{{height:300px;position:relative}}
.chart-wrap canvas{{width:100%;height:100%;display:block}}
.live-badge{{margin-top:8px;padding:9px 12px;border-radius:9px;background:#080f20;border:1px solid var(--line);font:11px 'DM Mono',monospace;color:var(--accent);min-height:36px}}
.status{{display:none;margin-top:10px;padding:10px 12px;border-radius:9px;font-size:11px}}
.status.show{{display:block}}
.status.good{{background:rgba(71,215,160,.12);border:1px solid rgba(71,215,160,.4);color:var(--green)}}
.status.bad{{background:rgba(255,113,135,.12);border:1px solid rgba(255,113,135,.4);color:#ff9aab}}
.status.info{{background:rgba(70,200,245,.12);border:1px solid rgba(70,200,245,.4);color:#b8ebff}}
.controls{{display:flex;gap:8px;flex-wrap:wrap;margin:12px 0}}
.controls .btn{{flex:1}}
.metrics{{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin-top:12px}}
.metric{{background:#080f20;border:1px solid var(--line);border-radius:10px;padding:10px}}
.metric small{{display:block;font-size:9px;color:var(--muted)}}
.metric strong{{font:16px 'DM Mono',monospace}}
.chord-table{{width:100%;border-collapse:collapse;margin-top:10px;font-size:11px}}
.chord-table th,.chord-table td{{border-bottom:1px solid var(--line);padding:7px 8px;text-align:left}}
.chord-table th{{color:var(--accent);font:10px 'DM Mono',monospace}}
@media(max-width:900px){{.hero,.grid-2,.loc-bar{{grid-template-columns:1fr}}}}
</style>
</head>
<body>
<header class="navbar"><div class="container">
  <div class="nav-top">
    <a class="brand" href="/demo"><div class="brand-mark">{cfg["icon"]}</div><span>EARTH JUKEBOX · {cfg["title"].upper()}</span></a>
    <a class="pill" href="/demo">← All 8 Modules Hub</a>
  </div>
  <nav class="param-nav" aria-label="Environmental parameters">{nav_links}</nav>
</div></header>

<main class="container">
  <section class="hero">
    <div>
      <div class="kicker">DEDICATED PARAMETER STUDIO · {category.upper()}</div>
      <h1>{cfg["icon"]} <span>{cfg["title"]}</span> Sonification</h1>
      <p>{cfg["subtitle"]}</p>
      <p style="font:11px 'DM Mono',monospace">Source: {cfg["dataset"]}</p>
    </div>
    <div style="text-align:center">
      <div class="earth-box"><canvas id="earth3d" aria-label="Interactive 3D Earth"></canvas></div>
      <div class="earth-hint">Flowing 3D Earth · Drag to rotate · Scroll to zoom</div>
    </div>
  </section>

  <!-- Single Unified Location Section -->
  <section class="panel" id="location">
    <div class="panel-head"><h3>Location Selector</h3><span>AUTO-GEOCODED COORDINATES</span></div>
    <div class="loc-bar">
      <div class="field"><label for="placeInput">Enter city, place, or landmark (coordinates auto-set)</label><input id="placeInput" type="search" value="{default_place}" placeholder="e.g. Tokyo, Reykjavik, Amazon, Mumbai..."></div>
      <button class="btn btn-primary" id="resolvePlaceBtn">Set Location</button>
      <button class="btn btn-secondary" id="geoBtn">◎ Use GPS</button>
    </div>
    <div class="chips" id="placeChoices"></div>
    <div class="loc-meta">
      <span id="locLabel">{default_place}</span>
      <span id="coordDisplay">Lat {default_lat}°, Lon {default_lon}°</span>
    </div>
    <input type="hidden" id="latInput" value="{default_lat}">
    <input type="hidden" id="lonInput" value="{default_lon}">
    <div id="locStatus" class="status"></div>
  </section>

  <!-- Query + Export -->
  <section class="panel">
    <div class="panel-head"><h3>Observation Window & Historical Export</h3><span>NASA DATA ADAPTER</span></div>
    <div style="display:grid;grid-template-columns:1fr 1fr auto auto auto;gap:10px;align-items:end">
      <div class="field"><label for="startDate">Start date</label><input id="startDate" type="date" value="2020-01-01"></div>
      <div class="field"><label for="endDate">End date</label><input id="endDate" type="date" value="2025-12-31"></div>
      <button class="btn btn-primary" id="loadBtn">Load Data &amp; Chords</button>
      <button class="btn btn-secondary" id="csvBtn">↓ CSV</button>
      <button class="btn btn-secondary" id="jsonBtn">↓ JSON</button>
    </div>
    <div id="dataStatus" class="status"></div>
  </section>

  <!-- Graph with Live Blinking Point + Sound Studio -->
  <section class="grid-2">
    <div class="panel">
      <div class="panel-head"><h3>Observation Graph &amp; Live Playback Blinker</h3><span id="unitBadge">UNIT</span></div>
      <div class="chart-wrap"><canvas id="obsChart"></canvas></div>
      <div class="live-badge" id="liveReadout">Load observations and press Play to watch the live blinking point on the graph.</div>
      <div class="metrics">
        <div class="metric"><small>POINTS</small><strong id="mCount">—</strong></div>
        <div class="metric"><small>AVERAGE</small><strong id="mMean">—</strong></div>
        <div class="metric"><small>MIN / MAX</small><strong id="mMinMax">—</strong></div>
      </div>
    </div>

    <div class="panel">
      <div class="panel-head"><h3>{cfg["title"]} Sound Studio</h3><span id="audioState">READY</span></div>
      <div class="live-badge" id="soundInfo">Key &amp; profile load with observations.</div>
      <div class="controls">
        <button class="btn btn-primary" id="playBtn" disabled>▶ Play</button>
        <button class="btn btn-secondary" id="pauseBtn" disabled>Ⅱ Pause</button>
        <button class="btn btn-secondary" id="stopBtn" disabled>■ Stop</button>
      </div>
      <div class="field"><label for="volSlider">Volume</label><input id="volSlider" type="range" min="0" max="100" value="70"></div>
      <div class="controls">
        <button class="btn btn-secondary" id="pdfCompactBtn">↓ PDF (Compact)</button>
        <button class="btn btn-secondary" id="pdfDetailedBtn">↓ PDF (Detailed)</button>
      </div>
      <div id="pdfStatus" class="status"></div>
    </div>
  </section>

  <!-- Hierarchical Chords View -->
  <section class="panel">
    <div class="panel-head"><h3>Hierarchical Chord Progression (Matched to Graph A–L)</h3><span id="tierSummary">—</span></div>
    <table class="chord-table">
      <thead><tr><th>Graph</th><th>Timestamp</th><th>Value</th><th>Chord &amp; Notes</th><th>Hz</th><th>Pitch Move</th><th>Register</th></tr></thead>
      <tbody id="chordBody"><tr><td colspan="7" style="color:var(--muted)">Load observations to inspect hierarchical chords.</td></tr></tbody>
    </table>
  </section>

  <!-- Media Lab (Photo & Video) -->
  <section class="panel">
    <div class="panel-head"><h3>Media Lab — Photo &amp; Video Sonification + Report</h3><span>VISUAL SIGNAL ANALYSIS</span></div>
    <div style="display:grid;grid-template-columns:1fr auto auto;gap:10px;align-items:end">
      <div class="field"><label for="mediaInput">Upload Earth/nature photo or video (.jpg, .png, .mp4, .webm)</label><input id="mediaInput" type="file" accept="image/*,video/mp4,video/webm,video/quicktime"></div>
      <button class="btn btn-primary" id="analyzeMediaBtn">Analyze &amp; Sonify Media</button>
      <button class="btn btn-secondary" id="mediaPdfBtn" disabled>↓ Media PDF</button>
    </div>
    <div id="mediaStatus" class="status"></div>
  </section>
</main>

<script src="https://cdn.jsdelivr.net/npm/three@0.128.0/build/three.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>
<script>
const CATEGORY = "{category}";
const SYNTH_MODE = "{cfg["synth_mode"]}";
const ACCENT = "{cfg["accent"]}";
const $ = id => document.getElementById(id);

let observations = [], soundParams = [], currentUnit = "", activeIndex = -1, mediaReportData = null;
let audioCtx = null, masterGain = null, isPlaying = false, playIdx = 0, playTimer = null, rafId = null;

function showStatus(id, msg, kind='info'){{ const el=$(id); el.textContent=msg; el.className=`status show ${{kind}}`; }}

// 1. Auto-geocode place name -> coordinates (no prompt popup)
let targetLat = Number($('latInput').value), targetLon = Number($('lonInput').value);
function applyPlace(name, lat, lon){{
  $('latInput').value = Number(lat).toFixed(4);
  $('lonInput').value = Number(lon).toFixed(4);
  $('locLabel').textContent = name;
  $('coordDisplay').textContent = `Lat ${{Number(lat).toFixed(4)}}°, Lon ${{Number(lon).toFixed(4)}}°`;
  targetLat = Number(lat); targetLon = Number(lon);
  updateEarthPin(targetLat, targetLon);
}}
async function resolvePlace(){{
  const q = $('placeInput').value.trim();
  if(q.length < 2){{ showStatus('locStatus', 'Enter at least 2 characters.', 'bad'); return; }}
  $('resolvePlaceBtn').disabled = true;
  try{{
    const r = await fetch(`/location/search?q=${{encodeURIComponent(q)}}`);
    const data = await r.json();
    if(!r.ok || !data.results?.length) throw new Error(data.detail || 'No matching place found.');
    const top = data.results[0];
    applyPlace(top.display_name, top.latitude, top.longitude);
    const chips = $('placeChoices'); chips.innerHTML = '';
    data.results.forEach(item => {{
      const b = document.createElement('button');
      b.className = 'chip';
      b.textContent = `${{item.display_name.split(',').slice(0,2).join(',')}} (${{Number(item.latitude).toFixed(2)}}°, ${{Number(item.longitude).toFixed(2)}}°)`;
      b.onclick = () => applyPlace(item.display_name, item.latitude, item.longitude);
      chips.appendChild(b);
    }});
    showStatus('locStatus', `Coordinates automatically set to ${{top.display_name}} (${{data.attribution}}).`, 'good');
  }}catch(e){{ showStatus('locStatus', e.message, 'bad'); }}
  finally{{ $('resolvePlaceBtn').disabled = false; }}
}}
$('resolvePlaceBtn').onclick = resolvePlace;
$('placeInput').addEventListener('keydown', e => {{ if(e.key === 'Enter'){{ e.preventDefault(); resolvePlace(); }} }});
$('geoBtn').onclick = () => {{
  if(!navigator.geolocation) return showStatus('locStatus', 'Geolocation unavailable.', 'bad');
  navigator.geolocation.getCurrentPosition(p => {{
    applyPlace('My Current Location', p.coords.latitude, p.coords.longitude);
    showStatus('locStatus', 'Browser GPS coordinates applied.', 'good');
  }}, () => showStatus('locStatus', 'Location permission denied.', 'bad'));
}};

// 2. Flowing 3D Earth (autoRotate + OrbitControls rotation/zoom)
let earthMarker = null, globeMesh = null;
function latLonToVec3(lat, lon, radius=1.02){{
  const phi = (90 - lat) * (Math.PI / 180), theta = (lon + 180) * (Math.PI / 180);
  return new THREE.Vector3(-radius * Math.sin(phi) * Math.cos(theta), radius * Math.cos(phi), radius * Math.sin(phi) * Math.sin(theta));
}}
function updateEarthPin(lat, lon){{
  if(earthMarker) earthMarker.position.copy(latLonToVec3(lat, lon, 1.03));
}}
(function initEarth(){{
  const canvas = $('earth3d');
  if(!canvas || !window.THREE) return;
  const scene = new THREE.Scene(), camera = new THREE.PerspectiveCamera(38, 1, 0.1, 100);
  camera.position.z = 3.1;
  const renderer = new THREE.WebGLRenderer({{canvas, alpha:true, antialias:true}});
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
  renderer.setSize(265, 265, false);

  globeMesh = new THREE.Mesh(
    new THREE.SphereGeometry(1, 64, 64),
    new THREE.MeshPhongMaterial({{color:0x2b79bd, specular:0x446688, shininess:16}})
  );
  scene.add(globeMesh);

  earthMarker = new THREE.Mesh(
    new THREE.SphereGeometry(0.032, 16, 16),
    new THREE.MeshBasicMaterial({{color:ACCENT}})
  );
  globeMesh.add(earthMarker);
  updateEarthPin(targetLat, targetLon);

  scene.add(new THREE.AmbientLight(0xffffff, 0.78));
  const dl = new THREE.DirectionalLight(0xffffff, 1.15); dl.position.set(4, 2, 5); scene.add(dl);

  const controls = window.THREE.OrbitControls ? new THREE.OrbitControls(camera, renderer.domElement) : null;
  if(controls){{
    controls.enableDamping = true;
    controls.dampingFactor = 0.06;
    controls.enableZoom = true;
    controls.minDistance = 1.5;
    controls.maxDistance = 5.5;
    controls.autoRotate = true;
    controls.autoRotateSpeed = 0.85;
  }}
  new THREE.TextureLoader().load('https://threejs.org/examples/textures/planets/earth_atmos_2048.jpg', tex => {{
    globeMesh.material.map = tex; globeMesh.material.color.set(0xffffff); globeMesh.material.needsUpdate = true;
  }});
  (function loop(){{
    requestAnimationFrame(loop);
    if(controls) controls.update();
    else globeMesh.rotation.y += 0.003;
    renderer.render(scene, camera);
  }})();
}})();

// 3. Chart Rendering with Accurate A-L Markers & Live Blinking Playback Point
function sampleMarkerIndices(n, max=12){{
  if(n <= 0) return [];
  const count = Math.min(max, n);
  const set = new Set();
  for(let i=0;i<count;i++) set.add(Math.round(i * (n - 1) / Math.max(1, count - 1)));
  return [...set].sort((a,b)=>a-b);
}}

function drawChart(){{
  const canvas = $('obsChart'), ctx = canvas.getContext('2d');
  const rect = canvas.getBoundingClientRect(), dpr = window.devicePixelRatio || 1;
  canvas.width = Math.max(1, Math.floor(rect.width * dpr));
  canvas.height = Math.max(1, Math.floor(rect.height * dpr));
  ctx.scale(dpr, dpr);
  const w = rect.width, h = rect.height;
  ctx.clearRect(0, 0, w, h);
  if(!observations.length){{
    ctx.fillStyle = '#96a6c2'; ctx.font = '12px DM Mono, monospace'; ctx.textAlign = 'center';
    ctx.fillText('Load observations or analyze media to render the interactive chart', w/2, h/2);
    return;
  }}
  const pad = {{l:52, r:18, t:24, b:30}}, cw = w - pad.l - pad.r, ch = h - pad.t - pad.b;
  const vals = observations.map(p => p.value), min = Math.min(...vals), max = Math.max(...vals);
  const span = (max - min) || 1, lo = min - span * 0.14, hi = max + span * 0.18;
  const x = i => pad.l + (observations.length === 1 ? cw/2 : (i / (observations.length - 1)) * cw);
  const y = v => pad.t + ((hi - v) / (hi - lo)) * ch;

  ctx.strokeStyle = 'rgba(150,166,194,0.16)'; ctx.fillStyle = '#96a6c2'; ctx.font = '10px DM Mono, monospace';
  for(let i=0;i<=4;i++){{
    const yy = pad.t + (ch * i) / 4, val = hi - ((hi - lo) * i) / 4;
    ctx.beginPath(); ctx.moveTo(pad.l, yy); ctx.lineTo(w - pad.r, yy); ctx.stroke();
    ctx.textAlign = 'right'; ctx.fillText(val.toFixed(1), pad.l - 8, yy + 3);
  }}

  // Line + area fill
  ctx.beginPath();
  observations.forEach((p, i) => i === 0 ? ctx.moveTo(x(i), y(p.value)) : ctx.lineTo(x(i), y(p.value)));
  ctx.strokeStyle = ACCENT; ctx.lineWidth = 2.4; ctx.stroke();

  // Alphabetical Chord Markers A-L (strictly matched to soundParams[idx])
  const chosen = sampleMarkerIndices(observations.length, 12);
  chosen.forEach((idx, mIdx) => {{
    const letter = String.fromCharCode(65 + mIdx);
    const sp = soundParams[idx];
    const arrow = sp?.pitch_direction === 'higher' ? '↑' : (sp?.pitch_direction === 'lower' ? '↓' : '');
    const cx = x(idx), cy = y(observations[idx].value) - 16;
    ctx.fillStyle = sp?.pitch_direction === 'higher' ? '#47d7a0' : (sp?.pitch_direction === 'lower' ? '#ff7187' : '#ffca70');
    ctx.beginPath(); ctx.arc(cx, cy, 9, 0, Math.PI * 2); ctx.fill();
    ctx.fillStyle = '#07101d'; ctx.font = 'bold 9px DM Mono, monospace'; ctx.textAlign = 'center';
    ctx.fillText(letter + arrow, cx, cy + 3);
  }});

  // LIVE BLINKING POINT ON GRAPH DURING SOUND PLAYBACK
  if(activeIndex >= 0 && activeIndex < observations.length){{
    const px = x(activeIndex), py = y(observations[activeIndex].value);
    const pulse = 0.5 + 0.5 * Math.sin(performance.now() / 110);
    // Vertical playhead
    ctx.strokeStyle = 'rgba(255,255,255,0.28)'; ctx.lineWidth = 1;
    ctx.beginPath(); ctx.moveTo(px, pad.t); ctx.lineTo(px, h - pad.b); ctx.stroke();
    // Outer blinking halo
    ctx.beginPath(); ctx.arc(px, py, 9 + pulse * 10, 0, Math.PI * 2);
    ctx.fillStyle = `rgba(255, 202, 112, ${{0.18 + 0.35 * pulse}})`; ctx.fill();
    // Inner glowing core
    ctx.beginPath(); ctx.arc(px, py, 5.5, 0, Math.PI * 2);
    ctx.fillStyle = '#ffffff'; ctx.fill();
    ctx.lineWidth = 2.5; ctx.strokeStyle = ACCENT; ctx.stroke();
  }}

  ctx.textAlign = 'center'; ctx.fillStyle = '#96a6c2'; ctx.font = '10px DM Mono, monospace';
  ctx.fillText(String(observations[0].timestamp).slice(0, 10), pad.l + 24, h - 8);
  ctx.fillText(String(observations[observations.length - 1].timestamp).slice(0, 10), w - pad.r - 24, h - 8);
}}

function renderChordTable(sonif){{
  const body = $('chordBody'); body.innerHTML = '';
  const params = sonif?.parameters || [];
  if(!params.length){{ body.innerHTML = '<tr><td colspan="7">No sound events available.</td></tr>'; return; }}
  const chosen = sampleMarkerIndices(params.length, 12);
  chosen.forEach((idx, mIdx) => {{
    const p = params[idx], tr = document.createElement('tr');
    const dir = p.pitch_direction === 'higher' ? '↑ Higher' : (p.pitch_direction === 'lower' ? '↓ Lower' : p.pitch_direction);
    tr.innerHTML = `<td><strong>${{String.fromCharCode(65 + mIdx)}}</strong></td><td>${{p.timestamp}}</td><td>${{p.original_value}}</td><td>${{p.chord_name}} (${{(p.chord_notes||[]).join(', ')}})</td><td>${{p.pitch_hz}} Hz</td><td>${{dir}}</td><td>${{(p.pitch_tier||'mid').toUpperCase()}}</td>`;
    body.appendChild(tr);
  }});
  const tiers = sonif?.chord_hierarchy?.level_3_register_tiers;
  if(tiers){{
    $('tierSummary').textContent = `HIGH: ${{tiers.high.event_count}} · MID: ${{tiers.mid.event_count}} · LOW: ${{tiers.low.event_count}}`;
  }}
}}

// 4. Category-Specific Web Audio Synthesis
async function ensureAudio(){{
  const AC = window.AudioContext || window.webkitAudioContext;
  if(!audioCtx){{ audioCtx = new AC(); masterGain = audioCtx.createGain(); masterGain.gain.value = $('volSlider').value / 100; masterGain.connect(audioCtx.destination); }}
  if(audioCtx.state === 'suspended') await audioCtx.resume();
}}
function playChordVoice(p){{
  if(!audioCtx || !masterGain) return;
  const now = audioCtx.currentTime;
  const freqs = (p.chord_frequencies_hz?.length ? p.chord_frequencies_hz : [p.pitch_hz]).map(Number);
  const dur = Math.max(0.12, Math.min(1.2, (p.duration_ms || 380) / 1000));
  const amp = Math.max(0.005, Math.min(0.45, Math.pow(10, (p.volume_db ?? -16) / 20))) / Math.sqrt(freqs.length);
  const waveMap = {{temperature:'sine', rain:'triangle', wind:'sawtooth', fires:'square', ocean:'sine', ice:'sine', storms:'sawtooth', vegetation:'triangle'}};
  const oscType = waveMap[SYNTH_MODE] || 'sine';

  freqs.forEach((hz, i) => {{
    const osc = audioCtx.createOscillator(), g = audioCtx.createGain();
    osc.type = oscType;
    osc.frequency.setValueAtTime(Math.max(40, Math.min(3500, hz)), now);
    g.gain.setValueAtTime(0.0001, now);
    g.gain.exponentialRampToValueAtTime(amp, now + (SYNTH_MODE === 'fires' ? 0.01 : 0.04));
    g.gain.exponentialRampToValueAtTime(0.0001, now + dur);
    if(SYNTH_MODE === 'wind' || SYNTH_MODE === 'storms'){{
      const filter = audioCtx.createBiquadFilter(); filter.type = 'lowpass'; filter.frequency.value = 600 + (p.intensity || 0.5) * 1400;
      osc.connect(filter); filter.connect(g);
    }} else {{
      osc.connect(g);
    }}
    g.connect(masterGain);
    osc.start(now + i * 0.008);
    osc.stop(now + dur + 0.04);
  }});
}}
function animateBlink(){{
  if(!isPlaying) return;
  drawChart();
  rafId = requestAnimationFrame(animateBlink);
}}
function stepPlay(){{
  if(!isPlaying) return;
  if(playIdx >= soundParams.length){{ stopPlay(); return; }}
  const p = soundParams[playIdx];
  activeIndex = Math.min(observations.length - 1, playIdx);
  playChordVoice(p);
  $('liveReadout').textContent = `● BLINKING: Point ${{playIdx + 1}}/${{soundParams.length}} | ${{p.timestamp}} | Value: ${{p.original_value}} ${{currentUnit}} | ${{p.chord_name}} (${{p.pitch_hz}} Hz, ${{p.pitch_direction}})`;
  playIdx++;
  playTimer = setTimeout(stepPlay, Math.max(110, Math.min(1100, p.duration_ms || 380)));
}}
async function startPlay(){{
  if(!soundParams.length) return;
  await ensureAudio();
  if(isPlaying) return;
  isPlaying = true;
  $('audioState').textContent = 'PLAYING';
  $('playBtn').disabled = true; $('pauseBtn').disabled = false; $('stopBtn').disabled = false;
  animateBlink();
  stepPlay();
}}
function pausePlay(){{
  isPlaying = false; clearTimeout(playTimer); cancelAnimationFrame(rafId);
  $('audioState').textContent = 'PAUSED';
  $('playBtn').disabled = false; $('pauseBtn').disabled = true;
}}
function stopPlay(){{
  isPlaying = false; clearTimeout(playTimer); cancelAnimationFrame(rafId);
  playIdx = 0; activeIndex = -1; drawChart();
  $('audioState').textContent = 'READY';
  $('playBtn').disabled = !soundParams.length; $('pauseBtn').disabled = true; $('stopBtn').disabled = true;
}}
$('playBtn').onclick = startPlay; $('pauseBtn').onclick = pausePlay; $('stopBtn').onclick = stopPlay;
$('volSlider').oninput = () => {{ if(masterGain) masterGain.gain.value = $('volSlider').value / 100; }};

// 5. Load NASA Observations & Chords + Exports
function applyLoadedData(obsList, sonif, unit, sourceLabel){{
  stopPlay();
  observations = obsList; soundParams = sonif?.parameters || []; currentUnit = unit || '';
  mediaReportData = null;
  $('unitBadge').textContent = currentUnit || 'UNIT';
  const vals = observations.map(o => o.value);
  $('mCount').textContent = vals.length;
  $('mMean').textContent = vals.length ? (vals.reduce((a,b)=>a+b,0)/vals.length).toFixed(2) : '—';
  $('mMinMax').textContent = vals.length ? `${{Math.min(...vals).toFixed(1)}} / ${{Math.max(...vals).toFixed(1)}}` : '—';
  $('soundInfo').textContent = `${{sonif.sound_profile}} · Key: ${{sonif.musical_key}} (${{sonif.scale_mode}})`;
  $('playBtn').disabled = !soundParams.length;
  renderChordTable(sonif);
  drawChart();
  showStatus('dataStatus', `Loaded ${{vals.length}} observations from ${{sourceLabel}}.`, 'good');
}}

$('loadBtn').onclick = async () => {{
  const lat = $('latInput').value, lon = $('lonInput').value, s = $('startDate').value, e = $('endDate').value;
  showStatus('dataStatus', 'Loading NASA observations & chords...', 'info');
  try{{
    const q = new URLSearchParams({{category:CATEGORY, latitude:lat, longitude:lon, start_date:s, end_date:e}});
    const r = await fetch(`/observations?${{q}}`);
    const data = await r.json();
    if(!r.ok) throw new Error(data.detail || 'Observation load failed.');
    if(!data.historical_data?.length) throw new Error('No observations returned for this location/window.');
    applyLoadedData(data.historical_data, data.sonification, data.unit, data.data_source?.dataset_name || 'NASA');
  }}catch(err){{ showStatus('dataStatus', err.message, 'bad'); }}
}};

async function exportData(fmt){{
  const q = new URLSearchParams({{latitude:$('latInput').value, longitude:$('lonInput').value, start_date:$('startDate').value, end_date:$('endDate').value, format:fmt}});
  const r = await fetch(`/data/export/${{CATEGORY}}?${{q}}`);
  if(!r.ok) return showStatus('dataStatus', 'Export failed.', 'bad');
  const blob = await r.blob(), url = URL.createObjectURL(blob), a = document.createElement('a');
  a.href = url; a.download = `earthjukebox_${{CATEGORY}}_history.${{fmt}}`; a.click(); URL.revokeObjectURL(url);
}}
$('csvBtn').onclick = () => exportData('csv');
$('jsonBtn').onclick = () => exportData('json');

async function downloadPdf(fmt){{
  showStatus('pdfStatus', `Generating interactive ${{fmt}} PDF...`, 'info');
  try{{
    const q = new URLSearchParams({{latitude:$('latInput').value, longitude:$('lonInput').value, start_date:$('startDate').value, end_date:$('endDate').value, report_format:fmt}});
    const r = await fetch(`/reports/${{CATEGORY}}/pdf?${{q}}`);
    if(!r.ok) throw new Error('PDF generation failed.');
    const blob = await r.blob(), url = URL.createObjectURL(blob), a = document.createElement('a');
    a.href = url; a.download = `earth_jukebox_${{CATEGORY}}_${{fmt}}.pdf`; a.click(); URL.revokeObjectURL(url);
    showStatus('pdfStatus', 'PDF downloaded with summary, annotated graphs, and hierarchical chords.', 'good');
  }}catch(e){{ showStatus('pdfStatus', e.message, 'bad'); }}
}}
$('pdfCompactBtn').onclick = () => downloadPdf('compact');
$('pdfDetailedBtn').onclick = () => downloadPdf('detailed');

// 6. Media Lab (Photo + Browser Video Frame Extraction -> Sonification & PDF)
async function extractVideoFrames(file, count=14){{
  const video = document.createElement('video');
  video.muted = true; video.playsInline = true;
  video.src = URL.createObjectURL(file);
  await new Promise((res, rej) => {{ video.onloadedmetadata = res; video.onerror = rej; }});
  const canvas = document.createElement('canvas');
  canvas.width = 220; canvas.height = Math.max(120, Math.round(220 * (video.videoHeight / (video.videoWidth || 1))));
  const ctx = canvas.getContext('2d'), frames = [], dur = Math.max(0.5, video.duration || 5);
  for(let i=0;i<count;i++){{
    video.currentTime = (dur * i) / Math.max(1, count - 1);
    await new Promise(res => {{ video.onseeked = res; }});
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
    frames.push(canvas.toDataURL('image/jpeg', 0.72));
  }}
  URL.revokeObjectURL(video.src);
  return frames;
}}

$('analyzeMediaBtn').onclick = async () => {{
  const file = $('mediaInput').files?.[0];
  if(!file) return showStatus('mediaStatus', 'Select a photo or video first.', 'bad');
  showStatus('mediaStatus', 'Analyzing uploaded media and generating sonification...', 'info');
  try{{
    let report;
    if(file.type.startsWith('video/')){{
      const frames = await extractVideoFrames(file, 14);
      const r = await fetch('/media/analyze-frames', {{
        method: 'POST', headers: {{'Content-Type': 'application/json'}},
        body: JSON.stringify({{category: CATEGORY, filename: file.name, location_name: $('locLabel').textContent, frames}})
      }});
      report = await r.json();
      if(!r.ok) throw new Error(report.detail || 'Video analysis failed.');
    }} else {{
      const fd = new FormData();
      fd.append('file', file); fd.append('category', CATEGORY); fd.append('location_name', $('locLabel').textContent);
      const r = await fetch('/media/analyze', {{method:'POST', body: fd}});
      report = await r.json();
      if(!r.ok) throw new Error(report.detail || 'Image analysis failed.');
    }}
    applyLoadedData(report.observations, report.sonification, report.unit, `Uploaded Media (${{file.name}})`);
    mediaReportData = report;
    $('mediaPdfBtn').disabled = false;
    showStatus('mediaStatus', `${{report.ai_summary?.summary || 'Media analyzed.'}}`, 'good');
  }}catch(e){{ showStatus('mediaStatus', e.message, 'bad'); }}
}};

$('mediaPdfBtn').onclick = async () => {{
  if(!mediaReportData) return;
  const r = await fetch('/media/report/pdf?report_format=detailed', {{
    method:'POST', headers:{{'Content-Type':'application/json'}}, body: JSON.stringify(mediaReportData)
  }});
  if(!r.ok) return showStatus('mediaStatus', 'Media PDF failed.', 'bad');
  const blob = await r.blob(), url = URL.createObjectURL(blob), a = document.createElement('a');
  a.href = url; a.download = `earth_jukebox_media_${{CATEGORY}}.pdf`; a.click(); URL.revokeObjectURL(url);
}};

window.addEventListener('resize', drawChart);
drawChart();
</script>
</body>
</html>"""


@router.get("/explore/{category}", response_class=HTMLResponse)
def get_parameter_page(category: str):
    slug = category.lower().strip()
    if slug not in CATEGORY_PAGES:
        raise HTTPException(status_code=404, detail=f"Unknown parameter page '{category}'.")
    return HTMLResponse(render_parameter_page(slug))