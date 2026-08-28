import { jsonResponse } from "./http.js";

export class WorkflowCoordinator {
  async fetch() {
    return jsonResponse({ error: "service not initialized" }, 503);
  }
}

export default {
  async fetch() {
    return jsonResponse({ error: "service not initialized" }, 503);
  }
};
