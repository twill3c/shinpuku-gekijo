// link_grover.mjs — 深リンク符号化/復号の検証 CLI(T-012)。
//   往復: node harness/link_grover.mjs --n 3 --marked "2,6" --t 4
//   復号: node harness/link_grover.mjs --hash "#n=3&m=2,6&t=4"
import { encodeLink, decodeLink } from "../web/js/link.js";

const args = process.argv.slice(2);
function argOf(flag) {
  const i = args.indexOf(flag);
  return i >= 0 && i + 1 < args.length ? args[i + 1] : null;
}

let out;
const hashArg = argOf("--hash");
if (hashArg !== null) {
  const decoded = decodeLink(hashArg);
  out = decoded === null ? { ok: false } : { ok: true, decoded };
} else {
  const n = Number(argOf("--n"));
  const marked = (argOf("--marked") ?? "").split(",").map(Number);
  const t = Number(argOf("--t"));
  const hash = encodeLink(n, marked, t);
  const decoded = decodeLink(hash);
  out = decoded === null ? { ok: false, hash } : { ok: true, hash, decoded };
}
process.stdout.write(JSON.stringify(out));
