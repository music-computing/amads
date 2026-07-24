window.MathJax = {
  tex: {
    inlineMath: [['$', '$'], ['\\(', '\\)']],
    displayMath: [['$$', '$$'], ['\\[', '\\]']],
    processEscapes: true,
    processEnvironments: true
  },
  startup: {
    ready: () => {
      MathJax.startup.defaultReady();
      MathJax.startup.promise.then(() => {
        console.log('MathJax initial typesetting complete');
      });
    }
  }
};

// Re-render math when page content changes (for Material theme)
if (typeof document$ !== 'undefined') {
  document$.subscribe(({ body }) => {
    MathJax.typesetPromise([body]).then(() => {
      console.log('MathJax re-rendering complete');
    });
  });
}
