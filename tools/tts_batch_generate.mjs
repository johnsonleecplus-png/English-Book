// Node script: 批量生成 MiniMax T2A v2 MP3 → public/audio/words/
// 50 并发, 已存在的跳过, 3 retry
import fs from 'node:fs';
import path from 'node:path';

// API key 必须从 env 拿 (PowerShell 跑 Node 时 MINIMAX_API_KEY 在 process.env 里)
// 注: 之前从 config.yaml 读会拿到 LLM key (sk-a8075...), TTS 端会 login fail
const API_KEY = process.env.MINIMAX_API_KEY;
if (!API_KEY) {
  console.error('MINIMAX_API_KEY env not set. PowerShell 跑: $env:MINIMAX_API_KEY = [Environment]::GetEnvironmentVariable("MINIMAX_API_KEY", "User"); node tools/tts_batch_generate.mjs');
  process.exit(1);
}
console.error(`Using key: ${API_KEY.slice(0, 10)}...${API_KEY.slice(-4)} (${API_KEY.length} chars)`);
const BASE = 'https://api.minimaxi.com/v1/t2a_v2';
const VOICE = 'English_Graceful_Lady';
const SPEED = 0.85;
const CONCURRENCY = 1;  // API 不支持并发, 严格 1 串行

const PENDING = 'D:\\10-网页集合站\\tts\\pending_words.json';
const DEST = 'D:\\10-English-Book\\public\\audio\\words';

if (!fs.existsSync(DEST)) fs.mkdirSync(DEST, { recursive: true });

const pending = JSON.parse(fs.readFileSync(PENDING, 'utf-8'));
const todo = pending.filter(w => !fs.existsSync(path.join(DEST, `${w}.mp3`)));
console.error(`pending: ${pending.length}, todo (skip existing): ${todo.length}`);

const stats = { ok: 0, fail: 0, total: todo.length, errors: [] };
const start = Date.now();

async function genOne(word) {
  const outPath = path.join(DEST, `${word}.mp3`);
  const payload = {
    model: 'speech-02-hd',
    text: word,
    voice_setting: { voice_id: VOICE, speed: SPEED, vol: 1.0, pitch: 0 },
    audio_setting: { sample_rate: 32000, bitrate: 128000, format: 'mp3' },
  };
  for (let attempt = 0; attempt < 3; attempt++) {
    try {
      const r = await fetch(BASE, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${API_KEY}`, 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
        signal: AbortSignal.timeout(30000),
      });
      if (!r.ok) {
        const t = await r.text();
        if (attempt < 2 && (r.status === 429 || r.status >= 500)) {
          await new Promise(res => setTimeout(res, 1500));
          continue;
        }
        stats.fail++;
        stats.errors.push({ word, status: r.status, body: t.slice(0, 100) });
        return;
      }
      const data = await r.json();
      const hex = data?.data?.audio ?? data?.audio;
      if (!hex || hex.length < 100) {
        if (attempt < 2) {
          await new Promise(res => setTimeout(res, 1500));
          continue;
        }
        stats.fail++;
        stats.errors.push({ word, body: `no audio (len=${hex?.length||0}, base=${JSON.stringify(data?.base_resp||{}).slice(0,80)})` });
        return;
      }
      fs.writeFileSync(outPath, Buffer.from(hex, 'hex'));
      stats.ok++;
      return;
    } catch (e) {
      if (attempt < 2) {
        await new Promise(res => setTimeout(res, 1500));
        continue;
      }
      stats.fail++;
      stats.errors.push({ word, error: String(e).slice(0, 100) });
    }
  }
}

async function main() {
  // 简单的并发池
  const queue = todo.slice();
  const workers = Array(CONCURRENCY).fill(0).map(async () => {
    while (queue.length > 0) {
      const w = queue.shift();
      await genOne(w);
      if ((stats.ok + stats.fail) % 50 === 0) {
        const elapsed = (Date.now() - start) / 1000;
        const rate = (stats.ok + stats.fail) / elapsed;
        const eta = (stats.total - stats.ok - stats.fail) / rate;
        console.error(`  [${stats.ok + stats.fail}/${stats.total}] ok=${stats.ok} fail=${stats.fail} rate=${rate.toFixed(1)}/s eta=${eta.toFixed(0)}s`);
      }
    }
  });
  await Promise.all(workers);
  const elapsed = (Date.now() - start) / 1000;
  console.error(`\nDone: ok=${stats.ok} fail=${stats.fail} in ${elapsed.toFixed(0)}s (${stats.ok / elapsed.toFixed(0)}/s)`);
  if (stats.errors.length > 0) {
    console.error('Errors (first 20):');
    stats.errors.slice(0, 20).forEach(e => console.error('  ' + JSON.stringify(e)));
  }
  // 写统计
  fs.writeFileSync('D:\\10-网页集合站\\tts\\stats.json', JSON.stringify(stats, null, 2));
}

main().catch(e => { console.error(e); process.exit(1); });
