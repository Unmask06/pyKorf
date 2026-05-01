// Fetches openapi.json from the running pyKorf server, then generates types.
// Falls back to cached file if server is unavailable.
import { writeFileSync, existsSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const ROOT = join(__dirname, '..');
const OUTPUT = join(ROOT, 'openapi.json');
const URL = 'http://localhost:8000/openapi.json';

async function main() {
  try {
    const resp = await fetch(URL);
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    const data = await resp.json();
    writeFileSync(OUTPUT, JSON.stringify(data, null, 2));
    const count = Object.keys(data.paths || {}).length;
    console.log(`\u2705 Fetched openapi.json from ${URL}`);
    console.log(`   Endpoints: ${count}`);
  } catch (err) {
    if (existsSync(OUTPUT)) {
      console.warn(`\u26A0\uFE0F  Server not running at ${URL}`);
      console.warn(`   Using cached ${OUTPUT}`);
    } else {
      console.error(`\u274C Cannot fetch ${URL} and no cached file exists.`);
      console.error(`   Start pyKorf server first: uv run pykorf`);
      process.exit(1);
    }
  }
}

main();
