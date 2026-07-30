/* dashboard mock — count-up + feed reveal on scroll-into-view */
function dashMock() {
  return {
    feedIn: false,
    stats: [
      { k: "Controls met", d: "+12%", dc: "var(--green)", live: false, target: 87, disp: "0",
        ico: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9"><path d="M9 11l3 3L22 4"/><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"/></svg>` },
      { k: "Documents", d: "+5%", dc: "var(--green)", live: false, target: 1240, disp: "0",
        ico: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><path d="M14 2v6h6"/></svg>` },
      { k: "Open gaps", d: "-2", dc: "var(--amber)", live: true, target: 6, disp: "0",
        ico: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/></svg>` },
      { k: "In review", d: "Active", dc: "var(--amber)", live: true, target: 3, disp: "0",
        ico: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9"><path d="M21 12a9 9 0 1 1-6.219-8.56"/></svg>` },
    ],
    feed: [
      { id: 1, i: "JD", n: "J. Doe", q: "Mapped Article 21 supply-chain controls", t: "2m", c: "var(--green)" },
      { id: 2, i: "MB", n: "M. Byrd", q: "Flagged gap in incident-response plan", t: "14m", c: "var(--amber)" },
      { id: 3, i: "SR", n: "S. Reyes", q: "Uploaded board-oversight evidence", t: "22m", c: "var(--green)" },
      { id: 4, i: "TK", n: "T. Klein", q: "Reviewed 72h notification workflow", t: "38m", c: "var(--green)" },
    ],
    proc: [
      { id: 1, n: "risk_register_2026.xlsx", m: "Article 21 · mapping", p: 82 },
      { id: 2, n: "ir_policy_v3.pdf", m: "Article 23 · parsing", p: 45 },
    ],
    init(el) {
      const io = new IntersectionObserver((es) => {
        es.forEach(e => { if (e.isIntersecting) { this.run(); io.disconnect(); } });
      }, { threshold: .3 });
      io.observe(el);
    },
    run() {
      this.feedIn = true;
      this.stats.forEach(s => {
        const dur = 1300, t0 = performance.now();
        const tick = (t) => {
          const p = Math.min((t - t0) / dur, 1);
          const eased = 1 - Math.pow(1 - p, 3);
          s.disp = Math.round(s.target * eased).toLocaleString('en-US');
          if (p < 1) requestAnimationFrame(tick);
        };
        requestAnimationFrame(tick);
      });
    }
  }
}
