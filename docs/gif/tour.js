// Records frames of a short dashboard tour: node gif_tour.js <url> <outdir>
const { chromium } = require('playwright');
const [url, out] = process.argv.slice(2);
(async () => {
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 1200, height: 1000 }, deviceScaleFactor: 1 });
  const errs = []; p.on('pageerror', e => errs.push(e.message));
  let n = 0; const frames = [];
  const shot = async (ms) => { const f = `${out}/f${String(n++).padStart(2, '0')}.png`; await p.screenshot({ path: f }); frames.push([f, ms]); };
  const top = async (sel, off = 10) => { await p.evaluate(([s, o]) => { const el = document.querySelector(s); window.scrollTo(0, el.getBoundingClientRect().top + scrollY - o); }, [sel, off]); await p.waitForTimeout(700); };
  await p.goto(url + '#lang=es'); await p.waitForTimeout(3500);
  await shot(2200);                                   // header + current situation
  await top('#passes', 70); await shot(1800);         // upcoming passes
  // a bloom date in the viewer, zoom in, coordinates, mark a point
  await p.evaluate(() => openViewer('Hatillo', '2026-01-14', false)); await p.waitForTimeout(1500);
  await top('#viewer'); await shot(1800);
  const box = await p.locator('#viewer .zoombox').nth(1).boundingBox();
  const fx = 0.22, fy = 0.75; // south-western arm
  for (const f of [1.7, 1.7]) {
    await p.evaluate(([fx, fy, f]) => { const b = document.querySelector('#viewer .zoombox');
      VIEWZOOM.zoomAt(b.clientWidth * fx, b.clientHeight * fy, f); }, [fx, fy, f]);
    await p.mouse.move(box.x + box.width * fx, box.y + box.height * fy);
    await p.waitForTimeout(500); await shot(900);
  }
  await p.click('#v-tools .mark'); await p.mouse.move(box.x + box.width * 0.45, box.y + box.height * 0.55);
  await p.waitForTimeout(400); await shot(1200);
  await p.mouse.click(box.x + box.width * 0.45, box.y + box.height * 0.55); await p.waitForTimeout(500); await shot(1800);
  // bloom-frequency map
  await top('#m-tools', 4); await p.mouse.move(400, 500); await p.waitForTimeout(800); await shot(2400);
  // history chart and temperature
  await top('#charts', 140); await shot(2000);
  await top('#charts-temp', 140); await shot(2000);
  await top('#puntos', 70); await shot(1800);
  require('fs').writeFileSync(`${out}/frames.json`, JSON.stringify(frames));
  console.log('frames', frames.length, 'errors', errs); await b.close();
})();
