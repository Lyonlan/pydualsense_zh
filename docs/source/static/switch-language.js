(function () {
  try {
    var path = window.location.pathname || "";
    var base = path.replace(/[?#].*$/, "");
    var parts = base.split("/").filter(Boolean);
    var idxZh = parts.indexOf("zh");
    var isZh = idxZh !== -1;
    var basename = parts.length ? parts[parts.length - 1] : "index.html";
    var supported = [
      "index.html",
      "usage.html",
      "api.html",
      "examples.html",
      "ds_enum.html",
      "ds_main.html",
      "ds_eventsystem.html",
    ];
    if (!supported.includes(basename)) {
      if (basename === "" || basename === "index.html") {
        basename = "index.html";
      } else {
        return;
      }
    }
    var altParts = parts.slice();
    if (isZh) {
      altParts.splice(idxZh, 1);
    } else {
      altParts.splice(altParts.length - 1, 0, "zh");
    }
    var alt = "/" + altParts.join("/");
    if (!alt.endsWith(".html")) {
      if (!alt.endsWith("/")) alt += "/";
      alt += "index.html";
    }
    var btn = document.createElement("a");
    btn.href = alt;
    btn.textContent = isZh ? "English" : "中文";
    btn.setAttribute("aria-label", "Switch language");
    btn.className = "lang-switch";
    document.addEventListener("DOMContentLoaded", function () {
      document.body.appendChild(btn);
    });
  } catch (e) {}
})();
