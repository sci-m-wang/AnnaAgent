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

  function createSwitcher() {
    var links = buildLinks();
    var nav = document.createElement("nav");
    nav.className = "language-switcher";
    nav.setAttribute("aria-label", "Language switcher");
    nav.innerHTML = [
      '<a class="' + (!links.isChinese ? "active" : "") + '" href="' + links.englishHref + '">English</a>',
      '<span aria-hidden="true"> / </span>',
      '<a class="' + (links.isChinese ? "active" : "") + '" href="' + links.chineseHref + '">中文</a>'
    ].join("");
    document.body.appendChild(nav);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", createSwitcher);
  } else {
    createSwitcher();
  }
})();
