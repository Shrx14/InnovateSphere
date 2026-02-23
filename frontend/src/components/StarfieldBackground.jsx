import { useEffect, useRef } from 'react';

/**
 * GPU-friendly animated starfield with shooting comets.
 * Renders on a fixed <canvas> behind all page content.
 */
const StarfieldBackground = () => {
  const canvasRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');

    let animationId;
    let stars = [];
    let comets = [];

    const STAR_COUNT = 140;
    const COMET_INTERVAL_MIN = 2500;  // ms
    const COMET_INTERVAL_MAX = 6000;

    const resize = () => {
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
    };
    resize();
    window.addEventListener('resize', resize);

    // Initialize stars
    const initStars = () => {
      stars = [];
      for (let i = 0; i < STAR_COUNT; i++) {
        stars.push({
          x: Math.random() * canvas.width,
          y: Math.random() * canvas.height,
          radius: Math.random() * 1.8 + 0.3,
          baseAlpha: Math.random() * 0.6 + 0.2,
          alpha: 0,
          twinkleSpeed: Math.random() * 0.015 + 0.005,
          twinklePhase: Math.random() * Math.PI * 2,
          // Subtle drift
          dx: (Math.random() - 0.5) * 0.05,
          dy: (Math.random() - 0.5) * 0.03,
        });
      }
    };
    initStars();

    // Spawn a shooting comet
    const spawnComet = () => {
      const side = Math.random();
      let x, y, angle;

      if (side < 0.6) {
        // From top
        x = Math.random() * canvas.width;
        y = -10;
        angle = Math.PI / 4 + Math.random() * (Math.PI / 6); // downward-right
      } else if (side < 0.8) {
        // From left
        x = -10;
        y = Math.random() * canvas.height * 0.5;
        angle = Math.PI / 6 + Math.random() * (Math.PI / 6);
      } else {
        // From right
        x = canvas.width + 10;
        y = Math.random() * canvas.height * 0.3;
        angle = Math.PI - Math.PI / 4 - Math.random() * (Math.PI / 6);
      }

      const speed = 4 + Math.random() * 6;

      comets.push({
        x,
        y,
        vx: Math.cos(angle) * speed,
        vy: Math.sin(angle) * speed,
        tail: [],
        tailLength: 25 + Math.floor(Math.random() * 20),
        life: 1.0,
        decay: 0.003 + Math.random() * 0.004,
        size: 1.5 + Math.random() * 1.5,
        hue: Math.random() < 0.5 ? 230 : (Math.random() < 0.5 ? 270 : 340), // blue, purple, or pink
      });
    };

    // Schedule comets
    let cometTimer;
    const scheduleComet = () => {
      const delay = COMET_INTERVAL_MIN + Math.random() * (COMET_INTERVAL_MAX - COMET_INTERVAL_MIN);
      cometTimer = setTimeout(() => {
        spawnComet();
        scheduleComet();
      }, delay);
    };
    // Spawn first comet quickly
    setTimeout(() => spawnComet(), 800);
    scheduleComet();

    // Animation loop
    const animate = (time) => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      // Draw stars
      for (const star of stars) {
        star.twinklePhase += star.twinkleSpeed;
        star.alpha = star.baseAlpha * (0.5 + 0.5 * Math.sin(star.twinklePhase));

        // Subtle drift
        star.x += star.dx;
        star.y += star.dy;

        // Wrap around
        if (star.x < -5) star.x = canvas.width + 5;
        if (star.x > canvas.width + 5) star.x = -5;
        if (star.y < -5) star.y = canvas.height + 5;
        if (star.y > canvas.height + 5) star.y = -5;

        // Glow effect
        const gradient = ctx.createRadialGradient(
          star.x, star.y, 0,
          star.x, star.y, star.radius * 3
        );
        gradient.addColorStop(0, `rgba(200, 210, 255, ${star.alpha})`);
        gradient.addColorStop(0.4, `rgba(180, 190, 255, ${star.alpha * 0.4})`);
        gradient.addColorStop(1, 'rgba(180, 190, 255, 0)');

        ctx.beginPath();
        ctx.arc(star.x, star.y, star.radius * 3, 0, Math.PI * 2);
        ctx.fillStyle = gradient;
        ctx.fill();

        // Core dot
        ctx.beginPath();
        ctx.arc(star.x, star.y, star.radius, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(230, 235, 255, ${star.alpha})`;
        ctx.fill();
      }

      // Draw comets
      for (let i = comets.length - 1; i >= 0; i--) {
        const comet = comets[i];

        // Update position
        comet.x += comet.vx;
        comet.y += comet.vy;
        comet.life -= comet.decay;

        // Add to tail
        comet.tail.unshift({ x: comet.x, y: comet.y });
        if (comet.tail.length > comet.tailLength) comet.tail.pop();

        // Draw tail
        for (let t = 0; t < comet.tail.length; t++) {
          const point = comet.tail[t];
          const progress = t / comet.tail.length;
          const tailAlpha = (1 - progress) * comet.life * 0.6;
          const tailSize = comet.size * (1 - progress * 0.8);

          ctx.beginPath();
          ctx.arc(point.x, point.y, tailSize, 0, Math.PI * 2);
          ctx.fillStyle = `hsla(${comet.hue}, 70%, 75%, ${tailAlpha})`;
          ctx.fill();
        }

        // Draw comet head with glow
        const headGradient = ctx.createRadialGradient(
          comet.x, comet.y, 0,
          comet.x, comet.y, comet.size * 6
        );
        headGradient.addColorStop(0, `hsla(${comet.hue}, 80%, 90%, ${comet.life * 0.8})`);
        headGradient.addColorStop(0.3, `hsla(${comet.hue}, 70%, 70%, ${comet.life * 0.3})`);
        headGradient.addColorStop(1, `hsla(${comet.hue}, 60%, 60%, 0)`);

        ctx.beginPath();
        ctx.arc(comet.x, comet.y, comet.size * 6, 0, Math.PI * 2);
        ctx.fillStyle = headGradient;
        ctx.fill();

        // Core
        ctx.beginPath();
        ctx.arc(comet.x, comet.y, comet.size, 0, Math.PI * 2);
        ctx.fillStyle = `hsla(${comet.hue}, 90%, 95%, ${comet.life})`;
        ctx.fill();

        // Remove dead or off-screen comets
        if (
          comet.life <= 0 ||
          comet.x < -100 || comet.x > canvas.width + 100 ||
          comet.y < -100 || comet.y > canvas.height + 100
        ) {
          comets.splice(i, 1);
        }
      }

      animationId = requestAnimationFrame(animate);
    };

    animationId = requestAnimationFrame(animate);

    return () => {
      cancelAnimationFrame(animationId);
      clearTimeout(cometTimer);
      window.removeEventListener('resize', resize);
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      className="fixed inset-0 pointer-events-none"
      style={{ zIndex: 0 }}
      aria-hidden="true"
    />
  );
};

export default StarfieldBackground;
