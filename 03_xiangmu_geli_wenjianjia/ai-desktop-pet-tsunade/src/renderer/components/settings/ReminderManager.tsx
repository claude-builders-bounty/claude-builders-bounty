/**
 * ReminderManager — 提醒管理
 *
 * 职责：
 * 1. 展示提醒列表（标题、内容、cron 表达式、启用状态、语音播报）
 * 2. 新建提醒：填写标题/内容/cron/是否语音
 * 3. 切换提醒启用/禁用、删除提醒
 * 4. 通过 zustand store 的 reminders slice 与 preload API 同步
 * 5. 不可变性：提醒数组通过 [...arr] / filter / map 生成新数组
 */

import { useCallback, useState } from "react";

import { useReminders } from "@/hooks/usePetApi";

/** ReminderManager 属性 */
export interface ReminderManagerProps {
  /** 是否可见 */
  visible: boolean;
  /** 关闭回调 */
  onClose: () => void;
}

/** 新建提醒表单字段 */
interface NewReminder {
  title: string;
  content: string;
  cron: string;
  voice: boolean;
}

/** 简单 cron 表达式校验（分钟 小时 日 月 周，共 5 位） */
function validateCron(cron: string): { valid: boolean; message?: string } {
  const trimmed = cron.trim();
  if (!trimmed) {
    return { valid: false, message: "cron 表达式不能为空" };
  }

  const parts = trimmed.split(/\s+/);
  if (parts.length !== 5) {
    return {
      valid: false,
      message: "cron 表达式应为 5 位：分钟 小时 日 月 周",
    };
  }

  const ranges: { min: number; max: number }[] = [
    { min: 0, max: 59 },   // 分钟
    { min: 0, max: 23 },   // 小时
    { min: 1, max: 31 },   // 日期
    { min: 1, max: 12 },   // 月份
    { min: 0, max: 6 },    // 星期
  ];

  for (let i = 0; i < 5; i++) {
    const part = parts[i];
    const { min, max } = ranges[i];
    const items = part.split(",");
    for (const item of items) {
      const segment = item.trim();
      if (segment === "*") continue;

      // 支持步进：*/n 或 base/n
      if (segment.includes("/")) {
        const [base, stepStr] = segment.split("/");
        const step = parseInt(stepStr, 10);
        if (!step || step <= 0) {
          return { valid: false, message: `第 ${i + 1} 位步进值非法：${segment}` };
        }
        const baseVal = base === "*" ? min : parseInt(base, 10);
        if (isNaN(baseVal) || baseVal < min || baseVal > max) {
          return {
            valid: false,
            message: `第 ${i + 1} 位基数超出范围 ${min}-${max}：${segment}`,
          };
        }
        continue;
      }

      // 支持范围：start-end
      if (segment.includes("-")) {
        const [startStr, endStr] = segment.split("-");
        const start = parseInt(startStr, 10);
        const end = parseInt(endStr, 10);
        if (
          isNaN(start) ||
          isNaN(end) ||
          start < min ||
          end > max ||
          start > end
        ) {
          return {
            valid: false,
            message: `第 ${i + 1} 位范围非法：${segment}`,
          };
        }
        continue;
      }

      // 单值
      const val = parseInt(segment, 10);
      if (isNaN(val) || val < min || val > max) {
        return {
          valid: false,
          message: `第 ${i + 1} 位值超出范围 ${min}-${max}：${segment}`,
        };
      }
    }
  }

  return { valid: true };
}

