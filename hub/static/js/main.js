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

  // Flash toasts: dismiss on click, or after a while. Only the floating
  // toasts — inline .flash notices on pages (e.g. "You're signed up") stay.
  var dismiss = function (f) {
    f.style.transition = "opacity .4s"; f.style.opacity = "0";
    setTimeout(function () { f.remove(); }, 400);
  };
  document.querySelectorAll(".toasts .flash").forEach(function (f) {
    var btn = f.querySelector(".toast-close");
    if (btn) { btn.addEventListener("click", function () { dismiss(f); }); }
    // Errors and warnings stay until closed; confirmations fade after 8s.
    if (!/flash-(danger|warning)/.test(f.className)) {
      setTimeout(function () { dismiss(f); }, 8000);
    }
  });

  // "Copy link" buttons (e.g. the calendar feed).
  document.querySelectorAll("[data-copy]").forEach(function (btn) {
    btn.addEventListener("click", function () {
      var text = btn.getAttribute("data-copy");
      var done = function () {
        var old = btn.textContent;
        btn.textContent = "Copied ✓";
        setTimeout(function () { btn.textContent = old; }, 2000);
      };
      if (navigator.clipboard) {
        navigator.clipboard.writeText(text).then(done, function () { window.prompt("Copy this link:", text); });
      } else {
        window.prompt("Copy this link:", text);
      }
    });
  });

  // Close the account menu when clicking elsewhere.
  var menu = document.querySelector(".user-menu");
  if (menu) {
    document.addEventListener("click", function (e) {
      if (menu.open && !menu.contains(e.target)) { menu.open = false; }
    });
  }

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

  // Hero "match": light a clinical question and an AI expertise, draw the two
  // links into the centre, and name the project they form. Loops through pairs.
  var match = document.querySelector(".hero-match");
  if (match) {
    var pairs = JSON.parse(match.getAttribute("data-pairs"));
    var lefts = match.querySelectorAll(".m-left");
    var rights = match.querySelectorAll(".m-right");
    var pathL = match.querySelector(".m-path-l");
    var pathR = match.querySelector(".m-path-r");
    var card = match.querySelector(".m-card");
    var title = match.querySelector(".m-title");
    var pulse = match.querySelector(".m-pulse");

    var curve = function (x1, y1, x2, y2) {
      var mx = (x1 + x2) / 2;
      return "M" + x1 + "," + y1 + " C" + mx + "," + y1 + " " + mx + "," + y2 + " " + x2 + "," + y2;
    };
    var draw = function (path, node, endX) {
      var x = +node.getAttribute("data-x"), y = +node.getAttribute("data-y");
      path.setAttribute("d", curve(x, y, endX, 240));
      var len = path.getTotalLength();
      path.style.transition = "none";
      path.style.strokeDasharray = len;
      path.style.strokeDashoffset = len;
      path.style.opacity = 1;
      path.getBoundingClientRect();            // flush so the transition runs
      path.style.transition = "stroke-dashoffset .8s ease, opacity .4s ease";
      path.style.strokeDashoffset = 0;
    };
    var show = function (p) {
      lefts[p[0]].classList.add("lit");
      rights[p[1]].classList.add("lit");
      title.textContent = p[2];
    };

    if (reduce) {
      show(pairs[0]);
    } else {
      match.classList.add("anim");
      var i = 0;
      var step = function () {
        var p = pairs[i++ % pairs.length];
        match.querySelectorAll(".lit").forEach(function (n) { n.classList.remove("lit"); });
        pathL.style.opacity = 0; pathR.style.opacity = 0;
        card.classList.add("dim");
        setTimeout(function () { lefts[p[0]].classList.add("lit"); }, 350);
        setTimeout(function () { rights[p[1]].classList.add("lit"); }, 700);
        setTimeout(function () {
          draw(pathL, lefts[p[0]], 195);
          draw(pathR, rights[p[1]], 365);
        }, 900);
        setTimeout(function () {
          title.textContent = p[2];
          card.classList.remove("dim");
          pulse.classList.remove("go"); pulse.getBoundingClientRect(); pulse.classList.add("go");
        }, 1750);
        setTimeout(step, 4300);
      };
      step();
    }
  }

  // Hackathon countdown (only ticks once the exact start time is configured).
  var cd = document.querySelector(".countdown[data-exact='1']");
  if (cd) {
    var target = new Date(cd.getAttribute("data-target")).getTime();
    var cells = {};
    cd.querySelectorAll("[data-cd]").forEach(function (b) { cells[b.getAttribute("data-cd")] = b; });
    var tick = function () {
      var s = Math.max(0, Math.floor((target - Date.now()) / 1000));
      cells.d.textContent = Math.floor(s / 86400);
      cells.h.textContent = String(Math.floor(s % 86400 / 3600)).padStart(2, "0");
      cells.m.textContent = String(Math.floor(s % 3600 / 60)).padStart(2, "0");
      cells.s.textContent = String(s % 60).padStart(2, "0");
    };
    tick();
    setInterval(tick, 1000);
  }
});
