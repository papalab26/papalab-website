import test from 'node:test';
import assert from 'node:assert/strict';
import { DEFAULT_TABLES, RULES, LEVELS, validTables, levelConfig, stars, unitSpeed } from '../js/rules.mjs';
import { QuestionDeck, makeOptions } from '../js/questions.mjs';
import { Battle, createEnemyPlan } from '../js/battle.mjs';
function rng(seed = 42) { return () => { seed = (seed * 1664525 + 1013904223) >>> 0; return seed / 4294967296; }; }

test('saved ranges accept only nonempty valid tables', () => {
  for (const value of [null, [], '7', [0], [10], [2,'3'], [NaN]]) assert.deepEqual(validTables(value), DEFAULT_TABLES);
  assert.deepEqual(validTables([7,7,2]), [2,7]);
});
test('single and multiple ranges cover every equation without adjacent repetition', () => {
  for (const tables of [[7], [2,5], [1,2,3,4,5,6,7,8,9]]) {
    const deck = new QuestionDeck(tables, rng()); const seen = new Set(); let previous = '';
    for (let i = 0; i < 1500; i++) { const q = deck.next(); assert.ok(tables.includes(q.a)); assert.ok(q.b >= 1 && q.b <= 9); assert.notEqual(q.key, previous); seen.add(q.key); previous = q.key; }
    assert.equal(seen.size, tables.length * 9);
    const flat = deck.groups.flat(); assert.equal(new Set(flat.map(q=>q.key)).size, tables.length * 9);
    assert.ok(Math.max(...deck.groups.map(g=>g.length)) - Math.min(...deck.groups.map(g=>g.length)) <= 1);
  }
});
test('four unique positive choices include exactly one answer for all 81 equations', () => {
  const positions = new Set();
  for (let a=1;a<=9;a++) for(let b=1;b<=9;b++) for(let seed=1;seed<=20;seed++) {
    const values=makeOptions(a,b,rng(seed)); assert.equal(values.length,4); assert.equal(new Set(values).size,4); assert.ok(values.every(n=>Number.isInteger(n)&&n>0)); assert.equal(values.filter(n=>n===a*b).length,1); positions.add(values.indexOf(a*b));
  }
  assert.equal(positions.size,4); assert.ok(makeOptions(9,9,rng()).some(n=>n>81));
});
test('CPU independently answers the selected tables with variable real army sizes and timing', () => {
  for (const tables of [[7],[1,2,3,4,5],[1,2,3,4,5,6,7,8,9]]) for(let level=0;level<5;level++) {
    const config=levelConfig(level,tables),plan=createEnemyPlan(config,rng(27+level));
    assert.equal(plan.length,LEVELS[level].waves);assert.equal(plan[0].at,5);
    assert.ok(new Set(plan.map(w=>w.count)).size>1);
    for(let i=0;i<plan.length;i++){
      const wave=plan[i];assert.ok(tables.includes(wave.a));assert.ok(wave.b>=1&&wave.b<=9);assert.equal(wave.answer,wave.a*wave.b);assert.equal(wave.count,Math.round(wave.answer*(1+level*.3)));assert.equal(config.enemyMultiplier,[1,1.3,1.6,1.9,2.2][level]);
      if(i){const delay=wave.at-plan[i-1].at;assert.ok(delay>=config.interval*.65-1e-9&&delay<=config.interval*1.4+1e-9);}
    }
    assert.ok(new Set(plan.slice(1).map((w,i)=>(w.at-plan[i].at).toFixed(3))).size>1);
    const battle=new Battle(level,tables,rng(27+level));assert.deepEqual(battle.enemyPlan,plan);assert.equal(battle.config.total,plan.reduce((sum,w)=>sum+w.count,0));
    const player=new QuestionDeck(tables,rng(99));for(let i=0;i<30;i++)player.next();assert.deepEqual(battle.enemyPlan,plan);
  }
  assert.deepEqual([0,1,3,4,7,8,10].map(stars),[0,1,1,2,2,3,3]);
});
test('correct 3x7 and 9x9 create exactly 21 and 81 independent grouped units within one second', () => {
  for (const [a,b] of [[3,7],[9,9]]) { const battle=new Battle(0,[a]);assert.equal(battle.summon(a,b),a*b);assert.equal(battle.allies.length+battle.pending.length,a*b);battle.step(1);assert.equal(battle.pending.length,0);assert.equal(battle.allies.length,a*b);assert.equal(new Set(battle.allies.map(u=>u.id)).size,a*b);for(let g=0;g<a;g++)assert.equal(battle.allies.filter(u=>u.group===g).length,b); }
});
test('each contact removes exactly one pair, including castle line priority', () => {
  for (const y of [300,RULES.defenseY]) { const battle=new Battle(0,[2]);battle.allies=[battle.unit('ally',350,y),battle.unit('ally',350,y)];battle.enemies=[battle.unit('enemy',350,y)];battle.step(.04);assert.equal(battle.allies.length,1);assert.equal(battle.enemies.length,0);assert.equal(battle.collisions,1);assert.equal(battle.hp,10); }
});
test('surviving enemy damages once, defeat overrides simultaneous cleared battlefield', () => {
  const battle=new Battle(0,[2]);battle.waves=battle.config.waves;battle.hp=1;battle.enemies=[battle.unit('enemy',350,RULES.defenseY)];battle.step(.04);assert.equal(battle.hp,0);assert.equal(battle.hits,1);assert.equal(battle.result,'lose');battle.step(10);assert.equal(battle.hits,1);
});
test('each CPU solution produces its exact independent army on its own scheduled completion time', () => {
  for(let level=0;level<5;level++){
    const battle=new Battle(level,[1,2,3,4,5],rng(77));battle.step(4.99);assert.equal(battle.waves,0);
    for(let i=0;i<battle.config.waves;i++){
      battle.enemies=[];const wave=battle.enemyPlan[i];battle.step(wave.at-battle.time+.001);
      assert.equal(battle.waves,i+1);assert.equal(battle.enemies.length+battle.pending.filter(item=>item.unit.side==='enemy').length,wave.count);assert.deepEqual(battle.lastEnemyAnswer,wave);assert.notEqual(battle.result,'lose');battle.step(.9);assert.equal(battle.pending.filter(item=>item.unit.side==='enemy').length,0);
    }
  }
});
test('no early victory; final wave cleared with HP remaining wins', () => {
  const battle=new Battle(0,[2]);battle.step(1);assert.equal(battle.result,null);battle.waves=battle.config.waves-1;battle.enemies=[];battle.step(.04);assert.equal(battle.result,null);battle.waves=battle.config.waves;battle.step(.04);assert.equal(battle.result,'win');
});
test('unintercepted march takes about 50 real seconds at different frame rates', () => {
  for(const fps of [30,60,120]){const battle=new Battle(0,[2]);battle.waves=battle.config.waves;battle.enemies=[battle.unit('enemy',350,RULES.enemyY)];for(let i=0;i<49*fps;i++)battle.step(1/fps);assert.equal(battle.hp,10);for(let i=0;i<fps+1;i++)battle.step(1/fps);assert.equal(battle.hp,9);assert.equal(battle.result,'win');}
});
test('allies intercept enemies from opposite sides and stay in rally zone after battle', () => {
  const battle=new Battle(0,[2]);battle.waves=battle.config.waves;battle.allies=[battle.unit('ally',150,580)];battle.enemies=[battle.unit('enemy',550,RULES.enemyY)];battle.step(45);assert.equal(battle.collisions,1);assert.equal(battle.hp,10);
  const waiting=new Battle(0,[2]);waiting.summon(3,7);waiting.waves=waiting.config.waves-1;waiting.time=0;waiting.step(10);assert.equal(waiting.allies.length,21);assert.ok(waiting.allies.every(u=>u.y>=RULES.rallyY));
});
test('five-level victories, retries and large armies remain independent', () => {
  for(let level=0;level<5;level++){const battle=new Battle(level,[9]);const batches=Math.ceil(battle.config.total/81)+2;for(let i=0;i<batches;i++)battle.summon(9,9);battle.step(1);assert.equal(battle.allies.length,batches*81);for(let t=0;t<210&&!battle.result;t++)battle.step(1);assert.equal(battle.result,'win');assert.ok(battle.hp>0);assert.equal(battle.waves,battle.config.waves);assert.equal(battle.pending.length,0);const loss=new Battle(level,[9]);loss.step(210);assert.equal(loss.result,'lose');assert.equal(loss.hp,0);const retry=new Battle(level,[9]);assert.equal(retry.allies.length,0);assert.equal(retry.time,0);assert.equal(retry.hp,10);assert.deepEqual(retry.config.tables,battle.config.tables);assert.equal(retry.config.waves,battle.config.waves);}
});

