/*
 * Experimental WebGL globe renderer — an ALTERNATIVE to the SVG globe,
 * activated only by ?renderer=webgl (globe projection). The SVG globe
 * stays the default and the fallback.
 *
 * Approach: texture-mapped orthographic sphere. The full-precision world
 * (477k points) is rasterised ONCE into an equirectangular texture; a
 * rotated sphere samples it in the fragment shader. A drag frame costs
 * one uniform update — no reprojection, no DOM writes.
 *
 * The SVG keeps everything interactive (dots, routes, arrows, popovers,
 * click targets): the canvas sits UNDER the transparent SVG and never
 * receives pointer events. Country state colours (revealed/current/
 * highlighted) are baked into the texture — call rebake() after any
 * class change (map.js does this; bake is ~a frame, not per-frame).
 *
 * Rotation reproduces d3-geo's rotate([lambda, phi]) for deltaGamma = 0
 * (verified against js/vendor/d3-geo.min.js `it()`): longitude shift,
 * then rotation about the cartesian Y axis. Front hemisphere = x' > 0.
 */
window.AtlasWebGLGlobe = (function () {
  "use strict";

  // Colours mirror css/app.css (#map .sphere/.country/.country.context/.graticule)
  var COLOR = {
    ocean: "#0d1420",
    land: "#2c3d4f",
    landStroke: "#6f8ca8",
    context: "#24303d",
    contextStroke: "#43596f",
    graticule: "#22303f"
  };

  var TW = 4096, TH = 2048;       // equirect texture
  var SEG_LON = 256, SEG_LAT = 128; // sphere tessellation

  var gl = null, canvas = null, program = null, tex = null;
  var sphereBuf = null, sphereCount = 0;
  var uRot = null, uFit = null;
  var world = null, lessonSet = null, geoPathCtor = null;
  var currentRot = [0, 0, 0];

  var VS = [
    "attribute vec2 a_ll;",
    "uniform vec3 u_rot;",   // d3 rotate(): [lambda, phi, gamma] degrees
    "uniform vec4 u_fit;",   // x: clip-x scale, y: clip-y scale (globe radius), z/w unused
    "varying vec2 v_uv;",
    "varying float v_edge;",
    "void main() {",
    "  float lon = radians(a_ll.x + u_rot.x);",
    "  float lat = radians(a_ll.y);",
    "  vec3 v = vec3(cos(lat) * cos(lon), cos(lat) * sin(lon), sin(lat));",
    // d3-geo rotationPhiGamma(deltaPhi, deltaGamma), replicated from
    // js/vendor/d3-geo.min.js `it()`: gamma rolls the view axis, and the
    // versor drag path DOES produce non-zero gamma — dropping it makes
    // the canvas sphere diverge from the SVG overlay mid-drag.
    "  float ph = radians(u_rot.y);",
    "  float gm = radians(u_rot.z);",
    "  float cp = cos(ph), sp = sin(ph), cg = cos(gm), sg = sin(gm);",
    "  float k = v.z * cp + v.x * sp;",
    "  vec3 r = vec3(v.x * cp - v.z * sp, v.y * cg - k * sg, k * cg + v.y * sg);",
    "  v_edge = r.x;",   // cartesian x > 0 <=> |relative longitude| < 90° (front hemisphere)
    "  v_uv = vec2((a_ll.x + 180.0) / 360.0, (90.0 - a_ll.y) / 180.0);",
    "  gl_Position = vec4(r.y * u_fit.x + u_fit.z, r.z * u_fit.y + u_fit.w, 0.0, 1.0);",  // d3 orthographic screen = (y, -z); GL y-up flips the sign; z/w = disc centre in clip
    "}"
  ].join("\n");

  var FS = [
    "precision mediump float;",
    "uniform sampler2D u_tex;",
    "varying vec2 v_uv;",
    "varying float v_edge;",
    "void main() {",
    "  if (v_edge < 0.0) discard;",
    "  float limb = smoothstep(0.0, 0.015, v_edge);",
    "  vec4 c = texture2D(u_tex, v_uv);",
    "  gl_FragColor = vec4(c.rgb * limb, 1.0);",
    "}"
  ].join("\n");

  function available() {
    try {
      var c = document.createElement("canvas");
      return !!(c.getContext("webgl2") || c.getContext("webgl"));
    } catch (e) {
      return false;
    }
  }

  function compile(type, src) {
    var sh = gl.createShader(type);
    gl.shaderSource(sh, src);
    gl.compileShader(sh);
    if (!gl.getShaderParameter(sh, gl.COMPILE_STATUS)) {
      throw new Error("webgl-globe shader: " + gl.getShaderInfoLog(sh));
    }
    return sh;
  }

  /* Rasterise the full-precision world onto an equirect canvas. */
  function bakeTexture() {
    var c = document.createElement("canvas");
    c.width = TW; c.height = TH;
    var ctx = c.getContext("2d");
    var proj = d3.geoEquirectangular()
      .scale(TW / (2 * Math.PI))
      .translate([TW / 2, TH / 2]);
    var path = d3.geoPath(proj, ctx);

    ctx.fillStyle = COLOR.ocean;
    ctx.fillRect(0, 0, TW, TH);

    // graticule, 15-degree steps (matching d3.geoGraticule10 density look)
    ctx.strokeStyle = COLOR.graticule;
    ctx.lineWidth = 1.5;
    ctx.beginPath();
    for (var lon = -180; lon <= 180; lon += 15) {
      var px = (lon + 180) / 360 * TW;
      ctx.moveTo(px, 0); ctx.lineTo(px, TH);
    }
    for (var lat = -75; lat <= 75; lat += 15) {
      var py = (90 - lat) / 180 * TH;
      ctx.moveTo(0, py); ctx.lineTo(TW, py);
    }
    ctx.stroke();

    for (var i = 0; i < world.length; i++) {
      var f = world[i];
      var inLesson = lessonSet && lessonSet.has(f.properties.iso3);
      ctx.beginPath();
      path(f);
      ctx.fillStyle = inLesson ? COLOR.land : COLOR.context;
      ctx.fill();
      ctx.strokeStyle = inLesson ? COLOR.landStroke : COLOR.contextStroke;
      ctx.lineWidth = 1.5;
      ctx.stroke();
    }
    return c;
  }

  function buildSphere() {
    var verts = [];
    for (var j = 0; j <= SEG_LAT; j++) {
      var lat = -90 + (180 * j) / SEG_LAT;
      for (var i = 0; i <= SEG_LON; i++) {
        var lon = -180 + (360 * i) / SEG_LON;
        verts.push(lon, lat);
      }
    }
    var idx = [];
    for (var jj = 0; jj < SEG_LAT; jj++) {
      for (var ii = 0; ii < SEG_LON; ii++) {
        var a = jj * (SEG_LON + 1) + ii;
        var b = a + 1, c2 = a + SEG_LON + 1, d2 = c2 + 1;
        idx.push(a, c2, b, b, c2, d2);
      }
    }
    var buf = gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER, buf);
    gl.bufferData(gl.ARRAY_BUFFER, new Float32Array(verts), gl.STATIC_DRAW);
    var ibuf = gl.createBuffer();
    gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, ibuf);
    gl.bufferData(gl.ELEMENT_ARRAY_BUFFER, new Uint16Array(idx), gl.STATIC_DRAW);
    sphereCount = idx.length;
    return buf;
  }

  function draw() {
    gl.viewport(0, 0, canvas.width, canvas.height);
    gl.clearColor(0, 0, 0, 0);
    gl.clear(gl.COLOR_BUFFER_BIT);
    gl.useProgram(program);
    gl.uniform3f(uRot, currentRot[0], currentRot[1], currentRot[2] || 0);
    gl.drawElements(gl.TRIANGLES, sphereCount, gl.UNSIGNED_SHORT, 0);
  }

  return {
    available: available,

    /* canvasEl: absolutely-positioned <canvas> sized over the svg.
     * world: GeoJSON features array; lessonIso3s: Set of in-lesson iso3. */
    init: function (canvasEl, worldFeatures, lessonIso3s) {
      canvas = canvasEl;
      world = worldFeatures;
      lessonSet = lessonIso3s;
      gl = canvas.getContext("webgl2", { antialias: true }) ||
           canvas.getContext("webgl", { antialias: true });
      if (!gl) {
        console.warn("webgl-globe: WebGL context unavailable on", navigator.userAgent);
        return false;
      }
      console.info("Atlas WebGL globe v9 active (texture-mapped, gamma-aware, viewBox-fit)");
      program = gl.createProgram();
      gl.attachShader(program, compile(gl.VERTEX_SHADER, VS));
      gl.attachShader(program, compile(gl.FRAGMENT_SHADER, FS));
      gl.linkProgram(program);
      if (!gl.getProgramParameter(program, gl.LINK_STATUS)) {
        console.error("webgl-globe link: " + gl.getProgramInfoLog(program));
        return false;
      }
      gl.useProgram(program);
      var aLL = gl.getAttribLocation(program, "a_ll");
      var buf = buildSphere();
      gl.bindBuffer(gl.ARRAY_BUFFER, buf);
      gl.enableVertexAttribArray(aLL);
      gl.vertexAttribPointer(aLL, 2, gl.FLOAT, false, 0, 0);
      uRot = gl.getUniformLocation(program, "u_rot");
      uFit = gl.getUniformLocation(program, "u_fit");
      gl.uniform1i(gl.getUniformLocation(program, "u_tex"), 0);

      if (tex) gl.deleteTexture(tex);
      tex = gl.createTexture();
      gl.activeTexture(gl.TEXTURE0);
      gl.bindTexture(gl.TEXTURE_2D, tex);
      gl.pixelStorei(gl.UNPACK_FLIP_Y_WEBGL, false);
      gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, gl.RGBA, gl.UNSIGNED_BYTE, bakeTexture());
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.REPEAT);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);
      return true;
    },

    /* fit(radiusPx, cssW, cssH, centerXpx, centerYpx):
     * globe disc radius and centre in canvas CSS pixels — computed by
     * map.js from the LIVE viewBox so wheel zoom (cursor-anchored) and
     * layout changes all track. */
    fit: function (radiusPx, cssW, cssH, centerXpx, centerYpx) {
      if (!gl) return;
      var dpr = window.devicePixelRatio || 1;
      var w = Math.max(2, Math.round(cssW * dpr));
      var h = Math.max(2, Math.round(cssH * dpr));
      if (canvas.width !== w || canvas.height !== h) {
        canvas.width = w; canvas.height = h;
      }
      var kx = (radiusPx * dpr) / (w / 2);   // globe radius in clip-x units
      var ky = (radiusPx * dpr) / (h / 2);   // in clip-y units
      var ox = ((centerXpx * dpr) - w / 2) / (w / 2);  // disc centre in clip (x: GL and css share the left origin)
      var oy = ((h - centerYpx * dpr) - h / 2) / (h / 2);  // y: GL origin is BOTTOM, css origin is TOP -> flip
      gl.useProgram(program);
      gl.uniform4f(uFit, kx, ky, ox, oy);
      draw();
    },

    setRotation: function (rot) {
      if (!gl) return;
      currentRot = rot;
      draw();
    },

    /* Re-bake country state colours (revealed/current/highlighted).
     * classFn(iso3) -> array of extra classes for that country. */
    rebake: function () {
      if (!gl || !tex) return;
      gl.bindTexture(gl.TEXTURE_2D, tex);
      gl.pixelStorei(gl.UNPACK_FLIP_Y_WEBGL, false);
      gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, gl.RGBA, gl.UNSIGNED_BYTE, bakeTexture());
      draw();
    },

    dispose: function () {
      if (gl) {
        var ext = gl.getExtension("WEBGL_lose_context");
        if (ext) ext.loseContext();
      }
      gl = null; canvas = null; program = null; tex = null;
    }
  };
})();
