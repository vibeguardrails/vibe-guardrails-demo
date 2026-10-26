import os, json, time, urllib.request, sys
MODEL = "grok-4.20-0309-non-reasoning"
prompt = open("PROMPT.md").read()
rules = open("rules/AGENTS.md").read()
def call(messages):
    body = json.dumps({"model": MODEL, "messages": messages, "temperature": 0.7}).encode()
    req = urllib.request.Request("https://api.x.ai/v1/chat/completions", data=body,
        headers={"Authorization": "Bearer " + os.environ["XAI_API_KEY"], "Content-Type": "application/json"})
    r = json.load(urllib.request.urlopen(req, timeout=600))
    return r["choices"][0]["message"]["content"], r.get("usage"), r.get("model")
log = []
for cond in ["before", "after"]:
    for i in range(1, 4):
        msgs = [{"role": "user", "content": prompt}]
        if cond == "after":
            msgs.insert(0, {"role": "system", "content": "Project instructions (AGENTS.md in the repo root):\n\n" + rules})
        out, usage, model = call(msgs)
        open(f"{cond}/run-{i}.md", "w").write(out)
        log.append({"condition": cond, "run": i, "model": model, "temperature": 0.7, "usage": usage, "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())})
        print(cond, i, len(out), usage, flush=True)
json.dump(log, open("run-log.json", "w"), indent=2)
