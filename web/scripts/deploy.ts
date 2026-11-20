/**
 * npm run deploy — publish web/dist to the gh-pages branch of the repository's `origin` (GitHub Pages).
 *
 * The site is built locally (`npm run build`, IMAGES=icons): GitHub Actions cannot build it, the game
 * files it reads are only on this computer. The branch gets one commit per deploy (force-pushed), so
 * old game images do not pile up in its history.
 *
 * Refuses to publish a dist/ built with IMAGES=full (full portraits are for local builds only).
 */
import { spawnSync } from "node:child_process";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";

const WEB = path.resolve(import.meta.dirname, "..");
const ROOT = path.resolve(WEB, "..");
const DIST = path.join(WEB, "dist");
const BRANCH = "gh-pages";

const die = (msg: string): never => {
  console.error(`deploy: ${msg}`);
  process.exit(1);
};
const git = (args: string[], cwd = ROOT, quiet = false) => {
  const r = spawnSync("git", args, { cwd, encoding: "utf8", stdio: quiet ? "pipe" : ["ignore", "inherit", "inherit"] });
  if (r.status !== 0) die(`git ${args.join(" ")} failed${quiet ? `: ${r.stderr}` : ""}`);
  return (r.stdout ?? "").trim();
};

if (!fs.existsSync(path.join(DIST, "index.html"))) die("web/dist/index.html not found — run npm run build first");
const manifest = JSON.parse(fs.readFileSync(path.join(WEB, "src", "generated", "images.json"), "utf8"));
if (manifest.mode === "full" || fs.existsSync(path.join(DIST, "img", "portrait"))) {
  die("dist/ was built with IMAGES=full (full portraits) — rebuild with npm run build (IMAGES=icons)");
}

const remote = git(["remote", "get-url", "origin"], ROOT, true);
const sha = git(["rev-parse", "--short", "HEAD"], ROOT, true);
const dirty = git(["status", "--porcelain"], ROOT, true) ? " (uncommitted changes)" : "";
const name = git(["config", "user.name"], ROOT, true);
const email = git(["config", "user.email"], ROOT, true);

const tmp = fs.mkdtempSync(path.join(os.tmpdir(), "yog-pages-"));
try {
  fs.cpSync(DIST, tmp, { recursive: true });
  fs.writeFileSync(path.join(tmp, ".nojekyll"), ""); // serve files as they are (no Jekyll)
  git(["init", "-q", "-b", BRANCH], tmp);
  git(["add", "-A"], tmp);
  git(["-c", `user.name=${name}`, "-c", `user.email=${email}`, "commit", "-q", "-m",
    `Deploy site from ${sha}${dirty}\n\nBuilt locally with IMAGES=${manifest.mode}.`], tmp);
  git(["push", "--force", "-q", remote, `${BRANCH}:${BRANCH}`], tmp);
  console.log(`deployed web/dist (${sha}${dirty}, IMAGES=${manifest.mode}) to ${remote} branch ${BRANCH}`);
} finally {
  fs.rmSync(tmp, { recursive: true, force: true });
}
