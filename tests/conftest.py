"""shinpuku-gekijo テスト共通ヘルパ。

JS エンジンは harness/run_grover.mjs(Node CLI)経由で駆動し、
Python 参照実装 harness/reference_grover.py と JSON で突き合わせる。
"""
import json
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "harness"))


def run_js_raw(args: list[str], timeout: int = 60) -> subprocess.CompletedProcess:
    """run_grover.mjs を生で呼ぶ(不正構成の拒否検査 T-014 用)。"""
    cmd = ["node", str(ROOT / "harness" / "run_grover.mjs")] + args
    return subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8",
                          timeout=timeout, cwd=ROOT)


def run_js(n: int, marked: list[int], iters: int, timeout: int = 60) -> dict:
    """JS エンジンで iters 反復を実行し、全半歩の状態を含む JSON を返す。"""
    proc = run_js_raw(["--n", str(n), "--marked", ",".join(map(str, marked)),
                       "--iters", str(iters)], timeout=timeout)
    assert proc.returncode == 0, f"run_grover.mjs failed: {proc.stderr}"
    return json.loads(proc.stdout)


def run_py(n: int, marked: list[int], iters: int) -> dict:
    """Python 参照実装で同じ実行をする。"""
    import reference_grover
    return reference_grover.run_grover(n, marked, iters)
