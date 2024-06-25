<!-- Hotjar Tracking Code for my site -->

(function (h, o, t, j, a, r) {
    h.hj = h.hj || function () {
        (h.hj.q = h.hj.q || []).push(arguments)
    };
    h._hjSettings = {hjid: 3418401, hjsv: 6};
    a = o.getElementsByTagName('head')[0];
    r = o.createElement('script');
    r.async = 1;
    r.src = t + h._hjSettings.hjid + j + h._hjSettings.hjsv;
    a.appendChild(r);
})(window, document, 'https://static.hotjar.com/c/hotjar-', '.js?sv=');

<!-- microsoft clarity -->
(function (c, l, a, r, i, t, y) {
    c[a] = c[a] || function () {
        (c[a].q = c[a].q || []).push(arguments)
    };
    t = l.createElement(r);
    t.async = 1;
    t.src = "https://www.clarity.ms/tag/" + i;
    y = l.getElementsByTagName(r)[0];
    y.parentNode.insertBefore(t, y);
})
(window, document, "clarity", "script", "mxnjub5utr"
);

<!-- Google tag (gtag.js) -->
let imported = document.createElement('script');
imported.async = true;
imported.src = 'https://www.googletagmanager.com/gtag/js?id=G-20SXF8539L';
document.head.appendChild(imported);

window.dataLayer = window.dataLayer || [];

function gtag() {
    dataLayer.push(arguments);
}

gtag('js', new Date());

gtag('config', 'G-20SXF8539L');

