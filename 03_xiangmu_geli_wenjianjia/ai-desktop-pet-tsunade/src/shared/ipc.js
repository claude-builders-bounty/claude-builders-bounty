/**
 * 共享 IPC 通道定义与类型
 * 主进程与渲染进程通过 preload 脚本的 contextBridge 通信，
 * 所有通道名统一定义在此，避免字符串拼写错误。
 */
/** 所有 IPC 通道名 */
export const IPC_CHANNELS = {
    // 窗口控制
    WINDOW_DRAG: "window:drag",
    WINDOW_CLOSE: "window:close",
    WINDOW_MINIMIZE: "window:minimize",
    WINDOW_TOGGLE_DEVTOOLS: "window:toggle-devtools",
    WINDOW_SET_CLICK_THROUGH: "window:set-click-through",
    WINDOW_SET_ALWAYS_ON_TOP: "window:set-always-on-top",
    // 宠物状态
    PET_GET_STATE: "pet:get-state",
    PET_SET_STATE: "pet:set-state",
    PET_SET_MOOD: "pet:set-mood",
    PET_PLAY_ANIMATION: "pet:play-animation",
    PET_TOGGLE_CLICK_THROUGH: "pet:toggle-click-through",
    // 聊天
    CHAT_SEND: "chat:send",
    CHAT_GET_HISTORY: "chat:get-history",
    CHAT_CLEAR_HISTORY: "chat:clear-history",
    CHAT_STREAM: "chat:stream",
    // 设置
    SETTINGS_GET: "settings:get",
    SETTINGS_SET: "settings:set",
    SETTINGS_GET_ALL: "settings:get-all",
    SETTINGS_SET_ALL: "settings:set-all",
    // 系统监控
    MONITOR_START: "monitor:start",
    MONITOR_STOP: "monitor:stop",
    MONITOR_STATS: "monitor:stats",
    // 提醒
    REMINDER_LIST: "reminder:list",
    REMINDER_ADD: "reminder:add",
    REMINDER_REMOVE: "reminder:remove",
    REMINDER_TOGGLE: "reminder:toggle",
    // 数据库
    DB_GET_CONVERSATIONS: "db:get-conversations",
    DB_GET_AFFECTION: "db:get-affection",
    DB_SET_AFFECTION: "db:set-affection",
};
/** 错误码 */
export const ERROR_CODES = {
    LLM_API_ERROR: "LLM_API_ERROR",
    LLM_INVALID_CONFIG: "LLM_INVALID_CONFIG",
    DB_ERROR: "DB_ERROR",
    WINDOW_ERROR: "WINDOW_ERROR",
    INVALID_INPUT: "INVALID_INPUT",
    UNKNOWN: "UNKNOWN",
};
/** 结构化应用错误 */
export class AppError extends Error {
    code;
    isOperational;
    constructor(message, code = ERROR_CODES.UNKNOWN, isOperational = true) {
        super(message);
        this.name = "AppError";
        this.code = code;
        this.isOperational = isOperational;
        Error.captureStackTrace(this, this.constructor);
    }
}
