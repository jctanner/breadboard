// Record the CC-75 Initiatives demo on w530 as a video.
//
// A headless Chrome on this machine browses the w530 Jira and GitLab emulator UIs while
// every pipeline action runs through demo.py on w530 over SSH (the same commands the demo
// script uses). Frames come from Chrome's screencast with their timestamps; waits for
// agent jobs are fast-forwarded (FF) and the encoder maps real time to video time.
//
//   node record.mjs            live run (model steps cost money via Model Relay)
//   DRY=1 node record.mjs      no model: replays finished jobs (REPLAY_* ids) instead
//
// Output: run-<stamp>/{frames/,frames.txt,events.log,demo.mp4}
import { spawn } from 'child_process';
import fs from 'fs';
import path from 'path';

const PW = process.env.PW_MODULE || 'playwright';
const { chromium } = await import(PW);
const DRY = process.env.DRY === '1';
const FF = Number(process.env.FF || 15);
const KEY = process.env.KEY || 'RHAISTRAT-75028';
const OPTIN = process.env.OPTIN || 'RHAISTRAT-75016';
const REPLAY = { autofix: ['rfe-autofixer', 361], live: ['strat-pipeline', 371], decompose: ['epic-decomposer', 398] };
const DOMAIN = process.env.BREADBOARD_DOMAIN || 'w530.local';
const STACK_IP = process.env.STACK_IP;      // the stack host's address, for Chrome's resolver
const STACK_SSH = process.env.STACK_SSH;    // user@host for ssh
if (!STACK_IP || !STACK_SSH) { console.error('set STACK_IP and STACK_SSH (see README.md)'); process.exit(2); }
const J = `https://jira.${DOMAIN}`, G = `https://gitlab.${DOMAIN}`;
const GROUP = 'redhat/rhel-ai/agentic-ci';
const OUT = path.resolve(process.env.OUT || `run-${new Date().toISOString().replace(/[-:]/g, '').slice(0, 15)}${DRY ? '-dry' : ''}`);
fs.mkdirSync(path.join(OUT, 'frames'), { recursive: true });

const t0 = Date.now();
const log = (...a) => { const line = `${new Date().toISOString()} ${a.join(' ')}`; console.log(line); fs.appendFileSync(path.join(OUT, 'events.log'), line + '\n'); };
const sleep = ms => new Promise(r => setTimeout(r, ms));

// --- remote commands -----------------------------------------------------------------
const SSH = ['-o', 'StrictHostKeyChecking=yes', '-o', 'BatchMode=yes', '-o', 'ServerAliveInterval=30', STACK_SSH];
const REMOTE_DIR = process.env.REMOTE_DIR || '~/breadboard-cc75/var/demos/initiatives';
const REMOTE_CA = process.env.REMOTE_CA || '$HOME/.cache/cc75/w530-ca.crt';
const ENV = `cd ${REMOTE_DIR} && export BREADBOARD_DOMAIN=${DOMAIN} BREADBOARD_CA_FILE=${REMOTE_CA} && `;
function remote(cmd, onLine = () => {}) {
  return new Promise(resolve => {
    const p = spawn('ssh', [...SSH, ENV + cmd]);
    let out = '', buf = '';
    const feed = d => { out += d; buf += d; let i; while ((i = buf.indexOf('\n')) >= 0) { const l = buf.slice(0, i); buf = buf.slice(i + 1); log('remote>', l.slice(0, 200)); onLine(l); } };
    p.stdout.on('data', feed); p.stderr.on('data', feed);
    p.on('close', code => { if (buf) onLine(buf); resolve({ code, out }); });
  });
}
async function api(url) {
  const r = await remote(`curl -s --cacert $BREADBOARD_CA_FILE -u admin:admin '${url}'`);
  try { return JSON.parse(r.out); } catch { return null; }
}
const pid = name => encodeURIComponent(`${GROUP}/${name}`);
const ui = url => url.replace(`${G}/${GROUP}/`, `${G}/ui/${GROUP}/`);

