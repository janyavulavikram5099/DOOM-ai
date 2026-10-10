/**
 * VIKRAM AI - Cinema-Grade 3D Holographic Spherical AI Core & Waveform Visualizer
 * Golden-Amber Holographic Globe (Faithfully recreated from Marvel / EDITH / Hologram Core Reference).
 * Features:
 *   - Volumetric 3D spherical point cloud (320+ nodes) with glowing golden nodes and holographic mesh filaments
 *   - Multi-latitude 3D circular rings with sci-fi tick marks and rotating segment blocks
 *   - Multiple gyroscopic tilted orbital rings with independent spin velocities
 *   - 3D orbiting data sparks and energy fragments floating around the sphere
 *   - Sci-fi outer chronometer dial with radial tick notches and rotating caliper brackets
 *   - Radiant golden energy core with pulsating corona filaments
 *   - Dynamic voice and audio reactivity (expands sphere, accelerates spin, intensifies bloom)
 */

class CoreVisualizer {
  constructor(coreCanvasId, waveCanvasId) {
    this.coreCanvas = document.getElementById(coreCanvasId);
    this.coreCtx = this.coreCanvas ? this.coreCanvas.getContext('2d') : null;

    this.waveCanvas = document.getElementById(waveCanvasId);
    this.waveCtx = this.waveCanvas ? this.waveCanvas.getContext('2d') : null;

    // Tactical World Map Backdrop Canvas (Backside of AI Circle)
    this.mapBackdropCanvas = document.getElementById('world-map-backdrop-canvas');
    this.mapBackdropCtx = this.mapBackdropCanvas ? this.mapBackdropCanvas.getContext('2d') : null;
    this.backdropPanLon = 0;

    this.audioLevel = 0.0;
    this.targetLevel = 0.0;
    this.phase = 0;
    this.state = 'IDLE';

    // 3D Angles
    this.rotY = 0;          // Continuous primary yaw spin
    this.rotX = 0.44;       // 25° pitch tilt towards camera
    this.rotZ = 0.09;       // subtle roll tilt
    this.orbitAngle1 = 0;   // Gyroscopic ring 1
    this.orbitAngle2 = 0;   // Gyroscopic ring 2
    this.orbitAngle3 = 0;   // Gyroscopic ring 3
    this.orbitAngle4 = 0;   // Gyroscopic ring 4

    // Base Dimensions
    this.baseRadius = 124;
    this.persp = 440;

    // Initialize 3D Fibonacci Sphere Nodes (140 nodes for crisp holographic transparency)
    this.nodes = [];
    this.initSphericalNodes(140);

    // Initialize floating orbital sparks
    this.sparks = [];
    this.initOrbitalSparks(45);

    // Initialize Outer HUD Ticks
    this.ticks = [];
    for (let i = 0; i < 72; i++) {
      this.ticks.push({
        angle: (i / 72) * Math.PI * 2,
        isMajor: i % 6 === 0
      });
    }

    // Initialize Cosmic Starfield (240+ twinkling stars filling the AI circle)
    this.stars = [];
    this.shootingStars = [];
    this.lastShootingStarTime = 0;
    this.initStarfield(240);

    // Initialize World Map (Tactical Background & 3D Rotating Continents)
    this.mapPanLon = 0;
    this.initWorldMap();

    this.animate = this.animate.bind(this);
    requestAnimationFrame(this.animate);
  }

  initSphericalNodes(count) {
    this.nodes = [];
    const goldenRatio = (1 + Math.sqrt(5)) / 2;
    const phi = 2 * Math.PI * (1 - 1 / goldenRatio); // ~2.39996 rad

    for (let i = 0; i < count; i++) {
      const y = 1 - (i / (count - 1)) * 2; // y: 1 to -1
      const radiusAtY = Math.sqrt(Math.max(0, 1 - y * y));
      const theta = phi * i;

      const x = Math.cos(theta) * radiusAtY;
      const z = Math.sin(theta) * radiusAtY;

      this.nodes.push({
        baseX: x,
        baseY: y,
        baseZ: z,
        size: (i % 6 === 0) ? 2.5 : (i % 3 === 0 ? 1.8 : 1.2),
        sparklePhase: Math.random() * Math.PI * 2,
        sparkleSpeed: 0.03 + Math.random() * 0.05,
        isBeacon: i % 12 === 0
      });
    }
  }

  initOrbitalSparks(count) {
    this.sparks = [];
    for (let i = 0; i < count; i++) {
      this.sparks.push({
        radiusMul: 0.85 + Math.random() * 0.45,
        inclination: (Math.random() - 0.5) * Math.PI,
        azimuth: Math.random() * Math.PI * 2,
        speed: (0.01 + Math.random() * 0.02) * (Math.random() > 0.5 ? 1 : -1),
        size: 0.8 + Math.random() * 1.6,
        opacity: 0.4 + Math.random() * 0.6
      });
    }
  }

  initStarfield(count) {
    this.stars = [];
    for (let i = 0; i < count; i++) {
      // Uniform circular distribution (sqrt ensures even areal density)
      const r = Math.sqrt(Math.random()) * 172;
      const angle = Math.random() * Math.PI * 2;
      const randType = Math.random();

      let size, isHero = false;
      if (randType > 0.92) {
        size = 1.9 + Math.random() * 1.1; // Bright hero sparkle star
        isHero = true;
      } else if (randType > 0.62) {
        size = 1.0 + Math.random() * 0.8; // Medium glowing star
      } else {
        size = 0.4 + Math.random() * 0.55; // Distant micro star
      }

      // Star spectral colors (diamond white, cyber cyan, emerald starlight)
      const hueChoice = Math.random();
      let color;
      if (hueChoice > 0.55) {
        color = '255, 255, 255';
      } else if (hueChoice > 0.3) {
        color = '185, 255, 235';
      } else if (hueChoice > 0.12) {
        color = '95, 255, 175';
      } else {
        color = '220, 245, 255';
      }

      this.stars.push({
        r: r,
        angle: angle,
        baseSize: size,
        isHero: isHero,
        color: color,
        twinklePhase: Math.random() * Math.PI * 2,
        twinkleSpeed: 0.02 + Math.random() * 0.055,
        driftSpeed: (0.00025 + Math.random() * 0.0005) * (i % 2 === 0 ? 1 : -1),
        pulseBase: 0.35 + Math.random() * 0.45
      });
    }

    this.shootingStars = [];
    this.lastShootingStarTime = 0;
  }

