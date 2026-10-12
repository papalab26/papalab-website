export const DEFAULT_TABLES = [2, 3, 4, 5];
export const LEVELS = [
  { name: '新兵練習', interval: 12, waves: 6, enemyMultiplier: 1 },
  { name: '敵軍集結', interval: 11, waves: 7, enemyMultiplier: 1.3 },
  { name: '守城作戰', interval: 10, waves: 8, enemyMultiplier: 1.6 },
  { name: '大軍壓境', interval: 9, waves: 9, enemyMultiplier: 1.9 },
  { name: '最後防線', interval: 8, waves: 10, enemyMultiplier: 2.2 },
];
export const RULES = { enemyThinkMin: .65, enemyThinkMax: 1.4, castleHP: 10, firstWave: 5, marchSeconds: 50, feedbackSeconds: .8, spawnSeconds: .85, countdownSeconds: 3, width: 700, height: 700, enemyY: 28, defenseY: 600, rallyY: 120, radius: 9, cancelSeconds: 1.2 };
export function validTables(value) {
  if (!Array.isArray(value) || !value.length || value.some(n => !Number.isInteger(n) || n < 1 || n > 9)) return [...DEFAULT_TABLES];
  return [...new Set(value)].sort((a, b) => a - b);
}
export function levelConfig(index, tables) {
  const base = LEVELS[index];
  if (!base) throw new RangeError('Unknown level');
  return { ...base, tables: validTables(tables) };
}
export function enemyThinkSeconds(interval, rng = Math.random) {
  return interval * (RULES.enemyThinkMin + rng() * (RULES.enemyThinkMax - RULES.enemyThinkMin));
}
export function unitSpeed() { return (RULES.defenseY - RULES.enemyY) / RULES.marchSeconds; }
export function stars(hp) { return hp >= 8 ? 3 : hp >= 4 ? 2 : hp > 0 ? 1 : 0; }
