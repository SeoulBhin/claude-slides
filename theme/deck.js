// 발표 넘김 + 차트 그리기. build.py 가 덱 HTML 안에 그대로 넣는다(외부 파일·CDN 없음).
(() => {
  const NS = "http://www.w3.org/2000/svg";
  const el = (tag, attrs, text) => {
    const n = document.createElementNS(NS, tag);
    for (const k in attrs) n.setAttribute(k, attrs[k]);
    if (text != null) n.textContent = text;
    return n;
  };
  const list = s => s.split("|").map(x => x.trim());

  // <div class="chart" data-type="bar|line" data-labels="월|화" data-values="120|98" [data-series="이번주|지난주" data-values2="..."] [data-unit="건"]>
  document.querySelectorAll(".chart").forEach(c => {
    const labels = list(c.dataset.labels);
    const series = [list(c.dataset.values).map(Number)];
    if (c.dataset.values2) series.push(list(c.dataset.values2).map(Number));
    const unit = c.dataset.unit || "";
    const colors = ["var(--brand)", "var(--brand-2)"];
    const W = 1000, H = 400, L = 40, B = 40, T = 30;
    const max = Math.max(...series.flat()) * 1.15 || 1;
    const y = v => T + (H - T - B) * (1 - v / max);
    const svg = el("svg", { viewBox: `0 0 ${W} ${H}`, preserveAspectRatio: "xMidYMid meet" });
    [0.25, 0.5, 0.75].forEach(f => svg.append(el("line", { x1: L, x2: W, y1: y(max / 1.15 * f), y2: y(max / 1.15 * f), stroke: "var(--line)", "stroke-dasharray": "4 6" })));
    svg.append(el("line", { x1: L, x2: W, y1: H - B, y2: H - B, stroke: "#c9cfdc", "stroke-width": 2 }));
    const slot = (W - L) / labels.length;
    labels.forEach((lb, i) => svg.append(el("text", { x: L + slot * (i + 0.5), y: H - 12, "text-anchor": "middle" }, lb)));

    if (c.dataset.type === "line") {
      series.slice().reverse().forEach((vals, r) => { // 두 번째 계열을 먼저 그려 첫 계열 라벨이 가려지지 않게
        const s = series.length - 1 - r;
        const pts = vals.map((v, i) => [L + slot * (i + 0.5), y(v)]);
        svg.append(el("polyline", { points: pts.join(" "), fill: "none", stroke: colors[s], "stroke-width": 4 }));
        pts.forEach(([px, py], i) => {
          svg.append(el("circle", { cx: px, cy: py, r: 7, fill: "#fff", stroke: colors[s], "stroke-width": 4 }));
          if (s === 0) svg.append(el("text", { x: px, y: py - 16, "text-anchor": "middle", class: "v" }, vals[i].toLocaleString() + unit));
        });
      });
    } else {
      const bw = slot * 0.6 / series.length;
      series.forEach((vals, s) => vals.forEach((v, i) => {
        const x = L + slot * i + slot * 0.2 + bw * s;
        svg.append(el("rect", { x, y: y(v), width: bw - 6, height: H - B - y(v), rx: 6, fill: colors[s] }));
        svg.append(el("text", { x: x + bw / 2 - 3, y: y(v) - 10, "text-anchor": "middle", class: s ? "" : "v" }, v.toLocaleString() + unit));
      }));
    }
    if (c.dataset.series) list(c.dataset.series).forEach((nm, s) => {
      svg.append(el("rect", { x: W - 220 + s * 110, y: 0, width: 14, height: 14, rx: 4, fill: colors[s] }));
      svg.append(el("text", { x: W - 200 + s * 110, y: 13 }, nm));
    });
    c.append(svg);
  });

  // 발표 모드: ← → 스페이스로 넘김, 화면 크기에 맞춰 축소
  const slides = [...document.querySelectorAll(".slide")];
  slides.forEach((s, i) => { s.dataset.n = i + 1; s.dataset.total = slides.length; });
  const bar = document.body.appendChild(document.createElement("div"));
  bar.className = "progress";
  let cur = Math.max(0, Number(location.hash.slice(1)) - 1 || 0);
  const show = () => {
    slides.forEach((s, i) => s.classList.toggle("on", i === cur));
    bar.style.width = ((cur + 1) / slides.length) * 100 + "%";
    document.documentElement.style.setProperty("--fit", Math.min(innerWidth / 1280, innerHeight / 720));
    history.replaceState(null, "", "#" + (cur + 1));
  };
  addEventListener("keydown", e => {
    if (["ArrowRight", "PageDown", " "].includes(e.key)) cur = Math.min(cur + 1, slides.length - 1);
    else if (["ArrowLeft", "PageUp"].includes(e.key)) cur = Math.max(cur - 1, 0);
    else return;
    e.preventDefault(); show();
  });
  addEventListener("click", () => { cur = Math.min(cur + 1, slides.length - 1); show(); });
  addEventListener("resize", show);
  show();
})();
