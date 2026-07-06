// Small progressive-enhancement helpers for the Collaboration Hub.
document.addEventListener("DOMContentLoaded", function () {
  // Confirm destructive actions.
  document.querySelectorAll("[data-confirm]").forEach(function (el) {
    el.addEventListener("submit", function (e) {
      if (!window.confirm(el.getAttribute("data-confirm"))) {
        e.preventDefault();
      }
    });
  });

  // On the project form, show the "actual outcomes" field only when Completed.
  var statusSel = document.getElementById("status-select");
  if (statusSel) {
    var toggle = function () {
      var completed = statusSel.value === "Completed";
      document.querySelectorAll("[data-when-completed]").forEach(function (n) {
        n.style.display = completed ? "" : "none";
      });
      document.querySelectorAll("[data-when-not-completed]").forEach(function (n) {
        n.style.display = completed ? "none" : "";
      });
    };
    statusSel.addEventListener("change", toggle);
    toggle();
  }

  // Toggle inline join-request message box.
  var joinToggle = document.getElementById("join-toggle");
  if (joinToggle) {
    joinToggle.addEventListener("click", function () {
      var box = document.getElementById("join-box");
      if (box) box.style.display = box.style.display === "none" ? "block" : "none";
    });
  }

  // Auto-dismiss flash messages after a few seconds.
  setTimeout(function () {
    document.querySelectorAll(".flash").forEach(function (f) {
      f.style.transition = "opacity .5s"; f.style.opacity = "0";
      setTimeout(function () { f.remove(); }, 500);
    });
  }, 6000);

  // Count-up animation for stat numbers that carry a data-count target.
  var reduce = window.matchMedia &&
    window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  document.querySelectorAll("[data-count]").forEach(function (el) {
    var target = parseInt(el.getAttribute("data-count"), 10);
    if (isNaN(target) || reduce) { return; }
    var start = null, dur = 1100;
    el.textContent = "0";
    function step(ts) {
      if (start === null) { start = ts; }
      var p = Math.min((ts - start) / dur, 1);
      var eased = 1 - Math.pow(1 - p, 3); // ease-out cubic
      el.textContent = Math.round(eased * target);
      if (p < 1) { requestAnimationFrame(step); }
    }
    requestAnimationFrame(step);
  });

  // Hero concept-graph: staggered build → hold → clear → rebuild (a loop).
  var net = document.querySelector(".hero-net");
  if (net && !reduce) {
    net.classList.add("anim");
    // document order = flow order: data → topics → concepts → outcome
    var nodes = net.querySelectorAll(".bub");
    var STAGGER = 180, HOLD = 3200, GAP = 1000;
    function build() {
      nodes.forEach(function (n, idx) {
        setTimeout(function () { n.classList.add("show"); }, idx * STAGGER);
      });
      setTimeout(function () {
        nodes.forEach(function (n) { n.classList.remove("show"); });
        setTimeout(build, GAP);          // reboot after the fade-out
      }, nodes.length * STAGGER + HOLD);
    }
    build();
  }
});
