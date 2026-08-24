// run_grover.mjs — テスト・検証用 CLI。
//   node harness/run_grover.mjs --n 3 --marked "2,6" --iters 4
// iters 反復を実行し、初期状態+全半歩の状態ベクトルを JSON で stdout へ。
import {
  createGrover, oracle, diffuse, successProb, optimalIterations, classicalReference,
} from "../web/js/engine.js";

const args = process.argv.slice(2);
function argOf(flag, def) {
  const i = args.indexOf(flag);
  return i >= 0 && i + 1 < args.length ? args[i + 1] : def;
}

try {
  const n = Number(argOf("--n", "NaN"));
  const markedStr = argOf("--marked", "");
  const marked = markedStr === "" ? [] : markedStr.split(",").map(Number);
  const iters = Number(argOf("--iters", "0"));
  if (!Number.isInteger(iters) || iters < 0) throw new RangeError(`iters が不正: ${iters}`);

  const g = createGrover(n, marked);
  const states = [Array.from(g.state)];
  const halfsteps = ["init"];
  const probs = [successProb(g)];
  for (let t = 0; t < iters; t++) {
    oracle(g);
    states.push(Array.from(g.state));
    halfsteps.push("oracle");
    probs.push(successProb(g));
    diffuse(g);
    states.push(Array.from(g.state));
    halfsteps.push("diffuse");
    probs.push(successProb(g));
  }
  const out = {
    impl: "js",
    n: g.n, N: g.N, k: g.k, marked: g.marked,
    theta: g.theta,
    tstar: optimalIterations(g.N, g.k),
    classical: classicalReference(g.N),
    oracleCalls: g.oracleCalls,
    halfsteps, states, successProbs: probs,
  };
  process.stdout.write(JSON.stringify(out));
} catch (e) {
  process.stderr.write(String(e && e.message ? e.message : e));
  process.exit(1);
}