  initWorldMap() {
    this.worldPolygons = (typeof window !== 'undefined' && window.WORLD_MAP_POLYGONS) ? window.WORLD_MAP_POLYGONS : [];
    this.worldCapitals = (typeof window !== 'undefined' && window.WORLD_CAPITALS) ? window.WORLD_CAPITALS : [];

    // Pre-calculate 3D spherical vertices for all polygon rings
    this.world3DPolygons = [];
    if (this.worldPolygons && this.worldPolygons.length > 0) {
      for (let i = 0; i < this.worldPolygons.length; i++) {
        const ring = this.worldPolygons[i];
        const ring3D = [];
        for (let j = 0; j < ring.length; j++) {
          const lon = ring[j][0];
          const lat = ring[j][1];
          const radLon = (lon * Math.PI) / 180;
          const radLat = (lat * Math.PI) / 180;
          ring3D.push({
            x: Math.cos(radLat) * Math.sin(radLon),
            y: -Math.sin(radLat),
            z: Math.cos(radLat) * Math.cos(radLon)
          });
        }
        this.world3DPolygons.push(ring3D);
      }
    }
  }

  setAudioLevel(level) {
    this.targetLevel = Math.max(0, Math.min(1.0, level));
  }

  setState(state) {
    this.state = state;
    const coreEl = document.getElementById('ai-core');
    if (!coreEl) return;

    coreEl.className = 'ai-core-container';

    switch (state) {
      case 'LISTENING':
        coreEl.classList.add('state-listening');
        break;
      case 'PROCESSING':
        coreEl.classList.add('state-processing');
        break;
      case 'EXECUTING':
        coreEl.classList.add('state-executing');
        break;
      case 'SPEAKING':
        coreEl.classList.add('state-speaking');
        break;
      case 'SUCCESS':
        coreEl.classList.add('state-success');
        break;
      case 'ERROR':
        coreEl.classList.add('state-error');
        break;
      case 'AUTHENTICATION REQUIRED':
        coreEl.classList.add('state-security');
        break;
      default:
        coreEl.classList.add('state-idle');
        break;
    }
  }

  // 3D Matrix Projection
  project3D(x, y, z, cx, cy, R) {
    const px = x * R;
    const py = y * R;
    const pz = z * R;

    // 1. Yaw rotation around Y axis
    const cosY = Math.cos(this.rotY), sinY = Math.sin(this.rotY);
    const x1 = px * cosY + pz * sinY;
    const z1 = -px * sinY + pz * cosY;

    // 2. Pitch tilt around X axis
    const cosX = Math.cos(this.rotX), sinX = Math.sin(this.rotX);
    const y2 = py * cosX - z1 * sinX;
    const z2 = py * sinX + z1 * cosX;

    // 3. Roll around Z axis
    const cosZ = Math.cos(this.rotZ), sinZ = Math.sin(this.rotZ);
    const x3 = x1 * cosZ - y2 * sinZ;
    const y3 = x1 * sinZ + y2 * cosZ;

    // Perspective projection
    const scale = this.persp / (this.persp + z2);
    const screenX = cx + x3 * scale;
    const screenY = cy + y3 * scale;

    const normZ = z2 / R;
    const alpha = Math.max(0.12, Math.min(1.0, (normZ + 1.25) / 2.3));

    return {
      x: screenX,
      y: screenY,
      z: z2,
      scale: scale,
      alpha: alpha,
      isFront: z2 > -15
    };
  }

  // Project tilted orbital ring point
  projectTilted(radius, angle, tiltX, tiltZ, spinAngle, cx, cy) {
    const rx = Math.cos(angle + spinAngle) * radius;
    const rz = Math.sin(angle + spinAngle) * radius;
    const ry = 0;

    const cosTX = Math.cos(tiltX), sinTX = Math.sin(tiltX);
    const y1 = ry * cosTX - rz * sinTX;
    const z1 = ry * sinTX + rz * cosTX;

    const cosTZ = Math.cos(tiltZ), sinTZ = Math.sin(tiltZ);
    const x2 = rx * cosTZ - y1 * sinTZ;
    const y2 = rx * sinTZ + y1 * cosTZ;

    const cosY = Math.cos(this.rotY * 0.45), sinY = Math.sin(this.rotY * 0.45);
    const x3 = x2 * cosY + z1 * sinY;
    const z3 = -x2 * sinY + z1 * cosY;

    const scale = this.persp / (this.persp + z3);
    return {
      x: cx + x3 * scale,
      y: cy + y2 * scale,
      z: z3,
      alpha: Math.max(0.15, Math.min(1.0, (z3 + radius) / (2 * radius)))
    };
  }

