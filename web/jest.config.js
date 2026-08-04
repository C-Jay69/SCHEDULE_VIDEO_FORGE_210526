// Minimal Jest config for the videoforge-web package.
// We don't have full Next.js test infra set up — that's intentionally
// skipped to avoid pulling in jsdom + a heavier test runner that nobody
// uses today. This config runs plain TypeScript unit tests against
// lib/utils.ts and lib/auth.ts using ts-jest with a node environment.

module.exports = {
  testEnvironment: "node",
  roots: ["<rootDir>/tests"],
  testMatch: ["**/test_*.ts", "**/?(*.)+(spec|test).ts"],
  transform: {
    "^.+\\.tsx?$": [
      "ts-jest",
      {
        tsconfig: {
          jsx: "react",
          esModuleInterop: true,
          module: "commonjs",
          target: "es2020",
          moduleResolution: "node",
          resolveJsonModule: true,
          strict: false,
          skipLibCheck: true,
        },
      },
    ],
  },
  moduleNameMapper: {
    "^@/(.*)$": "<rootDir>/$1",
  },
};
