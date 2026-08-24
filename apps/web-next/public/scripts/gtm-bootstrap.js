(function () {
  var bootstrapScript = document.currentScript;
  var gtmId = bootstrapScript && bootstrapScript.dataset.gtmId;

  if (!gtmId || window.__mwGtmBootstrapLoaded) {
    return;
  }

  window.__mwGtmBootstrapLoaded = true;
  window.dataLayer = window.dataLayer || [];
  window.dataLayer.push({
    "gtm.start": new Date().getTime(),
    event: "gtm.js"
  });

  var firstScript = document.getElementsByTagName("script")[0];
  var gtmScript = document.createElement("script");
  gtmScript.async = true;
  gtmScript.src =
    "https://www.googletagmanager.com/gtm.js?id=" + encodeURIComponent(gtmId);
  firstScript.parentNode.insertBefore(gtmScript, firstScript);
})();
