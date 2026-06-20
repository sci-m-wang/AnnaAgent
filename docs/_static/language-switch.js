(function () {
  function buildLinks() {
    var marker = "/AnnaAgent/";
    var path = window.location.pathname;
    var markerIndex = path.indexOf(marker);
    var base = markerIndex >= 0 ? path.slice(0, markerIndex + marker.length) : "/";
    var relative = path.indexOf(base) === 0 ? path.slice(base.length) : path.replace(/^\/+/, "");
    var isChinese = relative === "zh" || relative === "zh/" || relative.indexOf("zh/") === 0;
    var suffix = window.location.search + window.location.hash;
    var rest = isChinese ? relative.replace(/^zh\/?/, "") : relative;

    if (!rest) {
      rest = "";
    }

    return {
      isChinese: isChinese,
      englishHref: base + rest + suffix,
      chineseHref: base + "zh/" + rest + suffix
    };
  }

  function createButton(label, href, isActive) {
    var button = document.createElement("button");
    button.type = "button";
    button.className = "language-switcher__button";
    button.textContent = label;
    button.setAttribute("aria-pressed", isActive ? "true" : "false");
    if (isActive) {
      button.classList.add("active");
    }
    button.addEventListener("click", function () {
      if (!button.classList.contains("active")) {
        window.location.assign(href);
      }
    });
    return button;
  }

  function createSwitcher() {
    var links = buildLinks();
    var nav = document.createElement("nav");
    var label = document.createElement("span");
    nav.className = "language-switcher";
    nav.setAttribute("aria-label", "Language switcher");

    label.className = "language-switcher__label";
    label.textContent = links.isChinese ? "语言" : "Language";
    nav.appendChild(label);
    nav.appendChild(createButton("English", links.englishHref, !links.isChinese));
    nav.appendChild(createButton("中文", links.chineseHref, links.isChinese));
    document.body.appendChild(nav);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", createSwitcher);
  } else {
    createSwitcher();
  }
})();
