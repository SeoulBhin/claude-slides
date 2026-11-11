"""덱을 만든 세션이 끝난 뒤 사람이(또는 CI가) 돌리는 최종 확인.

    python verify.py decks/주간보고 samples/01_주간보고.csv samples/01_주간보고_메모.txt

1. 검사기(build.py·theme/·test_build.py)가 마지막 커밋과 같은지 git 으로 본다.
   바뀌었으면 원본으로 되돌리고 실패 처리한다 — 덱 만든 세션이 검사기를 고쳤다는 뜻이라서.
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
    changed = git("diff", "--name-only", "HEAD", "--", *GUARDED).stdout.split()
    if changed:
        print("✗ 검사기가 바뀌었다:", ", ".join(changed), "→ 마지막 커밋으로 되돌린다", flush=True)
        git("checkout", "HEAD", "--", *GUARDED)
    py = sys.executable
    ok = subprocess.run([py, "test_build.py"], cwd=ROOT).returncode == 0
    ok = subprocess.run([py, "build.py", *args], cwd=ROOT).returncode == 0 and ok
    return 0 if ok and not changed else 1


if __name__ == "__main__":
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    sys.exit(main(*sys.argv[1:]))
