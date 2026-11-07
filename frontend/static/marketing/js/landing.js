/* Landing page — shared scroll + motion */

/* ---- Lenis smooth scroll (respects reduced-motion) ---- */
(function () {
  if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
  const lenis = new Lenis({ duration: 1.1, smoothWheel: true });
  window.lenis = lenis;
  function raf(t) { lenis.raf(t); requestAnimationFrame(raf); }
  requestAnimationFrame(raf);
  document.querySelectorAll('a[href^="#"]:not(.nav-link)').forEach(a => {
    a.addEventListener("click", e => {
      const el = document.querySelector(a.getAttribute("href"));
      if (el) { e.preventDefault(); lenis.scrollTo(el, { offset: -70 }); }
    });
  });
})();

/* ---- scroll reveal + section dividers ---- */
(function () {
  const opts = { threshold: .12, rootMargin: "0px 0px -8% 0px" };
  const onEnter = (entries, io) => {
    entries.forEach(en => {
      if (en.isIntersecting) {
        en.target.classList.add("in");
        io.unobserve(en.target);
      }
    });
  };
  const revealIo = new IntersectionObserver(onEnter, opts);
  document.querySelectorAll(".reveal").forEach(el => revealIo.observe(el));

  const dividerIo = new IntersectionObserver(onEnter, { threshold: .15, rootMargin: "0px 0px -5% 0px" });
  document.querySelectorAll(".section-divider").forEach(el => dividerIo.observe(el));

  const heroDivider = document.querySelector(".section-divider--hero");
  if (heroDivider) {
    requestAnimationFrame(() => heroDivider.classList.add("in", "is-visible"));
  }
})();
