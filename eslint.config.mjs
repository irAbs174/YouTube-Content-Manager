import { defineConfig, globalIgnores } from "eslint/config";

export default defineConfig([
  // `backend/.venv` is created by `make install` — keep it out of the lint run.
  globalIgnores([".next/**", "out/**", "build/**", "next-env.d.ts", "backend/.venv/**"]),
]);