// --- browser and recording -----------------------------------------------------------
const browser = await chromium.launch({ executablePath: process.env.CHROME || '/usr/bin/google-chrome', args: [`--host-resolver-rules=MAP *.${DOMAIN} ${STACK_IP}`] });
const ctx = await browser.newContext({ ignoreHTTPSErrors: true, viewport: { width: 1280, height: 720 }, httpCredentials: { username: 'admin', password: 'admin' } });
const page = await ctx.newPage();
const cdp = await ctx.newCDPSession(page);
let nframes = 0;
const index = fs.openSync(path.join(OUT, 'frames.txt'), 'a');
cdp.on('Page.screencastFrame', async f => {
  const name = `frames/${String(nframes++).padStart(6, '0')}.jpg`;
  fs.writeFileSync(path.join(OUT, name), Buffer.from(f.data, 'base64'));
  fs.writeSync(index, `${f.metadata.timestamp} ${name}\n`);
  cdp.send('Page.screencastFrameAck', { sessionId: f.sessionId }).catch(() => {});
});
const segments = [[Date.now() / 1000, 1]];
const fast = () => { state.since = Date.now() / 1000; speed(FF); };
const speed = x => { segments.push([Date.now() / 1000, x]); state.ff = x > 1 ? x : 0; draw(); };

// The caption bar (bottom), an optional terminal card (top right) and the FF badge.
const state = { step: '', title: '', sub: '', term: [], ff: 0, since: 0 };
function overlay(s) {
  const mk = (id, css) => { let e = document.getElementById(id); if (!e) { e = document.createElement('div'); e.id = id; Object.assign(e.style, css); document.documentElement.appendChild(e); } return e; };
  const cap = mk('__cap', { position: 'fixed', left: '0', right: '0', bottom: '0', zIndex: 2147483647, background: 'rgba(14,17,24,.92)', color: '#f4f6fa', font: '15px/1.4 system-ui,sans-serif', padding: '12px 22px', pointerEvents: 'none', display: 'flex', alignItems: 'center', gap: '18px', boxShadow: '0 -2px 12px rgba(0,0,0,.25)' });
  cap.replaceChildren();
  const step = document.createElement('div'); step.textContent = s.step; Object.assign(step.style, { font: '700 13px system-ui', letterSpacing: '.06em', textTransform: 'uppercase', color: '#8fb0ff', whiteSpace: 'nowrap' });
  const body = document.createElement('div'); body.style.flex = '1';
  const title = document.createElement('div'); title.textContent = s.title; title.style.font = '600 19px/1.3 system-ui,sans-serif';
  const sub = document.createElement('div'); sub.textContent = s.sub; sub.style.color = '#b9c0cc';
  body.append(title); if (s.sub) body.append(sub);
  cap.append(step, body);
  if (s.ff) {
    const b = document.createElement('div'); Object.assign(b.style, { font: '700 15px ui-monospace,monospace', background: '#f0bf6a', color: '#1d1f23', padding: '6px 10px', borderRadius: '6px', whiteSpace: 'nowrap' });
    const tick = () => { const e = Math.max(0, Math.floor(Date.now() / 1000 - s.since)); b.textContent = `⏩ ${s.ff}×  ${String(Math.floor(e / 60)).padStart(2, '0')}:${String(e % 60).padStart(2, '0')}`; };
    tick(); clearInterval(window.__capTick); window.__capTick = setInterval(tick, 250); cap.append(b);
  } else clearInterval(window.__capTick);
  const term = mk('__term', { position: 'fixed', top: '14px', right: '14px', zIndex: 2147483647, maxWidth: '620px', background: 'rgba(20,22,28,.94)', color: '#d7f7d0', font: '13px/1.45 ui-monospace,monospace', padding: '10px 14px', borderRadius: '8px', pointerEvents: 'none', whiteSpace: 'pre-wrap', boxShadow: '0 6px 24px rgba(0,0,0,.35)' });
  term.textContent = s.term.join('\n'); term.style.display = s.term.length ? 'block' : 'none';
}
function draw() { return page.evaluate(overlay, state).catch(() => {}); }
page.on('load', () => { draw(); });
page.on('domcontentloaded', () => { draw(); });
const caption = (step, title, sub = '') => { Object.assign(state, { step, title, sub }); log('caption', step, '|', title); return draw(); };
const term = lines => { state.term = lines; return draw(); };