test('both armies move at the same speed and cancellation retains a visible 1.2-second noncombat animation', () => {
  const moving=new Battle(0,[2]);moving.allies=[moving.unit('ally',200,500)];moving.enemies=[moving.unit('enemy',200,250)];
  moving.step(1);assert.ok(Math.abs((500-moving.allies[0].y)-unitSpeed())<1e-6);assert.ok(Math.abs((moving.enemies[0].y-250)-unitSpeed())<1e-6);
  const battle=new Battle(0,[2]);battle.allies=[battle.unit('ally',350,300)];battle.enemies=[battle.unit('enemy',350,300)];battle.step(.04);
  assert.equal(battle.allies.length,0);assert.equal(battle.enemies.length,0);assert.equal(battle.effects[0].pair.length,2);assert.equal(battle.effects[0].max,1.2);
  battle.step(.55);assert.ok(battle.effects.some(e=>e.kind==='star'));
  battle.step(.7);assert.ok(!battle.effects.some(e=>e.kind==='star'));assert.equal(battle.collisions,1);
});

test('enemy formations use the same groups, columns and 0.85-second staged entry as allies', () => {
  const battle=new Battle(0,[3]);battle.summon(3,7);
  const allies=[...battle.allies,...battle.pending.map(item=>item.unit)];
  battle.pending=[];battle.allies=[];battle.queueFormation('enemy',3,7,21);
  const enemies=[...battle.enemies,...battle.pending.map(item=>item.unit)];
  assert.equal(battle.enemies.length,1);assert.equal(battle.pending.length,20);
  for(let i=0;i<21;i++){assert.equal(enemies[i].x,allies[i].x);assert.equal(enemies[i].group,allies[i].group);assert.equal(enemies[i].y-RULES.enemyY,allies[i].y-(RULES.defenseY-22));}
  battle.step(.9);assert.equal(battle.enemies.length,21);assert.equal(battle.pending.length,0);
});
test('pending enemies block victory until the whole final formation has entered and cleared', () => {
  const battle=new Battle(0,[3]);battle.waves=battle.config.waves;battle.queueFormation('enemy',3,7,21);battle.enemies=[];
  battle.step(.01);assert.equal(battle.result,null);assert.ok(battle.pending.length>0);
  battle.step(1);battle.enemies=[];battle.step(.04);assert.equal(battle.result,'win');
});
