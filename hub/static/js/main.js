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
});
