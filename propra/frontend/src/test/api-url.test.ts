import { describe, it, expect } from "vitest";
import fs from "fs";
import path from "path";

describe("AdvisorPage API URL configuration", () => {
  it("should not contain hardcoded onrender.com domain", () => {
    const advisorPagePath = path.join(__dirname, "../pages/AdvisorPage.tsx");
    const sourceCode = fs.readFileSync(advisorPagePath, "utf-8");
    const hasHardcodedUrl = sourceCode.includes("proplaw-graphrag.onrender.com");
    expect(hasHardcodedUrl).toBe(false);
  });

  it("should use import.meta.env.VITE_API_URL for API endpoint", () => {
    const advisorPagePath = path.join(__dirname, "../pages/AdvisorPage.tsx");
    const sourceCode = fs.readFileSync(advisorPagePath, "utf-8");
    const usesEnvVar = sourceCode.includes("import.meta.env.VITE_API_URL");
    expect(usesEnvVar).toBe(true);
  });
});
