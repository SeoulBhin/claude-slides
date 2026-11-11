"""덱을 만든 세션이 끝난 뒤 사람이(또는 CI가) 돌리는 최종 확인.

    python verify.py decks/주간보고 samples/01_주간보고.csv samples/01_주간보고_메모.txt

1. 검사기(build.py·theme/·test_build.py)가 원격(GitHub)에 올라간 것과 같은지 git 으로 본다.
   바뀌었으면 원본으로 되돌리고 실패 처리한다 — 덱 만든 세션이 검사기를 고쳤다는 뜻이라서.
   덱 폴더 밖에 다른 파일이 바뀌거나 생겼으면 아무것도 실행하지 않고 멈춘다.
2. 원본 검사기로 test_build.py 와 build.py 를 다시 돌린다.

--allowedTools 는 "묻지 않고 허용할 목록"이지 칸막이가 아니다(auto 모드에선 목록 밖 편집도 된다).
그래서 막는 대신 끝난 뒤 코드로 확인한다.
"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent
GUARDED = ["build.py", "theme", "test_build.py", "verify.py"]


def main(*args):
    sys.stdout.reconfigure(encoding="utf-8")
    git = lambda *a: subprocess.run(["git", *a], cwd=ROOT, capture_output=True, text=True, encoding="utf-8")
    # 기준은 HEAD 가 아니라 원격(@{u}) — 세션이 고친 걸 커밋해 버리면 HEAD 와의 diff 는 비어 버린다.
    # ponytail: 세션이 git push 까지 하면 원격도 바뀐다. 그것까지 막으려면 기준 커밋 해시를 저장소 밖에 둘 것
    base = "@{u}"
    if git("rev-parse", "--verify", "-q", base).returncode:
        sys.exit("✗ 원격 추적 브랜치가 없다 — 검사기 원본을 비교할 기준이 없다")
    # decks/ 밖의 변경·새 파일은 전부 실패. 루트에 json.py 같은 파일을 심으면 아래에서 파이썬을 돌릴 때 그 코드가 실행된다
    status = git("status", "--porcelain", "--untracked-files=all").stdout.splitlines()
    outside = sorted({ln[3:].strip('"') for ln in status if not ln[3:].strip('"').startswith("decks/")}
                     | {p for p in git("diff", "--name-only", base, "HEAD").stdout.split() if not p.startswith("decks/")})
    stray = [p for p in outside if not any(p == g or p.startswith(g + "/") for g in GUARDED)]
    if stray:
        sys.exit(f"✗ 덱 폴더 밖에 바뀌거나 생긴 파일이 있다: {', '.join(stray)} — 아무것도 실행하지 않고 멈춘다")
    changed = [p for p in outside if p not in stray]
    if changed:
        print("✗ 검사기가 바뀌었다:", ", ".join(changed), "→ 원격 원본으로 되돌린다", flush=True)
        git("checkout", base, "--", *GUARDED)
    py = sys.executable
    ok = subprocess.run([py, "test_build.py"], cwd=ROOT).returncode == 0
    ok = subprocess.run([py, "build.py", *args], cwd=ROOT).returncode == 0 and ok
    return 0 if ok and not changed else 1


if __name__ == "__main__":
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    sys.exit(main(*sys.argv[1:]))
