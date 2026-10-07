// Open external links in page content in a new tab; site links stay in the current tab.
document$.subscribe(() => {
  for (const link of document.querySelectorAll(".md-content a[href]")) {
    if (link.hostname && link.hostname !== location.hostname) {
      link.target = "_blank";
      link.rel = "noopener";
    }
  }
});
