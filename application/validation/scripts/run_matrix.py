#!/usr/bin/env python3
"""
Batch runner for the persona-adherence validation matrix.

For each (attribute, env) probe task, run 1 positive + 1 negative persona trial
through Harbor (CAPI Opus 4.8), then LLM-judge each trajectory. Aggregate into a
per-cell result: did the positive persona express X, did the negative express Y.

Usage:
    python run_matrix.py [--attrs a,b] [--envs survey,chat] [--n 1]
      --n = personas per polarity (default 1 → 1 pos + 1 neg per cell)

Writes application/validation/results/matrix_results.json + prints a table.
Designed to be run in the background (survey/chat fast; web/osapp slow, ~2-5min).
"""
from __future__ import annotations
import argparse, json, os, re, subprocess, sys, time
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
TASKS = REPO / "application/validation/tasks"
RECIPES = REPO / "application/validation/recipes/_matrix"
RESULTS = REPO / "application/validation/results"
MANIFEST = REPO / "persona/datasets/validation-subset/manifest.json"
JUDGE = REPO / "application/validation/scripts/judge_adherence.py"

ATTRS = ["code-comment-style", "code-naming-verbosity", "code-summary-documentation",
         "cog-emoji-use", "cog-humor", "cog-politeness", "cog-storytelling",
         "cog-use-of-jargon", "cog-verbosity", "register"]
# slug (dashes) <-> attribute id (underscores)
def attr_id(slug): return slug.replace("-", "_")

ENVS = {
 "survey":      {"agent": "persona-json-survey",  "model": "anthropic/claude-opus-4-8", "extra": ""},
 "chat":        {"agent": "persona-claude-code",  "model": "claude-opus-4.8",           "extra": ""},
 "web":         {"agent": "persona-openhands-sdk","model": "openai/claude-opus-4.8",    "extra": "max_iterations: 20"},
 "osapp-linux": {"agent": "persona-computer-1",   "model": "openai/claude-opus-4.8",    "extra": "api_base: https://api.githubcopilot.com"},
}

def token():
    for f in ("/mnt/nvme/jintao/project/fastedit/fastedit/.env",
              "/mnt/nvme/jintao/project/adk-measurement/.env"):
        p = Path(f)
        if p.is_file():
            for ln in p.read_text().splitlines():
                if ln.startswith("GITHUB_COPILOT_TOKEN="):
                    return ln.split("=",1)[1].strip().strip("'\"")
    sys.exit("no token")

def personas_for(attr_slug):
    m = json.loads(MANIFEST.read_text())
    aid = attr_id(attr_slug)
    pos, neg = [], []
    for p in m["personas"]:
        for h in p["attribute_hits"]:
            if h["attribute"] == aid:
                (pos if h["polarity"]=="positive" else neg).append((p["persona_id"], h["value"]))
    return pos, neg

def env_of(base_env):  # env key used in task dir name
    return base_env

