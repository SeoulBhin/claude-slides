"""python test_build.py — 숫자 검사가 맞게 잡고 맞게 통과시키는지."""
from build import check_numbers

SRC = "날짜,문의\n월,142,131\n화,128,125\n"

# 통과: CSV 숫자 그대로, 합계·증감률은 원본 숫자로 된 계산식
assert check_numbers('<b>142</b><b data-calc="142+128">270</b><b data-calc="(142-128)/128*100">10.9%</b>', SRC) == []
# 걸림: 원본에 없는 숫자(지어낸 숫자)
assert check_numbers("<b>150</b>", SRC) == ["원본에 없는 숫자: 150"]
# 걸림: 계산 틀림
assert any("계산 불일치" in e for e in check_numbers('<b data-calc="142+128">280</b>', SRC))
# 걸림: 계산식에 원본에 없는 숫자
assert any("원본에 없음" in e for e in check_numbers('<b data-calc="142+999">1141</b>', SRC))
# 걸림: 차트 data-values 에 지어낸 값
assert check_numbers('<div class="chart" data-values="142|77"></div>', SRC) == ["원본에 없는 숫자: 77"]
print("ok")
