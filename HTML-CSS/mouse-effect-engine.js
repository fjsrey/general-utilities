/*!
 * MouseEffectEngine.js
 * ------------------------------------------------------------
 * Librería para crear efectos visuales interactivos en el navegador
 * en función del movimiento del ratón.
 *
 * ✅ Compatible con navegadores modernos (Chrome, Firefox, Edge, Safari, IE11+)
 * ✅ No usa módulos ni sintaxis moderna incompatible
 *
 * Uso básico:
 *   const engine = new MouseEffectEngine("gridGlow", { ...config });
 *
 * Efectos disponibles:
 *   - "gridGlow": Cuadrícula que reacciona al pasar el ratón.
 *   - "waveTrail": Rastro de ondas al mover el cursor.
 *   - "particleTrail": Partículas flotantes que siguen el ratón.
 *   - "stars": Simula estrellas en 3D que vuelan hacia el usuario.
 *
 * API pública:
 *   - engine.enableEffect(nombre, config)   // Activa un efecto adicional
 *   - engine.disableEffect(nombre)         // Desactiva un efecto
 * ------------------------------------------------------------
 */

function MouseEffectEngine(effectName, config) {
  this.config = config || {};
  
  this.effects = {
    gridGlow: this.gridGlowEffect.bind(this),
    waveTrail: this.waveTrailEffect.bind(this),
    particleTrail: this.particleTrailEffect.bind(this),
    stars: this.starsEffect.bind(this),
    screenDistort: this.screenDistortEffect.bind(this)
  };

  this.activeEffects = {};

  if (this.effects[effectName]) {
    this.enableEffect(effectName, config);
  } else {
    console.warn("Efecto no definido:", effectName);
  }
}

MouseEffectEngine.prototype.enableEffect = function (name, config) {
  if (this.activeEffects[name]) return;
  if (this.effects[name]) {
    this.activeEffects[name] = this.effects[name](config || {});
  }
};

MouseEffectEngine.prototype.disableEffect = function (name) {
  var cleanup = this.activeEffects[name];
  if (typeof cleanup === "function") {
    cleanup();
  }
  delete this.activeEffects[name];
};

MouseEffectEngine.prototype.gridGlowEffect = function (config) {
  var mergedConfig = extend({
    size: 50,
    baseColor: "transparent",
    zIndex: 9999
  }, config);

  var cols = Math.ceil(window.innerWidth / mergedConfig.size);
  var rows = Math.ceil(window.innerHeight / mergedConfig.size);
  var grid = [];

  for (var y = 0; y < rows; y++) {
    for (var x = 0; x < cols; x++) {
      var cell = document.createElement("div");
      cell.className = "meg-cell meg-active";
      cell.style.position = "absolute";
      cell.style.left = (x * mergedConfig.size) + "px";
      cell.style.top = (y * mergedConfig.size) + "px";
      cell.style.width = mergedConfig.size + "px";
      cell.style.height = mergedConfig.size + "px";
      cell.style.backgroundColor = mergedConfig.baseColor;
      cell.style.opacity = "0.5";
      cell.style.transition = "transform 0.4s ease, background-color 0.6s ease, opacity 0.6s ease";
      cell.style.zIndex = mergedConfig.zIndex;

      attachEvent(cell, "mouseenter", gridAnimateIn.bind(null, cell, mergedConfig));
      attachEvent(cell, "mouseleave", gridAnimateOut.bind(null, cell, mergedConfig));

      document.body.appendChild(cell);
      grid.push(cell);
    }
  }

  var self = this;
  function onResize() {
    self.disableEffect("gridGlow");
    self.enableEffect("gridGlow", mergedConfig);
  }

  attachEvent(window, "resize", onResize);

  return function () {
    detachEvent(window, "resize", onResize);
    for (var i = 0; i < grid.length; i++) {
      if (grid[i].parentNode) grid[i].parentNode.removeChild(grid[i]);
    }
  };
};


