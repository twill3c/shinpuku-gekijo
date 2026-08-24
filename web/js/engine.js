// 振幅劇場エンジン — グローバー探索の厳密シミュレーション(純粋関数、UI 非依存)
//
// 状態は実振幅ベクトル(グローバー反復は実部分空間に閉じる — SPEC スコープ外条項)。
// 意味論(SPEC F-01/F-02, G-01..G-03):
//   - オラクル: 目印インデックスの振幅の符号を反転する
//   - 拡散: 平均まわりの反転 a ← 2·mean − a
//   - 1 反復 = オラクル + 拡散。乱数は使わない(N-02)
//   - t* は第一ピーク窓 t ∈ [0, ⌈π/(4θ)⌉] の argmax(同値 1e-12 は最小 t — G-02)

export function createGrover(n, marked) {
  if (!Number.isInteger(n) || n < 2 || n > 10) {
    throw new RangeError(`n は 2..10 の整数(受領: ${n})`);
  }
  const N = 2 ** n;
  if (!Array.isArray(marked) || marked.length === 0) {
    throw new RangeError("目印集合が空");
  }
  const set = new Set();
  for (const m of marked) {
    if (!Number.isInteger(m) || m < 0 || m >= N) {
      throw new RangeError(`目印 ${m} が範囲外(0..${N - 1})`);
    }
    if (set.has(m)) throw new RangeError(`目印 ${m} が重複`);
    set.add(m);
  }
  const k = set.size;
  if (k >= N) throw new RangeError(`目印が全件(k=${k}, N=${N})— 探索が定義されない`);
  const theta = Math.asin(Math.sqrt(k / N));
  const state = new Float64Array(N).fill(1 / Math.sqrt(N));
  return {
    n, N, k,
    marked: [...set].sort((a, b) => a - b),
    markedSet: set,
    theta,
    state,
    oracleCalls: 0,
    halfsteps: 0, // 実行済み半歩数(偶数 = 反復の切れ目)
  };
}

export function oracle(g) {
  for (const i of g.marked) g.state[i] = -g.state[i];
  g.oracleCalls += 1;
  g.halfsteps += 1;
}

export function diffuse(g) {
  let sum = 0;
  const a = g.state;
  for (let i = 0; i < g.N; i++) sum += a[i];
  const twoMean = 2 * (sum / g.N);
  for (let i = 0; i < g.N; i++) a[i] = twoMean - a[i];
  g.halfsteps += 1;
}

export function iterate(g) {
  oracle(g);
  diffuse(g);
}

// 完了済み反復数(オラクル+拡散の組)
export function iterations(g) {
  return Math.floor(g.halfsteps / 2);
}

export function successProb(g) {
  let s = 0;
  for (const i of g.marked) s += g.state[i] * g.state[i];
  return s;
}

// 理論成功確率 P(t) = sin²((2t+1)θ)
export function theoryProb(N, k, t) {
  const theta = Math.asin(Math.sqrt(k / N));
  return Math.sin((2 * t + 1) * theta) ** 2;
}

// 最適反復 t*(第一ピーク窓の argmax — G-02)
export function optimalIterations(N, k) {
  const theta = Math.asin(Math.sqrt(k / N));
  const hi = Math.ceil(Math.PI / (4 * theta));
  let bestT = 0, bestP = -1;
  for (let t = 0; t <= hi; t++) {
    const p = Math.sin((2 * t + 1) * theta) ** 2;
    if (p > bestP + 1e-12) { bestT = t; bestP = p; }
  }
  return bestT;
}

// 古典対照(SPEC F-07: 期待 N/2・最悪 N)
export function classicalReference(N) {
  return { expected: N / 2, worst: N };
}
