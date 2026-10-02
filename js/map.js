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
  let baseRotation = null;   // globe: initial rotate() for the lesson
  let drawnFeatures = [];    // [{el, feature}] for globe re-projection
  let overlayPaths = [];     // [{el, points}] re-projected on rotate
  let pointedIso3 = null;    // country currently pointed at by an arrow
  let pointedCoords = null;  // or: arbitrary lon/lat being pointed at
  let stopDots = [];         // [{id, coords}] journey stop dots
  let graticuleEl = null;
  let sphereEl = null;
  let currentLesson = null;

  function isGlobe() { return projectionName === "globe"; }

  // Largest polygon of a (multi)polygon feature, by outer-ring
  // spherical area — the "main" landmass. Whole-feature centroids of
  // countries with far-flung territories (France incl. overseas
  // departments) land in the ocean; the largest polygon's doesn't.
  function mainPolygon(f) {
    const g = f.geometry;
    if (!g || g.type === "Polygon") return f;
    if (g.type !== "MultiPolygon" || !g.coordinates.length) return f;
    let best = null, bestArea = -1;
    for (const poly of g.coordinates) {
      const ring = poly[0];
      if (!ring || ring.length < 3) continue;
      let s = 0;
      const n = ring.length;
      for (let i = 0; i < n; i++) {
        const [x1, y1] = ring[i], [x2, y2] = ring[(i + 1) % n];
        s += (x2 - x1) * Math.PI / 180 *
          (2 + Math.sin(y1 * Math.PI / 180) + Math.sin(y2 * Math.PI / 180));
      }
      const area = Math.abs(s);
      if (area > bestArea) { bestArea = area; best = poly; }
    }
    return best
      ? { type: "Feature", properties: f.properties, geometry: { type: "Polygon", coordinates: best } }
      : f;
  }

  function mainCentroid(f) {
    return d3.geoCentroid(mainPolygon(f));
  }

  // centroid + max angular radius (radians) of a feature — used to cull
  // backside features cheaply during globe drag re-projection
  function featureOrbit(feature) {
    const c = d3.geoCentroid(feature);
    const cx = c[0] * Math.PI / 180, cy = c[1] * Math.PI / 180;
    let maxAngle = 0;
    const visit = (ring) => {
      for (const [lon, lat] of ring) {
        const lx = lon * Math.PI / 180, ly = lat * Math.PI / 180;
        // central angle between ring point and centroid
        const cosA = Math.sin(cy) * Math.sin(ly) +
          Math.cos(cy) * Math.cos(ly) * Math.cos(lx - cx);
        const a = Math.acos(Math.min(1, Math.max(-1, cosA)));
        if (a > maxAngle) maxAngle = a;
      }
    };
    const g = feature.geometry;
    if (g.type === "Polygon") g.coordinates.forEach(visit);
    else if (g.type === "MultiPolygon") g.coordinates.forEach((p) => p.forEach(visit));
    return { centroid: c, maxAngle };
  }

  // --- public API ---------------------------------------------------

  const AtlasMap = {
    init(svgEl) {
      svg = svgEl;
      const defs = document.createElementNS(svg.namespaceURI, "defs");
      defs.innerHTML =
        '<marker id="arrowhead" viewBox="0 0 10 10" refX="10" refY="5" ' +
        'markerWidth="6" markerHeight="6" orient="auto-start-reverse">' +
        '<path d="M 0 0 L 10 5 L 0 10 z" fill="context-stroke"/>' +
        '</marker>' +
        '<marker id="arrowhead-point" viewBox="0 0 10 10" refX="10" refY="5" ' +
        'markerUnits="userSpaceOnUse" markerWidth="26" markerHeight="26" ' +
        'orient="auto-start-reverse">' +
        '<path d="M 0 0 L 10 5 L 0 10 z" fill="#ffd24a" stroke="#222" stroke-width="0.4"/>' +
        "</marker>";
      svg.appendChild(defs);
    },

    async loadWorld() {
      if (world) return world;
      // script-tag data (file://-safe); fetched only as a fallback for
      // legacy embedding
      if (window.ATLAS_WORLD_DATA) {
        var topo = window.ATLAS_WORLD_DATA;
      } else {
        const res = await fetch("geo/countries-10m-simple.json");
        topo = await res.json();
      }
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
        baseRotation = [-cx, -cy, 0];
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

        // precompute centroid + max angular radius per feature once,
        // so drag re-projection can cull backside features cheaply
        // (after the render loop below has filled drawnFeatures, so
        // schedule on next tick)
        Promise.resolve().then(() => {
          for (const df of drawnFeatures) df.orbit = featureOrbit(df.feature);
        });
      } else {
        sphereEl = null;
        graticuleEl = null;
        // fit the projection to the lesson's view polygon (Mercator
        // cannot represent the poles — clamp before fitting). A
        // near-whole-globe view (>=355 deg wide) breaks fitExtent
        // (scale collapses to ~0), so fit to the full sphere instead.
        const viewSpan = ((view.lon1 - view.lon0 + 360) % 360) || 360;
        let fitPoly = viewPoly;
        if (viewSpan >= 355) {
          fitPoly = { type: "Sphere" };
        } else if (projectionName === "mercator") {
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
      // re-project every drawn path after a globe rotation.
      // Backside culling: a feature is visible only if the angle between
      // the view centre and its centroid is < 90° + its angular radius.
      // (graticule still covers the full sphere; d3 clips it correctly)
      const rot = projection.rotate();
      const centre = [-rot[0], -rot[1]];
      const deg = Math.PI / 180;
      for (const { el, feature, orbit } of drawnFeatures) {
        if (orbit) {
          const c = orbit.centroid;
          const cosA = Math.sin(centre[1] * deg) * Math.sin(c[1] * deg) +
            Math.cos(centre[1] * deg) * Math.cos(c[1] * deg) *
            Math.cos((c[0] - centre[0]) * deg);
          const angle = Math.acos(Math.min(1, Math.max(-1, cosA)));
          if (angle > Math.PI / 2 + orbit.maxAngle) {
            el.setAttribute("d", "");
            continue;
          }
        }
        el.setAttribute("d", geoPath(feature) || "");
      }
      for (const { el, points, fixed } of overlayPaths) {
        if (fixed) continue; // pixel-space overlay: redrawn separately
        el.setAttribute("d", points.map((c, i) => {
          const [x, y] = projection(c);
          if (x == null || isNaN(x)) return "";
          return (i === 0 ? "M" : "L") + x.toFixed(2) + " " + y.toFixed(2);
        }).join(" "));
      }
      this._redrawPointOverlay(false);
      this._reprojectStopDots();
      this._updateGraticule();
    },

    _reprojectStopDots() {
      if (!overlay || !stopDots.length) return;
      for (const el of [...overlay.querySelectorAll(".stop-dot")]) {
        const s = stopDots.find((d) => d.id === el.dataset.stop);
        if (!s) continue;
        const c = projection(s.coords);
        if (!c || c[0] == null || isNaN(c[0])) {
          el.setAttribute("cx", -100); // off-canvas (backside)
          el.setAttribute("cy", -100);
          continue;
        }
        el.setAttribute("cx", c[0]);
        el.setAttribute("cy", c[1]);
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

    setCurrent(iso3) {
      if (!group) return;
      group.querySelectorAll(".current").forEach((el) => el.classList.remove("current"));
      const el = this.element(iso3);
      if (el) el.classList.add("current");
    },

    clearCurrent() {
      if (group) group.querySelectorAll(".current").forEach((el) => el.classList.remove("current"));
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

    // sea voyage route: waypoints joined by quadratic Bezier segments
    // (bows seaward) so the line curves around coastlines instead of
    // cutting straight across land. Waypoints sit offshore; control
    // points extend the tangent directions, giving a smooth S/C-shaped
    // fair curve through the ports of call.
    addSeaRoute(points, color = "#ffd24a") {
      const pts = [];
      for (const c of points) {
        const [x, y] = projection(c);
        if (x == null || isNaN(x)) continue;
        pts.push([x, y]);
      }
      if (pts.length < 2) return null;
      const d = [`M${pts[0][0].toFixed(2)} ${pts[0][1].toFixed(2)}`];
      for (let i = 1; i < pts.length; i++) {
        const p0 = pts[i - 1], p1 = pts[i];
        // antimeridian split: a jump wider than half the map means the
        // segment crosses ±180°; drawing it straight would slash across
        // the whole map. Break the path there (separate visual segment).
        if (Math.abs(p1[0] - p0[0]) > 490) {
          d.push(`M${p1[0].toFixed(2)} ${p1[1].toFixed(2)}`);
          continue;
        }
        // control point: midpoint pushed along the average of the
        // incoming and outgoing directions (Catmull-Rom-like), which
        // rounds every corner without overshooting into land much
        const pPrev = pts[i - 2] || p0, pNext = pts[i + 1] || p1;
        let t1 = [p0[0] - pPrev[0], p0[1] - pPrev[1]];
        let t2 = [pNext[0] - p1[0], pNext[1] - p1[1]];
        const norm = (v) => {
          const l = Math.hypot(v[0], v[1]) || 1;
          return [v[0] / l, v[1] / l];
        };
        t1 = norm(t1); t2 = norm(t2);
        const chord = Math.hypot(p1[0] - p0[0], p1[1] - p0[1]);
        // gentle bow: rounds corners without straying far from the
        // waypoint track (large bows can drag the curve over land)
        const k = Math.min(chord * 0.18, 90);
        const c1 = [p0[0] + t1[0] * k, p0[1] + t1[1] * k];
        const c2 = [p1[0] - t2[0] * k, p1[1] - t2[1] * k];
        d.push(`C${c1[0].toFixed(2)} ${c1[1].toFixed(2)} ${c2[0].toFixed(2)} ${c2[1].toFixed(2)} ${p1[0].toFixed(2)} ${p1[1].toFixed(2)}`);
      }
      const p = document.createElementNS(svg.namespaceURI, "path");
      p.setAttribute("d", d.join(" "));
      p.setAttribute("class", "arrow route searoute");
      p.setAttribute("stroke", color);
      overlay.appendChild(p);
      overlayPaths.push({ el: p, points });
      const len = p.getTotalLength();
      p.style.strokeDasharray = len;
      p.style.strokeDashoffset = len;
      p.getBoundingClientRect();
      p.style.transition = "stroke-dashoffset 1.6s linear";
      p.style.strokeDashoffset = "0";
      return p;
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
      p.setAttribute("class", "arrow route");
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

    // one line segment from->to (journey step mode). mode:
    //   "draw"    animate drawing from prev to next (default)
    //   "erase"   animate shortening back toward prev, then stay hidden
    //   "static"  drawn immediately, no animation (initial render)
    addSegment(from, to, color = "#ffd24a", mode = "draw") {
      const a = projection(from), b = projection(to);
      if (!a || !b || a[0] == null || b[0] == null || isNaN(a[0]) || isNaN(b[0])) return null;
      const p = document.createElementNS(svg.namespaceURI, "path");
      p.setAttribute("d", `M${a[0].toFixed(2)} ${a[1].toFixed(2)} L${b[0].toFixed(2)} ${b[1].toFixed(2)}`);
      p.setAttribute("class", "arrow route segment");
      p.setAttribute("stroke", color);
      overlay.appendChild(p);
      overlayPaths.push({ el: p, points: [from, to] });
      if (mode === "static") return p;
      const len = p.getTotalLength();
      p.style.strokeDasharray = len;
      if (mode === "erase") {
        // start fully drawn; commit; then animate to hidden (shortens
        // back toward `from`)
        p.style.strokeDashoffset = 0;
        p.getBoundingClientRect(); // commit starting state
        p.style.transition = "stroke-dashoffset 0.8s linear";
        p.style.strokeDashoffset = String(len);
      } else {
        // start hidden; commit; then animate the draw from->to
        p.style.strokeDashoffset = len;
        p.getBoundingClientRect(); // commit starting state
        p.style.transition = "stroke-dashoffset 0.8s linear";
        p.style.strokeDashoffset = "0";
      }
      return p;
    },

    clearOverlay() {
      overlayPaths = [];
      pointedIso3 = null;
      pointedCoords = null;
      if (overlay) overlay.innerHTML = "";
    },

    // globe: if the pointed country is now on the backside, rotate it
    // to face the viewer
    rotateToFace(iso3) {
      if (!isGlobe()) return;
      const f = this.feature(iso3);
      if (!f) return;
      const c = mainCentroid(f);
      const centre = projection.invert(
        [projection.translate()[0], projection.translate()[1]]);
      const deg = Math.PI / 180;
      const cosA = Math.sin(c[1] * deg) * Math.sin(centre[1] * deg) +
        Math.cos(c[1] * deg) * Math.cos(centre[1] * deg) *
        Math.cos((c[0] - centre[0]) * deg);
      if (Math.acos(Math.min(1, Math.max(-1, cosA))) > Math.PI / 3) {
        projection.rotate([-c[0], -c[1]]);
        this._reproject();
      }
    },


    // Static clickable dots for journey stops, at their exact lon/lat.
    // Dots re-project on globe rotation (lon/lat -> screen each time).
    // `focusedIdx` (stop index) gets the pulsing style; click fires cb(idx).
    // Locations visited more than once get ONE dot; hovering it shows a
    // popover listing each visit (year + place) so the user can pick.
    renderStopDots(stops, focusedIdx, onClick) {
      stopDots = stops.map((s, i) => ({ idx: i, coords: s.coords, id: s.id }));
      if (!overlay) return;
      this._removeStopPopover();
      for (const el of [...overlay.querySelectorAll(".stop-dot, .stop-badge")]) el.remove();
      // group visits by identical location
      const byCoords = new Map();
      stops.forEach((s, i) => {
        const k = s.coords[0].toFixed(3) + "," + s.coords[1].toFixed(3);
        if (!byCoords.has(k)) byCoords.set(k, []);
        byCoords.get(k).push(i);
      });
      for (const group of byCoords.values()) {
        const i = group[0];
        const s = stops[i];
        const c = this.project(s.coords);
        if (!c || c[0] == null || isNaN(c[0])) continue;
        const dot = document.createElementNS(svg.namespaceURI, "circle");
        dot.setAttribute("cx", c[0]);
        dot.setAttribute("cy", c[1]);
        dot.setAttribute("r", 3);
        const isFocused = group.includes(focusedIdx);
        dot.setAttribute("class", "stop-dot" + (isFocused ? " focused" : ""));
        dot.dataset.idx = i;
        dot.dataset.stop = s.id;
        dot.dataset.visits = group.join(",");
        if (group.length > 1) {
          dot.classList.add("multi");
          dot.addEventListener("mouseenter", () => {
            this._showStopPopover(dot, group.map((g) => stops[g]), group, onClick);
          });
          dot.addEventListener("mouseleave", (ev) => {
            // hide unless the pointer moved into the popover itself
            const pop = document.getElementById("stop-popover");
            if (pop && !pop.contains(ev.relatedTarget)) this._hideStopPopoverSoon();
          });
        }
        dot.addEventListener("click", (ev) => {
          ev.stopPropagation();
          if (group.length === 1) {
            if (onClick) onClick(i);
          }
        });
        overlay.appendChild(dot);
      }
    },

    // popover listing the visits of a multi-visit location; clicking an
    // entry fires onClick with that visit's stop index
    _showStopPopover(dot, groupStops, group, onClick) {
      this._removeStopPopover();
      const pop = document.createElement("div");
      pop.id = "stop-popover";
      pop.style.position = "fixed"; // positioned in viewport coords below
      pop.style.left = (Number(dot.getAttribute("cx")) + 10) + "px";
      pop.style.top = (Number(dot.getAttribute("cy")) - 8) + "px";
      groupStops.forEach((s, j) => {
        const item = document.createElement("div");
        item.className = "stop-pop-item";
        const nm = (s.names && (s.names[window.I18n && window.I18n.locale] || s.names["en-GB"] || Object.values(s.names)[0])) || s.id;
        item.textContent = (group[j] + 1) + ". " + s.year + " · " + nm;
        item.addEventListener("click", (ev) => {
          ev.stopPropagation();
          this._removeStopPopover();
          if (onClick) onClick(group[j]);
        });
        pop.appendChild(item);
      });
      const mapDiv = document.getElementById("map");
      // the popover is HTML and cannot live inside the <svg>; anchor it
      // in the svg's parent (#stage) using the dot's viewport position
      // (getBoundingClientRect accounts for viewBox scaling)
      const host = mapDiv ? mapDiv.parentElement : overlay.parentNode;
      const r = dot.getBoundingClientRect();
      pop.style.left = (r.right + 8) + "px";
      pop.style.top = Math.max(4, r.top - 8) + "px";
      host.appendChild(pop);
      // keep open while hovered; hide after the pointer leaves
      pop.addEventListener("mouseleave", () => this._removeStopPopover());
      // dismiss on outside click
      setTimeout(() => {
        document.addEventListener("click", this._popoverCloser = () => this._removeStopPopover(), { once: true });
      }, 0);
    },

    _hideStopPopoverSoon() {
      clearTimeout(this._popoverTimer);
      this._popoverTimer = setTimeout(() => {
        const pop = document.getElementById("stop-popover");
        if (pop && !pop.matches(":hover")) this._removeStopPopover();
      }, 250);
    },

    _removeStopPopover() {
      const old = document.getElementById("stop-popover");
      if (old) old.remove();
      if (this._popoverCloser) {
        document.removeEventListener("click", this._popoverCloser);
        this._popoverCloser = null;
      }
    },

    focusStopDot(idx) {
      if (!overlay) return;
      for (const el of [...overlay.querySelectorAll(".stop-dot")]) {
        const visits = (el.dataset.visits || el.dataset.idx).split(",").map(Number);
        el.classList.toggle("focused", visits.includes(Number(idx)));
      }
    },

    // ensure a stop dot is visible after globe rotation
    _reprojectStopDots() {
      if (!overlay) return;
      for (const el of [...overlay.querySelectorAll(".stop-dot")]) {
        const s = stopDots.find((d) => d.idx === Number(el.dataset.idx));
        if (!s) continue;
        const c = projection(s.coords);
        if (!c || c[0] == null || isNaN(c[0])) {
          el.setAttribute("cx", -100); // off-canvas (backside)
          el.setAttribute("cy", -100);
          continue;
        }
        // keep the fan offset applied for duplicates
        const dx = Number(el.dataset.dx || 0), dy = Number(el.dataset.dy || 0);
        el.setAttribute("cx", c[0] + dx);
        el.setAttribute("cy", c[1] + dy);
      }
      for (const el of [...overlay.querySelectorAll(".stop-badge")]) {
        const s = stopDots.find((d) => d.idx === Number(el.dataset.idx));
        if (!s) continue;
        const c = projection(s.coords);
        if (!c || c[0] == null || isNaN(c[0])) {
          el.setAttribute("x", -100);
          continue;
        }
        el.setAttribute("x", c[0]);
        el.setAttribute("y", c[1] - 14);
      }
    },

    // Point at a country: big animated arrow + pulsing dot at
    // its centroid. If the globe is showing and the country is on the
    // backside, rotate it to face the viewer first. The pointing
    // overlay is redrawn after globe drags (see _reproject).
    pointCountry(iso3) {
      pointedIso3 = iso3;
      pointedCoords = null;
      this._redrawPointOverlay(true);
    },

    // point at an arbitrary lon/lat (journey stops) instead of a country
    pointAt(coords) {
      pointedCoords = coords;
      pointedIso3 = null;
      this._redrawPointOverlay(true);
    },

    rotateToCoord(coords) {
      if (!isGlobe()) return;
      const centre = projection.invert(
        [projection.translate()[0], projection.translate()[1]]);
      const deg = Math.PI / 180;
      const cosA = Math.sin(coords[1] * deg) * Math.sin(centre[1] * deg) +
        Math.cos(coords[1] * deg) * Math.cos(centre[1] * deg) *
        Math.cos((coords[0] - centre[0]) * deg);
      if (Math.acos(Math.min(1, Math.max(-1, cosA))) > Math.PI / 3) {
        projection.rotate([-coords[0], -coords[1]]);
        this._reproject();
      }
    },

    _redrawPointOverlay(animate) {
      if (!overlay) return;
      for (const el of [...overlay.querySelectorAll(".point-arrow, .target-dot")]) {
        el.remove();
      }
      overlayPaths = overlayPaths.filter((o) => !o.fixed);
      let target = null, bbox = null;
      if (pointedCoords) {
        // journey stop: arbitrary coordinates, no feature/bbox
        const t = projection(pointedCoords);
        if (t && t[0] != null && !isNaN(t[0])) target = t;
      } else if (pointedIso3) {
      const f = this.feature(pointedIso3);
      if (!f) return;
      // use the largest polygon's centroid: whole-feature centroids of
      // countries with far-flung territories (France: 21 polygons incl.
      // overseas departments) land in the ocean
      const main = mainPolygon(f);
      target = projection(d3.geoCentroid(main));
      if (!target || target[0] == null || isNaN(target[0])) return;

      // arrow start: a point outside the main polygon's projected bbox
      // so tiny countries aren't covered by the arrowhead itself
      try { bbox = geoPath.bounds(main); } catch (e) { bbox = null; }
      }
      if (!target) return;
      let start = [target[0], target[1] - 90];
      if (bbox) {
        const [[x0, y0], [x1, y1]] = bbox;
        const cx = (x0 + x1) / 2;
        if (y0 > 130) start = [cx, y0 - 70];          // room above
        else if (y1 < 870) start = [cx, y1 + 70];     // room below
        else start = [x1 + 70, (y0 + y1) / 2];        // room to the right
        // ensure a minimum arrow length for visibility
        const dx = target[0] - start[0], dy = target[1] - start[1];
        const d = Math.hypot(dx, dy) || 1;
        const minLen = 70;
        if (d < minLen) {
          start = [target[0] - dx * minLen / d, target[1] - dy * minLen / d];
        }
      }
      const p = document.createElementNS(svg.namespaceURI, "path");
      // refX=10 anchors the marker TIP at the line end; end the line at
      // the main polygon's bbox edge (not the centroid) so the head
      // points AT the country instead of covering it / overshooting
      // micro-countries (Guernsey-class)
      let end = target;
      if (bbox) {
        const [[x0, y0], [x1, y1]] = bbox;
        const dx = target[0] - start[0], dy = target[1] - start[1];
        const len = Math.hypot(dx, dy) || 1;
        const ux = dx / len, uy = dy / len;
        for (let s = 2; s < 400; s += 2) {
          const px = target[0] - ux * s, py = target[1] - uy * s;
          if (px < x0 || px > x1 || py < y0 || py > y1) { end = [px, py]; break; }
        }
      }
      p.setAttribute("d", `M ${start[0].toFixed(1)} ${start[1].toFixed(1)} L ${end[0].toFixed(1)} ${end[1].toFixed(1)}`);
      p.setAttribute("class", "arrow point-arrow");
      p.setAttribute("marker-end", "url(#arrowhead-point)");
      overlay.appendChild(p);
      // The head's TIP is anchored at the line end (refX=10) and the
      // triangle tapers backward from it. Marker: 26px long, base
      // half-width 13px => half-width at s px behind the tip is s/2;
      // the shaft (9px wide, half 4.5) is only covered where s >= 9.
      // So the drawn dash must end >= 9px before the tip; use 12px
      // for anti-aliasing margin.
      const len = p.getTotalLength();
      const GAP = 12;
      p.style.strokeDasharray = len;
      if (animate) {
        p.style.strokeDashoffset = len;
        p.getBoundingClientRect(); // force layout
        p.style.transition = "stroke-dashoffset 0.8s ease-out";
        p.style.strokeDashoffset = GAP;
      } else {
        p.style.strokeDashoffset = GAP;
      }
      // fixed: pixel-space element — _reproject redraws it instead of
      // re-projecting lon/lat points
      overlayPaths.push({ el: p, fixed: true });

      // pulsing dot at the centroid — skip it when the arrowhead
      // already ends at/near the target (micro-countries): a dot
      // 2px past the tip just merges into the head as a blob
      const distEnd = end === target ? 0 : Math.hypot(target[0] - end[0], target[1] - end[1]);
      if (distEnd > 20) {
        const dot = document.createElementNS(svg.namespaceURI, "circle");
        dot.setAttribute("cx", target[0]);
        dot.setAttribute("cy", target[1]);
        dot.setAttribute("r", 6);
        dot.setAttribute("class", "target-dot");
        overlay.appendChild(dot);
      }
    },


    resetView() {
      if (baseView) svg.setAttribute("viewBox", `${baseView.x} ${baseView.y} ${baseView.w} ${baseView.h}`);
      // globe: also restore the lesson's initial rotation
      if (baseRotation && projectionName === "globe") {
        projection.rotate(baseRotation);
        this._reproject();
      }
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
          // rAF throttle: mousemove fires far more often than the
          // display refresh; re-project at most once per frame
          if (!this._rafPending) {
            this._rafPending = true;
            requestAnimationFrame(() => {
              this._rafPending = false;
              this._reproject();
            });
          }
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
