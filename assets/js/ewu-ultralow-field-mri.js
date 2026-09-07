(function () {
  "use strict";

  var filters = Array.prototype.slice.call(document.querySelectorAll(".paper-filter"));
  var papers = Array.prototype.slice.call(document.querySelectorAll(".paper-card"));
  var count = document.getElementById("paper-count");

  if (!filters.length || !papers.length || !count) return;

  var allowed = filters.map(function (button) {
    return button.getAttribute("data-filter");
  });

  function applyFilter(track, updateAddress) {
    var active = allowed.indexOf(track) >= 0 ? track : "all";
    var visible = 0;

    filters.forEach(function (button) {
      button.setAttribute(
        "aria-pressed",
        String(button.getAttribute("data-filter") === active)
      );
    });

    papers.forEach(function (paper) {
      var tracks = (paper.getAttribute("data-tracks") || "").split(/\s+/);
      var show = active === "all" || tracks.indexOf(active) >= 0;
      paper.hidden = !show;
      if (show) visible += 1;
    });

    count.textContent = visible + " / " + papers.length + " 篇";

    if (updateAddress && window.history && window.history.replaceState) {
      var params = new URLSearchParams(window.location.search);
      if (active === "all") params.delete("track");
      else params.set("track", active);
      var query = params.toString();
      window.history.replaceState(null, "", window.location.pathname + (query ? "?" + query : "") + window.location.hash);
    }
  }

  filters.forEach(function (button) {
    button.addEventListener("click", function () {
      applyFilter(button.getAttribute("data-filter"), true);
    });
  });

  var initial = new URLSearchParams(window.location.search).get("track") || "all";
  applyFilter(initial, false);
})();