MouseEffectEngine.prototype.screenDistortEffect = function (config) {
  var mergedConfig = extend({
    intensity: 15,         // Máxima cantidad de distorsión en px
    duration: 300,         // Duración de cada distorsión en ms
    minInterval: 2000,     // Intervalo mínimo entre distorsiones en ms
    maxInterval: 6000,     // Intervalo máximo entre distorsiones en ms
    zIndex: 99999
  }, config);

  var overlay = document.createElement("div");
  overlay.style.position = "fixed";
  overlay.style.left = "0";
  overlay.style.top = "0";
  overlay.style.width = "100vw";
  overlay.style.height = "100vh";
  overlay.style.pointerEvents = "none";
  overlay.style.zIndex = mergedConfig.zIndex;
  overlay.style.transition = "filter 0.2s, transform 0.2s";
  overlay.style.background = "transparent";
  document.body.appendChild(overlay);

  var running = true;
  function randomDistort() {
    if (!running) return;

    // Distorsión: se aplica un filtro y/o transformación
    var x = Math.round(Math.random() * mergedConfig.intensity * 2 - mergedConfig.intensity);
    var y = Math.round(Math.random() * mergedConfig.intensity * 2 - mergedConfig.intensity);
    var scale = 1 + (Math.random() - 0.5) * 0.05;
    var blur = Math.round(Math.random() * 2);
    overlay.style.backdropFilter = "blur(" + blur + "px)";
    overlay.style.transform = "translate(" + x + "px," + y + "px) scale(" + scale + ")";
    overlay.style.background = "rgba(255,255,255,0.01)"; // Sutil overlay

    setTimeout(function () {
      // Quita la distorsión
      overlay.style.backdropFilter = "none";
      overlay.style.transform = "none";
      overlay.style.background = "transparent";
      if (running) {
        var next = Math.random() * (mergedConfig.maxInterval - mergedConfig.minInterval) + mergedConfig.minInterval;
        setTimeout(randomDistort, next);
      }
    }, mergedConfig.duration);
  }

  // Inicia el ciclo de distorsión
  var initial = Math.random() * (mergedConfig.maxInterval - mergedConfig.minInterval) + mergedConfig.minInterval;
  var timer = setTimeout(randomDistort, initial);

  // Cleanup
  return function () {
    running = false;
    clearTimeout(timer);
    if (overlay.parentNode) overlay.parentNode.removeChild(overlay);
  };
};



function gridAnimateIn(cell, config) {
  var maxScale = Math.random() * 2 + 1.2;
  var newColor = "hsl(" + Math.floor(Math.random() * 360) + ",100%,70%)";
  cell.style.transform = "scale(" + maxScale + ")";
  cell.style.opacity = 0.9;
  cell.style.backgroundColor = newColor;
}

function gridAnimateOut(cell, config) {
  cell.style.transform = "scale(1)";
  cell.style.opacity = 0.5;
  cell.style.backgroundColor = config.baseColor;
}

MouseEffectEngine.prototype.waveTrailEffect = function (config) {
  var mergedConfig = extend({
    trailColor: "rgba(0,255,255,0.3)",
    trailSize: 15,
    lifetime: 500,
    zIndex: 9999
  }, config);

  var style = document.createElement("style");
  style.innerHTML =
    ".wave-trail-dot{" +
    "position:absolute;border-radius:50%;pointer-events:none;" +
    "width:" + mergedConfig.trailSize + "px;height:" + mergedConfig.trailSize + "px;" +
    "background-color:" + mergedConfig.trailColor + ";z-index:" + mergedConfig.zIndex + ";" +
    "animation:wave-fadeout " + mergedConfig.lifetime + "ms forwards ease-out;" +
    "}" +
    "@keyframes wave-fadeout{" +
    "0%{transform:scale(1);opacity:1;}" +
    "100%{transform:scale(2);opacity:0;}" +
    "}";
  document.head.appendChild(style);

  function handler(e) {
    var dot = document.createElement("div");
    dot.className = "wave-trail-dot";
    dot.style.left = (e.clientX - mergedConfig.trailSize / 2) + "px";
    dot.style.top = (e.clientY - mergedConfig.trailSize / 2) + "px";
    document.body.appendChild(dot);
    setTimeout(function () {
      if (dot.parentNode) dot.parentNode.removeChild(dot);
    }, mergedConfig.lifetime + 50);
  }

  attachEvent(document, "mousemove", handler);

  return function () {
    detachEvent(document, "mousemove", handler);
    if (style.parentNode) style.parentNode.removeChild(style);
  };
};

