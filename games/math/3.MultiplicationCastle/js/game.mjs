import { AudioPlayer } from './audio.mjs';
import { DEFAULT_TABLES, LEVELS, RULES, validTables, stars } from './rules.mjs';
import { QuestionDeck } from './questions.mjs';
import { Battle } from './battle.mjs';
import { Renderer } from './art.mjs';
const $ = id => document.getElementById(id);
const STORAGE = 'papalab-multiplication-castle-v1';
export class Game {
  constructor() {
    this.selected = [...DEFAULT_TABLES]; this.soundOn = true;
    try { const saved = JSON.parse(localStorage.getItem(STORAGE)); if (saved) { this.selected = validTables(saved.tables); if (typeof saved.sound === 'boolean') this.soundOn = saved.sound; } } catch {}
    this.audio = new AudioPlayer(this.soundOn); this.renderer = new Renderer($('battle'));
    this.phase = 'menu'; this.battle = null; this.level = 0; this.totals = []; this.round = null;
    this.questionID = 0; this.question = null; this.feedbackLeft = 0; this.countdownLeft = 0;
    this.heldKeys = new Set(); this.pointerArm = null; this.lastAttempt = -Infinity; this.inputReadyAt = 0;
    this.savedFocus = null; this.lastFrame = null; this.runTables = [...this.selected]; this.formationLeft = 0;
    this.bind(); this.renderTables(); this.syncSound();
    requestAnimationFrame(t => this.frame(t));
  }
  save() { try { localStorage.setItem(STORAGE, JSON.stringify({ tables: this.selected, sound: this.soundOn })); } catch {} }
  bind() {
    $('select-all').addEventListener('click', () => { this.audio.unlock(); this.selected = [1,2,3,4,5,6,7,8,9]; this.save(); this.renderTables(); });
    $('start').addEventListener('click', () => { this.audio.unlock(); this.runTables = [...this.selected]; this.totals = []; this.startLevel(0); });
    document.querySelectorAll('.sound').forEach(button => button.addEventListener('click', () => { this.audio.unlock(); this.soundOn = !this.soundOn; this.audio.enabled = this.soundOn; if (!this.soundOn) this.audio.stopMusic(); this.save(); this.syncSound(); }));
    $('pause').addEventListener('click', () => this.pause()); $('hint').addEventListener('click', () => this.showHint());
    for (let i = 0; i < 4; i++) {
      const button = document.createElement('button'); button.className = 'answer'; button.dataset.index = i;
      button.innerHTML = `<kbd>${i + 1}</kbd><span></span>`;
      button.addEventListener('pointerdown', event => { if (!event.isPrimary) return; this.pointerArm = { index: i, id: this.questionID }; });
      button.addEventListener('pointerup', event => { if (!event.isPrimary) return; const arm = this.pointerArm; this.pointerArm = null; if (arm && arm.index === i && arm.id === this.questionID) this.answer(i); });
      button.addEventListener('pointercancel', () => { this.pointerArm = null; });
      button.addEventListener('click', event => { if (event.detail === 0) this.answer(i); });
      $('answers').append(button);
    }
    window.addEventListener('pointerup', () => { this.pointerArm = null; });
    window.addEventListener('keydown', event => {
      if (event.key === 'Tab' && !$('dialog').hidden) { this.trapFocus(event); return; }
      if (event.key === 'Escape') { if (this.phase === 'playing' || this.phase === 'countdown') this.pause(); else if (this.phase === 'paused' || this.phase === 'hint') this.resume(); return; }
      if (!['1','2','3','4'].includes(event.key) || this.phase !== 'playing') return;
      event.preventDefault();
      if (event.repeat || this.heldKeys.has(event.key)) return;
      this.heldKeys.add(event.key); this.answer(Number(event.key) - 1);
    });
    window.addEventListener('keyup', event => this.heldKeys.delete(event.key));
    window.addEventListener('blur', () => { this.heldKeys.clear(); this.pointerArm = null; this.pause(); });
    document.addEventListener('visibilitychange', () => { if (document.hidden) { this.audio.stopMusic(); this.heldKeys.clear(); this.pointerArm = null; this.pause(); } });
    window.addEventListener('resize', () => this.renderer.resize());
  }
  syncSound() { document.querySelectorAll('.sound').forEach(button => { button.textContent = button.classList.contains('compact-sound') ? (this.soundOn ? '♫' : '×♫') : (this.soundOn ? '♫ 音樂開' : '♫ 音樂關'); button.setAttribute('aria-pressed', String(this.soundOn)); button.setAttribute('aria-label', this.soundOn ? '關閉音樂與音效' : '開啟音樂與音效'); }); }
  renderTables(note) {
    $('tables').replaceChildren();
    for (let n = 1; n <= 9; n++) {
      const button = document.createElement('button'); button.className = 'table-button'; button.setAttribute('aria-pressed', String(this.selected.includes(n))); button.setAttribute('aria-label', `${n} 的乘法`);
      button.innerHTML = `<span class="tick">✓</span><strong>${n}</strong>${n} 的乘法`;
      button.addEventListener('click', () => {
        this.audio.unlock();
        if (this.selected.includes(n)) { if (this.selected.length === 1) { $('selection-note').textContent = '至少選擇一種乘法喔！'; return; } this.selected = this.selected.filter(v => v !== n); }
        else this.selected = [...this.selected, n].sort((a, b) => a - b);
        this.save(); this.renderTables();
        $('tables').children[n - 1].focus({ preventScroll: true });
      });
      $('tables').append(button);
    }
    $('selection-note').textContent = note || `練習 ${this.selected.join('、')} 的乘法`;
  }
  startLevel(index) {
    this.closeDialog(false); this.level = index; this.battle = new Battle(index, this.runTables); this.deck = new QuestionDeck(this.runTables);
    this.round = { correct: 0, wrong: 0, summoned: 0 }; this.countdownLeft = RULES.countdownSeconds; this.feedbackLeft = 0; this.formationLeft = 0; this.heldKeys.clear(); this.pointerArm = null;
    this.phase = 'countdown'; this.lastFrame = null; document.body.classList.add('playing'); $('menu').hidden = true; $('game').hidden = false;
    $('countdown').hidden = false; $('countdown-number').textContent = '3'; $('formation').hidden = true;
    $('level-kicker').textContent = `第 ${index + 1} 關 / ${LEVELS.length} 關`; $('level-name').textContent = LEVELS[index].name;
    $('practice-tables').textContent = `${this.runTables.join('、')} 的乘法`;
    this.newQuestion(); this.updateHUD(); $('pause').focus({ preventScroll: true });
  }
  newQuestion() {
    this.questionID++; this.question = { ...this.deck.next(), locked: false, wrong: new Set() };
    this.feedbackLeft = 0; this.inputReadyAt = performance.now() + 200;
    $('question').textContent = `${this.question.a} × ${this.question.b} = ?`;
    $('feedback').textContent = '想一想，你的小兵正在等你！'; $('feedback').className = 'feedback'; $('hint').hidden = true;
    [...$('answers').children].forEach((button, i) => { button.querySelector('span').textContent = this.question.options[i]; button.className = 'answer'; button.disabled = this.phase !== 'playing'; button.setAttribute('aria-label', `選項 ${i + 1}：${this.question.options[i]}`); });
  }
  answer(index) {
    const now = performance.now(), previous = this.lastAttempt; this.lastAttempt = now;
    if (this.phase !== 'playing' || !this.question || this.question.locked || this.question.wrong.has(index) || !Number.isInteger(index) || index < 0 || index > 3 || now < this.inputReadyAt || now - previous < 200) return;
    this.audio.unlock();
    const q = this.question, button = $('answers').children[index];
    if (q.options[index] === q.answer) {
      q.locked = true; [...$('answers').children].forEach(b => b.disabled = true); button.classList.add('correct'); this.round.correct++; this.round.summoned += this.battle.summon(q.a, q.b);
      $('feedback').textContent = `答對了！${q.a} × ${q.b} = ${q.answer}，${q.answer} 名小兵出發！`; $('feedback').className = 'feedback good';
      this.feedbackLeft = RULES.feedbackSeconds; this.formationLeft = 1.1; $('formation').textContent = `${q.a} 隊 · 每隊 ${q.b} 人`; $('formation').hidden = false; $('hint').hidden = true; this.audio.play('correct');
    } else {
      q.wrong.add(index); button.classList.add('wrong'); button.disabled = true; this.round.wrong++;
      $('feedback').textContent = '再想想，你可以的！'; $('feedback').className = 'feedback wrong'; $('hint').hidden = q.wrong.size < 2; this.audio.play('wrong');
    }
    this.updateHUD();
  }
  pause() {
    if (!['playing','countdown'].includes(this.phase)) return;
    this.returnPhase = this.phase; this.phase = 'paused'; this.audio.stopMusic();
    this.openDialog({ art: '☁', kicker: '小隊休息一下', title: '休息好了，再出發', message: '戰場與題目都會在這裡等你。', actions: [['繼續遊戲', () => this.resume(), 'primary'], ['重新挑戰', () => this.startLevel(this.level)], ['回主選單', () => this.menu()]] });
  }
  resume() {
    if (!['paused','hint'].includes(this.phase)) return;
    this.phase = this.returnPhase; this.lastFrame = null; this.lastAttempt = -Infinity; this.closeDialog();
  }
  showHint() {
    if (this.phase !== 'playing' || this.question.locked || this.question.wrong.size < 2) return;
    this.returnPhase = this.phase; this.phase = 'hint'; this.audio.stopMusic(); const q = this.question;
    this.openDialog({ art: '✦', kicker: '一起用分組來想想', title: `${q.a} 組，每組 ${q.b} 人`, message: '把每一組的人數加起來，就是要召喚的小兵數量。', actions: [['我想再試試', () => this.resume(), 'primary']] });
    const groups = document.createElement('div'); groups.className = 'hint-groups';
    for (let i = 0; i < q.a; i++) { const group = document.createElement('div'); group.className = 'hint-group'; group.innerHTML = `<small>第 ${i + 1} 組</small>${Array(q.b).fill('●').join(' ')}<small>${q.b} 人</small>`; groups.append(group); }
    const addition = document.createElement('p'); addition.className = 'addition'; addition.textContent = `${Array(q.a).fill(q.b).join(' + ')} = ?`; $('dialog-content').append(groups, addition);
  }
  menu() {
    this.phase = 'menu'; this.battle = null; this.question = null; this.feedbackLeft = 0; this.formationLeft = 0; this.totals = []; this.pointerArm = null; this.heldKeys.clear();
    this.closeDialog(false); document.body.classList.remove('playing'); $('game').hidden = true; $('menu').hidden = false; $('formation').hidden = true; $('countdown').hidden = true; this.renderTables(); $('start').focus({ preventScroll: true });
  }
  finish() {
    if (this.phase !== 'playing' || !this.battle.result) return;
    this.feedbackLeft = 0; this.formationLeft = 0; $('formation').hidden = true; this.battle.pending = [];
    [...$('answers').children].forEach(button => button.disabled = true);
    const won = this.battle.result === 'win', final = won && this.level === LEVELS.length - 1;
    this.phase = won ? 'won' : 'lost'; this.audio.stopMusic();
    if (won) { this.totals[this.level] = { ...this.round, hp: this.battle.hp, stars: stars(this.battle.hp) }; this.audio.play('win'); }
    const rating = stars(this.battle.hp);
    const actions = won ? [[final ? '再玩一次' : '下一關', () => { if (final) this.totals = []; this.startLevel(final ? 0 : this.level + 1); }, 'primary'], ['回主選單', () => this.menu()]] : [['重新挑戰', () => this.startLevel(this.level), 'primary'], ['回主選單', () => this.menu()]];
    this.openDialog({ art: won ? '★'.repeat(rating) + '☆'.repeat(3 - rating) : '♡', kicker: final ? '五關挑戰完成！' : `第 ${this.level + 1} 關 · ${LEVELS[this.level].name}`, title: final ? '乘法小隊，大成功！' : won ? '城堡守住了！' : '再一起試一次吧', message: won ? '每一位小兵，都是你認真思考的成果。' : '這次的練習也很棒！慢慢想，小兵會再陪你出發。', actions });
    this.stats(this.round, this.battle.hp);
    if (final) { const total = this.totals.reduce((a, b) => ({ correct: a.correct + b.correct, wrong: a.wrong + b.wrong, summoned: a.summoned + b.summoned }), { correct: 0, wrong: 0, summoned: 0 }); const label = document.createElement('p'); label.className = 'totals-title'; label.textContent = '五關總統計'; $('dialog-content').append(label); this.stats(total, null); }
  }
  stats(stats, hp) {
    const grid = document.createElement('div'); grid.className = 'stats-grid';
    for (const [label, number] of [['答對題數',stats.correct],['答錯次數',stats.wrong],['召喚士兵',stats.summoned],...(hp === null ? [] : [['城堡生命',`${hp} / 10`]])]) { const cell = document.createElement('div'); cell.className = 'stat'; cell.innerHTML = `${label}<strong>${number}</strong>`; grid.append(cell); }
    $('dialog-content').append(grid);
  }
  openDialog({ art, kicker, title, message, actions }) {
    this.savedFocus = document.activeElement; $('dialog-art').textContent = art; $('dialog-kicker').textContent = kicker; $('dialog-title').textContent = title; $('dialog-message').textContent = message; $('dialog-content').replaceChildren(); $('dialog-actions').replaceChildren();
    for (const [text, action, style] of actions) { const button = document.createElement('button'); button.className = style || 'secondary'; button.textContent = text; button.addEventListener('click', action); $('dialog-actions').append(button); }
    $('dialog').hidden = false; document.querySelector('.app').inert = true; $('dialog-actions').firstElementChild.focus({ preventScroll: true });
  }
  closeDialog(restore = true) { $('dialog').hidden = true; document.querySelector('.app').inert = false; if (restore && this.savedFocus?.isConnected) this.savedFocus.focus({ preventScroll: true }); }
  trapFocus(event) { const buttons = [...$('dialog').querySelectorAll('button')]; const index = buttons.indexOf(document.activeElement); if (event.shiftKey && index <= 0) { event.preventDefault(); buttons.at(-1).focus(); } else if (!event.shiftKey && index === buttons.length - 1) { event.preventDefault(); buttons[0].focus(); } }
  advance(seconds) {
    if (this.phase === 'countdown') { this.countdownLeft -= seconds; $('countdown-number').textContent = Math.max(1, Math.ceil(this.countdownLeft)); if (this.countdownLeft <= 0) { const leftover = -this.countdownLeft; this.phase = 'playing'; $('countdown').hidden = true; this.inputReadyAt = performance.now(); [...$('answers').children].forEach(button => button.disabled = false); if (leftover > 0) this.advance(leftover); } return; }
    if (this.phase !== 'playing') return;
    // Break at feedback boundary so newly summoned units and questions share one clock.
    let remaining = seconds;
    while (remaining > 1e-9 && this.phase === 'playing') {
      const dt = Math.min(remaining, .04, this.feedbackLeft > 0 ? this.feedbackLeft : Infinity);
      this.battle.step(dt); this.formationLeft = Math.max(0, this.formationLeft - dt); if (!this.formationLeft) $('formation').hidden = true;
      if (this.battle.result) { this.finish(); break; }
      if (this.feedbackLeft > 0) { this.feedbackLeft = Math.max(0, this.feedbackLeft - dt); if (this.feedbackLeft < 1e-9) this.newQuestion(); }
      remaining -= dt;
    }
    const events = new Set(this.battle.clearEvents()); for (const name of ['spawn','cancel','hit']) if (events.has(name)) this.audio.play(name);
  }
  updateHUD() {
    if (!this.battle) return;
    const b = this.battle; $('hp').textContent = `${b.hp} / 10`; $('health-fill').style.width = `${b.hp * 10}%`; $('health-fill').style.background = b.hp < 4 ? '#d9927b' : '#8cbc8b';
    $('wave-count').textContent = `${b.waves} / ${b.config.waves}`; $('ally-count').textContent = b.allies.length; $('enemy-count').textContent = b.enemies.length;
    $('wave-info').textContent = b.lastEnemyAnswer ? `上批 ${b.lastEnemyAnswer.count} 人 · 共 ${b.config.total} 人` : `敵方 ${b.config.enemyMultiplier} 倍兵力 · 共 ${b.config.total} 人`;
    $('correct-count').textContent = this.round.correct; $('summon-count').textContent = this.round.summoned;
    const answer = b.lastEnemyAnswer;
    $('battle-note').textContent = answer && b.time - answer.at < 3 ? `敵方 ${answer.a} × ${answer.b} = ${answer.answer}，${answer.multiplier > 1 ? `${answer.multiplier} 倍 → ` : ''}${answer.count} 人出發！` : b.waves >= b.config.waves ? '最後一批已出發，加油！' : `敵方解題中 · ${Math.max(0, Math.ceil(b.enemyPlan[b.waves].at - b.time))} 秒後出兵`;
  }
  frame(timestamp) {
    const dt = this.lastFrame === null ? 0 : Math.max(0, (timestamp - this.lastFrame) / 1000); this.lastFrame = timestamp;
    this.audio.updateMusic(!document.hidden && ['menu','playing','countdown'].includes(this.phase));
    if (dt) this.advance(dt); if (this.battle) { this.renderer.draw(this.battle, this.battle.time); this.updateHUD(); }
    requestAnimationFrame(t => this.frame(t));
  }
}
export const game = new Game();
