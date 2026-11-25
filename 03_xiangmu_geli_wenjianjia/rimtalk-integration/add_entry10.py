import json

with open(r"D:/Ai/Agent/gongzuoqu/03_xiangmu_geli_wenjianjia/rimtalk-integration/RimTalk_Aether_Maya_Full_CN.json", "r", encoding="utf-8") as f:
    preset = json.load(f)

preset['entries'].append({
  "name": "入植者档案注入",
  "role": "System",
  "position": "Relative",
  "enabled": True,
  "inChatDepth": 0,
  "isMainChatHistory": False,
  "customRole": "",
  "content": "[入植者档案 -- Scriban 模板]\n\n{{~ capture nl ~}}\n{{~ \"\" ~}}\n{{~ end ~}}\n\n{{ for p in pawns }}\n# 档案: {{ p.name }}\n全名: {{ p.fullname }}\n性别: {{ p.gender }}\n年龄: {{ p.age }}\n派系: {{ p.faction }}\n{{~ \n  profile_text = p.profile | StripFormattingTags | string.replace \"Memory:\" \"当前情绪修正:\" \n~}}\n{{- for line in (profile_text | string.split nl | array.offset 2) }}\n{{ line }}\n{{- end }}\n\n# {{ p.name }} 当前活动:\n{{ p.job | string.capitalize | StripFormattingTags }}\n\n# {{ p.name }} 持有物品:\n{{~ if p.inventory.innerContainer.Count > 0 ~}}\n{{- for line in p.inventory.innerContainer -}}\n{{ line.LabelCap | StripFormattingTags }}\n{{ end -}}\n{{~ else ~}}\n- (无持有物)\n{{~ end ~}}\n\n# {{ p.name }} 需求:\n心情: {{ p.needs.mood.MoodString }}\n{{ for need in p.needs.AllNeeds | array.offset 1 -}}{{- if need.CurCategory | string.size > 0 -}}{{ need.Def }}: {{ need.CurCategory }}\n{{ end }}{{ end }}\n\n# {{ p.name }} 状态与资格\n是殖民者: {{ p.IsColonist }}\n是婴儿: {{ IsBaby p }}\n是访客: {{ IsVisitor p }}\n是敌人: {{ IsEnemy p }}\n是奴隶: {{ p.IsSlave }}\n是囚犯: {{ p.IsPrisoner }}\n战斗中: {{ IsInCombat p }}\n危险中: {{ IsInDanger p }}\n可对话: {{ IsTalkEligible p }}\n\n## {{ p.name }} 心理档案（隐性 -- 驱动所有输出）:\n{{~ \n  # 安全访问：先查父对象，再取字段\n  if p.psychProfile != null\n    attachment = p.psychProfile.attachment\n    defense_primary = p.psychProfile.defensePrimary\n    defense_secondary = p.psychProfile.defenseSecondary\n    schemas = p.psychProfile.schemas\n    needs = p.psychProfile.needs\n    moral = p.psychProfile.moralCompass\n  else\n    attachment = \"安全型\"\n    defense_primary = \"压抑\"\n    defense_secondary = \"幽默\"\n    schemas = [\"情感剥夺\", \"缺陷/羞耻\"]\n    needs = [\"安全\", \"连接\", \"自主\"]\n    moral = \"忠诚优于普世：血缘优先\"\n  end\n~}}\n依恋: {{ attachment }}\n主防御: {{ defense_primary }} | 次防御: {{ defense_secondary }}\n核心图式: {{ schemas | array.join \", \" }}\n核心需求: {{ needs | array.join \", \" }}\n道德指针: {{ moral }}\n\n## {{ p.name }} 近期记忆与视角 -- 仅供参考:\n\n# 内在视角\n{{- for line in (StripFormattingTags p.et_thoughts | string.split nl | array.offset 1) }}\n{{ line }}\n{{- end }}\n\n# 按时间事件\n{{ p.memory }}\n\n# {{ p.name }} 位置与周围\n位置: {{ p.location }}\n环境美观: {{ p.beauty }}\n地形: {{ p.terrain }}\n洁净度: {{ p.cleanliness }}\n{{ p.name }} 周围事物:\n{{- for line in p.surroundings | string.split nl }}\n- {{ line }}\n{{- end }}\n{{ end -}}"
})

with open(r"D:/Ai/Agent/gongzuoqu/03_xiangmu_geli_wenjianjia/rimtalk-integration/RimTalk_Aether_Maya_Full_CN.json", "w", encoding="utf-8") as f:
    json.dump(preset, f, ensure_ascii=False, indent=2)

print("Entry 10 added")