  drawCoreHologram() {
    if (!this.coreCtx) return;
    const ctx = this.coreCtx;
    const w = this.coreCanvas.width;
    const h = this.coreCanvas.height;
    const cx = w / 2;
    const cy = h / 2;

    ctx.clearRect(0, 0, w, h);

    // Audio level smoothing
    this.audioLevel += (this.targetLevel - this.audioLevel) * 0.22;
    const bounce = this.audioLevel * 20;
    const currentR = this.baseRadius + bounce;

    // Speed calculation
    let spinSpeed = 0.0085;
    if (this.state === 'PROCESSING') spinSpeed = 0.04;
    else if (this.state === 'LISTENING') spinSpeed = 0.016;
    else if (this.state === 'SPEAKING') spinSpeed = 0.02 + this.audioLevel * 0.022;

    this.rotY += spinSpeed;
    this.orbitAngle1 += spinSpeed * 1.4;
    this.orbitAngle2 -= spinSpeed * 1.1;
    this.orbitAngle3 += spinSpeed * 0.85;
    this.orbitAngle4 -= spinSpeed * 1.6;

    // Color tones (Cyber Matrix Neon Green)
    let primaryGold = '0, 255, 136';
    let brightGold = '180, 255, 215';
    let haloAmber = '0, 200, 100';

    if (this.state === 'ERROR') {
      primaryGold = '255, 60, 90';
      brightGold = '255, 180, 190';
      haloAmber = '255, 20, 40';
    } else if (this.state === 'SUCCESS') {
      primaryGold = '0, 255, 170';
      brightGold = '180, 255, 220';
      haloAmber = '0, 200, 120';
    }

    // 0. Cosmic Starfield Background filling the AI Circle
    this.drawStarfield(ctx, cx, cy, primaryGold, brightGold);

    // 1. Outer 2D Sci-Fi Dial & Tick Ring
    this.drawOuterHUD(ctx, cx, cy, primaryGold, brightGold);

    // 2. 3D Latitude Rings
    this.drawLatitudeRings(ctx, cx, cy, currentR, primaryGold, brightGold);

    // 3. 3D Longitude Meridians
    this.drawMeridians(ctx, cx, cy, currentR, primaryGold);

    // 4. Gyroscopic Tilted Orbiting Rings & Bright Arc Sectors
    this.drawOrbitRings(ctx, cx, cy, currentR, primaryGold, brightGold);

    // 5. Volumetric Point Cloud & Holographic Circuit Mesh
    this.drawPointCloud(ctx, cx, cy, currentR, primaryGold, brightGold, haloAmber);

    // 6. Floating 3D Orbital Sparks
    this.drawOrbitalSparks(ctx, cx, cy, currentR, primaryGold, brightGold);

    // 7. Luminous Golden Energy Core & Radial Corona
    this.drawCenterEnergyCore(ctx, cx, cy, primaryGold, brightGold);
  }

