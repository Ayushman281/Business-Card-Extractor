// Run after a hosted build, or against a separately deployed static directory.
import { mkdirSync, writeFileSync } from "node:fs";
import { resolve } from "node:path";

const value = (process.env.API_BASE_URL || "").trim();
let apiBaseUrl = "";
if (value) {
  const url = new URL(value);
  if (!["https:", "http:"].includes(url.protocol) || url.username || url.password || url.search || url.hash || url.pathname !== "/") {
    throw new Error("API_BASE_URL must be an HTTP(S) origin without credentials, a path, query or fragment.");
  }
  apiBaseUrl = url.origin;
}
const directory = resolve(process.argv[2] || "dist");
mkdirSync(directory, { recursive: true });
writeFileSync(resolve(directory, "app-config.json"), JSON.stringify({ apiBaseUrl }) + "\n");
console.log("Updated runtime API configuration in", directory);