def run_trial(attr_slug, env, pol, pid, val, tok, idx=0):
    cfg = ENVS[env]
    task = f"probe-{env}_{attr_slug}"
    taskdir = TASKS / task
    if not taskdir.is_dir():
        return {"error": f"no task {task}"}
    job = f"mx-{env}-{attr_slug}-{pol}-{pid}"
    recipe = RECIPES / f"{job}.yaml"
    RECIPES.mkdir(parents=True, exist_ok=True)
    extra = f", {cfg['extra']}" if cfg["extra"] else ""
    recipe.write_text(
        f"job_name: {job}\njobs_dir: jobs\nn_attempts: 1\nn_concurrent_trials: 1\n"
        f"environment: {{ type: docker, delete: true }}\n"
        f"agents: [{{ name: {cfg['agent']}, model_name: {cfg['model']}, "
        f"kwargs: {{ persona_path: persona/datasets/validation-subset/persona_{pid}.yaml{extra} }} }}]\n"
        f"tasks: [{{ path: application/validation/tasks/{task} }}]\n")

    env_vars = dict(os.environ)
    env_vars["CAPI_API_KEY"] = tok; env_vars["CAPI_BASE_URL"] = "https://api.githubcopilot.com"
    env_vars["PYTHONPATH"] = ":".join([str(REPO), str(REPO/"environment/runtime"),
                                       str(REPO/"packages/playground/src"), str(REPO/"application/playground")])
    if env == "survey":
        env_vars["MATRIX_SURVEY_TASK_PATH"] = str(taskdir)
    if env in ("web","osapp-linux"):
        env_vars["OPENAI_API_KEY"] = tok; env_vars["OPENAI_BASE_URL"] = "https://api.githubcopilot.com"
        env_vars["LLM_API_KEY"] = tok; env_vars["LLM_BASE_URL"] = "https://api.githubcopilot.com"
    if env == "chat":
        env_vars.pop("ANTHROPIC_API_KEY", None)
        env_vars["ANTHROPIC_AUTH_TOKEN"] = tok; env_vars["ANTHROPIC_BASE_URL"] = "https://api.githubcopilot.com"

    subprocess.run(["rm","-rf",f"jobs/{job}"], cwd=REPO)
    to = 500 if env in ("web","osapp-linux") else 250
    try:
        subprocess.run(["uv","run","harbor","run","-c",f"application/validation/recipes/_matrix/{job}.yaml"],
                       cwd=REPO, env=env_vars, timeout=to,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except subprocess.TimeoutExpired:
        pass
    # judge
    try:
        r = subprocess.run(["python3", str(JUDGE), f"jobs/{job}",
                            "--attribute", attr_id(attr_slug), "--value", val],
                           cwd=REPO, env=env_vars, timeout=180,
                           capture_output=True, text=True)
        out = r.stdout
        m = re.search(r'"attribute_expressed":\s*(true|false)', out)
        expressed = (m.group(1)=="true") if m else None
        conf = re.search(r'"confidence":\s*([0-9.]+)', out)
        return {"expressed": expressed, "confidence": float(conf.group(1)) if conf else None,
                "persona": pid, "value": val, "job": job}
    except Exception as e:
        return {"error": str(e)[:100], "persona": pid, "job": job}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--attrs", default=",".join(ATTRS))
    ap.add_argument("--envs", default=",".join(ENVS))
    ap.add_argument("--n", type=int, default=1)
    ap.add_argument("--skip_done", action="store_true", help="skip cells whose shard already exists")
    ap.add_argument("--one", default="", help="run a single cell: env/attr/pol (for parallel dispatch)")
    args = ap.parse_args()

    if args.one:
        # spec: env/attr/pol/idx
        parts = args.one.split("/")
        env, a, pol = parts[0], parts[1], parts[2]
        idx = int(parts[3]) if len(parts) > 3 else 0
        tok = token()
        cells = RESULTS / "cells"; cells.mkdir(parents=True, exist_ok=True)
        pos, neg = personas_for(a)
        pool = pos if pol == "pos" else neg
        if len(pool) <= idx:
            print(f"no {pol}#{idx} persona for {a}"); return
        pid, val = pool[idx]
        shard = cells / f"{env}__{a}__{pol}__{idx}.json"
        if args.skip_done and shard.is_file():
            print(f"skip {args.one}"); return
        print(f"run {args.one} persona_{pid}", flush=True)
        res = run_trial(a, env, pol, pid, val, tok, idx)
        res.update({"attr": a, "env": env, "pol": pol})
        shard.write_text(json.dumps(res, ensure_ascii=False, indent=2))
        print(f"done {args.one}: expressed={res.get('expressed')}", flush=True)
        return
    attrs = args.attrs.split(","); envs = args.envs.split(",")
    tok = token()
    cells = RESULTS / "cells"
    cells.mkdir(parents=True, exist_ok=True)
    total = len(attrs)*len(envs)*2*args.n
    done = 0
    for a in attrs:
        pos, neg = personas_for(a)
        for env in envs:
            for pol, pool in (("pos",pos),("neg",neg)):
                for i, (pid, val) in enumerate(pool[:args.n]):
                    done += 1
                    # per-trial shard file → safe for parallel runners
                    shard = cells / f"{env}__{a}__{pol}__{i}.json"
                    if args.skip_done and shard.is_file():
                        print(f"[{done}/{total}] skip (done) {env}/{a}/{pol}", flush=True)
                        continue
                    print(f"[{done}/{total}] {env}/{a}/{pol} persona_{pid}", flush=True)
                    res = run_trial(a, env, pol, pid, val, tok)
                    res.update({"attr": a, "env": env, "pol": pol})
                    shard.write_text(json.dumps(res, ensure_ascii=False, indent=2))
    print("\nDONE. shards ->", cells)

if __name__ == "__main__":
    main()
