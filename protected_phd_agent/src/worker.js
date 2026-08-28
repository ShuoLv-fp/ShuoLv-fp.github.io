import { jsonResponse } from "./http.js";

export { WorkflowCoordinator } from "./coordinator.js";

export default {
  async fetch() {
    return jsonResponse({ error: "service not initialized" }, 503);
  }
};
