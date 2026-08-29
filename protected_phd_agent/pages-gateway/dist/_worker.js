export default {
  fetch(request, env) {
    return env.PHD_AGENT_SERVICE.fetch(request);
  }
};
