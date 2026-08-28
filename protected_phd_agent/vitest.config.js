import { cloudflareTest } from "@cloudflare/vitest-pool-workers";
import { defineConfig } from "vitest/config";

export default defineConfig({
  plugins: [
    cloudflareTest({
      wrangler: { configPath: "./wrangler.jsonc" },
      miniflare: {
        bindings: {
          WORKFLOW_PASSWORD: "synthetic-test-password",
          SESSION_SECRET: "synthetic-session-secret-with-32-bytes",
          RATE_LIMIT_SECRET: "synthetic-rate-limit-secret-32-bytes",
          MIGRATION_SECRET: "synthetic-migration-secret-32-bytes"
        }
      }
    })
  ]
});
