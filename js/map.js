/* map.js — SVG map rendering on top of world-atlas TopoJSON + d3-geo.
 *
 * d3-geo's equirectangular projection handles antimeridian cutting
 * (Russia/Fiji wrap) and proper path generation.
 *
 * Exposes window.AtlasMap:
 *   init(svgEl)                      -> prepare defs/markers
 *   loadWorld() -> Promise<features> -> [{iso3, name, geometry}]
 *   render(lesson)                   -> draw countries for the lesson view
 *   feature(iso3)                    -> geo feature
 *   setClickHandler(fn)              -> fn(iso3)
 *   highlight(iso3, cls) / clearHighlights(cls)
 *   reveal(iso3) / clearRevealed()
 *   centroid(iso3) -> [x, y] (projected)
 *   project([lon, lat]) -> [x, y]
 *   addArrow(points, color)          -> animated dashed path with arrowhead
 *   zoomBy(factor) / resetView()
 */
(function () {
  "use strict";

  const d3 = window.d3;

  let svg = null;
  let world = null;          // feature list with iso3 + name + geometry
  let group = null;          // <g id="countries">
  let overlay = null;        // <g id="overlay"> for arrows etc.
  let clickHandler = null;
  let projection = null;
  let geoPath = null;
  let baseView = null;       // {x, y, w, h}

  // --- public API ---------------------------------------------------

  const AtlasMap = {
    init(svgEl) {
      svg = svgEl;
      const defs = document.createElementNS(svg.namespaceURI, "defs");
      defs.innerHTML =
        '<marker id="arrowhead" viewBox="0 0 10 10" refX="8" refY="5" ' +
        'markerWidth="6" markerHeight="6" orient="auto-start-reverse">' +
        '<path d="M 0 0 L 10 5 L 0 10 z" fill="context-stroke"/>' +
        "</marker>";
      svg.appendChild(defs);
    },

    async loadWorld() {
      if (world) return world;
      const res = await fetch("geo/countries-110m.json");
      const topo = await res.json();
      const feats = topojson.feature(topo, topo.objects.countries).features;
      world = feats
        .filter((f) => f.properties && f.properties.iso3)
        .map((f) => ({
          type: "Feature",               // d3.geoPath requires proper GeoJSON
          properties: { iso3: f.properties.iso3, name: f.properties.name },
          geometry: f.geometry,
        }));
      return world;
    },

    feature(iso3) {
      return world ? world.find((f) => f.properties.iso3 === iso3) : null;
    },

    render(lesson) {
      if (!world) throw new Error("call loadWorld() first");
      svg.innerHTML = "";
      this.init(svg);

      // Fit projection to the lesson's requested geographic view.
      const view = lesson.view || { lon0: -170, lat0: -60, lon1: 190, lat1: 84 };
      const cx = (view.lon0 + view.lon1) / 2;
      const cy = (view.lat0 + view.lat1) / 2;

      // Equirectangular, fixed scale (2 svg units per degree at equator)
      // so stroke widths stay consistent across lessons.
      projection = d3.geoEquirectangular()
        .scale((180 / Math.PI) * 2)
        .center([cx, cy])
        .translate([0, 0]);
      geoPath = d3.geoPath(projection);

      const [[x0, y0], [x1, y1]] = this._viewBounds(view);
      const w = Math.max(x1 - x0, 1), h = Math.max(y1 - y0, 1);
      baseView = { x: x0, y: y0, w, h };
      svg.setAttribute("viewBox", `${x0} ${y0} ${w} ${h}`);
      svg.setAttribute("preserveAspectRatio", "xMidYMid meet");

      group = document.createElementNS(svg.namespaceURI, "g");
      group.setAttribute("id", "countries");
      overlay = document.createElementNS(svg.namespaceURI, "g");
      overlay.setAttribute("id", "overlay");
      svg.appendChild(group);
      svg.appendChild(overlay);

      const inView = new Set((lesson.countries || []).map((c) => c.iso3));
      const margin = 5; // svg-unit slack for the bounds test
      for (const f of world) {
        const [[fx0, fy0], [fx1, fy1]] = geoPath.bounds(f);
        // skip features entirely outside the view box
        if (fx1 < x0 - margin || fx0 > x1 + margin || fy1 < y0 - margin || fy0 > y1 + margin) continue;
        const inLesson = inView.has(f.properties.iso3);
        const el = document.createElementNS(svg.namespaceURI, "path");
        el.setAttribute("d", geoPath(f) || "");
        el.setAttribute("class", inLesson ? "country" : "country context");
        el.dataset.iso3 = f.properties.iso3;
        el.addEventListener("click", (ev) => {
          ev.stopPropagation();
          if (clickHandler) clickHandler(f.properties.iso3);
        });
        group.appendChild(el);
      }
    },

    _viewBounds(view) {
      // project the four corners and take the enclosing box
      const pts = [
        [view.lon0, view.lat0], [view.lon1, view.lat0],
        [view.lon1, view.lat1], [view.lon0, view.lat1],
      ].map((c) => projection(c));
      const xs = pts.map((p) => p[0]), ys = pts.map((p) => p[1]);
      return [[Math.min(...xs), Math.min(...ys)], [Math.max(...xs), Math.max(...ys)]];
    },

    setClickHandler(fn) { clickHandler = fn; },

    element(iso3) {
      return group ? group.querySelector(`[data-iso3="${iso3}"]`) : null;
    },

    highlight(iso3, cls = "highlighted") {
      const el = this.element(iso3);
      if (el) el.classList.add(cls);
    },

    clearHighlights(cls = "highlighted") {
      if (!group) return;
      group.querySelectorAll("." + cls).forEach((el) => el.classList.remove(cls));
    },

    reveal(iso3) {
      const el = this.element(iso3);
      if (el) el.classList.add("revealed");
    },

    clearRevealed() {
      if (group) group.querySelectorAll(".revealed").forEach((el) => el.classList.remove("revealed"));
    },

    centroid(iso3) {
      const f = this.feature(iso3);
      return f ? projection(d3.geoCentroid(f)) : null;
    },

    project([lon, lat]) {
      return projection([lon, lat]);
    },

    addArrow(points, color = "#ffd24a") {
      // points: [[lon, lat], ...] — projected then drawn with dash animation
      const d = points.map((c, i) => {
        const [x, y] = projection(c);
        return (i === 0 ? "M" : "L") + x.toFixed(2) + " " + y.toFixed(2);
      }).join(" ");
      const p = document.createElementNS(svg.namespaceURI, "path");
      p.setAttribute("d", d);
      p.setAttribute("class", "arrow");
      p.setAttribute("stroke", color);
      overlay.appendChild(p);
      const len = p.getTotalLength();
      p.style.strokeDasharray = len;
      p.style.strokeDashoffset = len;
      p.getBoundingClientRect(); // force layout
      p.style.transition = "stroke-dashoffset 1.6s linear";
      p.style.strokeDashoffset = "0";
      return p;
    },

    clearOverlay() {
      if (overlay) overlay.innerHTML = "";
    },

    resetView() {
      if (baseView) svg.setAttribute("viewBox", `${baseView.x} ${baseView.y} ${baseView.w} ${baseView.h}`);
    },

    zoomBy(factor) {
      const vb = svg.viewBox.baseVal;
      const cx = vb.x + vb.width / 2, cy = vb.y + vb.height / 2;
      const w = vb.width / factor, h = vb.height / factor;
      svg.setAttribute("viewBox", `${cx - w / 2} ${cy - h / 2} ${w} ${h}`);
    },

    panBy(dx, dy) {
      const vb = svg.viewBox.baseVal;
      svg.setAttribute("viewBox", `${vb.x + dx} ${vb.y + dy} ${vb.width} ${vb.height}`);
    },

    attachNavigation() {
      svg.addEventListener("wheel", (ev) => {
        ev.preventDefault();
        this.zoomBy(ev.deltaY < 0 ? 1.2 : 1 / 1.2);
      }, { passive: false });

      let dragging = false, lastX = 0, lastY = 0;
      svg.addEventListener("mousedown", (ev) => { dragging = true; lastX = ev.clientX; lastY = ev.clientY; });
      window.addEventListener("mouseup", () => { dragging = false; });
      svg.addEventListener("mousemove", (ev) => {
        if (!dragging) return;
        const vb = svg.viewBox.baseVal;
        const rect = svg.getBoundingClientRect();
        const scale = vb.width / rect.width;
        this.panBy((lastX - ev.clientX) * scale, (lastY - ev.clientY) * scale);
        lastX = ev.clientX; lastY = ev.clientY;
        svg.style.cursor = "grabbing";
      });
      svg.addEventListener("mouseleave", () => { svg.style.cursor = ""; });
    },
  };

  window.AtlasMap = AtlasMap;
})();
