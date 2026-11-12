/**
 * Демо-запись интерфейса TAO: обзор, наведение, эффекты, AI-панель, тема.
 * Запуск: node tools/demo-record.mjs <token>
 * Результат: /tmp/tao-demo/tao-demo.webm (потом ffmpeg -> gif)
 */
import { chromium } from '/home/golden/.npm/_npx/9833c18b2d85bc59/node_modules/playwright/index.mjs';
import fs from 'node:fs';

const TOKEN = process.argv[2];
const OUT = '/tmp/tao-demo';
fs.rmSync(OUT, { recursive: true, force: true });
fs.mkdirSync(OUT, { recursive: true });

const W = 1440, H = 810;
const sleep = ms => new Promise(r => setTimeout(r, ms));

const browser = await chromium.launch({
  executablePath: '/usr/bin/chromium',
  args: ['--force-color-profile=srgb', '--font-render-hinting=none', '--no-sandbox'],
});
const ctx = await browser.newContext({
  viewport: { width: W, height: H },
  deviceScaleFactor: 1,
  colorScheme: 'dark',
  locale: 'ru-RU',
});
const page = await ctx.newPage();

// кадры снимаем через CDP-скринкаст: ffmpeg от Playwright не нужен
const framesDir = OUT + '/frames';
fs.mkdirSync(framesDir, { recursive: true });
const client = await ctx.newCDPSession(page);
let frameNo = 0;
client.on('Page.screencastFrame', async ev => {
  const name = framesDir + '/f' + String(frameNo++).padStart(5, '0') + '.jpg';
  fs.writeFileSync(name, Buffer.from(ev.data, 'base64'));
  try { await client.send('Page.screencastFrameAck', { sessionId: ev.sessionId }); } catch (e) {}
});
await client.send('Page.startScreencast', { format: 'jpeg', quality: 82, maxWidth: W, maxHeight: H, everyNthFrame: 2 });
page.on('dialog', d => d.dismiss());

await page.goto(`http://127.0.0.1:8848/?token=${TOKEN}`, { waitUntil: 'networkidle' });
await page.waitForTimeout(1200);

// тёмная тема + русский
await page.evaluate(() => {
  try { localStorage.setItem('tao.theme', 'dark'); } catch (e) {}
  if (window.tamI18n) tamI18n.setLang('ru');
  if (document.documentElement.dataset.theme !== 'dark') { try { toggleTheme(); } catch (e) {} }
});
await page.waitForTimeout(900);
await page.evaluate(() => { try { closeAll(); } catch (e) {} });

const move = async (x, y, steps = 18) => {
  await page.mouse.move(x, y, { steps });
  await page.waitForTimeout(120);
};
const click = async (sel, wait = 600) => {
  const el = await page.$(sel);
  if (!el) return false;
  const b = await el.boundingBox();
  if (!b) return false;
  await move(b.x + b.width / 2, b.y + b.height / 2, 14);
  await page.mouse.down(); await page.waitForTimeout(70); await page.mouse.up();
  await page.waitForTimeout(wait);
  return true;
};

// 1. медленный проход мышью по строкам аккаунтов (эффект наведения)
const rows = await page.$$('#board tbody tr, .accounts-table tbody tr, tbody tr');
for (const r of rows.slice(0, 3)) {
  const b = await r.boundingBox();
  if (b) { await move(b.x + b.width * 0.55, b.y + b.height / 2, 12); await page.waitForTimeout(260); }
}

// 2. навигация: наведение на пункты (магнит + бегунок)
const nav = await page.$$('.nav-item');
for (const n of nav.slice(0, 4)) {
  const b = await n.boundingBox();
  if (b) { await move(b.x + b.width / 2, b.y + b.height / 2, 10); await page.waitForTimeout(220); }
}

// 3. вкладка «Инструменты»
await click('.nav-item[data-nav="toolbox"]', 1200);
await page.waitForTimeout(500);
const cards = await page.$$('.tb-card, .tool-card, #toolbox .card, .stage .card');
for (const c of cards.slice(0, 3)) {
  const b = await c.boundingBox();
  if (b) { await move(b.x + b.width * 0.5, b.y + b.height * 0.4, 12); await page.waitForTimeout(300); }
}

// 4. назад в аккаунты, открыть AI-панель
await click('.nav-item[data-nav="accounts"]', 900);
await page.waitForTimeout(400);
await click('#aiFab', 1100);
await page.waitForTimeout(700);

// 5. в AI-панели: навести на подсказки, ввести вопрос
const chips = await page.$$('#aiPanel .ai-chip, #aiPanel .ai-suggest button, #aiPanel .ai-row');
for (const c of chips.slice(0, 3)) {
  const b = await c.boundingBox();
  if (b) { await move(b.x + b.width / 2, b.y + b.height / 2, 10); await page.waitForTimeout(260); }
}
const input = await page.$('#aiInput');
if (input) {
  const b = await input.boundingBox();
  await move(b.x + 120, b.y + b.height / 2, 10);
  await page.mouse.down(); await page.mouse.up();
  await page.waitForTimeout(200);
  await page.keyboard.type('Покажи все авторизованные аккаунты', { delay: 45 });
  await page.waitForTimeout(500);
}

// 6. закрыть панель (та самая кнопка), пауза
const closed = await click('#aiPanel header button:last-child', 900);
if (!closed) { await page.keyboard.press('Escape'); await page.waitForTimeout(700); }
await page.waitForTimeout(500);

// 7. переключение темы
await click('#themeBtn', 900);
await page.waitForTimeout(900);
await click('#themeBtn', 900);
await page.waitForTimeout(600);

// 8. финал: курсор по пустому месту, чтобы видны были эффекты
await move(W * 0.45, H * 0.55, 20);
await page.waitForTimeout(500);
await move(W * 0.7, H * 0.3, 20);
await page.waitForTimeout(700);

try { await client.send('Page.stopScreencast'); } catch (e) {}
await page.waitForTimeout(300);
await ctx.close();
await browser.close();
console.log(JSON.stringify({ out: OUT, frames: frameNo }));
