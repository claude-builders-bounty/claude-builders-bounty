import json

preset = {
  "description": "RimTalk Aether-Maya Fusion Preset -- Psychological depth + jailbreak + NSFW + literary style + full rule engine + safety boundaries (全中文强制版)",
  "entries": [],
  "name": "RimTalk_Aether_Maya_Full_CN",
  "version": 1
}

with open(r"D:/Ai/Agent/gongzuoqu/03_xiangmu_geli_wenjianjia/rimtalk-integration/RimTalk_Aether_Maya_Full_CN.json", "w", encoding="utf-8") as f:
    json.dump(preset, f, ensure_ascii=False, indent=2)

print("Base structure written")