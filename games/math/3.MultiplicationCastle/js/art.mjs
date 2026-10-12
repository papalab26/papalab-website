import { RULES } from './rules.mjs';
const TAU = Math.PI * 2;
function ellipse(c, x, y, rx, ry, color) { c.fillStyle = color; c.beginPath(); c.ellipse(x, y, rx, ry, 0, 0, TAU); c.fill(); }
function rect(c, x, y, w, h, r, color) { c.fillStyle = color; c.beginPath(); c.roundRect(x, y, w, h, r); c.fill(); }
function star(c, x, y, radius, color, rotation = 0) {
  c.fillStyle = color; c.beginPath();
  for (let i = 0; i < 10; i++) { const a = rotation + i * Math.PI / 5 - Math.PI / 2, r = i % 2 ? radius * .45 : radius; const px = x + Math.cos(a) * r, py = y + Math.sin(a) * r; if (!i) c.moveTo(px, py); else c.lineTo(px, py); }
  c.closePath(); c.fill();
}
function castle(c) {
  ellipse(c, 350, 672, 130, 15, '#52725122');
  rect(c, 274, 622, 152, 62, 5, '#d7e5da');
  rect(c, 282, 625, 137, 8, 2, '#f7fbef');
  for (const x of [260, 415]) {
    rect(c, x, 612, 32, 77, 6, '#bed8cf');
    c.fillStyle = '#76a4b8'; c.beginPath(); c.moveTo(x - 8, 615); c.lineTo(x + 16, 589); c.lineTo(x + 40, 615); c.closePath(); c.fill();
    rect(c, x + 10, 634, 12, 17, [6, 6, 0, 0], '#fff1ae');
    rect(c, x + 5, 659, 23, 3, 1, '#a6c9bd');
  }
  for (let x = 298; x < 416; x += 24) rect(c, x, 613, 14, 14, 2, '#c8ddcc');
  rect(c, 330, 646, 40, 38, [20, 20, 0, 0], '#839e99');
  rect(c, 337, 652, 26, 32, [13, 13, 0, 0], '#a3b9ac');
  c.strokeStyle = '#748f88'; c.lineWidth = 2; c.beginPath(); c.moveTo(350, 660); c.lineTo(350, 684); c.stroke();
  for (const x of [307, 390]) rect(c, x, 644, 10, 15, [5, 5, 0, 0], '#fff0b2');
  c.strokeStyle = '#859e95'; c.lineWidth = 3; c.beginPath(); c.moveTo(350, 613); c.lineTo(350, 581); c.stroke();
  c.fillStyle = '#e9ba66'; c.beginPath(); c.moveTo(351, 581); c.lineTo(382, 589); c.lineTo(351, 600); c.closePath(); c.fill();
}
function landscape(c) {
  const g = c.createLinearGradient(0, 0, 0, 700); g.addColorStop(0, '#d9e9bb'); g.addColorStop(.6, '#e4edc7'); g.addColorStop(1, '#c5dfbc'); c.fillStyle = g; c.fillRect(0, 0, 700, 700);
  // The two paths and rally clearing explain where each side enters.
  c.fillStyle = '#e8ddaf'; c.beginPath(); c.moveTo(238, 0); c.bezierCurveTo(250, 160, 430, 270, 326, 470); c.lineTo(290, 700); c.lineTo(410, 700); c.bezierCurveTo(392, 470, 463, 274, 367, 116); c.lineTo(345, 0); c.closePath(); c.fill();
  ellipse(c, 351, 358, 160, 117, '#ede6bc88');
  ellipse(c, 350, 124, 281, 29, '#e9edcc');
  c.strokeStyle = '#b8cea4'; c.lineWidth = 2; c.setLineDash([5, 9]); c.beginPath(); c.moveTo(35, 110); c.lineTo(665, 110); c.stroke(); c.setLineDash([]);
  c.fillStyle = '#849976'; c.font = '12px "Segoe UI",sans-serif'; c.textAlign = 'center'; c.fillText('小兵集合區', 350, 111);
  for (let i = 0; i < 46; i++) {
    const x = 26 + (i * 137 % 650), y = 70 + (i * 71 % 520);
    if (x > 250 && x < 440) continue;
    ellipse(c, x, y, 3, 2, '#bed394');
    if (i % 3 === 0) { ellipse(c, x + 7, y - 4, 3, 3, '#fff5cc'); ellipse(c, x + 7, y - 4, 1.2, 1.2, '#deb478'); }
  }
  for (const [x, y] of [[26, 180], [661, 236], [39, 443], [672, 485]]) {
    ellipse(c, x + 4, y + 29, 25, 8, '#50754518'); rect(c, x - 4, y, 8, 27, 3, '#bbaa83'); ellipse(c, x, y - 5, 23, 26, '#96bc8b'); ellipse(c, x - 10, y, 17, 17, '#a6ca96'); ellipse(c, x + 12, y - 2, 18, 18, '#8ab281');
  }
  c.strokeStyle = '#a6bea4'; c.lineWidth = 3; c.setLineDash([9, 8]); c.beginPath(); c.moveTo(20, RULES.defenseY); c.lineTo(680, RULES.defenseY); c.stroke(); c.setLineDash([]);
  castle(c);
  rect(c, 253, 8, 194, 26, 12, '#fff6decc'); c.fillStyle = '#b27e64'; c.font = '11px "Segoe UI",sans-serif'; c.fillText('敵軍從這裡出發 ↓', 350, 25);
}
function soldierSprite(side, frame) {
  const image = document.createElement('canvas'); image.width = 40; image.height = 46;
  const c = image.getContext('2d'), enemy = side === 'enemy', step = Math.sin(frame * Math.PI / 2) * 1.4;
  ellipse(c, 20, 38, 11, 3.5, '#496e4f22');
  rect(c, 13, 29 + step, 5, 9, 2, '#718591'); rect(c, 22, 29 - step, 5, 9, 2, '#718591');
  rect(c, 10, 20, 20, 14, 6, enemy ? '#d58d73' : '#6ba7cb');
  ellipse(c, 9, 26 - step, 3, 4, '#edceaa'); ellipse(c, 31, 26 + step, 3, 4, '#edceaa');
  ellipse(c, 20, 16, 12, 11, '#f4d4ad');
  if (enemy) { c.fillStyle = '#d99376'; c.beginPath(); c.moveTo(6, 15); c.lineTo(9, 6); c.lineTo(20, 1); c.lineTo(31, 6); c.lineTo(34, 15); c.closePath(); c.fill(); rect(c, 7, 13, 26, 5, 2, '#b97865'); }
  else { ellipse(c, 20, 10, 13, 9, '#80b6d4'); rect(c, 6, 13, 28, 5, 3, '#5c94b7'); }
  ellipse(c, 16, 20, 1.2, 1.4, '#53626a'); ellipse(c, 24, 20, 1.2, 1.4, '#53626a');
  ellipse(c, 11.5, 23, 2.2, 1.5, '#eab19c'); ellipse(c, 28.5, 23, 2.2, 1.5, '#eab19c');
  c.strokeStyle = '#a98771'; c.lineWidth = 1; c.beginPath(); c.arc(20, 23, 2, 0, Math.PI); c.stroke();
  return image;
}
export class Renderer {
  constructor(canvas) {
    this.canvas = canvas; this.ctx = canvas.getContext('2d');
    this.background = document.createElement('canvas'); this.background.width = 700; this.background.height = 700; landscape(this.background.getContext('2d'));
    this.sprites = { ally: [0, 1, 2, 3].map(i => soldierSprite('ally', i)), enemy: [0, 1, 2, 3].map(i => soldierSprite('enemy', i)) };
    this.resize();
  }
  resize() { this.dpr = Math.min(window.devicePixelRatio || 1, 2); this.canvas.width = 700 * this.dpr; this.canvas.height = 700 * this.dpr; this.ctx.setTransform(this.dpr, 0, 0, this.dpr, 0, 0); }
  draw(battle, time = 0) {
    const c = this.ctx; c.clearRect(0, 0, 700, 700); c.drawImage(this.background, 0, 0);
    if (!battle) return;
    // Portrait terrain fills the taller field; keep the soldiers' proportions intact.
    const spriteAspect = window.innerWidth <= 600 && window.innerHeight > window.innerWidth ? this.canvas.clientWidth / Math.max(1, this.canvas.clientHeight) : 1;
    for (const side of ['allies', 'enemies']) for (const unit of battle[side]) {
      const frame = Math.floor(unit.age * 3.5 + unit.id % 4) % 4;
      c.drawImage(this.sprites[unit.side][frame], unit.x - 14, unit.y - 20 * spriteAspect, 28, 32 * spriteAspect);
    }
    for (const effect of battle.effects) {
      c.save(); c.globalAlpha = Math.min(1, effect.life * 4);
      if (effect.kind === 'star') {
        const progress = 1 - effect.life / effect.max;
        // Retain harmless visual copies briefly, then let smoke and stars drift away.
        c.globalAlpha = Math.min(1, (1 - progress) * 1.7);
        if (progress < .32) {
          c.save(); c.globalAlpha = 1 - progress / .32;
          const scale = 1 - progress * .6;
          for (const unit of effect.pair || []) c.drawImage(this.sprites[unit.side][0], unit.x - 14 * scale, unit.y - 20 * spriteAspect * scale, 28 * scale, 32 * spriteAspect * scale);
          c.restore();
        }
        const spread = progress * 26;
        for (let i = 0; i < 5; i++) {
          const angle = i * TAU / 5;
          ellipse(c, effect.x + Math.cos(angle) * spread * .5, effect.y + Math.sin(angle) * spread * .4, 7 + progress * 8, 6 + progress * 5, i % 2 ? '#f8ecd1' : '#fff9e9');
        }
        for (let i = 0; i < 4; i++) star(c, effect.x + Math.cos(i * TAU / 4 + .4) * spread, effect.y + Math.sin(i * TAU / 4 + .4) * spread - progress * 8, 5 * (1 - progress) + 2, i % 2 ? '#fff9e4' : '#e7be69', progress * .9);
      } else if (effect.kind === 'hit') { ellipse(c, effect.x, effect.y, 10 + (1 - effect.life / .55) * 20, 6, '#e7a285'); star(c, effect.x, effect.y - 10, 8, '#e0a061'); }
      else { c.strokeStyle = effect.side === 'enemy' ? '#d79779' : '#81aeb6'; c.lineWidth = 2; c.beginPath(); c.arc(effect.x, effect.y, 4 + (1 - effect.life / .3) * 12, 0, TAU); c.stroke(); }
      c.restore();
    }
  }
}