async function go(url) { log('goto', url); await page.goto(url, { waitUntil: 'domcontentloaded' }).catch(e => log('goto error', e.message)); await draw(); await sleep(800); }
async function scroll(px, steps = 12, pause = 120) { for (let i = 0; i < steps; i++) { await page.mouse.wheel(0, px / steps); await sleep(pause); } }
async function showSection(text) {
  await page.evaluate(t => { const h = [...document.querySelectorAll('h3,h2')].find(x => x.textContent.trim().startsWith(t)); if (h) window.scrollTo({ top: h.getBoundingClientRect().top + window.scrollY - 80 }); }, text).catch(() => {});
  await sleep(1200);
}
async function demo(cmd, onLine) {
  const shown = [`$ demo.py ${cmd}`];
  await term(shown);
  const r = await remote(`python3 scripts/demo.py ${cmd}`, l => { if (l.trim() && !l.startsWith('01O')) { shown.push(l.slice(0, 90)); if (shown.length > 7) shown.splice(1, 1); term(shown); } onLine?.(l); });
  return r;
}
async function tailJob(project, job, label) {
  await go(`${G}/ui/${GROUP}/${project}/-/jobs/${job}`);
  await page.evaluate(() => { document.querySelector('[data-ci-scroll-bottom]')?.click(); window.scrollTo(0, document.body.scrollHeight); }).catch(() => {});
  fast();
  let status = '';
  for (;;) {
    const j = await api(`${G}/api/v4/projects/${pid(project)}/jobs/${job}`);
    status = j?.status || status;
    if (['success', 'failed', 'canceled'].includes(status)) break;
    if (DRY) { await sleep(8000); status = j?.status; break; }
    await sleep(20000);
    await page.evaluate(() => { if (!document.getElementById('__cap')) location.reload(); }).catch(() => {});
  }
  await sleep(4000);
  speed(1);
  log('job', project, job, status);
  await caption(state.step, `${label}: ${status === 'success' ? 'job passed' : `job ${status}`}`, state.sub);
  await sleep(3000);
  return status;
}
async function playedJob(project, pipeline, name) {
  for (let i = 0; i < 120; i++) {
    const jobs = await api(`${G}/api/v4/projects/${pid(project)}/pipelines/${pipeline}/jobs`) || [];
    const j = jobs.find(x => x.name === name);
    if (j && j.status !== 'manual' && j.status !== 'created') return j.id;
    await sleep(10000);
  }
  return null;
}
async function labelsOf(keys) {
  const out = {};
  for (const k of keys) out[k] = ((await api(`${J}/rest/api/2/issue/${k}?fields=labels`))?.fields?.labels || []).sort().join(' ');
  return out;
}

// --- the demo --------------------------------------------------------------------------
const title = async (h, p) => {
  await page.setContent(`<body style="margin:0;height:100vh;display:grid;place-items:center;background:#11141b;color:#eef1f6;font-family:system-ui,sans-serif"><div style="max-width:880px;padding:40px"><div style="color:#8fb0ff;font-weight:700;letter-spacing:.08em;text-transform:uppercase;font-size:14px">CC-75 · breadboard on w530 · synthetic data</div><h1 style="font-size:46px;line-height:1.15;margin:14px 0 18px">${h}</h1><p style="font-size:20px;line-height:1.5;color:#b9c0cc;margin:0">${p}</p></div></body>`);
  await sleep(6000);
};

