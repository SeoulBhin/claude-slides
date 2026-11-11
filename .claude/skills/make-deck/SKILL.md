---
name: make-deck
description: 회의 자료(CSV·회의록·기획 문서 등)를 읽어 회사 공통 테마의 HTML 발표 덱과 PDF를 만든다. "이걸로 발표자료 만들어줘", "PPT 만들어줘", "슬라이드로 정리해줘", "덱 만들어줘"처럼 자료 파일을 주고 발표용으로 바꿔 달라고 할 때 쓴다.
---

# make-deck

자료 파일 → `decks/<이름>/slides.html`(슬라이드 본문만) → `python build.py` 가 테마를 입혀 `<이름>.html`·`<이름>.pdf` 를 만들고 검사한다.
디자인은 `theme/theme.css` 가 정한다. 너는 **내용과 구성만** 쓴다.

## 순서

1. 자료를 전부 읽는다. CSV 는 합계·평균·증감을 직접 암산하지 말고 `python -c` 로 계산한다.
2. 듣는 사람이 회의에서 **결정하거나 알아야 할 것**을 먼저 정하고, 그걸 위해 장을 짠다. 자료 순서를 그대로 옮기지 않는다.
3. `decks/<이름>/slides.html` 을 쓴다(아래 부품만 사용, `<html>`·`<style>`·`<script>` 금지).
4. `python build.py decks/<이름> <자료 파일들>` 을 돌린다.
5. `✗` 가 하나라도 나오면 slides.html 을 고치고 4로. **통과할 때까지 끝내지 않는다.**
   - `build.py`·`theme/` 는 **절대 고치지 않는다.** 검사기가 틀렸다고 보이면 고치지 말고 멈춘 뒤, 어떤 입력에서 왜 틀렸는지 사용자에게 보고한다.
6. 사용자에게 HTML·PDF 경로, 장 수, 자료에서 일부러 뺀 내용을 짧게 알린다.

## 덱 구성 규칙

- 5~8장. 첫 장은 표지(`cover`), 마지막 장은 "결정할 것/다음 할 일".
- 한 장에 메시지 하나. `h2` 는 주제어가 아니라 **결론 문장**("문의 12% 증가, 수요일 장애 탓"), 근거는 그 아래.
- 숫자 비교·추이는 표나 글보다 `chart`, 핵심 숫자 3~4개는 `kpis`, 일정은 `steps`.
- 글머리표는 한 장에 4개 이하, 한 줄 30자 안팎. 문장 대신 명사형으로 끊어도 된다.
- 자료에 없는 사실·숫자·사람 이름을 만들지 않는다. 모르는 건 "미정"이라고 쓴다.
- 회의록처럼 정리 안 된 자료는 결정사항·담당자·기한을 뽑아 표로 만든다.

## 숫자 규칙 (build.py 가 강제한다)

- 덱에 나오는 두 자리 이상 숫자는 **자료에 그대로 있어야** 한다.
- 계산한 숫자(합계·증감률·평균)는 계산식을 붙인다. 계산식에는 자료에 있는 숫자만 쓴다:
  `<b data-calc="(684-565)/565*100">21.1%</b>`
  build.py 가 식을 계산해 표시값(소수 자릿수 기준 반올림)과 비교한다. 부호는 비교하지 않으니 `up`/`down` 클래스나 +/− 로 표시한다.
- 날짜는 자료 표기를 따른다(`11/24`, `2026-11-05` 등). 자료에 없는 형태로 바꾸면 검사에 걸린다.

## 부품

```html
<section class="slide cover">
  <h1>고객지원 주간보고</h1>
  <p>11월 1주차 · 고객지원팀</p>
</section>

<section class="slide">
  <h2>결론 문장<small>보조 설명 한 줄</small></h2>
  <p class="lead">한 줄 핵심</p>
  <div class="kpis">
    <div><b>634</b><span>문의 건수</span></div>
    <div><b class="up" data-calc="(634-565)/565*100">12.2%</b><span>지난주 대비</span></div>
  </div>
</section>

<section class="slide">
  <h2>막대/선 차트</h2>
  <!-- data-type: bar | line. 값은 | 로 구분. 두 번째 계열은 선택 -->
  <div class="chart" data-type="bar" data-labels="월|화|수"
       data-values="142|128|151" data-values2="118|121|115"
       data-series="이번주|지난주" data-unit="건"></div>
</section>

<section class="slide">
  <h2>표와 2단</h2>
  <div class="cols">
    <table>
      <tr><th>항목</th><th class="num">값</th></tr>
      <tr><td>문의</td><td class="num">634</td></tr>
    </table>
    <ul><li>설명</li></ul>
  </div>
</section>

<section class="slide">
  <h2>일정</h2>
  <ol class="steps"><li><b>1~2주</b>FAQ 정리</li><li><b>3~4주</b>사내 테스트</li></ol>
</section>
```

그 밖에 쓸 수 있는 클래스: `muted`(회색 글자), `up`(초록), `down`(빨강). 인라인 `style` 은 쓰지 않는다 — 넘치면 내용을 줄이거나 장을 나눈다.
