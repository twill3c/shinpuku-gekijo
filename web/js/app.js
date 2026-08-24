// app.js — 振幅劇場 UI 配線。エンジン(engine.js)は純粋関数のまま、ここで舞台に載せる。
import {
  createGrover, oracle, diffuse, successProb, optimalIterations,
  theoryProb, classicalReference, iterations,
} from "./engine.js";
import { encodeLink, decodeLink } from "./link.js";

// ---------------------------------------------------------------- 状態
let n = 3;
let marked = [5];          // 目印集合(ソート済み)
let g = null;              // グローバー実行体
let nextHalf = "oracle";   // 次の半歩
let timer = null;          // 自動再生

const $ = (id) => document.getElementById(id);
const canvas = $("amps");
const ctx = canvas.getContext("2d");

const COLORS = {
  gold: "#d9a84e", silver: "#8d93a8", shu: "#d4644a",
  seiji: "#7fb8a8", line: "#363b55", inkSoft: "#9a97a8",
};

// ---------------------------------------------------------------- 構成
function rebuild(toIters = 0) {
  stopPlay();
  g = createGrover(n, marked);
  nextHalf = "oracle";
  for (let t = 0; t < toIters; t++) { oracle(g); diffuse(g); }
  setLastOp(toIters === 0
    ? "初期状態 — 全候補が等しい振幅 1/√N"
    : `${toIters} 反復を実行(オラクル+拡散 × ${toIters})`);
  render();
  syncHash();
}

function setN(newN) {
  n = newN;
  const N = 2 ** n;
  marked = [N >> 1]; // 既定の目印: 中央の候補(決定論 — N-02)
  rebuild(0);
}

function toggleMarked(idx) {
  const N = 2 ** n;
  const set = new Set(marked);
  if (set.has(idx)) set.delete(idx); else set.add(idx);
  if (set.size === 0 || set.size >= N) return; // 空・全件は不許可(SPEC スコープ外)
  marked = [...set].sort((a, b) => a - b);
  rebuild(0);
}

// ---------------------------------------------------------------- 実行
function halfstep() {
  if (nextHalf === "oracle") {
    oracle(g);
    nextHalf = "diffuse";
    setLastOp("オラクル — 目印の符号を反転(金の棒が軸の下へ)");
  } else {
    const mean = Array.from(g.state).reduce((s, a) => s + a, 0) / g.N;
    diffuse(g);
    nextHalf = "oracle";
    setLastOp(`拡散 — 平均 ${mean.toFixed(4)} まわりの反転(目印が跳ね上がる)`);
  }
  render();
  syncHash();
}

function fullIter() {
  if (nextHalf === "diffuse") halfstep(); // 半端を先に閉じる
  halfstep(); halfstep();
}

function runTo(t) {
  stopPlay();
  rebuild(t);
}

function overshootTarget() {
  const tstar = optimalIterations(g.N, g.k);
  return tstar + Math.ceil(tstar / 2) + 1; // SPEC G-05 の t_over
}

// ---------------------------------------------------------------- 自動再生
function stopPlay() {
  if (timer !== null) { clearInterval(timer); timer = null; $("btn-play").textContent = "自動再生"; }
}
function togglePlay() {
  if (timer !== null) { stopPlay(); return; }
  const hz = Number($("speed").value);
  $("btn-play").textContent = "停止";
  timer = setInterval(() => {
    if (iterations(g) >= curveTmax()) { stopPlay(); return; }
    halfstep();
  }, 1000 / hz);
}

// ---------------------------------------------------------------- 描画
function curveTmax() {
  const tstar = optimalIterations(g.N, g.k);
  return Math.max(overshootTarget() + Math.max(2, tstar), 8, iterations(g) + 1);
}

