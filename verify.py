"""덱을 만든 세션이 끝난 뒤 사람이(또는 CI가) 돌리는 최종 확인.

    python verify.py decks/주간보고 samples/01_주간보고.csv samples/01_주간보고_메모.txt

작업 폴더는 덱 만든 세션이 마음대로 고칠 수 있다(파일·커밋·git 설정·훅·.gitignore 까지).
그래서 작업 폴더의 검사기는 믿지 않는다.

1. GitHub 원본 저장소(REPO)를 임시 폴더에 새로 받는다. 작업 폴더의 git 설정·훅은 타지 않는다.
2. 작업 폴더 검사기(build.py·test_build.py·verify.py·theme/)가 원본과 다르면 원본으로 덮어쓰고 실패 처리한다.
3. 덱의 slides.html 한 파일만 원본 쪽에 복사해서, 원본 검사기로 test_build.py 와 build.py 를 돌린다.
   통과하면 만들어진 html·pdf 를 덱 폴더로 가져온다.

verify.py 자체도 세션이 고칠 수 있다. 확실히 하려면 세션 밖에서 받은 사본으로 돌린다:
    git clone https://github.com/SeoulBhin/claude-slides.git %TEMP%/cs && python %TEMP%/cs/verify.py decks/주간보고 ...
"""
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = "https://github.com/SeoulBhin/claude-slides.git"
CHECKER = ["build.py", "test_build.py", "verify.py", "theme/theme.css", "theme/deck.js"]
# ponytail: 세션이 GitHub 에 push 까지 하면 원본도 바뀐다. 그것까지 막으려면 믿는 커밋 해시를 저장소 밖에 적어 두고 대조할 것


def same(a: Path, b: Path) -> bool:
    return a.exists() and a.read_bytes().replace(b"\r\n", b"\n") == b.read_bytes().replace(b"\r\n", b"\n")


def main(deck, *sources):
    sys.stdout.reconfigure(encoding="utf-8")
    deck = Path(deck).resolve()
    here = deck.parent.parent                      # decks/<이름> 의 두 단계 위 = 작업 저장소
    sources = [str(Path(p).resolve()) for p in sources]
    with tempfile.TemporaryDirectory() as tmp:
        clean = Path(tmp) / "repo"
        r = subprocess.run(["git", "-c", "core.hooksPath=", "clone", "-q", "--depth", "1", REPO, str(clean)],
                           cwd=tmp, capture_output=True, text=True, encoding="utf-8")
        if r.returncode:
            sys.exit("✗ 원본 저장소를 받지 못했다: " + r.stderr.strip())
        changed = [f for f in CHECKER if not same(here / f, clean / f)]
        if changed:
            print("✗ 검사기가 바뀌었다:", ", ".join(changed), "→ 원본으로 덮어쓴다", flush=True)
            for f in changed:
                (here / f).parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(clean / f, here / f)
        out = clean / "decks" / deck.name
        out.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(deck / "slides.html", out / "slides.html")
        py = [sys.executable, "-E", "-s"]          # 환경변수·사용자 site-packages 로 끼어드는 코드도 막는다
        ok = subprocess.run([*py, "test_build.py"], cwd=clean).returncode == 0
        ok = subprocess.run([*py, "build.py", f"decks/{deck.name}", *sources], cwd=clean).returncode == 0 and ok
        if ok:
            for f in out.glob(f"{deck.name}.*"):
                shutil.copyfile(f, deck / f.name)
    return 0 if ok and not changed else 1


if __name__ == "__main__":
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    sys.exit(main(*sys.argv[1:]))
