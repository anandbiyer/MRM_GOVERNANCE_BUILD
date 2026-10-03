// Mock-up parity harness (CLAUDE.md Part 0 → Review agents; owned by the mockup-parity-tester agent).
//
// Two projects run the same checklist twice:
//   mockup — the static HTML the customer has seen, opened over file://
//   app    — the running application on :5173 (start it first; this config never starts it)
//
// Not part of CI: the app project needs a running backend, frontend and seeded database.
import { defineConfig, devices } from "@playwright/test";
import path from "node:path";
import { pathToFileURL } from "node:url";

const REPO_ROOT = path.resolve(__dirname, "..", "..");

/** The mock-up is a single self-contained HTML file; file:// is enough, no server needed. */
export const MOCKUP_URL = pathToFileURL(
  path.join(REPO_ROOT, "C_Requirements", "_OLD", "MRM_Governance_MIS_Demo.html"),
).href;

const VIEWPORT = { width: 1440, height: 900 };

export default defineConfig({
  testDir: "./tests",
  // The app project shares one SQLite database and one business date: never run it in parallel.
  workers: 1,
  fullyParallel: false,
  forbidOnly: !!process.env.CI,
  reporter: [
    ["list"],
    ["html", { outputFolder: "playwright-report", open: "never" }],
    // The mockup-parity-tester reads this to build its report table.
    ["json", { outputFile: path.join(REPO_ROOT, "D_Reviews", "DC_mockup_review", "latest.json") }],
  ],
  use: {
    viewport: VIEWPORT,
    screenshot: "only-on-failure",
    trace: "retain-on-failure",
  },
  projects: [
    {
      name: "mockup",
      use: {
        ...devices["Desktop Chrome"],
        viewport: VIEWPORT,
        baseURL: MOCKUP_URL,
        // The mock-up reads prefers-reduced-motion (see its REDUCED constant) and renders each step
        // instantly instead of running the timed walkthrough, so screens are stable to assert on.
        reducedMotion: "reduce",
      },
    },
    {
      name: "app",
      use: {
        ...devices["Desktop Chrome"],
        viewport: VIEWPORT,
        // `localhost`, not `127.0.0.1`: AC_frontend/vite.config.ts sets no `host`, so Vite binds to
        // localhost only, which resolves to ::1 first on Windows — 127.0.0.1 refuses the connection.
        // (Part 0 and the agent spec say 127.0.0.1; that address does not answer.)
        baseURL: "http://localhost:5173",
      },
    },
  ],
});
