import { RULES, levelConfig, enemyThinkSeconds, unitSpeed } from './rules.mjs';
import { QuestionDeck } from './questions.mjs';
export function createEnemyPlan(config, rng = Math.random) {
  const deck = new QuestionDeck(config.tables, rng);
  let at = RULES.firstWave;
  return Array.from({ length: config.waves }, (_, i) => {
    if (i) at += enemyThinkSeconds(config.interval, rng);
    const question = deck.next();
    return { at, a: question.a, b: question.b, answer: question.answer, multiplier: config.enemyMultiplier, count: Math.max(1, Math.round(question.answer * config.enemyMultiplier)) };
  });
}
export class Battle {
  constructor(index, tables, rng = Math.random) {
    this.config = levelConfig(index, tables); this.rng = rng;
    this.enemyPlan = createEnemyPlan(this.config, rng);
    this.config.total = this.enemyPlan.reduce((sum, wave) => sum + wave.count, 0);
    this.lastEnemyAnswer = null;
    this.time = 0; this.hp = RULES.castleHP; this.waves = 0; this.id = 0;
    this.allies = []; this.enemies = []; this.pending = []; this.effects = []; this.events = [];
    this.result = null; this.collisions = 0; this.hits = 0;
  }
  unit(side, x, y, group = 0) { return { id: this.id++, side, x, y, group, age: 0, dead: false }; }
  summon(a, b) {
    if (this.result) return 0;
    const count = a * b;
    this.queueFormation('ally', a, b, count);
    this.events.push('spawn'); return count;
  }
  queueFormation(side, a, b, count) {
    const teams = Math.ceil(count / b);
    for (let i = 0; i < count; i++) {
      const group = Math.floor(i / b), member = i % b;
      const center = 42 + (group + .5) * (RULES.width - 84) / teams;
      const y = (side === 'enemy' ? RULES.enemyY : RULES.defenseY - 22) + Math.floor(member / 3) * 10;
      this.pending.push({ at: this.time + (count === 1 ? 0 : i / (count - 1) * RULES.spawnSeconds), unit: this.unit(side, center + (member % 3 - 1) * 13, y, group) });
    }
    this.flushPending();
  }
  flushPending() {
    this.pending = this.pending.filter(item => { if (item.at <= this.time + 1e-9) { (item.unit.side === 'enemy' ? this.enemies : this.allies).push(item.unit); this.effects.push({ x: item.unit.x, y: item.unit.y, side: item.unit.side, kind: 'spawn', life: .3 }); return false; } return true; });
  }
  spawnWave() {
    const wave = this.enemyPlan[this.waves];
    if (!wave) return;
    this.lastEnemyAnswer = wave;
    this.queueFormation('enemy', wave.a, wave.b, wave.count);
    this.waves++; this.events.push('wave');
  }
  step(seconds) {
    if (this.result || !Number.isFinite(seconds) || seconds <= 0) return;
    let remaining = seconds;
    while (remaining > 1e-9 && !this.result) { const dt = Math.min(.04, remaining); this.tick(dt); remaining -= dt; }
  }
  tick(dt) {
    this.time += dt;
    while (this.waves < this.config.waves && this.time + 1e-9 >= this.enemyPlan[this.waves].at) this.spawnWave();
    this.flushPending();
    const speed = unitSpeed();
    for (const e of this.enemies) { e.y += speed * dt; e.age += dt; }
    const alliesByID = new Map(this.allies.map(a => [a.id, a]));
    const targets = new Map();
    const intercept = (a, e) => {
      const horizontal = e.x - a.x, vertical = e.y - a.y;
      const distanceSquared = horizontal * horizontal + vertical * vertical;
      if (distanceSquared <= (RULES.radius * 2) ** 2) return { seconds: 0, y: e.y };
      if (vertical >= 0) return null;
      const seconds = distanceSquared / (-2 * vertical * speed), y = e.y + speed * seconds;
      return y <= RULES.defenseY ? { seconds, y } : null;
    };
    // Reserve one interceptor per enemy; the other soldiers keep a broad defensive line.
    // Without reservations an entire slow army would chase the same few enemies.
    for (const e of this.enemies) {
      let soldier = alliesByID.get(e.interceptorID);
      let meeting = soldier && !targets.has(soldier.id) ? intercept(soldier, e) : null;
      if (!meeting) {
        soldier = null;
        for (const a of this.allies) {
          if (targets.has(a.id)) continue;
          const candidate = intercept(a, e);
          if (candidate && (!meeting || candidate.seconds < meeting.seconds)) { soldier = a; meeting = candidate; }
        }
      }
      e.interceptorID = soldier?.id;
      if (soldier) targets.set(soldier.id, { x: e.x, y: meeting.y });
    }
    for (const a of this.allies) {
      a.age += dt;
      const target = targets.get(a.id);
      const tx = target ? target.x : 38 + (a.id * 17 % 35) * 18;
      const ty = target ? target.y : RULES.rallyY + (Math.floor(a.id / 35) % 8) * 18;
      const dx = tx - a.x, dy = ty - a.y, length = Math.hypot(dx, dy), distance = Math.min(length, speed * dt);
      if (length) { a.x += dx / length * distance; a.y += dy / length * distance; }
    }
    // Spatial buckets bound collision work; dead flags ensure one pair per unit.
    const cellSize = RULES.radius * 2;
    const buckets = new Map();
    for (const a of this.allies) { const key = `${Math.floor(a.x / cellSize)},${Math.floor(a.y / cellSize)}`; if (!buckets.has(key)) buckets.set(key, []); buckets.get(key).push(a); }
    for (const e of this.enemies) {
      const cx = Math.floor(e.x / cellSize), cy = Math.floor(e.y / cellSize);
      find: for (let ox = -1; ox <= 1; ox++) for (let oy = -1; oy <= 1; oy++) for (const a of buckets.get(`${cx + ox},${cy + oy}`) || []) {
        if (!a.dead && Math.hypot(a.x - e.x, a.y - e.y) <= RULES.radius * 2) { a.dead = true; e.dead = true; this.collisions++; this.effects.push({ x: (a.x + e.x) / 2, y: (a.y + e.y) / 2, kind: 'star', life: RULES.cancelSeconds, max: RULES.cancelSeconds, pair: [{ x: a.x, y: a.y, side: a.side }, { x: e.x, y: e.y, side: e.side }] }); this.events.push('cancel'); break find; }
      }
    }
    // Castle damage happens only after interception, once per surviving enemy.
    for (const e of this.enemies) if (!e.dead && e.y >= RULES.defenseY) { e.dead = true; this.hp = Math.max(0, this.hp - 1); this.hits++; this.effects.push({ x: e.x, y: RULES.defenseY, kind: 'hit', life: .55 }); this.events.push('hit'); }
    this.allies = this.allies.filter(a => !a.dead); this.enemies = this.enemies.filter(e => !e.dead);
    this.effects = this.effects.filter(effect => { effect.life -= dt; return effect.life > 0; });
    if (this.hp <= 0) this.result = 'lose';
    else if (this.waves === this.config.waves && this.enemies.length === 0 && !this.pending.some(item => item.unit.side === 'enemy')) this.result = 'win';
    if (this.result) this.pending = [];
  }
  clearEvents() { const events = this.events; this.events = []; return events; }
}
