import json, wave, numpy as np
from kokoro import KPipeline
script = json.load(open('script.json'))
pipe = KPipeline(lang_code='a')
SR = 24000; LEAD, LINE_GAP, SCENE_GAP, END = 1.5, 0.5, 1.1, 7.0
def synth(text):
    a = np.concatenate([np.asarray(x) for _, _, x in pipe(text, voice='af_heart', speed=0.95)])
    a = a / max(1e-6, np.abs(a).max()) * 0.9
    nz = np.where(np.abs(a) > 0.01)[0]          # trim leading/trailing silence
    return a[max(0, nz[0] - 1200): nz[-1] + 2400]
t = LEAD; timeline = []; chunks = [np.zeros(int(LEAD * SR))]
for sc in script:
    s0 = t; lines = []
    for li, text in enumerate(sc['lines']):
        a = synth(text); d = len(a) / SR
        lines.append({'text': text, 'start': round(t, 3), 'end': round(t + d, 3)})
        chunks.append(a); t += d
        gap = LINE_GAP if li < len(sc['lines']) - 1 else SCENE_GAP
        chunks.append(np.zeros(int(gap * SR))); t += gap
    timeline.append({'id': sc['id'], 'start': round(s0, 3), 'end': round(t, 3), 'lines': lines})
timeline.append({'id': 'end', 'start': round(t, 3), 'end': round(t + END, 3), 'lines': []})
chunks.append(np.zeros(int(END * SR))); t += END
audio = (np.concatenate(chunks) * 32767).astype(np.int16)
with wave.open('narration.wav', 'wb') as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes(audio.tobytes())
json.dump({'duration': round(t, 3), 'scenes': timeline}, open('timeline.json', 'w'), indent=1)
print('total', round(t, 1), 's')