await cdp.send('Page.startScreencast', { format: 'jpeg', quality: 72, maxWidth: 1280, maxHeight: 720 });
let ok = true;
try {
  await title('An Initiative, end to end', `Autofix, strategy, human sign-off and decomposition into Epics, run by the production pipelines (on <code>main</code>) against emulated Jira and GitLab. Waiting on agents is fast-forwarded; everything else is real time.${DRY ? '<br><br><b>Dry run:</b> replays finished jobs; no model calls.' : ''}`);

  await caption('1 · The board', 'Synthetic Initiatives in the Jira emulator', '79 synthetic issues: invented text, no real keys or names. Labels drive every stage.');
  await go(`${J}/issues?jql=${encodeURIComponent('project = RHAISTRAT AND issuetype = Initiative ORDER BY key ASC')}`);
  await sleep(2500); await scroll(900, 18, 220); await sleep(1500);

  await caption('1 · The board', `${KEY}: the Initiative we follow`, 'Problem, goal, scope, requirements R1–R6 and acceptance. A product manager wrote it; agents take it from here.');
  await go(`${J}/browse/${KEY}`);
  await sleep(2500); await scroll(1400, 24, 220); await sleep(1500);

  await caption('2 · Opt in', 'A human opts an Initiative in to autofix', `${OPTIN} gets initiative-autofix-opt-in: the canary boundary. Nothing without the label is touched.`);
  await go(`${J}/browse/${OPTIN}`); await sleep(2000);
  if (!DRY) await demo(`optin ${OPTIN}`); else await term([`$ demo.py optin ${OPTIN}`, '(dry run: not applied)']);
  await go(`${J}/browse/${OPTIN}`); await sleep(4000); await term([]);

  // Autofix ------------------------------------------------------------------------------
  const optedIn = (await api(`${J}/rest/api/3/search/jql?jql=${encodeURIComponent('project = RHAISTRAT AND issuetype = Initiative AND labels = initiative-autofix-opt-in')}&maxResults=100&fields=labels`))?.issues?.map(i => i.key) || [];
  const before = await labelsOf(optedIn);
  await caption('3 · Autofix', "rfe-autofixer's Initiative schedule fires", 'Up to 3 opted-in Initiatives that are new or changed: assess, review against the rubric, fix or reject, label.');
  let afPipeline, afJob;
  if (!DRY) {
    await demo('autofix --limit 3', l => { const m = l.match(/pipeline (\d+): (\S+)/); if (m) afPipeline = Number(m[1]); });
    if (afPipeline) { await go(`${G}/ui/${GROUP}/rfe-autofixer/-/pipelines/${afPipeline}`); await sleep(4000); fast(); afJob = await playedJob('rfe-autofixer', afPipeline, 'autofix-initiative'); speed(1); }
  } else afJob = REPLAY.autofix[1];
  await term([]);
  const afStatus = afJob ? await tailJob('rfe-autofixer', afJob, 'Autofix') : 'missing';
  const after = await labelsOf(optedIn);
  const changed = optedIn.filter(k => before[k] !== after[k]);
  log('autofix changed', changed.join(',') || '(none)');
  await caption('3 · Autofix', changed.length ? `Autofix labelled ${changed.length} Initiative${changed.length > 1 ? 's' : ''}: ${changed.join(', ')}` : 'Autofix results', 'Outcome labels: rubric pass, feasibility, alignment with the parent Outcome, or needs attention.');
  await go(`${J}/issues?jql=${encodeURIComponent('project = RHAISTRAT AND issuetype = Initiative AND labels = initiative-autofix-opt-in ORDER BY key ASC')}`);
  await sleep(5000);
  for (const k of changed.slice(0, 2)) { await go(`${J}/browse/${k}`); await sleep(1500); await page.evaluate(() => { const l = [...document.querySelectorAll('*')].find(e => e.textContent.trim() === 'LABELS' || e.textContent.trim() === 'Labels'); l?.scrollIntoView({ block: 'center' }); }).catch(() => {}); await sleep(4000); }
  if (!DRY && afStatus !== 'success') throw new Error(`autofix ${afStatus}`);

  // Live strategy ----------------------------------------------------------------------------
  await caption('4 · Strategy', `strat-pipeline on main writes the strategy for ${KEY}`, 'A live Initiative run needs INITIATIVE_LIVE=on (the proposed cutover flag); strat-creator runs in a Fullsend sandbox, then an independent review.');
  let lvPipeline, lvJob;
  if (!DRY) {
    await demo(`live ${KEY}`, l => {
      const m = l.match(/^pipeline (\d+): /); if (m) { lvPipeline = Number(m[1]); go(`${G}/ui/${GROUP}/strat-pipeline/-/pipelines/${lvPipeline}`).then(fast); }
      const p = l.match(/played workflow-single-rfe: .*\/jobs\/(\d+)/); if (p) lvJob = Number(p[1]);
    });
    speed(1);
  } else lvJob = REPLAY.live[1];
  await term([]);
  const lvStatus = lvJob ? await tailJob('strat-pipeline', lvJob, 'Strategy') : 'missing';
  await caption('4 · Strategy', `${KEY} now carries its strategy and review`, 'strat-creator-rubric-pass, plus the strategy and review documents attached to the ticket.');
  await go(`${J}/browse/${KEY}`); await sleep(2000);
  await page.evaluate(() => { const l = [...document.querySelectorAll('*')].find(e => e.textContent.trim() === 'LABELS' || e.textContent.trim() === 'Labels'); l?.scrollIntoView({ block: 'center' }); }).catch(() => {});
  await sleep(4000); await showSection('Attachments'); await sleep(4000);
  // The filename link downloads; the row's View button (/attachment/<id>/view) renders it inline.
  const views = await page.evaluate(() => [...document.querySelectorAll('tr')].map(tr => [tr.querySelector('a')?.textContent.trim(), tr.querySelector('a[href^="/attachment/"][href$="/view"]')?.getAttribute('href')]).filter(([n, h]) => n && h)).catch(() => []);
  const view = suffix => views.find(([n]) => n.endsWith(suffix))?.[1];
  if (view('strategy.md')) {
    await caption('4 · Strategy', 'The strategy strat-creator wrote', 'Approach, components, phasing, risks and the requirements it traces back to.');
    await go(J + view('strategy.md')); await sleep(2500); await scroll(3600, 45, 260); await sleep(1500);
  }
  if (view('review.md')) {
    await caption('4 · Strategy', 'And the independent review', 'Scored against the strategy rubric; a pass is what lets the Initiative move on to sign-off.');
    await go(J + view('review.md')); await sleep(2500); await scroll(1800, 25, 260); await sleep(2000);
  }
  if (!DRY && lvStatus !== 'success') throw new Error(`strategy ${lvStatus}`);

  // Sign-off -------------------------------------------------------------------------------
  await caption('5 · Sign-off', 'The one manual gate: a human signs off the strategy', 'strat-creator-human-sign-off. Only signed-off Initiatives are decomposed (here, only this one).');
  await go(`${J}/browse/${KEY}`); await sleep(2000);
  if (!DRY) await demo(`signoff ${KEY}`); else await term([`$ demo.py signoff ${KEY}`, '(dry run: not applied)']);
  await go(`${J}/browse/${KEY}`);
  await page.evaluate(() => { const l = [...document.querySelectorAll('*')].find(e => e.textContent.trim() === 'LABELS' || e.textContent.trim() === 'Labels'); l?.scrollIntoView({ block: 'center' }); }).catch(() => {});
  await sleep(5000); await term([]);

  // Decompose ------------------------------------------------------------------------------
  await caption('6 · Decompose', 'epic-decomposer splits the Initiative into Epics', 'epic-creator #40 (rhai-initiative workload): decompose, adversarial review, revise until accepted, then create the Epics in Jira.');
  let dcPipeline, dcJob;
  if (!DRY) {
    await demo('decompose', l => {
      const m = l.match(/^pipeline (\d+): /); if (m) { dcPipeline = Number(m[1]); go(`${G}/ui/${GROUP}/epic-decomposer/-/pipelines/${dcPipeline}`).then(fast); }
      const p = l.match(/played decompose-initiatives: .*\/jobs\/(\d+)/); if (p) dcJob = Number(p[1]);
    });
    speed(1);
  } else dcJob = REPLAY.decompose[1];
  await term([]);
  const dcStatus = dcJob ? await tailJob('epic-decomposer', dcJob, 'Decompose') : 'missing';
  await caption('6 · Decompose', `${KEY} now has its Epics`, 'Each Epic has the Initiative as parent, a Blocks link and the epic-creator-auto-decomposed label on the Initiative.');
  await go(`${J}/browse/${KEY}`); await sleep(2000); await showSection('Child Issues'); await sleep(2000); await scroll(500, 10, 250); await sleep(4000);
  const child = await page.$('a.issue-key-link[href^="/issue/RHAI-"]');
  if (child) { await caption('6 · Decompose', 'One of the new Epics', 'Scope, acceptance criteria and dependencies, written from the approved strategy.'); await go(new URL(await child.getAttribute('href'), J).href); await sleep(2500); await scroll(1600, 25, 260); await sleep(2500); }
  if (!DRY && dcStatus !== 'success') throw new Error(`decompose ${dcStatus}`);

  await caption('7 · Results', 'Every run leaves a record in its results repository', 'epic-decomposer-results: the plan, reviews, submission receipts and an HTML report, per run.');
  await go(`${G}/ui/${GROUP}/epic-decomposer-results`); await sleep(6000);
} catch (e) {
  ok = false; log('stopped:', e.message);
  await caption('Stopped', `The run stopped: ${e.message}`, 'Recorded as it happened.');
  await sleep(4000);
}
state.term = []; speed(1);
await title(ok ? 'Initiative → strategy → sign-off → Epics' : 'Run stopped early', ok ? `Same jobs, same labels, same gates as production, on synthetic data. Total wall time ${Math.round((Date.now() - t0) / 60000)} minutes.` : 'See events.log.');
await cdp.send('Page.stopScreencast');
await sleep(500);
await browser.close();
fs.closeSync(index);
log('frames', nframes, 'ok', ok);