function render() {
  drawBars();
  drawCurve();
  const t = iterations(g);
  const p = successProb(g);
  $("st-t").textContent = String(t) + (nextHalf === "oracle" ? "" : "+½");
  $("st-calls").textContent = String(g.oracleCalls);
  $("st-prob").textContent = (p * 100).toFixed(2) + "%";
  $("st-theory").textContent = nextHalf === "oracle"
    ? (theoryProb(g.N, g.k, t) * 100).toFixed(2) + "%" : "(半歩の途中)";
  $("st-tstar").textContent = `t* = ${optimalIterations(g.N, g.k)}`;
  const c = classicalReference(g.N);
  $("st-classical").textContent = `${c.expected}〜最悪 ${c.worst}`;
  $("n-info").textContent = `N = ${g.N}`;
  $("marked-info").textContent = `目印 ${g.k} 件(棒をクリックで変更)`;
  $("btn-half").textContent = nextHalf === "oracle" ? "半歩:次はオラクル" : "半歩:次は拡散";
}

function setLastOp(text) { $("last-op").textContent = text; }

function drawBars() {
  const dpr = window.devicePixelRatio || 1;
  const w = canvas.clientWidth, h = canvas.clientHeight;
  if (canvas.width !== Math.round(w * dpr)) { canvas.width = Math.round(w * dpr); canvas.height = Math.round(h * dpr); }
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  ctx.clearRect(0, 0, w, h);

  const N = g.N;
  const a = g.state;
  const pad = 8;
  const innerW = w - pad * 2;
  const barW = innerW / N;
  const maxAmp = Math.max(0.15, ...Array.from(a, Math.abs)) * 1.15;
  const y0 = h / 2;
  const scale = (h / 2 - 14) / maxAmp;

  // 軸
  ctx.strokeStyle = COLORS.line;
  ctx.lineWidth = 1;
  ctx.beginPath(); ctx.moveTo(pad, y0); ctx.lineTo(w - pad, y0); ctx.stroke();

  // 平均線
  const mean = Array.from(a).reduce((s, v) => s + v, 0) / N;
  ctx.strokeStyle = COLORS.seiji;
  ctx.setLineDash([6, 5]);
  ctx.beginPath();
  ctx.moveTo(pad, y0 - mean * scale);
  ctx.lineTo(w - pad, y0 - mean * scale);
  ctx.stroke();
  ctx.setLineDash([]);

  // 棒
  const mset = g.markedSet;
  const gap = barW > 4 ? 1 : 0;
  for (let i = 0; i < N; i++) {
    const x = pad + i * barW;
    const v = a[i] * scale;
    ctx.fillStyle = mset.has(i) ? COLORS.gold : COLORS.silver;
    if (v >= 0) ctx.fillRect(x, y0 - v, Math.max(barW - gap, 0.5), Math.max(v, 0.75));
    else ctx.fillRect(x, y0, Math.max(barW - gap, 0.5), -v);
  }

  // 負側の目印は朱の縁取りで強調(反転の瞬間が読めるように)
  ctx.strokeStyle = COLORS.shu;
  ctx.lineWidth = 1.5;
  for (const i of g.marked) {
    if (a[i] < 0) {
      const x = pad + i * barW;
      ctx.strokeRect(x + 0.5, y0, Math.max(barW - gap - 1, 0.5), -a[i] * scale);
    }
  }

  // 目盛(振幅の指標)
  ctx.fillStyle = COLORS.inkSoft;
  ctx.font = "11px Consolas, monospace";
  ctx.fillText(`±${maxAmp.toFixed(2)}`, pad + 2, 13);
  ctx.fillText(`平均 ${mean.toFixed(4)}`, pad + 2, h - 6);
}

