// Re-film shots the live recording missed, from the run's end state (no model calls).
//   node clips.mjs <run-dir>   -> <run-dir>/clip-S.mp4 (strategy doc), clip-E.mp4 (Epics, results)
import { spawn } from 'child_process';
import fs from 'fs';
import path from 'path';
const { chromium } = await import(process.env.PW_MODULE || 'playwright');
const RUN = path.resolve(process.argv[2]);
const DOMAIN = process.env.BREADBOARD_DOMAIN || 'w530.local';
const STACK_IP = process.env.STACK_IP;      // the stack host's address, for Chrome's resolver
if (!STACK_IP) { console.error('set STACK_IP (see README.md)'); process.exit(2); }
const J = `https://jira.${DOMAIN}`, G = `https://gitlab.${DOMAIN}/ui/redhat/rhel-ai/agentic-ci`;
const KEY = process.env.KEY || 'RHAISTRAT-75028';
const sleep = ms => new Promise(r => setTimeout(r, ms));

const browser = await chromium.launch({ executablePath: process.env.CHROME || '/usr/bin/google-chrome', args: [`--host-resolver-rules=MAP *.${DOMAIN} ${STACK_IP}`] });
const ctx = await browser.newContext({ ignoreHTTPSErrors: true, viewport: { width: 1280, height: 720 }, httpCredentials: { username: 'admin', password: 'admin' } });
const page = await ctx.newPage();
const cdp = await ctx.newCDPSession(page);
const state = { step: '', title: '', sub: '' };
function overlay(s) {
  let cap = document.getElementById('__cap');
  if (!cap) { cap = document.createElement('div'); cap.id = '__cap'; Object.assign(cap.style, { position: 'fixed', left: '0', right: '0', bottom: '0', zIndex: 2147483647, background: 'rgba(14,17,24,.92)', color: '#f4f6fa', font: '15px/1.4 system-ui,sans-serif', padding: '12px 22px', pointerEvents: 'none', display: 'flex', alignItems: 'center', gap: '18px', boxShadow: '0 -2px 12px rgba(0,0,0,.25)' }); document.documentElement.appendChild(cap); }
  cap.replaceChildren();
  const step = document.createElement('div'); step.textContent = s.step; Object.assign(step.style, { font: '700 13px system-ui', letterSpacing: '.06em', textTransform: 'uppercase', color: '#8fb0ff', whiteSpace: 'nowrap' });
  const body = document.createElement('div'); body.style.flex = '1';
  const t = document.createElement('div'); t.textContent = s.title; t.style.font = '600 19px/1.3 system-ui,sans-serif';
  const sub = document.createElement('div'); sub.textContent = s.sub; sub.style.color = '#b9c0cc';
  body.append(t, sub); cap.append(step, body);
}
const draw = () => page.evaluate(overlay, state).catch(() => {});
page.on('load', draw); page.on('domcontentloaded', draw);
const caption = (step, title, sub) => { Object.assign(state, { step, title, sub }); return draw(); };
const go = async url => { await page.goto(url, { waitUntil: 'networkidle' }).catch(() => {}); await draw(); await sleep(800); };
const scroll = async (px, steps = 20, pause = 200) => { for (let i = 0; i < steps; i++) { await page.mouse.wheel(0, px / steps); await sleep(pause); } };
const toHeading = async text => { await page.evaluate(t => { const h = [...document.querySelectorAll('h3,h2')].find(x => x.textContent.trim().startsWith(t)); if (h) window.scrollTo({ top: h.getBoundingClientRect().top + window.scrollY - 80 }); }, text); await sleep(1500); };

async function clip(name, body) {
  const dir = path.join(RUN, `clip-${name}`); fs.rmSync(dir, { recursive: true, force: true }); fs.mkdirSync(dir);
  const frames = [];
  const on = async f => { frames.push([f.metadata.timestamp, Buffer.from(f.data, 'base64')]); cdp.send('Page.screencastFrameAck', { sessionId: f.sessionId }).catch(() => {}); };
  cdp.on('Page.screencastFrame', on);
  await cdp.send('Page.startScreencast', { format: 'jpeg', quality: 72, maxWidth: 1280, maxHeight: 720 });
  await body();
  await sleep(300);
  await cdp.send('Page.stopScreencast'); cdp.off('Page.screencastFrame', on);
  let list = '';
  frames.forEach(([t, d], i) => { fs.writeFileSync(path.join(dir, `${i}.jpg`), d); list += `file '${i}.jpg'\nduration ${((frames[i + 1]?.[0] ?? t + 1.5) - t).toFixed(4)}\n`; });
  list += `file '${frames.length - 1}.jpg'\n`;
  fs.writeFileSync(path.join(dir, 'list.txt'), list);
  await new Promise(r => spawn('ffmpeg', ['-loglevel', 'error', '-y', '-f', 'concat', '-i', 'list.txt', '-vf', 'fps=30,scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2,format=yuv420p', '-c:v', 'libx264', '-crf', '23', `../clip-${name}.mp4`], { cwd: dir, stdio: 'inherit' }).on('close', r));
  console.log(name, frames.length, 'frames');
}

// S: after "RHAISTRAT-75028 now carries its strategy and review", before sign-off.
await clip('S', async () => {
  await caption('4 · Strategy', `${KEY} now carries its strategy and review`, 'strat-creator-rubric-pass, plus the strategy and review documents attached to the ticket.');
  await go(`${J}/browse/${KEY}`); await toHeading('Attachments'); await sleep(3500);
  const views = await page.evaluate(() => [...document.querySelectorAll('tr')].map(tr => [tr.querySelector('a')?.textContent.trim(), tr.querySelector('a[href^="/attachment/"][href$="/view"]')?.getAttribute('href')]).filter(([n, h]) => n && h));
  const view = suffix => views.find(([n]) => n.endsWith(suffix))?.[1];
  await caption('4 · Strategy', 'The strategy strat-creator wrote', 'Approach, components, phasing, risks and the requirements it traces back to.');
  await go(J + view('strategy.md')); await sleep(2500); await scroll(3600, 45, 260); await sleep(1500);
  await caption('4 · Strategy', 'And the independent review', 'Scored against the strategy rubric; a pass is what lets the Initiative move on to sign-off.');
  await go(J + view('review.md')); await sleep(2500); await scroll(1800, 25, 260); await sleep(2000);
});

// E: replaces the run's closing shots ("now has its Epics" and the results repository).
await clip('E', async () => {
  await caption('6 · Decompose', `${KEY} now has its Epics`, 'Ten RHAI Epics with the Initiative as parent; the Initiative is labelled epic-creator-auto-decomposed.');
  await go(`${J}/browse/${KEY}`); await toHeading('Child Issues'); await sleep(6000); await scroll(500, 10, 250); await sleep(3000);
  const href = await page.$eval('a.issue-key-link[href^="/issue/RHAI-"]', a => a.getAttribute('href')).catch(() => null);
  if (href) {
    await caption('6 · Decompose', 'One of the new Epics', 'Scope, acceptance criteria and dependencies, written from the approved strategy.');
    await go(J + href); await sleep(2500); await scroll(1600, 25, 260); await sleep(2500);
  }
  await caption('7 · Results', 'Every run leaves a record in its results repository', 'epic-decomposer-results: the plan, reviews, submission receipts and an HTML report, per run.');
  await go(`${G}/epic-decomposer-results`); await sleep(6000);
});
await browser.close();
