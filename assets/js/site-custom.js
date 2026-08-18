/* ==========================================================================
   Custom interactions: pub-figure lightbox, section scrollspy,
   sticky current-section bar, nav highlighting, back-to-top button
   ========================================================================== */
(function ($) {
  "use strict";

  $(document).ready(function () {

    /* ---------- 1. Publication figures: lightbox (works with .webp) ---------- */
    $("a[data-lightbox]").magnificPopup({
      type: "image",
      tLoading: "Loading image #%curr%...",
      gallery: {
        enabled: true,
        navigateByImgClick: true,
        preload: [0, 1]
      },
      image: {
        tError: '<a href="%url%">Image #%curr%</a> could not be loaded.'
      },
      removalDelay: 300,
      mainClass: "mfp-zoom-in",
      closeOnContentClick: true,
      midClick: true
    });

    /* ---------- 2. Section scrollspy + sticky current-section bar ---------- */

    // Build the section list from the masthead navigation anchors.
    // The nav labels are already localized (EN/ZH), so no DOM probing needed.
    var sections = [];
    $(".masthead__menu a[href*='#']").each(function () {
      var href = $(this).attr("href") || "";
      var hash = href.split("#")[1];
      if (!hash) return;
      var title = $.trim($(this).text()).replace(/\s+/g, " ");
      sections.push({ id: hash, title: title });
    });

    var $bar = $("#section-bar");
    var $barTitle = $("#section-bar .bar-title");
    var lastActiveId = null;

    function setActiveSection(id) {
      if (id === lastActiveId) return;
      lastActiveId = id;

      // nav highlighting (exact hash match)
      $(".masthead__menu-item").removeClass("active");
      $(".masthead__menu a").each(function () {
        var h = ($(this).attr("href") || "").split("#")[1];
        if (h && h === id) {
          $(this).closest(".masthead__menu-item").addClass("active");
        }
      });

      // sticky bar
      var sec = sections.filter(function (s) { return s.id === id; })[0];
      if (sec) {
        $barTitle.text(sec.title);
        $bar.attr("data-target", sec.id).addClass("visible");
      } else {
        $bar.removeClass("visible");
      }
    }

    function onScroll() {
      var top = $(window).scrollTop() + 90; // masthead offset
      var current = null;
      sections.forEach(function (s) {
        var $el = $("#" + s.id);
        if ($el.length && $el.offset().top <= top) {
          current = s;
        }
      });
      setActiveSection(current ? current.id : null);

      // back-to-top visibility
      $("#back-to-top").toggleClass("visible", $(window).scrollTop() > 400);
    }

    $(window).on("scroll", onScroll);
    onScroll();

    /* ---------- 3. Sticky bar click: jump back to section start ---------- */
    $bar.on("click", function () {
      var id = $(this).attr("data-target");
      if (!id) return;
      var $el = $("#" + id);
      if ($el.length) {
        $("html, body").animate({ scrollTop: $el.offset().top - 55 }, 300);
      }
    });

    /* ---------- 4. Back to top ---------- */
    $("#back-to-top").on("click", function () {
      $("html, body").animate({ scrollTop: 0 }, 400);
    });

  });
})(jQuery);
