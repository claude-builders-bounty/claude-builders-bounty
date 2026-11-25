// sql.js 类型声明
declare module 'sql.js' {
  export interface ParamsCallback {
    (params: unknown[]): void;
  }

  export interface Database {
    exec(sql: string): QueryResults[];
    prepare(sql: string): Statement;
    export(): Uint8Array;
    close(): void;
    run(sql: string, params?: unknown[]): this;
    each(sql: string, params: unknown[], callback: ParamsCallback, done?: () => void): this;
  }

  export interface Statement {
    bind(params: unknown[]): this;
    get(): Row | undefined;
    all(): Row[];
    run(): this;
    reset(): this;
    free(): void;
    getAsObject(): Record<string, unknown> | undefined;
  }

  export interface QueryResults {
    columns: string[];
    values: unknown[][];
  }

  export type Row = unknown[];

  export interface SqlJsStatic {
    (): Promise<{ Database: new (data?: Uint8Array) => Database }>;
  }

  const initSqlJs: SqlJsStatic;
  export default initSqlJs;
}