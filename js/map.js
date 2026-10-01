/* map.js — SVG map rendering on top of world-atlas TopoJSON.
 *
 * Exposes window.AtlasMap:
 *   init(svgEl)                      -> prepare defs/markers
 *   loadWorld() -> Promise<features> -> [{iso3, name, geometry}]
 *   render(lesson, opts)             -> draw countries for the lesson view
 *   setClickHandler(fn)              -> fn(iso3)
 *   highlight(iso3, cls) / clearHighlights(cls)
 *   reveal(iso3) / clearRevealed()
 *   centroid(iso3) -> [x, y]
 *   addArrow(points, color)          -> animated dashed path with arrowhead
 *   zoomBy(factor) / resetView()
 *
 * Projection: equirectangular clipped to the lesson's `view` box.
 */
(function () {
  "use strict";

  let svg = null;
  let world = null;          // feature list with iso3 + name + geometry
  let byIso3 = new Map();    // iso3 -> feature
  let group = null;          // <g id="countries">
  let overlay = null;        // <g id="overlay"> for arrows etc.
  let clickHandler = null;
  let baseView = null;       // {x, y, w, h}

  function equirect([lon, lat]) {
    return [lon, -lat];
  }

  // --- geo helpers -------------------------------------------------

  function pathFromGeometry(geom) {
    const polys = geom.type === "Polygon" ? [geom.coordinates]
      : geom.type === "MultiPolygon" ? geom.coordinates : [];
    return polys.map((poly) =>
      poly.map((ring) =>
        ring.map((c, i) => {
          const [x, y] = equirect(c);
          return (i === 0 ? "M" : "L") + x.toFixed(2) + " " + y.toFixed(2);
        }).join(" ") + " Z"
      ).join(" ")
    ).join(" ");
  }

  function boundsOfGeometry(geom) {
    let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
    const polys = geom.type === "Polygon" ? [geom.coordinates]
      : geom.type === "MultiPolygon" ? geom.coordinates : [];
    for (const poly of polys) {
      for (const ring of poly) {
        for (const [lon, lat] of ring) {
          const [x, y] = equirect([lon, lat]);
          if (x < minX) minX = x; if (x > maxX) maxX = x;
          if (y < minY) minY = y; if (y > maxY) maxY = y;
        }
      }
    }
    return { minX, minY, maxX, maxY };
  }

  function biggestPolygon(geom) {
    const polys = geom.type === "Polygon" ? [geom]
      : geom.type === "MultiPolygon" ? geom.coordinates.map((p) => ({ type: "Polygon", coordinates: p }))
      : [];
    let best = null, bestArea = -1;
    for (const poly of polys) {
      const ring = poly.coordinates[0];
      let area = 0;
      for (let i = 0; i < ring.length - 1; i++) {
        const [x1, y1] = equirect(ring[i]);
        const [x2, y2] = equirect(ring[i + 1]);
        area += x1 * y2 - x2 * y1;
      }
      area = Math.abs(area / 2);
      if (area > bestArea) { bestArea = area; best = poly; }
    }
    return best;
  }

  function centroidOf(feature) {
    const poly = biggestPolygon(feature.geometry);
    if (!poly) return null;
    const ring = poly.coordinates[0];
    let cx = 0, cy = 0, a = 0;
    for (let i = 0; i < ring.length - 1; i++) {
      const [x1, y1] = equirect(ring[i]);
      const [x2, y2] = equirect(ring[i + 1]);
      const cross = x1 * y2 - x2 * y1;
      a += cross;
      cx += (x1 + x2) * cross;
      cy += (y1 + y2) * cross;
    }
    a /= 2;
    if (a === 0) return null;
    return [cx / (6 * a), cy / (6 * a)];
  }

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
          iso3: f.properties.iso3,
          name: f.properties.name,
          geometry: f.geometry,
        }));
      byIso3 = new Map(world.map((f) => [f.iso3, f]));
      return world;
    },

    render(lesson, opts = {}) {
      if (!world) throw new Error("call loadWorld() first");
      svg.innerHTML = "";
      this.init(svg);

      const view = lesson.view || { lon0: -170, lat0: -60, lon1: 190, lat1: 84 };
      const [x0, y0] = equirect([view.lon0, view.lat1]);
      const [x1, y1] = equirect([view.lon1, view.lat0]);
      baseView = { x: x0, y: y0, w: x1 - x0, h: y1 - y0 };
      svg.setAttribute("viewBox", `${x0} ${y0} ${x1 - x0} ${y1 - y0}`);
      svg.setAttribute("preserveAspectRatio", "xMidYMid meet");

      group = document.createElementNS(svg.namespaceURI, "g");
      group.setAttribute("id", "countries");
      overlay = document.createElementNS(svg.namespaceURI, "g");
      overlay.setAttribute("id", "overlay");
      svg.appendChild(group);
      svg.appendChild(overlay);

      const inView = new Set((lesson.countries || []).map((c) => c.iso3));
      for (const f of world) {
        if (inView.size && !inView.has(f.iso3)) continue;
        const b = boundsOfGeometry(f.geometry);
        // skip features entirely outside the view box
        if (b.maxX < x0 || b.minX > x1 || b.maxY < y0 || b.minY > y1) continue;
        const el = document.createElementNS(svg.namespaceURI, "path");
        el.setAttribute("d", pathFromGeometry(f.geometry));
        el.setAttribute("class", "country");
        el.dataset.iso3 = f.iso3;
        el.addEventListener("click", (ev) => {
          ev.stopPropagation();
          if (clickHandler) clickHandler(f.iso3);
        });
        group.appendChild(el);
      }
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
      const f = byIso3.get(iso3);
      return f ? centroidOf(f) : null;
    },

    addArrow(points, color = "#ffd24a") {
      // points: [[lon, lat], ...] — drawn on the overlay with a dash animation
      const d = points.map((c, i) => {
        const [x, y] = equirect(c);
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