MouseEffectEngine.prototype.particleTrailEffect = function (config) {
  var mergedConfig = extend({
    particleCount: 3,
    size: 6,
    color: "#ffffff",
    lifetime: 1000,
    zIndex: 10000
  }, config);

  var style = document.createElement("style");
  style.innerHTML =
    ".particle{" +
    "position:absolute;border-radius:50%;pointer-events:none;" +
    "width:" + mergedConfig.size + "px;height:" + mergedConfig.size + "px;" +
    "background-color:" + mergedConfig.color + ";opacity:1;" +
    "z-index:" + mergedConfig.zIndex + ";" +
    "animation:particle-fade " + mergedConfig.lifetime + "ms linear forwards;" +
    "}" +
    "@keyframes particle-fade{" +
    "to{transform:translateY(-20px) scale(0.5);opacity:0;}" +
    "}";
  document.head.appendChild(style);

  function handler(e) {
    for (var i = 0; i < mergedConfig.particleCount; i++) {
      var dot = document.createElement("div");
      dot.className = "particle";
      dot.style.left = (e.clientX + (Math.random() * 20 - 10)) + "px";
      dot.style.top = (e.clientY + (Math.random() * 20 - 10)) + "px";
      document.body.appendChild(dot);
      (function (el) {
        setTimeout(function () {
          if (el.parentNode) el.parentNode.removeChild(el);
        }, mergedConfig.lifetime + 50);
      })(dot);
    }
  }

  attachEvent(document, "mousemove", handler);

  return function () {
    detachEvent(document, "mousemove", handler);
    if (style.parentNode) style.parentNode.removeChild(style);
  };
};

MouseEffectEngine.prototype.starsEffect = function (config) {
  var mergedConfig = extend({
    starCount: 150,
    color: "#ffffff",
    size: 2,
    speed: 2,
    zIndex: 999,
    perspective: 800
  }, config);

  var stars = [];
  var mouseX = 0, mouseY = 0;
  var width = window.innerWidth;
  var height = window.innerHeight;
  var centerX = width / 2;
  var centerY = height / 2;

  var container = document.createElement("div");
  container.style.position = "fixed";
  container.style.top = 0;
  container.style.left = 0;
  container.style.width = "100%";
  container.style.height = "100%";
  container.style.zIndex = mergedConfig.zIndex;
  container.style.pointerEvents = "none";
  container.style.overflow = "hidden";
  document.body.appendChild(container);

  for (var i = 0; i < mergedConfig.starCount; i++) {
    var star = document.createElement("div");
    star.style.position = "absolute";
    star.style.width = mergedConfig.size + "px";
    star.style.height = mergedConfig.size + "px";
    star.style.backgroundColor = mergedConfig.color;
    star.style.borderRadius = "50%";
    resetStar(star);
    container.appendChild(star);
    stars.push(star);
  }

  function resetStar(star) {
    star._x = (Math.random() - 0.5) * width * 2;
    star._y = (Math.random() - 0.5) * height * 2;
    star._z = Math.random() * mergedConfig.perspective;
  }

  function animateStars() {
    for (var i = 0; i < stars.length; i++) {
      var star = stars[i];
      star._z -= mergedConfig.speed;
      if (star._z <= 0) resetStar(star);

      var perspective = mergedConfig.perspective / star._z;
      var x = star._x * perspective + centerX + (mouseX - centerX) * 0.02;
      var y = star._y * perspective + centerY + (mouseY - centerY) * 0.02;

      if (x < 0 || x > width || y < 0 || y > height) {
        resetStar(star);
        continue;
      }

      star.style.left = x + "px";
      star.style.top = y + "px";
      star.style.opacity = 1 - star._z / mergedConfig.perspective;
      star.style.transform = "scale(" + (1 - star._z / mergedConfig.perspective) + ")";
    }

    requestAnimationFrame(animateStars);
  }

  function onMouseMove(e) {
    mouseX = e.clientX;
    mouseY = e.clientY;
  }

  attachEvent(document, "mousemove", onMouseMove);
  animateStars();

  return function () {
    detachEvent(document, "mousemove", onMouseMove);
    if (container.parentNode) container.parentNode.removeChild(container);
  };
};

function extend(target, source) {
  for (var key in source) {
    if (source.hasOwnProperty(key)) {
      target[key] = source[key];
    }
  }
  return target;
}

function attachEvent(el, evt, handler) {
  if (el.addEventListener) el.addEventListener(evt, handler, false);
  else if (el.attachEvent) el.attachEvent("on" + evt, handler);
}

function detachEvent(el, evt, handler) {
  if (el.removeEventListener) el.removeEventListener(evt, handler, false);
  else if (el.detachEvent) el.detachEvent("on" + evt, handler);
}
