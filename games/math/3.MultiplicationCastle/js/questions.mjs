import { validTables } from './rules.mjs';
export function shuffle(values, rng = Math.random) {
  const copy = [...values];
  for (let i = copy.length - 1; i > 0; i--) { const j = Math.floor(rng() * (i + 1)); [copy[i], copy[j]] = [copy[j], copy[i]]; }
  return copy;
}
export function makeOptions(a, b, rng = Math.random) {
  const answer = a * b;
  const candidates = shuffle([a + b, answer - a, answer + a, answer - b, answer + b, (a - 1) * b, (a + 1) * b, a * (b - 1), a * (b + 1)], rng);
  const wrong = new Set();
  for (const n of candidates) { if (n > 0 && n !== answer) wrong.add(n); if (wrong.size === 3) break; }
  for (let offset = 1; wrong.size < 3; offset++) for (const n of [answer + offset, answer - offset]) { if (n > 0 && n !== answer && wrong.size < 3) wrong.add(n); }
  return shuffle([answer, ...wrong], rng);
}
export class QuestionDeck {
  constructor(tables, rng = Math.random) {
    this.rng = rng; this.last = ''; this.turn = 0;
    const bank = validTables(tables).flatMap(a => Array.from({ length: 9 }, (_, i) => ({ a, b: i + 1, answer: a * (i + 1), key: `${a}x${i + 1}` })));
    bank.sort((x, y) => x.answer - y.answer || x.a - y.a || x.b - y.b);
    // Partition complete equations by rank, never duplicate them between groups.
    this.groups = [0, 1, 2].map(i => bank.slice(Math.floor(i * bank.length / 3), Math.floor((i + 1) * bank.length / 3)));
    this.bags = this.groups.map(group => shuffle(group, rng));
  }
  next() {
    const i = this.turn++ % 3;
    if (!this.bags[i].length) this.bags[i] = shuffle(this.groups[i], this.rng);
    let q = this.bags[i].pop();
    if (q.key === this.last) { const other = this.bags[i].findIndex(v => v.key !== this.last); if (other >= 0) { const swap = this.bags[i][other]; this.bags[i][other] = q; q = swap; } }
    this.last = q.key;
    return { ...q, options: makeOptions(q.a, q.b, this.rng) };
  }
}
