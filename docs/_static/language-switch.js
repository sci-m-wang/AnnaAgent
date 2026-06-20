(function () {
  function buildLinks() {
    var path = window.location.pathname;
    var marker = "/AnnaAgent/";
    var markerIndex = path.indexOf(marker);
    var base = markerIndex >= 0 ? path.slice(0, markerIndex + marker.length) : "/";
    var relative = path.indexOf(base) === 0 ? path.slice(base.length) : path.replace(/^\/+/, "");
    var isZh = relative === "zh" || relative === "zh/" || relative.indexOf("zh/") === 0;
    var suffix = window.location.search + window.location.hash;
    var enHref;
    var zhHref;

    if (isZh) {
      var rest = relative.replace(/^zh\/?/, "");
      enHref = base + rest + suffix;
      zhHref = base + relative + suffix;
    } else {
      enHref = base + relative + suffix;
      zhHref = base + "zh/" + relative + suffix;
    }

    return { isZh: isZh, enHref: enHref, zhHref: zhHref };
  }

  function createSwitcher() {
    var links = buildLinks();
    var nav = document.createElement("nav");
    nav.className = "language-switcher";
    nav.setAttribute("aria-label", "Language switcher");
    nav.innerHTML = [
      '<a class="' + (!links.isZh ? "active" : "") + '" href="' + links.enHref + '">English</a>',
      '<span aria-hidden="true"> / </span>',
      '<a class="' + (links.isZh ? "active" : "") + '" href="' + links.zhHref + '">中文</a>'
    ].join("");
    document.body.appendChild(nav);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", createSwitcher);
  } else {
    createSwitcher();
  }
})();