function drawCurve() {
  const svg = $("curve");
  const W = 900, H = 260, padL = 40, padR = 16, padT = 14, padB = 30;
  const tmax = curveTmax();
  const { N, k } = g;
  const tstar = optimalIterations(N, k);
  const x = (t) => padL + (t / tmax) * (W - padL - padR);
  const y = (p) => H - padB - p * (H - padT - padB);

  let els = "";
  // 罫線(確率 0, 0.5, 1)
  for (const p of [0, 0.5, 1]) {
    els += `<line x1="${padL}" y1="${y(p)}" x2="${W - padR}" y2="${y(p)}" stroke="#363b55" stroke-width="1"/>`;
    els += `<text x="${padL - 6}" y="${y(p) + 4}" text-anchor="end" font-size="11" fill="#9a97a8" font-family="Consolas,monospace">${p}</text>`;
  }
  // 理論曲線(実数 t の連続波 — 回り込みも見える)
  const pts = [];
  const steps = 240;
  for (let i = 0; i <= steps; i++) {
    const t = (i / steps) * tmax;
    pts.push(`${x(t).toFixed(1)},${y(Math.sin((2 * t + 1) * g.theta) ** 2).toFixed(1)}`);
  }
  els += `<polyline points="${pts.join(" ")}" fill="none" stroke="#7fb8a8" stroke-width="1.5" opacity="0.8"/>`;
  // t* 線
  els += `<line x1="${x(tstar)}" y1="${padT}" x2="${x(tstar)}" y2="${H - padB}" stroke="#d9a84e" stroke-width="1.5" stroke-dasharray="5 4"/>`;
  els += `<text x="${x(tstar) + 4}" y="${padT + 10}" font-size="11" fill="#d9a84e" font-family="Consolas,monospace">t*=${tstar}</text>`;
  // 整数 t の点
  for (let t = 0; t <= tmax; t++) {
    const p = theoryProb(N, k, t);
    els += `<circle cx="${x(t)}" cy="${y(p)}" r="3" fill="#7fb8a8"/>`;
  }
  // 現在位置(完了反復のみ打点)
  const tNow = iterations(g);
  if (nextHalf === "oracle") {
    const pNow = successProb(g);
    els += `<circle cx="${x(tNow)}" cy="${y(pNow)}" r="5.5" fill="none" stroke="#d4644a" stroke-width="2.5"/>`;
  }
  // 横軸目盛
  const tickEvery = tmax <= 12 ? 1 : Math.ceil(tmax / 12);
  for (let t = 0; t <= tmax; t += tickEvery) {
    els += `<text x="${x(t)}" y="${H - padB + 16}" text-anchor="middle" font-size="11" fill="#9a97a8" font-family="Consolas,monospace">${t}</text>`;
  }
  els += `<text x="${(padL + W - padR) / 2}" y="${H - 4}" text-anchor="middle" font-size="11" fill="#9a97a8">反復 t</text>`;
  svg.innerHTML = els;
}

// ---------------------------------------------------------------- 深リンク
function syncHash() {
  const t = iterations(g);
  history.replaceState(null, "", encodeLink(n, marked, nextHalf === "oracle" ? t : t));
}

function applyHash() {
  const d = decodeLink(location.hash);
  if (d === null) return false;
  n = d.n;
  marked = d.marked;
  $("n-select").value = String(n);
  rebuild(d.t);
  return true;
}

// ---------------------------------------------------------------- 配線
function init() {
  const sel = $("n-select");
  for (let i = 2; i <= 10; i++) {
    const opt = document.createElement("option");
    opt.value = String(i);
    opt.textContent = `n = ${i}(N = ${2 ** i})`;
    sel.appendChild(opt);
  }
  sel.value = "3";
  sel.addEventListener("change", () => setN(Number(sel.value)));

  $("btn-half").addEventListener("click", () => { stopPlay(); halfstep(); });
  $("btn-iter").addEventListener("click", () => { stopPlay(); fullIter(); });
  $("btn-optimal").addEventListener("click", () => runTo(optimalIterations(g.N, g.k)));
  $("btn-overshoot").addEventListener("click", () => runTo(overshootTarget()));
  $("btn-reset").addEventListener("click", () => rebuild(0));
  $("btn-play").addEventListener("click", togglePlay);

  canvas.addEventListener("click", (ev) => {
    const rect = canvas.getBoundingClientRect();
    const pad = 8;
    const innerW = rect.width - pad * 2;
    const idx = Math.floor(((ev.clientX - rect.left - pad) / innerW) * g.N);
    if (idx >= 0 && idx < g.N) toggleMarked(idx);
  });

  window.addEventListener("resize", () => render());

  if (!applyHash()) rebuild(0);
}

init();
