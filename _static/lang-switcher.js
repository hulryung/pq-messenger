(function () {
  var origin = window.location.origin;
  var hostname = window.location.hostname;
  var path = window.location.pathname;

  // Determine the base prefix.
  //   - Custom domain (pqc.hulryung.com, pqmsg.hulryung.com, etc.): no prefix.
  //   - GitHub Pages default URL (hulryung.github.io/<repo>/...):
  //       use the first path segment as the repo prefix.
  var base = '';
  if (hostname === 'hulryung.github.io') {
    var firstSeg = path.split('/').filter(Boolean)[0];
    if (firstSeg) base = '/' + firstSeg;
  }

  var rest = path.substring(base.length) || '/';
  var isKo = rest === '/ko' || rest === '/ko/' || rest.indexOf('/ko/') === 0;

  var otherPath, otherUrl, label, thisLang, otherLang;
  if (isKo) {
    var stripped = rest.substring(3) || '/';
    otherPath = base + stripped;
    label = 'English';
    thisLang = 'ko';
    otherLang = 'en';
  } else {
    otherPath = base + '/ko' + (rest === '/' ? '/' : rest);
    label = '한글';
    thisLang = 'en';
    otherLang = 'ko';
  }
  otherUrl = origin + otherPath;
  var thisUrl = origin + path;

  // Inject hreflang alternate links for SEO (Google cross-language indexing).
  function addAlt(lang, href) {
    var link = document.createElement('link');
    link.rel = 'alternate';
    link.hreflang = lang;
    link.href = href;
    document.head.appendChild(link);
  }
  addAlt(thisLang, thisUrl);
  addAlt(otherLang, otherUrl);
  addAlt('x-default', isKo ? otherUrl : thisUrl);

  function inject() {
    if (document.getElementById('lang-switcher')) return;
    var el = document.createElement('div');
    el.id = 'lang-switcher';
    el.style.cssText =
      'position:fixed;top:10px;right:12px;z-index:10000;' +
      'background:#fff;padding:6px 12px;border:1px solid rgba(0,0,0,0.15);' +
      'border-radius:6px;font-size:13px;' +
      'box-shadow:0 2px 6px rgba(0,0,0,0.1);';
    el.innerHTML =
      '<a href="' + otherUrl + '" style="color:#333;text-decoration:none;">' +
      '\u{1F310} ' + label + '</a>';
    document.body.appendChild(el);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', inject);
  } else {
    inject();
  }

  // Auto-redirect Korean-preferring users landing on the English intro (first visit only)
  var isEnIntro = !isKo && (
    rest === '/' || rest === '/intro.html' || rest === '/index.html'
  );
  if (isEnIntro && !sessionStorage.getItem('_lang_shown')) {
    sessionStorage.setItem('_lang_shown', '1');
    var lang = (navigator.language || navigator.userLanguage || '').toLowerCase();
    if (lang.indexOf('ko') === 0) {
      window.location.replace(base + '/ko/intro.html');
    }
  }
})();
