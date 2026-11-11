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
import os
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


def put(src: Path, dst: Path, root: Path):
    """dst 에 쓴다. 세션이 심은 링크(심볼릭·하드·정션)를 따라 저장소 밖에 쓰지 않는다."""
    # resolve() 는 심볼릭 링크·정션을 끝까지 따라가므로, 폴더가 링크면 저장소 밖으로 나온다
    if not dst.parent.resolve().is_relative_to(root.resolve()):
        sys.exit(f"✗ {dst} 가 저장소 밖을 가리킨다(링크된 폴더) — 쓰지 않고 멈춘다")
    # 같은 폴더에 임시 파일로 쓴 뒤 이름을 바꿔 끼운다 — 기존 dst 가 심볼릭·하드 링크여도 링크 너머엔 안 쓴다
    fd, tmp = tempfile.mkstemp(dir=dst.parent)
    os.close(fd)
    shutil.copyfile(src, tmp)
    os.replace(tmp, dst)


def main(deck, *sources):
    sys.stdout.reconfigure(encoding="utf-8")
    deck = Path(deck).absolute()
    if deck.is_symlink() or deck.is_junction() or not deck.resolve().is_relative_to(deck.parent.parent.resolve()):
        sys.exit("✗ 덱 폴더가 링크다 — 멈춘다")
    here = deck.parent.parent                      # decks/<이름> 의 두 단계 위 = 작업 저장소
    deck = deck.resolve()
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
                put(clean / f, here / f, here)
        slides = deck / "slides.html"
        if slides.is_symlink() or not slides.resolve().is_relative_to(deck):
            sys.exit("✗ slides.html 이 링크다(덱 폴더 밖 파일을 읽게 할 수 있다) — 멈춘다")
        out = clean / "decks" / deck.name
        out.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(slides, out / "slides.html")
        # -E: PYTHONPATH 같은 환경변수로 끼어드는 코드를 막는다. -s·-I 는 안 쓴다(playwright 가 사용자 site-packages 에 있음).
        # 한계: 덱 세션은 같은 Windows 사용자로 돈다. 사용자 site-packages·python.exe·브라우저 캐시를 고칠 수 있는 세션이면
        # 어떤 플래그로도 못 막는다 — 그 수준은 세션을 다른 계정·샌드박스에서 돌려서 막을 일이다
        py = [sys.executable, "-E"]
        ok = subprocess.run([*py, "test_build.py"], cwd=clean).returncode == 0
        ok = subprocess.run([*py, "build.py", f"decks/{deck.name}", *sources], cwd=clean).returncode == 0 and ok
        if ok:
            for f in out.glob(f"{deck.name}.*"):
                put(f, deck / f.name, here)
    return 0 if ok and not changed else 1


if __name__ == "__main__":
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    sys.exit(main(*sys.argv[1:]))
