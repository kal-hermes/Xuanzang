/* map.js — SVG map rendering on top of world-atlas TopoJSON + d3-geo.
 *
 * Supports selectable projections:
 *   equirectangular | mercator | naturalEarth | robinson | globe
 * "globe" is d3's orthographic projection with drag-to-rotate; paths
 * are re-projected on drag (backside is clipped by the projection).
 *
 * Exposes window.AtlasMap:
 *   init(svgEl)                      -> prepare defs/markers
 *   loadWorld() -> Promise<features> -> GeoJSON Features (properties.iso3)
 *   render(lesson, opts)             -> draw; opts.projection = name
 *   feature(iso3) / setClickHandler(fn)
 *   highlight(iso3, cls) / clearHighlights(cls)
 *   reveal(iso3) / clearRevealed()
 *   centroid(iso3) / project([lon, lat])
 *   addArrow(points, color) / clearOverlay()
 *   zoomBy / resetView / attachNavigation (drag = rotate on globe, pan otherwise)
 */
(function () {
  "use strict";

  const d3 = window.d3;

  const PROJECTIONS = {
    equirectangular: () => d3.geoEquirectangular(),
    mercator: () => d3.geoMercator(),
    naturalEarth: () => d3.geoNaturalEarth1(),
    robinson: () => d3.geoRobinson(),
    globe: () => d3.geoOrthographic(),
  };

  const GLOBE_RADIUS = 240; // svg units, fixed so stroke widths stay sane

  let svg = null;
  let world = null;
  let group = null;          // <g id="countries">
  let overlay = null;        // <g id="overlay"> arrows etc.
  let clickHandler = null;
  let projection = null;
  let projectionName = "equirectangular";
  let geoPath = null;
  let baseView = null;       // {x, y, w, h}
  let drawnFeatures = [];    // [{el, feature}] for globe re-projection
  let overlayPaths = [];     // [{el, points}] re-projected on rotate
  let graticuleEl = null;
  let sphereEl = null;
  let currentLesson = null;

  function isGlobe() { return projectionName === "globe"; }

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
      const res = await fetch("geo/countries-10m.json");
      const topo = await res.json();
      const feats = topojson.feature(topo, topo.objects.countries).features;
      // The enriched TopoJSON maps split entities to the same iso3
      // (N. Cyprus -> CYP, Somaliland -> SOM). Merge duplicates into a
      // single MultiPolygon feature so each country is exactly one
      // <path> that highlights/hovers as a unit.
      const byIso3 = new Map();
      for (const f of feats) {
        if (!f.properties || !f.properties.iso3) continue;
        const iso3 = f.properties.iso3;
        if (!byIso3.has(iso3)) {
          byIso3.set(iso3, {
            type: "Feature",
            properties: { iso3, name: f.properties.name },
            geometry: f.geometry,
          });
        } else {
          const merged = byIso3.get(iso3);
          const polys = [];
          const push = (g) => {
            if (g.type === "Polygon") polys.push(g.coordinates);
            else if (g.type === "MultiPolygon") polys.push(...g.coordinates);
          };
          push(merged.geometry);
          push(f.geometry);
          merged.geometry = { type: "MultiPolygon", coordinates: polys };
        }
      }
      world = [...byIso3.values()];
      return world;
    },

    feature(iso3) {
      return world ? world.find((f) => f.properties.iso3 === iso3) : null;
    },

    render(lesson, opts = {}) {
      if (!world) throw new Error("call loadWorld() first");
      currentLesson = lesson;
      projectionName = PROJECTIONS[opts.projection] ? opts.projection : "equirectangular";
      svg.innerHTML = "";
      this.init(svg);
      drawnFeatures = [];
      overlayPaths = [];

      const view = lesson.view || { lon0: -170, lat0: -60, lon1: 190, lat1: 84 };
      // NOTE: ring wound clockwise — d3-geo treats CCW rings as holes
      // (the complement), which would fit the whole world instead.
      const viewPoly = {
        type: "Polygon",
        coordinates: [[
          [view.lon0, view.lat0], [view.lon0, view.lat1],
          [view.lon1, view.lat1], [view.lon1, view.lat0],
          [view.lon0, view.lat0],
        ]],
      };

      projection = PROJECTIONS[projectionName]();
      geoPath = d3.geoPath(projection);

      if (isGlobe()) {
        // fixed-size globe centered on the lesson's view centre
        const cx = (view.lon0 + view.lon1) / 2;
        const cy = (view.lat0 + view.lat1) / 2;
        projection
          .scale(GLOBE_RADIUS)
          .translate([0, 0])
          .rotate([-cx, -cy]);
        const m = 16;
        baseView = { x: -GLOBE_RADIUS - m, y: -GLOBE_RADIUS - m, w: 2 * (GLOBE_RADIUS + m), h: 2 * (GLOBE_RADIUS + m) };
        svg.setAttribute("viewBox", `${baseView.x} ${baseView.y} ${baseView.w} ${baseView.h}`);

        sphereEl = document.createElementNS(svg.namespaceURI, "path");
        sphereEl.setAttribute("d", geoPath({ type: "Sphere" }) || "");
        sphereEl.setAttribute("class", "sphere");
        svg.appendChild(sphereEl);

        graticuleEl = document.createElementNS(svg.namespaceURI, "path");
        graticuleEl.setAttribute("class", "graticule");
        svg.appendChild(graticuleEl);
        this._updateGraticule();
      } else {
        sphereEl = null;
        graticuleEl = null;
        // fit the projection to the lesson's view polygon (Mercator
        // cannot represent the poles — clamp before fitting)
        let fitPoly = viewPoly;
        if (projectionName === "mercator") {
          const clamp = (v) => Math.max(-82, Math.min(82, v));
          const coords = viewPoly.coordinates[0].map(([lon, lat]) => [lon, clamp(lat)]);
          fitPoly = { type: "Polygon", coordinates: [coords] };
        }
        projection.fitExtent([[10, 10], [990, 990]], fitPoly);
        const [[bx0, by0], [bx1, by1]] = geoPath.bounds(fitPoly);
        baseView = { x: bx0, y: by0, w: bx1 - bx0, h: by1 - by0 };
        svg.setAttribute("viewBox", `${bx0} ${by0} ${bx1 - bx0} ${by1 - by0}`);
      }
      svg.setAttribute("preserveAspectRatio", "xMidYMid meet");

      group = document.createElementNS(svg.namespaceURI, "g");
      group.setAttribute("id", "countries");
      overlay = document.createElementNS(svg.namespaceURI, "g");
      overlay.setAttribute("id", "overlay");
      svg.appendChild(group);
      svg.appendChild(overlay);

      const inView = new Set((lesson.countries || []).map((c) => c.iso3));
      const margin = 5;
      const [[x0, y0], [x1, y1]] = [[baseView.x, baseView.y],
        [baseView.x + baseView.w, baseView.y + baseView.h]];
      for (const f of world) {
        if (!isGlobe()) {
          const [[fx0, fy0], [fx1, fy1]] = geoPath.bounds(f);
          if (fx1 < x0 - margin || fx0 > x1 + margin || fy1 < y0 - margin || fy0 > y1 + margin) continue;
        }
        const inLesson = inView.has(f.properties.iso3);
        const el = document.createElementNS(svg.namespaceURI, "path");
        el.setAttribute("d", geoPath(f) || "");
        el.setAttribute("class", inLesson ? "country" : "country context");
        el.dataset.iso3 = f.properties.iso3;
        el.addEventListener("click", (ev) => {
          ev.stopPropagation();
          if (clickHandler) clickHandler(f.properties.iso3);
        });
        drawnFeatures.push({ el, feature: f });
        group.appendChild(el);
      }
    },

    _updateGraticule() {
      if (!graticuleEl) return;
      const grat = d3.geoGraticule ? d3.geoGraticule() : null;
      if (!grat) { graticuleEl.setAttribute("d", ""); return; }
      graticuleEl.setAttribute("d", geoPath(grat()) || "");
    },

    _reproject() {
      // re-project every drawn path after a globe rotation
      for (const { el, feature } of drawnFeatures) {
        el.setAttribute("d", geoPath(feature) || "");
      }
      for (const { el, points } of overlayPaths) {
        el.setAttribute("d", points.map((c, i) => {
          const [x, y] = projection(c);
          if (x == null || isNaN(x)) return "";
          return (i === 0 ? "M" : "L") + x.toFixed(2) + " " + y.toFixed(2);
        }).join(" "));
      }
      this._updateGraticule();
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
      const segs = [];
      for (const c of points) {
        const [x, y] = projection(c);
        if (x == null || isNaN(x)) continue; // clipped (e.g. globe backside)
        segs.push((segs.length === 0 ? "M" : "L") + x.toFixed(2) + " " + y.toFixed(2));
      }
      const p = document.createElementNS(svg.namespaceURI, "path");
      p.setAttribute("d", segs.join(" "));
      p.setAttribute("class", "arrow");
      p.setAttribute("stroke", color);
      overlay.appendChild(p);
      overlayPaths.push({ el: p, points });
      const len = p.getTotalLength();
      p.style.strokeDasharray = len;
      p.style.strokeDashoffset = len;
      p.getBoundingClientRect(); // force layout
      p.style.transition = "stroke-dashoffset 1.6s linear";
      p.style.strokeDashoffset = "0";
      return p;
    },

    clearOverlay() {
      overlayPaths = [];
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
      let dragVersor = null;      // cartesian point under cursor at drag start (globe)
      let dragRotate = null;      // projection rotate() at drag start (globe)
      // d3's orthographic invert clamps off-disc points to the horizon
      // (finite garbage), so gate on distance from globe centre instead
      const onGlobe = (pt) => {
        const t = projection.translate();
        return Math.hypot(pt[0] - t[0], pt[1] - t[1]) <= projection.scale();
      };
      svg.addEventListener("mousedown", (ev) => {
        dragging = true; lastX = ev.clientX; lastY = ev.clientY;
        if (isGlobe()) {
          dragRotate = projection.rotate();
          const pt = this._svgPoint(ev);
          dragVersor = onGlobe(pt)
            ? versor.cartesian(projection.invert(pt))
            : null;
        }
      });
      window.addEventListener("mouseup", () => { dragging = false; });
      svg.addEventListener("mousemove", (ev) => {
        if (!dragging) return;
        const rect = svg.getBoundingClientRect();
        const vb = svg.viewBox.baseVal;
        if (isGlobe()) {
          if (!dragVersor) { lastX = ev.clientX; lastY = ev.clientY; return; }
          // canonical versor drag (Bostock): invert in the drag-START
          // rotation frame, multiply delta on the RIGHT of q0
          const pt = this._svgPoint(ev);
          if (!onGlobe(pt)) return; // cursor left the disc mid-drag
          const p = projection.rotate(dragRotate).invert(pt);
          if (!p || !isFinite(p[0]) || !isFinite(p[1])) return;
          const v1 = versor.cartesian(p);
          const q1 = versor.multiply(versor(dragRotate), versor.delta(dragVersor, v1));
          projection.rotate(versor.rotation(q1));
          this._reproject();
        } else {
          const scale = vb.width / rect.width;
          this.panBy((lastX - ev.clientX) * scale, (lastY - ev.clientY) * scale);
        }
        lastX = ev.clientX; lastY = ev.clientY;
        svg.style.cursor = "grabbing";
      });
      svg.addEventListener("mouseleave", () => { svg.style.cursor = ""; });
    },

    _svgPoint(ev) {
      // client coords -> svg user-space coords (accounts for viewBox + zoom)
      const rect = svg.getBoundingClientRect();
      const vb = svg.viewBox.baseVal;
      return [
        vb.x + (ev.clientX - rect.left) / rect.width * vb.width,
        vb.y + (ev.clientY - rect.top) / rect.height * vb.height,
      ];
    },
  };

  window.AtlasMap = AtlasMap;
})();
