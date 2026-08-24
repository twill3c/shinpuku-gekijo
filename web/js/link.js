// link.js — 深リンク #n=<int>&m=<csv>&t=<int> の符号化/復号(F-09)
// 復号は構成の妥当性(n 2..10・目印 1..N-1 件・重複なし・t ≥ 0)まで検査し、
// 不正は null を返す(例外にしない — UI は無視して既定構成で開く)。

export function encodeLink(n, marked, t) {
  return `#n=${n}&m=${marked.join(",")}&t=${t}`;
}

export function decodeLink(hash) {
  if (typeof hash !== "string" || !hash.startsWith("#")) return null;
  const params = new URLSearchParams(hash.slice(1));
  const nRaw = params.get("n"), mRaw = params.get("m"), tRaw = params.get("t");
  if (nRaw === null || mRaw === null) return null;
  const n = Number(nRaw);
  if (!Number.isInteger(n) || n < 2 || n > 10) return null;
  const N = 2 ** n;
  if (mRaw === "") return null;
  const marked = mRaw.split(",").map(Number);
  const seen = new Set();
  for (const m of marked) {
    if (!Number.isInteger(m) || m < 0 || m >= N || seen.has(m)) return null;
    seen.add(m);
  }
  if (seen.size >= N) return null;
  const t = tRaw === null ? 0 : Number(tRaw);
  if (!Number.isInteger(t) || t < 0) return null;
  return { n, marked: [...seen].sort((a, b) => a - b), t };
}