// --- encode: map real time to video time through the speed segments -----------------------
const lines = fs.readFileSync(path.join(OUT, 'frames.txt'), 'utf8').trim().split('\n').map(l => l.split(' ')).map(([t, f]) => [Number(t), f]);
const vt = t => { let v = 0; for (let i = 0; i < segments.length; i++) { const [s, x] = segments[i]; const e = segments[i + 1]?.[0] ?? Infinity; if (t <= s) break; v += (Math.min(t, e) - s) / x; } return v; };
let list = '';
for (let i = 0; i < lines.length; i++) {
  const [t, f] = lines[i];
  const d = i + 1 < lines.length ? vt(lines[i + 1][0]) - vt(t) : 3;
  list += `file '${f}'\nduration ${Math.max(d, 0.001).toFixed(4)}\n`;
}
list += `file '${lines.at(-1)[1]}'\n`;
fs.writeFileSync(path.join(OUT, 'concat.txt'), list);
await new Promise(r => spawn('ffmpeg', ['-loglevel', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', 'concat.txt', '-vf', 'fps=30,scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2,format=yuv420p', '-c:v', 'libx264', '-crf', '23', '-movflags', '+faststart', 'demo.mp4'], { cwd: OUT, stdio: 'inherit' }).on('close', r));
log('video', path.join(OUT, 'demo.mp4'));
