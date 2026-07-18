(function () {
  var input = document.getElementById("search-input");
  var results = document.getElementById("search-results");
  if (!input || !results) return;

  var data = null;
  fetch("data/teaser.json").then(function (r) { return r.json(); }).then(function (d) { data = d; });

  function esc(s) {
    var div = document.createElement("div");
    div.textContent = s || "";
    return div.innerHTML;
  }

  function render(list) {
    if (!list.length) {
      results.innerHTML = '<p class="empty">Ingen treff. Prøv et annet merke, modell eller feilkode.</p>';
      return;
    }
    results.innerHTML = list.slice(0, 30).map(function (e) {
      var codeBit = e.code ? " · " + esc(e.code) : "";
      return '<a href="' + e.u.slice(1) + '"><strong>' + esc(e.b) + (e.m ? " " + esc(e.m) : "") +
        '</strong> — ' + esc(e.s) + codeBit + '</a>';
    }).join("");
  }

  var timer;
  input.addEventListener("input", function () {
    clearTimeout(timer);
    var q = input.value.trim().toLowerCase();
    timer = setTimeout(function () {
      if (!data) return;
      if (!q) { results.innerHTML = ""; return; }
      var hits = data.filter(function (e) {
        return (e.t + " " + e.b + " " + e.m + " " + e.s + " " + (e.code || "")).toLowerCase().indexOf(q) !== -1;
      });
      render(hits);
    }, 120);
  });
})();
