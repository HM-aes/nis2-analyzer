/* Header — hero scope pre-check (Alpine) */
function scopeCheck() {
  return {
    step: 0, done: false,
    answers: [null, null, null],
    questions: [
      { q: "Which best describes your sector?",
        opts: ["Energy, transport, banking, health, water, digital infra", "Postal, waste, chemicals, food, manufacturing, research", "Public administration", "None of these"] },
      { q: "How large is your organisation?",
        opts: ["250+ staff, or €50M+ turnover", "50–249 staff, or €10M+ turnover", "Under 50 staff / €10M", "Not sure"] },
      { q: "Do you operate in more than one EU member state?",
        opts: ["Yes, several", "Two", "Just one", "Not in the EU"] },
    ],
    get verdict() {
      const sector = this.answers[0], size = this.answers[1];
      if (sector === 0 && size <= 1)
        return { mark: "!", title: "Likely an essential entity",
          note: "You'd fall under proactive supervision — audits and inspections, not just incident response." };
      if (sector <= 2 && size <= 1)
        return { mark: "!", title: "Likely an important entity",
          note: "In scope for the full Article 21 measures, with incident-triggered supervision." };
      if (sector === 3 || size === 2)
        return { mark: "?", title: "Possibly out of scope — worth confirming",
          note: "Size exceptions and sole-provider rules can pull smaller entities back in. The full check settles it." };
      return { mark: "?", title: "Needs a closer look",
          note: "Your answers sit near a threshold. The full assessment resolves it precisely." };
    },
    choose(i) {
      this.answers[this.step] = i;
      setTimeout(() => {
        if (this.step < this.questions.length - 1) this.step++;
        else this.done = true;
      }, 220);
    },
    reset() { this.step = 0; this.done = false; this.answers = [null, null, null]; }
  };
}
