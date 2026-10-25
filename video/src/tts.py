import json, subprocess, wave, numpy as np
script = json.load(open('script.json'))
PIPER = '/tmp/claude-0/ttsenv/bin/piper'; MODEL = 'voices/en_US-ryan-high.onnx'
SR = 22050; LEAD, LINE_GAP, SCENE_GAP, END = 1.5, 0.5, 1.1, 7.0
t = LEAD; timeline = []; chunks = [np.zeros(int(LEAD * SR), np.int16)]
for si, sc in enumerate(script):
    s0 = t; lines = []
    for li, text in enumerate(sc['lines']):
        f = f'lines/{sc["id"]}_{li}.wav'
        subprocess.run([PIPER, '-m', MODEL, '--length-scale', '1.08', '-f', f], input=text.encode(), check=True, capture_output=True)
        w = wave.open(f); assert w.getframerate() == SR
        a = np.frombuffer(w.readframes(w.getnframes()), np.int16)
        d = len(a) / SR
        lines.append({'text': text, 'start': round(t, 3), 'end': round(t + d, 3)})
        chunks.append(a); t += d
        gap = LINE_GAP if li < len(sc['lines']) - 1 else SCENE_GAP
        chunks.append(np.zeros(int(gap * SR), np.int16)); t += gap
    timeline.append({'id': sc['id'], 'start': round(s0, 3), 'end': round(t, 3), 'lines': lines})
timeline.append({'id': 'end', 'start': round(t, 3), 'end': round(t + END, 3), 'lines': []})
chunks.append(np.zeros(int(END * SR), np.int16)); t += END
audio = np.concatenate(chunks)
with wave.open('narration.wav', 'wb') as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes(audio.tobytes())
json.dump({'duration': round(t, 3), 'scenes': timeline}, open('timeline.json', 'w'), indent=1)
for s in timeline: print(f"{s['id']:11s} {s['start']:6.1f}–{s['end']:6.1f}  ({s['end']-s['start']:.1f}s)")
print('total', round(t, 1), 's')
