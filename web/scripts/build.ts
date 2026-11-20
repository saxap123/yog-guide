/**
 * npm run build [-- --images=icons|full|none]   (or the IMAGES environment variable; default icons)
 * data step -> image step -> type check -> vite build. No network.
 */
import { spawnSync } from "node:child_process";

const arg = process.argv.find((a) => a.startsWith("--images="))?.split("=")[1];
const images = (arg ?? process.env.IMAGES ?? "icons").toLowerCase();
if (!["icons", "full", "none"].includes(images)) {
  console.error(`--images / IMAGES must be icons, full or none (got "${images}")`);
  process.exit(2);
}
const env = { ...process.env, IMAGES: images };
const run = (cmd: string, args: string[], shell = false) => {
  // node itself is called without a shell (its path may contain spaces); npx needs one on Windows
  const opts = { stdio: "inherit" as const, env };
  const r = shell ? spawnSync([cmd, ...args].join(" "), { ...opts, shell: true }) : spawnSync(cmd, args, opts);
  if (r.status !== 0) process.exit(r.status ?? 1);
};
run(process.execPath, ["scripts/prepare-data.ts"]);
run(process.execPath, ["scripts/prepare-images.ts"]);
run("npx", ["tsc", "--noEmit"], true);
run("npx", ["vite", "build"], true);
console.log(`built with IMAGES=${images}`);
