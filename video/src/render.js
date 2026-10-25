const { chromium } = require('playwright');
const { spawn } = require('child_process');
const fs = require('fs');
(async () => {
  const mode = process.argv[2] || 'stills';
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1920, height: 1080 } });
  page.on('pageerror', e => console.error('PAGE ERROR', e.message));
  await page.goto('file://' + __dirname + '/anim.html');
  await page.evaluate(async () => { await document.fonts.ready; await document.fonts.load('600 40px Fredoka'); await document.fonts.load('600 40px Nunito'); });
  const TL = JSON.parse(fs.readFileSync(__dirname + '/timeline.json'));
  if (mode === 'stills') {
    const times = process.argv.slice(3).map(Number);
    for (const T of times) {
      const d = await page.evaluate(T => window.frameJPEG(T, 0.9), T);
      fs.writeFileSync(`${__dirname}/still_${String(T).padStart(6, '0')}.jpg`, Buffer.from(d.split(',')[1], 'base64'));
    }
  } else {
    const fps = 30, n = Math.ceil(TL.duration * fps);
    const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(fps), '-c:v', 'mjpeg', '-i', '-',
      '-i', __dirname + '/mix_norm.wav', '-c:v', 'libx264', '-preset', 'slow', '-crf', '20', '-pix_fmt', 'yuv420p', '-movflags', '+faststart',
      '-c:a', 'aac', '-b:a', '160k', '-shortest', __dirname + '/out.mp4'], { stdio: ['pipe', 'inherit', 'inherit'] });
    const t0 = Date.now();
    for (let f = 0; f < n; f++) {
      const d = await page.evaluate(T => window.frameJPEG(T, 0.95), f / fps);
      const ok = ff.stdin.write(Buffer.from(d.split(',')[1], 'base64'));
      if (!ok) await new Promise(r => ff.stdin.once('drain', r));
      if (f % 300 === 0) console.log(`frame ${f}/${n} ${((Date.now() - t0) / 1000).toFixed(0)}s`);
    }
    ff.stdin.end(); await new Promise(r => ff.on('close', r));
    console.log('done', ((Date.now() - t0) / 1000).toFixed(0), 's');
  }
  await browser.close();
})();
