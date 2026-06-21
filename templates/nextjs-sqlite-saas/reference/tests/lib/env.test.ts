import { afterEach, describe, expect, it, vi } from "vitest";

describe("env", () => {
  afterEach(() => {
    vi.unstubAllEnvs();
    vi.resetModules();
  });

  it("parses required env vars validated by Zod schema", async () => {
    const { env } = await import("@/lib/env");
    expect(env.DATABASE_URL).toBe(":memory:");
    expect(env.SESSION_SECRET.length).toBeGreaterThanOrEqual(32);
    expect(env.NEXT_PUBLIC_APP_URL).toMatch(/^https?:\/\//);
  });

  it("accepts file: and libsql: DATABASE_URL schemes", async () => {
    vi.stubEnv("DATABASE_URL", "file:./data/app.db");
    vi.stubEnv("SESSION_SECRET", "Test-Session-Secret-32-Chars-Minimum-X9");
    vi.stubEnv("NEXT_PUBLIC_APP_URL", "http://localhost:3000");
    vi.resetModules();

    const { env } = await import("@/lib/env");
    expect(env.DATABASE_URL).toBe("file:./data/app.db");
  });

  it("rejects DATABASE_URL without file:, libsql:, or :memory:", async () => {
    vi.stubEnv("DATABASE_URL", "postgres://localhost/db");
    vi.stubEnv("SESSION_SECRET", "Test-Session-Secret-32-Chars-Minimum-X9");
    vi.stubEnv("NEXT_PUBLIC_APP_URL", "http://localhost:3000");
    vi.resetModules();

    await expect(import("@/lib/env")).rejects.toThrow();
  });

  it("rejects SESSION_SECRET shorter than 32 characters", async () => {
    vi.stubEnv("DATABASE_URL", ":memory:");
    vi.stubEnv("SESSION_SECRET", "too-short");
    vi.stubEnv("NEXT_PUBLIC_APP_URL", "http://localhost:3000");
    vi.resetModules();

    await expect(import("@/lib/env")).rejects.toThrow();
  });

  it("rejects invalid NEXT_PUBLIC_APP_URL", async () => {
    vi.stubEnv("DATABASE_URL", ":memory:");
    vi.stubEnv("SESSION_SECRET", "Test-Session-Secret-32-Chars-Minimum-X9");
    vi.stubEnv("NEXT_PUBLIC_APP_URL", "not-a-url");
    vi.resetModules();

    await expect(import("@/lib/env")).rejects.toThrow();
  });
});
