// Original 100 BPM music-box march: C major, gentle pentatonic melody.
export const MUSIC = {
  stepSeconds: .3,
  melody: [
    72,76,79,76,74,72,67,0,
    69,72,76,72,74,76,79,0,
    77,76,74,72,69,72,74,0,
    74,79,77,76,74,71,72,0,
    72,76,79,81,79,76,74,72,
    69,72,76,79,76,74,72,0,
    77,81,79,77,76,74,72,69,
    74,71,67,71,72,76,72,0,
  ],
  chords: [[48,52,55],[45,48,52],[53,57,60],[55,59,62],[48,52,55],[45,48,52],[53,57,60],[55,59,62]],
};
export class AudioPlayer {
  constructor(enabled) { this.enabled = enabled; this.context = null; this.last = new Map(); this.musicGain = null; this.musicPlaying = false; this.musicStep = 0; this.nextNoteAt = 0; this.voices = new Set(); }
  unlock() { try { if (!this.context) this.context = new (window.AudioContext || window.webkitAudioContext)(); if (this.context.state === 'suspended') this.context.resume().catch(() => {}); } catch {} }
  updateMusic(active) {
    const c = this.context;
    if (!active || !this.enabled || !c || c.state !== 'running') { this.stopMusic(); return; }
    if (!this.musicPlaying) {
      if (!this.musicGain) { this.musicGain = c.createGain(); this.musicGain.connect(c.destination); }
      this.musicGain.gain.cancelScheduledValues(c.currentTime); this.musicGain.gain.setValueAtTime(0, c.currentTime); this.musicGain.gain.linearRampToValueAtTime(.7, c.currentTime + .12);
      this.musicPlaying = true; this.nextNoteAt = c.currentTime + .06;
    }
    // Schedule a short lookahead from the existing game loop, without extra timers.
    if (this.nextNoteAt < c.currentTime) this.nextNoteAt = c.currentTime + .02;
    while (this.nextNoteAt < c.currentTime + .18) {
      this.scheduleMusicStep(this.musicStep, this.nextNoteAt);
      this.musicStep = (this.musicStep + 1) % MUSIC.melody.length;
      this.nextNoteAt += MUSIC.stepSeconds;
    }
  }
  scheduleMusicStep(step, at) {
    const note = MUSIC.melody[step];
    if (note) this.musicNote(note, at, .36, .036, 'triangle');
    if (step % 8 === 0) for (const [i, pitch] of MUSIC.chords[Math.floor(step / 8)].entries()) this.musicNote(pitch, at + i * .035, 1.8, .014, 'sine');
    if (step % 4 === 0) this.musicNote(MUSIC.chords[Math.floor(step / 8)][0] - 12, at, .42, .022, 'sine');
  }
  musicNote(pitch, at, duration, volume, type) {
    const c = this.context, oscillator = c.createOscillator(), envelope = c.createGain();
    oscillator.type = type; oscillator.frequency.setValueAtTime(440 * 2 ** ((pitch - 69) / 12), at);
    envelope.gain.setValueAtTime(.0001, at); envelope.gain.linearRampToValueAtTime(volume, at + .012); envelope.gain.exponentialRampToValueAtTime(.0001, at + duration);
    oscillator.connect(envelope); envelope.connect(this.musicGain); this.voices.add(oscillator);
    oscillator.onended = () => { this.voices.delete(oscillator); oscillator.disconnect(); envelope.disconnect(); };
    oscillator.start(at); oscillator.stop(at + duration + .025);
  }
  stopMusic() {
    if (!this.musicPlaying) return;
    this.musicPlaying = false;
    const c = this.context;
    if (c && this.musicGain) { this.musicGain.gain.cancelScheduledValues(c.currentTime); this.musicGain.gain.setTargetAtTime(0, c.currentTime, .015); }
    for (const oscillator of this.voices) { try { oscillator.stop(c.currentTime + .06); } catch {} }
    this.voices.clear();
  }
  play(kind) {
    if (!this.enabled) return;
    const now = performance.now(); if (now - (this.last.get(kind) || -Infinity) < 90) return; this.last.set(kind, now);
    try {
      const c = this.context; if (!c || c.state !== 'running') return;
      const melodies = { correct: [523, 659, 784], wrong: [330, 294], spawn: [440, 523], cancel: [880], hit: [220, 165], win: [523, 659, 784, 1047] };
      const notes = melodies[kind] || [440];
      notes.forEach((frequency, i) => {
        const oscillator = c.createOscillator(), gain = c.createGain(), at = c.currentTime + i * .07;
        oscillator.type = 'sine'; oscillator.frequency.setValueAtTime(frequency, at);
        gain.gain.setValueAtTime(0, at); gain.gain.linearRampToValueAtTime(kind === 'cancel' ? .015 : .035, at + .012); gain.gain.exponentialRampToValueAtTime(.0001, at + .14);
        oscillator.connect(gain); gain.connect(c.destination); oscillator.start(at); oscillator.stop(at + .15);
      });
    } catch {}
  }
}
