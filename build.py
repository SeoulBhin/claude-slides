"""슬라이드 본문(slides.html) + 공통 테마 → 발표용 단일 HTML + PDF, 그리고 검사.

    python build.py decks/주간보고 samples/01_주간보고.csv samples/01_주간보고_메모.txt

검사 3가지(하나라도 걸리면 종료 코드 1):
  1. 숫자: 덱에 나온 두 자리 이상 숫자는 원본 자료에 그대로 있거나,
     data-calc="원본숫자로 된 계산식" 이 붙어 있고 계산 결과와 일치해야 한다.
  2. 넘침: 1280x720 슬라이드 밖으로 내용이 넘치면 안 된다.
  3. PDF: 쪽수 = 슬라이드 수.
"""
import html
import re
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).parent
NUM = re.compile(r"\d[\d,]*(?:\.\d+)?")
CALC = re.compile(r'<(\w+)[^>]*\bdata-calc="([^"]+)"[^>]*>(.*?)</\1>', re.S)
ATTR_VALUES = re.compile(r'\bdata-(?!calc\b)[\w-]+="([^"]+)"')
ACTIVE = re.compile(r"<\s*(?:script|style|iframe|object|embed|link|meta|svg)\b|\bon\w+\s*=|javascript:|\bstyle\s*=", re.I)


def nums(text):
    # ponytail: 한 자리 숫자(쪽번호·"3개" 등)는 검사 안 함 — 오탐이 더 많아서
    return {n.replace(",", "") for n in NUM.findall(text) if len(re.sub(r"\D", "", n)) >= 2}


def check_numbers(slides, sources):
    # CSV 의 "142,131,38" 을 천 단위 콤마로 읽어 한 숫자로 붙이지 않게, 콤마를 구분자로 본 경우도 합친다
    src = nums(sources) | nums(sources.replace(",", " "))
    # 스크립트·스타일이 들어가면 검사가 끝난 뒤 화면 숫자를 바꿀 수 있다 — 슬라이드는 정적 HTML 만
    errors = [f"슬라이드에 쓸 수 없는 HTML: {m!r}" for m in sorted(set(ACTIVE.findall(slides)))]
    for _, formula, shown in CALC.findall(slides):
        formula = html.unescape(formula)
        for n in nums(formula) - src - {"100"}:  # 100 은 백분율 환산 상수
            errors.append(f"계산식 {formula!r} 의 {n} 이 원본에 없음")
        if not re.fullmatch(r"[\d.,+\-*/() ]+", formula):
            errors.append(f"계산식에 숫자·사칙연산 말고 다른 게 있음: {formula!r}")
            continue
        # 위 fullmatch 로 숫자·사칙연산·괄호만 남겼으니 eval 해도 코드는 못 돈다
        got = eval(formula.replace(",", ""), {"__builtins__": {}})
        found = NUM.findall(re.sub(r"<[^>]+>", "", shown))
        if len(found) != 1:  # 첫 숫자만 맞추고 옆에 다른 숫자를 끼워 넣는 걸 막는다
            errors.append(f"data-calc 요소에는 숫자가 정확히 하나여야 함: {shown!r}")
            continue
        val = found[0].replace(",", "")
        digits = len(val.split(".")[1]) if "." in val else 0
        # ponytail: 부호는 화살표·+/- 로 따로 표시하므로 절댓값만 비교
        if abs(round(abs(got), digits) - float(val)) > 1e-9:
            errors.append(f"계산 불일치: {formula} = {got:.4f} 인데 덱에는 {val}")
    rest = CALC.sub("", slides)
    # data-values 만이 아니라 화면에 쓰일 수 있는 모든 data-* 속성(라벨·단위 등)의 숫자도 본다
    values = " ".join(v.replace("|", " ") for v in ATTR_VALUES.findall(rest))
    text = html.unescape(re.sub(r"<[^>]+>", " ", rest))
    for n in sorted(nums(text + " " + values) - src):
        errors.append(f"원본에 없는 숫자: {n}")
    return errors


def main(deck_dir, *source_paths):
    sys.stdout.reconfigure(encoding="utf-8")  # Windows cp949 콘솔에서 ✗ 출력
    deck_dir = ROOT / deck_dir
    slides = (deck_dir / "slides.html").read_text(encoding="utf-8")
    sources = "\n".join(Path(p).read_text(encoding="utf-8") for p in source_paths)
    h1 = re.search(r"<h1[^>]*>(.*?)</h1>", slides, re.S)
    title = html.unescape(re.sub(r"<[^>]+>", " ", h1[1])).strip() if h1 else deck_dir.name

    css = (ROOT / "theme/theme.css").read_text(encoding="utf-8")
    js = (ROOT / "theme/deck.js").read_text(encoding="utf-8")
    out = deck_dir / f"{deck_dir.name}.html"
    out.write_text(
        f'<!doctype html><html lang="ko"><head><meta charset="utf-8">'
        f'<meta name="viewport" content="width=device-width,initial-scale=1">'
        f"<title>{html.escape(title)}</title><style>{css}</style></head>"
        f'<body><main class="deck">{slides}</main><script>{js}</script></body></html>',
        encoding="utf-8",
    )

    errors = check_numbers(slides, sources)
    pdf = out.with_suffix(".pdf")
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1280, "height": 720})
        page.goto(out.resolve().as_uri())
        page.emulate_media(media="print")
        over = page.eval_on_selector_all(
            ".slide",
            "ss => ss.map((s, i) => [i + 1, s.scrollHeight - s.clientHeight, s.scrollWidth - s.clientWidth])"
                ".filter(([, h, w]) => h > 1 || w > 1)",
        )
        errors += [f"{i}번 슬라이드 넘침: 세로 {h}px, 가로 {w}px" for i, h, w in over]
        count = page.locator(".slide").count()
        page.pdf(path=pdf, width="1280px", height="720px", print_background=True, prefer_css_page_size=True)
        browser.close()
    pages = len(re.findall(rb"/Type\s*/Page\b", pdf.read_bytes()))
    if pages != count:
        errors.append(f"PDF 쪽수 {pages} != 슬라이드 {count}장")

    print(f"{out.relative_to(ROOT)}  /  {pdf.relative_to(ROOT)}  ({count}장)")
    for e in errors:
        print("  ✗", e)
    print("통과" if not errors else f"문제 {len(errors)}건 — slides.html 을 고치고 다시 돌린다")
    return 1 if errors else 0


if __name__ == "__main__":
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    sys.exit(main(*sys.argv[1:]))