/** 提醒管理面板 */
export function ReminderManager({
  visible,
  onClose,
}: ReminderManagerProps) {
  const {
    reminders,
    fetchReminders,
    addReminder,
    removeReminder,
    toggleReminder,
  } = useReminders();
  const [isAdding, setIsAdding] = useState(false);
  const [draft, setDraft] = useState<NewReminder>({
    title: "",
    content: "",
    cron: "0 9 * * *",
    voice: false,
  });
  const [cronError, setCronError] = useState<string | undefined>(undefined);

  // 面板显示时拉取提醒列表
  useCallback(() => {
    void fetchReminders();
  }, [])();

  const handleInputChange = useCallback(
    (field: keyof NewReminder) => (e: React.ChangeEvent<HTMLInputElement>) => {
      setDraft((prev) => ({ ...prev, [field]: e.currentTarget.value }));
      if (field === "cron") {
        const result = validateCron(e.currentTarget.value);
        setCronError(result.valid ? undefined : result.message);
      }
    },
    []
  );

  const handleCheckboxChange = useCallback(
    (field: keyof NewReminder) => () => {
      setDraft((prev) => ({ ...prev, [field]: !prev[field] as boolean }));
    },
    []
  );

  const handleAdd = useCallback(() => {
    const cronResult = validateCron(draft.cron);
    if (!cronResult.valid) {
      setCronError(cronResult.message);
      return;
    }
    if (!draft.title.trim()) {
      setCronError("提醒标题不能为空");
      return;
    }
    setCronError(undefined);
    void addReminder({
      title: draft.title,
      content: draft.content,
      cron: draft.cron,
      enabled: true,
      voice: draft.voice,
    });
    setDraft({ title: "", content: "", cron: "0 9 * * *", voice: false });
    setIsAdding(false);
  }, [addReminder, draft]);

  const handleToggle = useCallback(
    (id: string) => {
      void toggleReminder(id);
    },
    [toggleReminder]
  );

  const handleRemove = useCallback(
    (id: string) => {
      void removeReminder(id);
    },
    [removeReminder]
  );

  if (!visible) {
    return null;
  }

  return (
    <div className="fixed inset-0 z-40 flex flex-col bg-slate-950/95 backdrop-blur-sm">
      <div className="flex items-center justify-between px-5 py-3 border-b border-slate-800 bg-slate-900/80">
        <h2 className="text-sm font-semibold text-slate-100">定时提醒</h2>
        <button
          type="button"
          onClick={onClose}
          className="px-3 py-1.5 text-xs text-slate-400 hover:text-white transition"
        >
          关闭
        </button>
      </div>

      <div className="flex-1 overflow-y-auto p-4 scrollbar-hide">
        {reminders.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-slate-500">
            <p className="text-sm">暂无定时提醒</p>
            <p className="text-xs mt-1 text-slate-600">点击“+”新建一条提醒</p>
          </div>
        ) : (
          <ul className="space-y-2">
            {reminders.map((reminder) => (
              <li
                key={reminder.id}
                className="flex items-center justify-between px-4 py-3 rounded-xl bg-slate-800/60 border border-slate-700/50"
              >
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <span
                      className={`font-medium text-sm ${
                        reminder.enabled
                          ? "text-slate-100"
                          : "text-slate-500 line-through"
                      }`}
                    >
                      {reminder.title}
                    </span>
                    {reminder.voice && (
                      <span className="text-[10px] px-1.5 py-0.5 rounded bg-blue-900/30 text-blue-400">
                        语音
                      </span>
                    )}
                  </div>
                  <p className="text-xs text-slate-400 mt-0.5">
                    {reminder.content || "（无内容）"}
                  </p>
                  <p className="text-[10px] text-slate-500 mt-0.5">
                    cron：{reminder.cron} &nbsp;•&nbsp;
                    {reminder.enabled ? "启用" : "禁用"} &nbsp;•&nbsp;
                    创建于 {new Date(reminder.createdAt).toLocaleString("zh-CN")}
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    onClick={() => handleToggle(reminder.id)}
                    className={`px-2.5 py-1 rounded text-xs transition ${
                      reminder.enabled
                        ? "bg-slate-700 text-slate-200 hover:bg-slate-600"
                        : "bg-indigo-600 text-white hover:bg-indigo-500"
                    }`}
                  >
                    {reminder.enabled ? "禁用" : "启用"}
                  </button>
                  <button
                    type="button"
                    onClick={() => handleRemove(reminder.id)}
                    className="px-2.5 py-1 rounded text-xs text-red-400 hover:bg-red-900/30 transition"
                  >
                    删除
                  </button>
                </div>
              </li>
            ))}
          </ul>
        )}

        {isAdding && (
          <div className="mt-4 p-4 bg-slate-800/50 rounded-xl border border-slate-700/50 space-y-3">
            <input
              value={draft.title}
              onChange={handleInputChange("title")}
              placeholder="提醒标题"
              className="w-full px-3 py-2 rounded bg-slate-900 border border-slate-600 text-slate-100 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
            <input
              value={draft.content}
              onChange={handleInputChange("content")}
              placeholder="提醒内容（可选）"
              className="w-full px-3 py-2 rounded bg-slate-900 border border-slate-600 text-slate-100 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
            <div className="space-y-1">
              <label className="block text-xs text-slate-400 mb-1">cron 表达式</label>
              <input
                value={draft.cron}
                onChange={handleInputChange("cron")}
                placeholder="如 0 9 * * *（每天 9:00）"
                className="w-full px-3 py-2 rounded bg-slate-900 border border-slate-600 text-slate-100 focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
              {cronError && (
                <p className="text-[10px] text-red-400">{cronError}</p>
              )}
            </div>
            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={draft.voice}
                onChange={handleCheckboxChange("voice")}
                className="rounded bg-slate-900 border-slate-600 text-indigo-600 focus:ring-indigo-500"
              />
              <label className="text-xs text-slate-300">语音播报</label>
            </div>
            <div className="flex justify-end gap-2">
              <button
                type="button"
                onClick={() => {
                  setIsAdding(false);
                  setCronError(undefined);
                }}
                className="px-4 py-1.5 rounded text-xs text-slate-400 hover:text-white transition"
              >
                取消
              </button>
              <button
                type="button"
                onClick={handleAdd}
                className="px-4 py-1.5 rounded text-xs bg-indigo-600 text-white hover:bg-indigo-500 transition"
              >
                新建
              </button>
            </div>
          </div>
        )}
      </div>

      <div className="p-3 border-t border-slate-800 bg-slate-950/90">
        <button
          type="button"
          onClick={() => setIsAdding(true)}
          className="flex w-full items-center justify-center gap-2 px-4 py-2 rounded-xl bg-indigo-600/10 border border-indigo-500/30 text-indigo-400 text-sm hover:bg-indigo-600/20 hover:text-indigo-300 transition"
        >
          + 新建提醒
        </button>
      </div>
    </div>
  );
}

ReminderManager.displayName = "ReminderManager";
