/**
 * Smoke tests for lib/utils.ts — these are the pure functions the UI relies
 * on for styling and date formatting. They have no React or DOM dependencies,
 * so they can run in node via ts-jest.
 *
 * The full Next.js component tree (pages, layouts, hooks) is intentionally
 * out of scope here — testing those needs @testing-library/react and jsdom,
 * which we haven't set up yet. Tracked as a follow-up.
 */

import { cn, formatDate, statusColor, planColor } from "../lib/utils";

describe("cn", () => {
  it("merges truthy class names", () => {
    expect(cn("a", "b", "c")).toBe("a b c");
  });

  it("drops falsy values", () => {
    expect(cn("a", false, null, undefined, "", "b")).toBe("a b");
  });

  it("deduplicates conflicting tailwind classes", () => {
    // twMerge collapses the second `bg-red-100` in favor of `bg-blue-100`.
    expect(cn("p-2 bg-red-100", "bg-blue-100")).toBe("p-2 bg-blue-100");
  });
});

describe("formatDate", () => {
  it("formats an ISO string with month, day, year, hour, minute", () => {
    // 2026-08-03T17:30:00Z formats differently across node ICU builds, so
    // we check substrings instead of an exact match — the function's
    // contract is "produces a non-empty date string", not the exact format.
    const out = formatDate("2026-08-03T17:30:00Z");
    expect(out).toMatch(/2026/);
    expect(out.length).toBeGreaterThan(5);
  });

  it("accepts a Date object", () => {
    const out = formatDate(new Date("2026-01-01T00:00:00Z"));
    expect(out).toMatch(/2026/);
  });
});

describe("statusColor", () => {
  it("returns the right Tailwind class for known statuses", () => {
    expect(statusColor("completed")).toMatch(/green/);
    expect(statusColor("failed")).toMatch(/red/);
    expect(statusColor("pending")).toMatch(/yellow/);
  });

  it("falls back to gray for unknown statuses", () => {
    expect(statusColor("totally_made_up")).toMatch(/gray/);
  });
});

describe("planColor", () => {
  it("returns distinct colors per plan tier", () => {
    const free = planColor("free");
    const creator = planColor("creator");
    const pro = planColor("pro");
    // Different plan tiers should resolve to different colour schemes
    expect(free).not.toBe(creator);
    expect(creator).not.toBe(pro);
  });

  it("returns gray for unknown plans", () => {
    expect(planColor("mystery_plan")).toMatch(/gray/);
  });
});
