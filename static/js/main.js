/* SlotBook JavaScript. Each block below is one feature. */
(function () {
  "use strict";
  var root = document.documentElement;
  var $ = function (s, c) { return (c || document).querySelector(s); };
  var $$ = function (s, c) { return Array.prototype.slice.call((c || document).querySelectorAll(s)); };
  function store(key, value) { try { if (value === undefined) { return localStorage.getItem(key); } localStorage.setItem(key, value); } catch (e) { return null; } }

  /* 1. Loading animation: hide the overlay when the page has loaded */
  function hideLoader() { var l = $("#page-loader"); if (l) { l.classList.add("hide"); } }
  window.addEventListener("load", hideLoader);
  setTimeout(hideLoader, 3000); // safety: never block the page

  /* 2. Dark mode toggle (remembered in the browser) */
  var themeBtn = $("#theme-toggle");
  function setTheme(t) { root.setAttribute("data-theme", t); store("theme", t); if (themeBtn) { themeBtn.textContent = t === "dark" ? "Light" : "Dark"; } }
  if (themeBtn) {
    themeBtn.textContent = root.getAttribute("data-theme") === "dark" ? "Light" : "Dark";
    themeBtn.addEventListener("click", function () { setTheme(root.getAttribute("data-theme") === "dark" ? "light" : "dark"); });
  }

  /* 3. Mobile menu */
  var menuBtn = $("#menu-toggle"), nav = $("#site-nav");
  if (menuBtn && nav) {
    menuBtn.addEventListener("click", function () {
      var open = nav.classList.toggle("open");
      menuBtn.setAttribute("aria-expanded", open ? "true" : "false");
    });
  }

  /* 4. Scroll progress bar, sticky header shadow, back-to-top button */
  var bar = $("#scroll-progress"), header = $(".site-header"), topBtn = $("#back-to-top");
  function onScroll() {
    var h = document.documentElement, max = h.scrollHeight - h.clientHeight;
    if (bar) { bar.style.width = (max > 0 ? (h.scrollTop / max) * 100 : 0) + "%"; }
    if (header) { header.classList.toggle("scrolled", h.scrollTop > 10); }
    if (topBtn) { topBtn.classList.toggle("show", h.scrollTop > 400); }
  }
  window.addEventListener("scroll", onScroll, { passive: true }); onScroll();
  if (topBtn) { topBtn.addEventListener("click", function () { window.scrollTo({ top: 0, behavior: "smooth" }); }); }

  /* 5. Cookie banner */
  var cookie = $("#cookie-banner");
  if (cookie && !store("cookieChoice")) { cookie.classList.add("show"); }
  $$("[data-cookie]").forEach(function (b) {
    b.addEventListener("click", function () { store("cookieChoice", b.getAttribute("data-cookie")); cookie.classList.remove("show"); });
  });

  /* 6. Copy buttons: <button data-copy="text to copy"> */
  $$("[data-copy]").forEach(function (b) {
    b.addEventListener("click", function () {
      var text = b.getAttribute("data-copy") === "page-url" ? window.location.href : b.getAttribute("data-copy");
      var old = b.textContent;
      function done() { b.textContent = "Copied!"; setTimeout(function () { b.textContent = old; }, 1500); }
      if (navigator.clipboard) { navigator.clipboard.writeText(text).then(done); }
      else { var t = document.createElement("textarea"); t.value = text; document.body.appendChild(t); t.select(); document.execCommand("copy"); t.remove(); done(); }
    });
  });

  /* 7. Print buttons */
  $$("[data-print]").forEach(function (b) { b.addEventListener("click", function () { window.print(); }); });

  /* 8. Password visibility toggle */
  $$("input[type=password]").forEach(function (input) {
    var wrap = document.createElement("div"); wrap.className = "pw-wrap";
    input.parentNode.insertBefore(wrap, input); wrap.appendChild(input);
    var btn = document.createElement("button"); btn.type = "button"; btn.className = "pw-toggle"; btn.textContent = "Show";
    btn.setAttribute("aria-label", "Show or hide password"); wrap.appendChild(btn);
    btn.addEventListener("click", function () {
      var hidden = input.type === "password"; input.type = hidden ? "text" : "password"; btn.textContent = hidden ? "Hide" : "Show";
    });
  });

  /* 9. Confirmation modal: <form class="js-confirm" data-confirm="Are you sure?"> */
  var dialog = $("#confirm-dialog"), pendingForm = null;
  $$("form.js-confirm").forEach(function (form) {
    form.addEventListener("submit", function (e) {
      if (!dialog || typeof dialog.showModal !== "function") { if (!window.confirm(form.getAttribute("data-confirm"))) { e.preventDefault(); } return; }
      e.preventDefault(); pendingForm = form;
      $("#confirm-text").textContent = form.getAttribute("data-confirm") || "Are you sure?";
      dialog.showModal();
    });
  });
  if (dialog) {
    $("#confirm-yes").addEventListener("click", function () { dialog.close(); if (pendingForm) { pendingForm.submit(); } });
    $("#confirm-no").addEventListener("click", function () { dialog.close(); pendingForm = null; });
  }

  /* 10. Loading state on submit buttons (stops double clicks) */
  $$("form:not(.js-confirm):not(.search-form)").forEach(function (form) {
    form.addEventListener("submit", function () {
      var b = $("button[type=submit]", form); if (b) { b.classList.add("loading"); }
    });
  });

  /* 11. Form error state: mark inputs that have errors */
  $$(".errorlist").forEach(function (list) {
    var p = list.closest("p, div"); if (p) { p.classList.add("has-error"); var i = $("input, select, textarea", p); if (i) { i.setAttribute("aria-invalid", "true"); } }
  });

  /* 12. Messages fade out after a while (form success state) */
  $$(".message.success").forEach(function (m) { setTimeout(function () { m.style.opacity = "0"; }, 6000); });

  /* 13. Reveal on scroll (smooth animation) */
  var reveals = $$(".reveal");
  if ("IntersectionObserver" in window) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) { if (en.isIntersecting) { en.target.classList.add("visible"); io.unobserve(en.target); } });
    }, { threshold: 0.12 });
    reveals.forEach(function (el) { io.observe(el); });
  } else { reveals.forEach(function (el) { el.classList.add("visible"); }); }
})();