  // --- Cosmic Starfield & Tactical World Map Background filling the AI Circle ---
  drawStarfield(ctx, cx, cy, primaryGold, brightGold) {
    const starRadius = 175;

    ctx.save();
    // Clip strictly to the circular AI Core dial interior
    ctx.beginPath();
    ctx.arc(cx, cy, starRadius, 0, Math.PI * 2);
    ctx.clip();

    // 1. Deep cosmic space void background
    const spaceGrad = ctx.createRadialGradient(cx, cy, 15, cx, cy, starRadius);
    spaceGrad.addColorStop(0, 'rgba(2, 22, 14, 0.88)');
    spaceGrad.addColorStop(0.55, 'rgba(1, 14, 9, 0.94)');
    spaceGrad.addColorStop(0.85, 'rgba(1, 7, 5, 0.97)');
    spaceGrad.addColorStop(1, 'rgba(0, 3, 2, 0.99)');
    ctx.fillStyle = spaceGrad;
    ctx.fill();

    // 2. Swirling Cosmic Nebula Cloud
    const t = performance.now() * 0.0006;
    const nebGrad = ctx.createRadialGradient(
      cx + Math.cos(t * 0.5) * 45,
      cy + Math.sin(t * 0.4) * 40,
      10,
      cx,
      cy,
      starRadius * 0.92
    );
    nebGrad.addColorStop(0, `rgba(${primaryGold}, 0.09)`);
    nebGrad.addColorStop(0.5, `rgba(${primaryGold}, 0.035)`);
    nebGrad.addColorStop(1, 'transparent');
    ctx.fillStyle = nebGrad;
    ctx.fill();

    // Secondary deep-space dust veil
    const dustGrad = ctx.createRadialGradient(
      cx - Math.sin(t * 0.3) * 55,
      cy + Math.cos(t * 0.3) * 50,
      15,
      cx,
      cy,
      starRadius * 0.85
    );
    dustGrad.addColorStop(0, 'rgba(0, 180, 220, 0.05)');
    dustGrad.addColorStop(0.6, 'rgba(0, 120, 150, 0.02)');
    dustGrad.addColorStop(1, 'transparent');
    ctx.fillStyle = dustGrad;
    ctx.fill();

    // 3. Draw Stars
    for (let i = 0; i < this.stars.length; i++) {
      const s = this.stars[i];
      // Slow orbital drift
      s.angle += s.driftSpeed;
      s.twinklePhase += s.twinkleSpeed;

      const sx = cx + Math.cos(s.angle) * s.r;
      const sy = cy + Math.sin(s.angle) * s.r;

      // Twinkle calculation
      const twinkle = Math.sin(s.twinklePhase);
      const alpha = Math.max(0.18, Math.min(1.0, s.pulseBase + twinkle * 0.45));
      const currentSize = s.baseSize * (1 + twinkle * 0.22);

      // Star outer glow for hero / medium stars
      if (s.isHero || s.baseSize > 1.3) {
        ctx.beginPath();
        ctx.arc(sx, sy, currentSize * 2.6, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(${s.color}, ${alpha * 0.25})`;
        ctx.fill();

        // 4-point sparkle cross-spikes on hero stars
        if (s.isHero && alpha > 0.45) {
          const spikeLen = currentSize * 3.6;
          ctx.strokeStyle = `rgba(${s.color}, ${alpha * 0.65})`;
          ctx.lineWidth = 0.85;
          ctx.beginPath();
          // Horizontal spike
          ctx.moveTo(sx - spikeLen, sy);
          ctx.lineTo(sx + spikeLen, sy);
          // Vertical spike
          ctx.moveTo(sx, sy - spikeLen);
          ctx.lineTo(sx, sy + spikeLen);
          ctx.stroke();
        }
      }

      // Star core
      ctx.beginPath();
      ctx.arc(sx, sy, currentSize, 0, Math.PI * 2);
      ctx.fillStyle = `rgba(${s.color}, ${alpha})`;
      ctx.fill();
    }

    // 4. Occasional Shooting Star / Meteor Streak
    const now = performance.now();
    if (now - this.lastShootingStarTime > 2800 && Math.random() < 0.035) {
      this.lastShootingStarTime = now;
      const startAngle = Math.random() * Math.PI * 2;
      const startDist = 158;
      const sx = cx + Math.cos(startAngle) * startDist;
      const sy = cy + Math.sin(startAngle) * startDist;
      const travelAngle = startAngle + Math.PI * 0.72 + (Math.random() - 0.5) * 0.5;
      const speed = 4.8 + Math.random() * 3.2;

      this.shootingStars.push({
        x: sx,
        y: sy,
        vx: Math.cos(travelAngle) * speed,
        vy: Math.sin(travelAngle) * speed,
        len: 26 + Math.random() * 24,
        life: 1.0,
        decay: 0.024 + Math.random() * 0.018,
        color: Math.random() > 0.4 ? '210, 255, 235' : '255, 255, 255'
      });
    }

    // Render active shooting stars
    for (let i = this.shootingStars.length - 1; i >= 0; i--) {
      const ss = this.shootingStars[i];
      ss.x += ss.vx;
      ss.y += ss.vy;
      ss.life -= ss.decay;

      if (ss.life <= 0) {
        this.shootingStars.splice(i, 1);
        continue;
      }

      const tailX = ss.x - ss.vx * (ss.len / 5);
      const tailY = ss.y - ss.vy * (ss.len / 5);

      const meteorGrad = ctx.createLinearGradient(tailX, tailY, ss.x, ss.y);
      meteorGrad.addColorStop(0, 'rgba(0, 255, 150, 0)');
      meteorGrad.addColorStop(0.65, `rgba(${ss.color}, ${ss.life * 0.55})`);
      meteorGrad.addColorStop(1, `rgba(255, 255, 255, ${ss.life * 0.95})`);

      ctx.beginPath();
      ctx.moveTo(tailX, tailY);
      ctx.lineTo(ss.x, ss.y);
      ctx.strokeStyle = meteorGrad;
      ctx.lineWidth = 1.6;
      ctx.stroke();

      // Meteor head glow
      ctx.beginPath();
      ctx.arc(ss.x, ss.y, 2.0, 0, Math.PI * 2);
      ctx.fillStyle = `rgba(255, 255, 255, ${ss.life})`;
      ctx.fill();
    }

    ctx.restore();
  }

  // --- Tactical Holographic World Map on Backside of Circle ---
  drawTacticalWorldMapBackdrop() {
    if (!this.mapBackdropCtx) return;
    const ctx = this.mapBackdropCtx;
    const w = this.mapBackdropCanvas.width;
    const h = this.mapBackdropCanvas.height;
    const cx = w / 2;
    const cy = h / 2;

    ctx.clearRect(0, 0, w, h);

    if (!this.worldPolygons || this.worldPolygons.length === 0) {
      this.initWorldMap();
      if (!this.worldPolygons || this.worldPolygons.length === 0) return;
    }

    // Planetary slow drift
    this.backdropPanLon = (this.backdropPanLon + 0.035) % 360;

    let primaryColor = '0, 255, 136';
    let brightColor = '180, 255, 220';
    if (this.state === 'ERROR') {
      primaryColor = '255, 60, 90';
      brightColor = '255, 180, 190';
    } else if (this.state === 'SUCCESS') {
      primaryColor = '0, 255, 170';
      brightColor = '180, 255, 230';
    }

    const mapW = 860;
    const mapH = 430;
    const halfW = mapW / 2;
    const halfH = mapH / 2;

    ctx.save();

    // 1. Concentric Tactical Radar Range Rings behind the circle
    ctx.lineWidth = 0.8;
    [150, 230, 320, 420].forEach((r, idx) => {
      ctx.beginPath();
      ctx.arc(cx, cy, r, 0, Math.PI * 2);
      ctx.setLineDash(idx % 2 === 0 ? [4, 6] : [2, 8]);
      ctx.strokeStyle = `rgba(${primaryColor}, ${0.18 - idx * 0.03})`;
      ctx.stroke();
    });
    ctx.setLineDash([]);

    // 2. Latitude Grid Parallels & Labels
    const lats = [-60, -30, 0, 30, 60];
    for (let i = 0; i < lats.length; i++) {
      const lat = lats[i];
      const y = cy - (lat / 90) * halfH;

      ctx.beginPath();
      if (lat === 0) {
        ctx.setLineDash([8, 4]);
        ctx.strokeStyle = `rgba(${brightColor}, 0.5)`;
        ctx.lineWidth = 1.3;
      } else {
        ctx.setLineDash([3, 5]);
        ctx.strokeStyle = `rgba(${primaryColor}, 0.22)`;
        ctx.lineWidth = 0.8;
      }
      ctx.moveTo(cx - halfW, y);
      ctx.lineTo(cx + halfW, y);
      ctx.stroke();

      // Degree label
      ctx.font = '600 9px "Courier New", monospace';
      ctx.fillStyle = `rgba(${primaryColor}, 0.55)`;
      const latStr = lat === 0 ? 'EQUATOR 0°' : (lat > 0 ? `${lat}°N` : `${Math.abs(lat)}°S`);
      ctx.fillText(latStr, cx - halfW - 2, y - 3);
    }

    // 3. Longitude Meridians
    ctx.setLineDash([3, 5]);
    ctx.lineWidth = 0.8;
    ctx.strokeStyle = `rgba(${primaryColor}, 0.22)`;
    for (let m = -180; m <= 180; m += 30) {
      const adjM = ((m + this.backdropPanLon + 180) % 360) - 180;
      const x = cx + (adjM / 180) * halfW;
      if (x >= cx - halfW && x <= cx + halfW) {
        ctx.beginPath();
        ctx.moveTo(x, cy - halfH);
        ctx.lineTo(x, cy + halfH);
        ctx.stroke();
      }
    }
    ctx.setLineDash([]);

    // 4. Continents Vector Polygons
    ctx.lineWidth = 1.4;
    ctx.strokeStyle = `rgba(${brightColor}, 0.75)`;
    ctx.fillStyle = `rgba(${primaryColor}, 0.09)`;
    ctx.shadowColor = `rgb(${primaryColor})`;
    ctx.shadowBlur = 6;

    for (let i = 0; i < this.worldPolygons.length; i++) {
      const poly = this.worldPolygons[i];
      if (poly.length < 3) continue;

      ctx.beginPath();
      let hasStarted = false;
      let prevX = 0;

      for (let j = 0; j < poly.length; j++) {
        const pt = poly[j];
        const lon = pt[0];
        const lat = pt[1];

        const adjLon = ((lon + this.backdropPanLon + 180) % 360) - 180;
        const px = cx + (adjLon / 180) * halfW;
        const py = cy - (lat / 90) * halfH;

        if (!hasStarted) {
          ctx.moveTo(px, py);
          hasStarted = true;
          prevX = px;
        } else {
          if (Math.abs(px - prevX) > 200) {
            ctx.moveTo(px, py);
          } else {
            ctx.lineTo(px, py);
          }
          prevX = px;
        }
      }
      ctx.closePath();
      ctx.fill();
      ctx.stroke();
    }

    // 5. Strategic Inter-Continental Data Arcs (Flight / Comms Lines)
    const now = performance.now();
    const hubs = {};
    for (let i = 0; i < this.worldCapitals.length; i++) {
      const cap = this.worldCapitals[i];
      const adjLon = ((cap.lon + this.backdropPanLon + 180) % 360) - 180;
      hubs[cap.name] = {
        x: cx + (adjLon / 180) * halfW,
        y: cy - (cap.lat / 90) * halfH,
        name: cap.name
      };
    }

    const dataRoutes = [
      ['NEW YORK', 'LONDON'],
      ['LONDON', 'PARIS'],
      ['PARIS', 'CAIRO'],
      ['CAIRO', 'DUBAI'],
      ['DUBAI', 'NEW DELHI'],
      ['NEW DELHI', 'SINGAPORE'],
      ['SINGAPORE', 'TOKYO'],
      ['TOKYO', 'SYDNEY'],
      ['SAN FRANCISCO', 'TOKYO'],
      ['NEW YORK', 'SAO PAULO'],
      ['MOSCOW', 'BEIJING']
    ];

    ctx.shadowBlur = 0;
    for (let r = 0; r < dataRoutes.length; r++) {
      const [fromName, toName] = dataRoutes[r];
      const h1 = hubs[fromName];
      const h2 = hubs[toName];
      if (!h1 || !h2) continue;

      if (Math.abs(h1.x - h2.x) > 360) continue;

      const midX = (h1.x + h2.x) / 2;
      const midY = Math.min(h1.y, h2.y) - 35;

      // Arc curve
      ctx.beginPath();
      ctx.moveTo(h1.x, h1.y);
      ctx.quadraticCurveTo(midX, midY, h2.x, h2.y);
      ctx.strokeStyle = `rgba(${primaryColor}, 0.28)`;
      ctx.setLineDash([4, 4]);
      ctx.lineWidth = 1;
      ctx.stroke();

      // Traveling data packet
      const t = (now * 0.0006 + r * 0.18) % 1;
      const px = (1 - t) * (1 - t) * h1.x + 2 * (1 - t) * t * midX + t * t * h2.x;
      const py = (1 - t) * (1 - t) * h1.y + 2 * (1 - t) * t * midY + t * t * h2.y;

      ctx.beginPath();
      ctx.arc(px, py, 2.4, 0, Math.PI * 2);
      ctx.fillStyle = '#ffffff';
      ctx.shadowBlur = 8;
      ctx.shadowColor = `rgb(${brightColor})`;
      ctx.fill();
    }
    ctx.setLineDash([]);

    // 6. Strategic Global Capital Beacons
    for (let i = 0; i < this.worldCapitals.length; i++) {
      const cap = this.worldCapitals[i];
      const hub = hubs[cap.name];
      if (!hub) continue;

      if (hub.x < 10 || hub.x > w - 10) continue;

      // Hub Beacon Core
      ctx.beginPath();
      ctx.arc(hub.x, hub.y, 2.5, 0, Math.PI * 2);
      ctx.fillStyle = '#ffffff';
      ctx.shadowBlur = 8;
      ctx.shadowColor = `rgb(${brightColor})`;
      ctx.fill();

      // Sonar Pulse Ring
      const ripple = (now * 0.0014 + i * 0.35) % 1;
      const rippleR = 3 + ripple * 14;
      const rippleAlpha = (1 - ripple) * 0.7;

      ctx.beginPath();
      ctx.arc(hub.x, hub.y, rippleR, 0, Math.PI * 2);
      ctx.strokeStyle = `rgba(${brightColor}, ${rippleAlpha})`;
      ctx.lineWidth = 0.9;
      ctx.stroke();

      // Label
      ctx.font = '700 8px "Courier New", monospace';
      ctx.fillStyle = `rgba(${brightColor}, 0.85)`;
      ctx.fillText(cap.name, hub.x + 6, hub.y - 4);
    }

    // 7. Tactical Radar Recon Sweep Beam
    const sweepAngle = (now * 0.0007) % (Math.PI * 2);
    const sweepR = 430;
    const sweepX = cx + Math.cos(sweepAngle) * sweepR;
    const sweepY = cy + Math.sin(sweepAngle) * sweepR;

    const sweepGrad = ctx.createLinearGradient(cx, cy, sweepX, sweepY);
    sweepGrad.addColorStop(0, `rgba(${primaryColor}, 0.16)`);
    sweepGrad.addColorStop(0.7, `rgba(${primaryColor}, 0.03)`);
    sweepGrad.addColorStop(1, 'transparent');

    ctx.beginPath();
    ctx.moveTo(cx, cy);
    ctx.arc(cx, cy, sweepR, sweepAngle - 0.35, sweepAngle);
    ctx.closePath();
    ctx.fillStyle = sweepGrad;
    ctx.fill();

    ctx.beginPath();
    ctx.moveTo(cx, cy);
    ctx.lineTo(sweepX, sweepY);
    ctx.strokeStyle = `rgba(${brightColor}, 0.55)`;
    ctx.lineWidth = 1.2;
    ctx.stroke();

    // 8. Corner Tactical Telemetry Badges
    ctx.font = '700 9px "Courier New", monospace';
    ctx.fillStyle = `rgba(${primaryColor}, 0.75)`;
    ctx.fillText('[TACTICAL GLOBAL RECON // ORBITAL 450KM]', cx - halfW + 10, cy - halfH + 18);
    ctx.fillText('[GEO-GRID: 360° x 180° // 163 ACTIVE SECTORS]', cx + halfW - 250, cy - halfH + 18);
    ctx.fillText('[LOCATION: 28.6139° N, 77.2090° E // ASIA-PACIFIC]', cx - halfW + 10, cy + halfH - 8);
    ctx.fillText('[SURVEILLANCE MATRIX: ONLINE // 100% OFFLINE]', cx + halfW - 250, cy + halfH - 8);

    // 9. Soft Edge Vignette (Blends smoothly into dark cyber grid)
    const vignette = ctx.createRadialGradient(cx, cy, 280, cx, cy, 470);
    vignette.addColorStop(0, 'transparent');
    vignette.addColorStop(1, 'rgba(2, 12, 7, 0.95)');
    ctx.fillStyle = vignette;
    ctx.fillRect(0, 0, w, h);

    ctx.restore();
  }

  // --- Outer 2D Sci-Fi Chronometer Dial ---
  drawOuterHUD(ctx, cx, cy, primaryGold, brightGold) {
    const dialR = 175;

    // Outer guide circle
    ctx.beginPath();
    ctx.arc(cx, cy, dialR, 0, Math.PI * 2);
    ctx.strokeStyle = `rgba(${primaryGold}, 0.28)`;
    ctx.lineWidth = 1;
    ctx.stroke();

    // Radial tick notches
    ctx.beginPath();
    for (let i = 0; i < this.ticks.length; i++) {
      const t = this.ticks[i];
      const r1 = t.isMajor ? dialR - 10 : dialR - 5;
      const r2 = dialR;
      const x1 = cx + Math.cos(t.angle) * r1;
      const y1 = cy + Math.sin(t.angle) * r1;
      const x2 = cx + Math.cos(t.angle) * r2;
      const y2 = cy + Math.sin(t.angle) * r2;

      ctx.moveTo(x1, y1);
      ctx.lineTo(x2, y2);
    }
    ctx.strokeStyle = `rgba(${primaryGold}, 0.6)`;
    ctx.lineWidth = 1.2;
    ctx.stroke();

    // Rotating Caliper Brackets
    const bAngle = this.rotY * 0.75;
    ctx.save();
    ctx.shadowBlur = 8;
    ctx.shadowColor = `rgb(${primaryGold})`;

    for (let j = 0; j < 4; j++) {
      const startA = bAngle + (j * Math.PI * 2) / 4;
      ctx.beginPath();
      ctx.arc(cx, cy, dialR + 4, startA, startA + 0.32);
      ctx.strokeStyle = `rgba(${brightGold}, 0.9)`;
      ctx.lineWidth = 2.4;
      ctx.stroke();

      const tipX = cx + Math.cos(startA + 0.32) * (dialR + 8);
      const tipY = cy + Math.sin(startA + 0.32) * (dialR + 8);
      ctx.beginPath();
      ctx.arc(tipX, tipY, 1.8, 0, Math.PI * 2);
      ctx.fillStyle = '#ffffff';
      ctx.fill();
    }
    ctx.restore();
  }

  // --- 3D Latitude Rings ---
  drawLatitudeRings(ctx, cx, cy, R, primaryGold, brightGold) {
    const latitudes = [-70, -52, -34, -16, 0, 16, 34, 52, 70];

    latitudes.forEach((latDeg) => {
      const latRad = (latDeg * Math.PI) / 180;
      const rLat = Math.cos(latRad);
      const yLat = Math.sin(latRad);
      const steps = 48;
      const isEquator = latDeg === 0;

      for (let i = 0; i < steps; i++) {
        const a1 = (i / steps) * Math.PI * 2;
        const a2 = ((i + 1) / steps) * Math.PI * 2;

        const p1 = this.project3D(Math.cos(a1) * rLat, yLat, Math.sin(a1) * rLat, cx, cy, R);
        const p2 = this.project3D(Math.cos(a2) * rLat, yLat, Math.sin(a2) * rLat, cx, cy, R);

        const avgAlpha = (p1.alpha + p2.alpha) * 0.5;

        // Dashed styling on intermediate latitudes
        if (Math.abs(latDeg) === 34 || Math.abs(latDeg) === 52) {
          if (i % 3 === 0) continue;
        }

        ctx.beginPath();
        ctx.moveTo(p1.x, p1.y);
        ctx.lineTo(p2.x, p2.y);

        if (isEquator && p1.isFront) {
          ctx.strokeStyle = `rgba(${brightGold}, ${avgAlpha * 0.85})`;
          ctx.lineWidth = 1.8;
        } else {
          ctx.strokeStyle = `rgba(${primaryGold}, ${avgAlpha * (isEquator ? 0.7 : 0.38)})`;
          ctx.lineWidth = isEquator ? 1.4 : 0.9;
        }
        ctx.stroke();
      }
    });
  }

  // --- 3D Longitude Meridians ---
  drawMeridians(ctx, cx, cy, R, primaryGold) {
    const meridians = [0, 30, 60, 90, 120, 150];
    const steps = 40;

    meridians.forEach((mDeg) => {
      const mRad = (mDeg * Math.PI) / 180;

      for (let i = 0; i < steps; i++) {
        const phi1 = (i / steps) * Math.PI;
        const phi2 = ((i + 1) / steps) * Math.PI;

        const p1 = this.project3D(
          Math.sin(phi1) * Math.cos(mRad),
          Math.cos(phi1),
          Math.sin(phi1) * Math.sin(mRad),
          cx, cy, R
        );
        const p2 = this.project3D(
          Math.sin(phi2) * Math.cos(mRad),
          Math.cos(phi2),
          Math.sin(phi2) * Math.sin(mRad),
          cx, cy, R
        );

        const avgAlpha = (p1.alpha + p2.alpha) * 0.5;

        ctx.beginPath();
        ctx.moveTo(p1.x, p1.y);
        ctx.lineTo(p2.x, p2.y);
        ctx.strokeStyle = `rgba(${primaryGold}, ${avgAlpha * 0.32})`;
        ctx.lineWidth = 0.85;
        ctx.stroke();
      }
    });
  }

  // --- Gyroscopic Tilted Orbiting Rings & Arc Sectors ---
  drawOrbitRings(ctx, cx, cy, R, primaryGold, brightGold) {
    ctx.save();
    ctx.shadowBlur = 7;
    ctx.shadowColor = `rgb(${primaryGold})`;

    // Ring 1: Major Tilted Ring (42° inclination) with segmented tech tracks
    const r1 = R * 1.15;
    const steps1 = 54;
    for (let i = 0; i < steps1; i++) {
      const a1 = (i / steps1) * Math.PI * 2;
      const a2 = ((i + 1) / steps1) * Math.PI * 2;

      const p1 = this.projectTilted(r1, a1, 0.72, 0.28, this.orbitAngle1, cx, cy);
      const p2 = this.projectTilted(r1, a2, 0.72, 0.28, this.orbitAngle1, cx, cy);

      if (i % 4 === 0) continue;

      ctx.beginPath();
      ctx.moveTo(p1.x, p1.y);
      ctx.lineTo(p2.x, p2.y);
      ctx.strokeStyle = `rgba(${brightGold}, ${p1.alpha * 0.88})`;
      ctx.lineWidth = 1.9;
      ctx.stroke();
    }

    // Sliding bright data brackets on Ring 1
    for (let b = 0; b < 2; b++) {
      const blockA = this.orbitAngle1 * 1.6 + b * Math.PI;
      const bp = this.projectTilted(r1, blockA, 0.72, 0.28, 0, cx, cy);
      ctx.beginPath();
      ctx.arc(bp.x, bp.y, 3.4 * bp.alpha, 0, Math.PI * 2);
      ctx.fillStyle = '#ffffff';
      ctx.fill();
    }

    // Ring 2: Counter-inclined Outer Ring (-38° tilt)
    const r2 = R * 1.28;
    const steps2 = 48;
    for (let i = 0; i < steps2; i++) {
      const a1 = (i / steps2) * Math.PI * 2;
      const a2 = ((i + 1) / steps2) * Math.PI * 2;

      const p1 = this.projectTilted(r2, a1, -0.65, -0.42, this.orbitAngle2, cx, cy);
      const p2 = this.projectTilted(r2, a2, -0.65, -0.42, this.orbitAngle2, cx, cy);

      if (i % 5 === 0) continue;

      ctx.beginPath();
      ctx.moveTo(p1.x, p1.y);
      ctx.lineTo(p2.x, p2.y);
      ctx.strokeStyle = `rgba(${primaryGold}, ${p1.alpha * 0.7})`;
      ctx.lineWidth = 1.4;
      ctx.stroke();
    }

    // Ring 3: Steep Polar Ring (68° tilt)
    const r3 = R * 0.98;
    const steps3 = 40;
    for (let i = 0; i < steps3; i++) {
      const a1 = (i / steps3) * Math.PI * 2;
      const a2 = ((i + 1) / steps3) * Math.PI * 2;

      const p1 = this.projectTilted(r3, a1, 1.18, -0.16, this.orbitAngle3, cx, cy);
      const p2 = this.projectTilted(r3, a2, 1.18, -0.16, this.orbitAngle3, cx, cy);

      ctx.beginPath();
      ctx.moveTo(p1.x, p1.y);
      ctx.lineTo(p2.x, p2.y);
      ctx.strokeStyle = `rgba(${brightGold}, ${p1.alpha * 0.52})`;
      ctx.lineWidth = 1.1;
      ctx.stroke();
    }

    // Ring 4: Fast Inner Equatorial Ring with prominent bright arcs (like reference photo)
    const r4 = R * 1.06;
    for (let k = 0; k < 3; k++) {
      const arcStart = this.orbitAngle4 + (k * Math.PI * 2) / 3;
      const arcLen = 0.55;
      const arcSteps = 14;

      ctx.beginPath();
      for (let s = 0; s <= arcSteps; s++) {
        const ang = arcStart + (s / arcSteps) * arcLen;
        const pt = this.projectTilted(r4, ang, 0.25, 0.65, 0, cx, cy);
        if (s === 0) ctx.moveTo(pt.x, pt.y);
        else ctx.lineTo(pt.x, pt.y);
      }
      ctx.strokeStyle = `rgba(${brightGold}, 0.92)`;
      ctx.lineWidth = 2.6;
      ctx.stroke();
    }

    ctx.restore();
  }

  // --- Volumetric Point Cloud & Holographic Circuit Filaments ---
  drawPointCloud(ctx, cx, cy, R, primaryGold, brightGold, haloAmber) {
    const projectedNodes = [];

    // Project all nodes
    for (let i = 0; i < this.nodes.length; i++) {
      const n = this.nodes[i];
      n.sparklePhase += n.sparkleSpeed;
      const sparkle = 0.8 + 0.3 * Math.sin(n.sparklePhase);

      const proj = this.project3D(n.baseX, n.baseY, n.baseZ, cx, cy, R);
      projectedNodes.push({
        ...proj,
        size: n.size * proj.scale * sparkle,
        isBeacon: n.isBeacon
      });
    }

    // Draw holographic circuit mesh between adjacent front nodes
    ctx.beginPath();
    const maxLinkDist = 38 * (R / this.baseRadius);
    const len = projectedNodes.length;

    for (let i = 0; i < len; i += 2) {
      const p1 = projectedNodes[i];
      if (!p1.isFront) continue;

      for (let j = i + 1; j < Math.min(i + 8, len); j++) {
        const p2 = projectedNodes[j];
        if (!p2.isFront) continue;

        const dx = p1.x - p2.x;
        const dy = p1.y - p2.y;
        const dist = Math.sqrt(dx * dx + dy * dy);

        if (dist < maxLinkDist) {
          ctx.moveTo(p1.x, p1.y);
          ctx.lineTo(p2.x, p2.y);
        }
      }
    }
    ctx.strokeStyle = `rgba(${primaryGold}, 0.32)`;
    ctx.lineWidth = 0.85;
    ctx.stroke();

    // Render nodes
    ctx.save();
    for (let i = 0; i < projectedNodes.length; i++) {
      const p = projectedNodes[i];

      ctx.beginPath();
      ctx.arc(p.x, p.y, Math.max(0.7, p.size), 0, Math.PI * 2);

      if (p.isFront && p.alpha > 0.6) {
        // Bright front nodes
        ctx.shadowBlur = p.isBeacon ? 10 : 5;
        ctx.shadowColor = `rgb(${brightGold})`;
        ctx.fillStyle = p.isBeacon ? '#ffffff' : `rgba(${brightGold}, ${p.alpha})`;
      } else {
        // Softer back nodes
        ctx.shadowBlur = 0;
        ctx.fillStyle = `rgba(${primaryGold}, ${p.alpha * 0.52})`;
      }
      ctx.fill();

      // Beacon halo ring
      if (p.isBeacon && p.isFront) {
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.size * 2.2, 0, Math.PI * 2);
        ctx.strokeStyle = `rgba(${haloAmber}, ${p.alpha * 0.75})`;
        ctx.lineWidth = 0.9;
        ctx.stroke();
      }
    }
    ctx.restore();
  }

  // --- Floating 3D Orbital Sparks ---
  drawOrbitalSparks(ctx, cx, cy, R, primaryGold, brightGold) {
    ctx.save();
    for (let i = 0; i < this.sparks.length; i++) {
      const s = this.sparks[i];
      s.azimuth += s.speed;

      const r = R * s.radiusMul;
      const x = r * Math.cos(s.azimuth) * Math.cos(s.inclination);
      const y = r * Math.sin(s.inclination);
      const z = r * Math.sin(s.azimuth) * Math.cos(s.inclination);

      const p = this.project3D(x / R, y / R, z / R, cx, cy, R);

      if (p.isFront) {
        ctx.beginPath();
        ctx.arc(p.x, p.y, s.size * p.scale, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(${brightGold}, ${s.opacity * p.alpha})`;
        ctx.shadowBlur = 4;
        ctx.shadowColor = `rgb(${primaryGold})`;
        ctx.fill();
      }
    }
    ctx.restore();
  }

  // --- Luminous Golden Energy Core & Radial Corona ---
  drawCenterEnergyCore(ctx, cx, cy, primaryGold, brightGold) {
    const pulse = 1 + 0.1 * Math.sin(this.phase * 3.2) + this.audioLevel * 0.28;
    const coreR = 42 * pulse;

    // Multi-stage radial gradient
    const grad = ctx.createRadialGradient(cx, cy, 2, cx, cy, coreR);
    grad.addColorStop(0, '#ffffff');
    grad.addColorStop(0.22, `rgba(${brightGold}, 0.95)`);
    grad.addColorStop(0.52, `rgba(${primaryGold}, 0.68)`);
    grad.addColorStop(0.82, 'rgba(0, 200, 100, 0.28)');
    grad.addColorStop(1, 'rgba(0, 150, 70, 0)');

    ctx.save();
    ctx.shadowBlur = 28;
    ctx.shadowColor = `rgb(${primaryGold})`;
    ctx.beginPath();
    ctx.arc(cx, cy, coreR, 0, Math.PI * 2);
    ctx.fillStyle = grad;
    ctx.fill();

    // Radiating corona filaments
    const rayCount = 10;
    const rayAngleOffset = this.rotY * 1.6;
    ctx.beginPath();
    for (let r = 0; r < rayCount; r++) {
      const a = rayAngleOffset + (r * Math.PI * 2) / rayCount;
      const rx1 = cx + Math.cos(a) * 14;
      const ry1 = cy + Math.sin(a) * 14;
      const rx2 = cx + Math.cos(a) * (coreR + 14);
      const ry2 = cy + Math.sin(a) * (coreR + 14);

      ctx.moveTo(rx1, ry1);
      ctx.lineTo(rx2, ry2);
    }
    ctx.strokeStyle = `rgba(${brightGold}, 0.5)`;
    ctx.lineWidth = 1.3;
    ctx.stroke();

    ctx.restore();
  }

  // --- Frequency Waveform Canvas (Synced in Cyber Matrix Green) ---
  drawWaveform() {
    if (!this.waveCtx) return;
    const ctx = this.waveCtx;
    const width = this.waveCanvas.width;
    const height = this.waveCanvas.height;
    const midY = height / 2;

    ctx.clearRect(0, 0, width, height);

    this.phase += 0.08;
    const amplitude = (this.state === 'SPEAKING' || this.state === 'LISTENING')
      ? Math.max(12, this.audioLevel * 24 + 10)
      : 3;

    let strokeColor = 'rgba(0, 255, 136, 0.9)';
    let shadowClr = '#00ff88';

    if (this.state === 'ERROR') {
      strokeColor = 'rgba(255, 60, 90, 0.9)';
      shadowClr = '#ff3366';
    } else if (this.state === 'SUCCESS') {
      strokeColor = 'rgba(0, 255, 170, 0.9)';
      shadowClr = '#00ffaa';
    }

    ctx.beginPath();
    ctx.moveTo(0, midY);

    for (let x = 0; x < width; x++) {
      const freq = 0.038;
      const env = Math.sin((x / width) * Math.PI); // Window envelope
      const y = midY + Math.sin(x * freq + this.phase) * amplitude * env;
      ctx.lineTo(x, y);
    }

    ctx.strokeStyle = strokeColor;
    ctx.lineWidth = 2.2;
    ctx.shadowBlur = 10;
    ctx.shadowColor = shadowClr;
    ctx.stroke();
  }

  animate() {
    this.drawTacticalWorldMapBackdrop();
    this.drawCoreHologram();
    this.drawWaveform();
    requestAnimationFrame(this.animate);
  }
}

// Global visualizer instance
window.visualizer = null;
document.addEventListener('DOMContentLoaded', () => {
  window.visualizer = new CoreVisualizer('core-visualizer-canvas', 'waveform-canvas');
});
