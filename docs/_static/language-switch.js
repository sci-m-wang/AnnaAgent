(function () {
  var storageKey = "anna-docs-language";
  var labels = {
    "index.html": { en: "AnnaAgent Documentation", zh: "AnnaAgent 文档" },
    "quickstart.html": { en: "Quickstart", zh: "快速开始" },
    "configuration.html": { en: "Configuration", zh: "配置与 Workspace" },
    "cli-reference.html": { en: "CLI Reference", zh: "CLI 命令参考" },
    "deployment.html": { en: "Local SFT and vLLM Deployment", zh: "本地 SFT 与 vLLM 部署" },
    "data-memory.html": { en: "Case Data and Memory", zh: "案例数据与长期记忆" },
    "publishing.html": { en: "Project Publishing and Documentation", zh: "项目发布与文档站点" },
    "troubleshooting.html": { en: "Troubleshooting", zh: "故障排查" }
  };

  function preferredLanguage() {
    var saved = window.localStorage.getItem(storageKey);
    if (saved === "en" || saved === "zh") {
      return saved;
    }
    return /^zh/i.test(window.navigator.language || "") ? "zh" : "en";
  }

  function normalizePath(href) {
    var url;
    try {
      url = new URL(href, window.location.href);
    } catch (error) {
      return null;
    }
    if (url.origin !== window.location.origin) {
      return null;
    }
    var path = url.pathname;
    var marker = "/AnnaAgent/";
    var markerIndex = path.indexOf(marker);
    var relative = markerIndex >= 0 ? path.slice(markerIndex + marker.length) : path.replace(/^\/+/, "");
    if (!relative || relative === "/") {
      return "index.html";
    }
    if (relative.endsWith("/")) {
      return relative + "index.html";
    }
    return relative;
  }

  function currentPageKey() {
    return normalizePath(window.location.href) || "index.html";
  }

  function setRootLanguage(language) {
    document.documentElement.classList.toggle("language-zh", language === "zh");
    document.documentElement.classList.toggle("language-en", language === "en");
    document.documentElement.lang = language === "zh" ? "zh-CN" : "en";
  }

  function updateSwitcher(language) {
    document.querySelectorAll(".language-switcher button").forEach(function (button) {
      button.classList.toggle("active", button.dataset.language === language);
      button.setAttribute("aria-pressed", button.dataset.language === language ? "true" : "false");
    });
  }

  function updateSidebarLabels(language) {
    document.querySelectorAll('.sidebar-tree a[href], .related-pages a[href]').forEach(function (link) {
      var key = normalizePath(link.href);
      if (key && labels[key]) {
        link.textContent = labels[key][language];
      }
    });

    var brand = document.querySelector(".sidebar-brand-text");
    if (brand) {
      brand.textContent = labels["index.html"][language];
    }

    var caption = document.querySelector(".sidebar-tree .caption-text");
    if (caption) {
      caption.textContent = language === "zh" ? "目录" : "Contents";
    }
  }

  function updatePageTitle(language) {
    var key = currentPageKey();
    var label = labels[key] || labels["index.html"];
    document.title = label[language] + " - AnnaAgent";
    document.querySelectorAll("h1").forEach(function (heading) {
      if (!heading.closest(".lang")) {
        heading.textContent = label[language];
      }
    });
  }

  function updateLocalToc(language) {
    document.querySelectorAll('a[href^="#"]').forEach(function (link) {
      var id = decodeURIComponent(link.getAttribute("href").slice(1));
      if (!id) {
        return;
      }
      var target = document.getElementById(id);
      if (!target) {
        return;
      }
      var languageBlock = target.closest(".lang-en, .lang-zh");
      var listItem = link.closest("li") || link;
      if (!languageBlock) {
        listItem.hidden = false;
        return;
      }
      listItem.hidden = languageBlock.classList.contains("lang-zh") !== (language === "zh");
    });
  }

  function applyLanguage(language) {
    window.localStorage.setItem(storageKey, language);
    setRootLanguage(language);
    updateSwitcher(language);
    updateSidebarLabels(language);
    updatePageTitle(language);
    updateLocalToc(language);
  }

  function createSwitcher() {
    var nav = document.createElement("nav");
    nav.className = "language-switcher";
    nav.setAttribute("aria-label", "Language switcher");
    nav.innerHTML = [
      '<button type="button" data-language="en">English</button>',
      '<span aria-hidden="true"> / </span>',
      '<button type="button" data-language="zh">中文</button>'
    ].join("");
    nav.addEventListener("click", function (event) {
      var button = event.target.closest("button[data-language]");
      if (button) {
        applyLanguage(button.dataset.language);
      }
    });
    document.body.appendChild(nav);
    applyLanguage(preferredLanguage());
  }

  setRootLanguage(preferredLanguage());

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", createSwitcher);
  } else {
    createSwitcher();
  }
})();
