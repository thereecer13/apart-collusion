import json, wave, numpy as np
SR = 44100
T = json.load(open('timeline.json'))['duration']
n = int(T * SR); t = np.arange(n) / SR
rng = np.random.default_rng(7)
def note(f): return 440 * 2 ** ((f - 69) / 12)
# A minor-ish ambient progression, 8 s per chord: Am9, Fmaj7, Cmaj7, G6sus
chords = [[45, 57, 60, 64, 71], [41, 53, 57, 60, 64], [48, 55, 59, 64, 67], [43, 55, 59, 62, 64]]
CH = 8.0
pad = np.zeros((n, 2))
for k in range(int(T // CH) + 2):
    c = chords[k % 4]; s0 = k * CH - 1.5; s1 = s0 + CH + 3.0
    i0, i1 = max(0, int(s0 * SR)), min(n, int(s1 * SR))
    if i0 >= i1: continue
    tt = t[i0:i1] - s0; L = s1 - s0
    env = np.minimum(1, tt / 2.5) * np.minimum(1, (L - tt) / 2.5)
    for j, m in enumerate(c):
        f = note(m)
        for side, det in ((0, -0.12), (1, 0.12)):
            ph = 2 * np.pi * (f + det) * tt + j
            w = np.sin(ph) + 0.18 * np.sin(2 * ph) + 0.06 * np.sin(3 * ph)
            w *= 1 + 0.15 * np.sin(2 * np.pi * (0.13 + 0.03 * j) * tt)
            pad[i0:i1, side] += w * env * (0.5 if m < 50 else 0.22)
# sparse bell notes from the A minor pentatonic
pent = [69, 72, 74, 76, 79, 81, 84]
bell = np.zeros((n, 2))
tb = 3.0
while tb < T - 4:
    f = note(rng.choice(pent)); i0 = int(tb * SR); L = int(3.5 * SR); i1 = min(n, i0 + L)
    tt = t[i0:i1] - tb
    w = (np.sin(2 * np.pi * f * tt) + 0.3 * np.sin(2 * np.pi * 2.01 * f * tt)) * np.exp(-tt * 1.6) * np.minimum(1, tt / 0.01)
    pan = rng.uniform(0.25, 0.75)
    bell[i0:i1, 0] += w * (1 - pan) * 0.35; bell[i0:i1, 1] += w * pan * 0.35
    tb += rng.choice([1.5, 2.0, 2.5, 3.0])
mix = pad * 0.5 + bell
# simple stereo feedback-delay reverb
out = mix.copy()
for d, g in ((0.29, 0.35), (0.41, 0.3), (0.53, 0.25), (0.67, 0.2)):
    k = int(d * SR)
    for side in (0, 1):
        src = mix[:, 1 - side] if d in (0.41, 0.67) else mix[:, side]
        out[k:, side] += g * src[:-k]
fade = np.minimum(1, t / 3.0) * np.minimum(1, (T - t) / 4.0)
out *= fade[:, None]
out /= np.abs(out).max()
np.save('music.npy', out.astype(np.float32))
print('music', out.shape, 'seconds', n / SR)
