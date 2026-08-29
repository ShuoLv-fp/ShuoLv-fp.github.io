import { jsonResponse, secureHeaders } from "./http.js";

export { WorkflowCoordinator } from "./coordinator.js";

const PUBLIC_ASSETS = new Map([
  ["/", "/login.html"],
  ["/login.html", "/login.html"],
  ["/login.js", "/login.js"],
  ["/style.css", "/style.css"]
]);

function coordinator(env) {
  const id = env.WORKFLOW_COORDINATOR.idFromName("primary");
  return env.WORKFLOW_COORDINATOR.get(id);
}

function coordinatorRequest(request, publicOrigin) {
  const headers = new Headers(request.headers);
  headers.set("x-phd-agent-origin", publicOrigin);
  return new Request(request, { headers });
}

function isKnownApi(path, method) {
  if (path === "/api/login") return method === "POST";
  if (path === "/api/session" || path === "/api/bootstrap" || path === "/api/export") {
    return method === "GET";
  }
  if (path === "/api/logout" || path === "/api/admin/import") return method === "POST";
  return method === "PUT" && /^\/api\/(faculty|artifacts)\/[^/]+$/.test(path);
}

function withSecurityHeaders(response) {
  const headers = new Headers(response.headers);
  for (const [key, value] of secureHeaders()) headers.set(key, value);
  return new Response(response.body, {
    status: response.status,
    statusText: response.statusText,
    headers
  });
}

async function serveAsset(request, env, assetPath) {
  if (!new Set(["GET", "HEAD"]).has(request.method)) {
    return jsonResponse({ error: "method not allowed" }, 405, { Allow: "GET, HEAD" });
  }
  const url = new URL(request.url);
  url.pathname = assetPath;
  const assetRequest = new Request(url, request);
  return withSecurityHeaders(await env.ASSETS.fetch(assetRequest));
}

async function hasSession(request, stub) {
  const headers = new Headers();
  const cookie = request.headers.get("cookie");
  if (cookie) headers.set("cookie", cookie);
  const response = await stub.fetch("https://coordinator.internal/internal/auth", { headers });
  return response.status === 204;
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const path = url.pathname;
    const stub = coordinator(env);

    if (path.startsWith("/data/")) return jsonResponse({ error: "not found" }, 404);

    if (path.startsWith("/api/")) {
      if (!isKnownApi(path, request.method)) return jsonResponse({ error: "not found" }, 404);
      return stub.fetch(coordinatorRequest(request, url.origin));
    }

    if (PUBLIC_ASSETS.has(path)) return serveAsset(request, env, PUBLIC_ASSETS.get(path));

    const protectedAsset = path === "/app"
      ? "/index.html"
      : path === "/index.html" || path === "/app.js" || path.startsWith("/logos/")
        ? path
        : null;
    if (protectedAsset) {
      if (!(await hasSession(request, stub))) return jsonResponse({ error: "unauthorized" }, 401);
      return serveAsset(request, env, protectedAsset);
    }

    return jsonResponse({ error: "not found" }, 404);
  }
};
