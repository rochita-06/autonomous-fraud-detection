"use client";

import { useEffect, useRef } from "react";

const SIZE = 132;
const R = 50;
const N = 220;
const FOV = 260;

/** Rotating holographic point-sphere with orbital rings — pure canvas 3D projection. */
export default function HoloGlobe() {
  const ref = useRef<HTMLCanvasElement | null>(null);

  useEffect(() => {
    const canvas = ref.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    canvas.width = SIZE * dpr;
    canvas.height = SIZE * dpr;
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);

    // fibonacci sphere points
    const pts: { x: number; y: number; z: number }[] = [];
    const golden = Math.PI * (3 - Math.sqrt(5));
    for (let i = 0; i < N; i++) {
      const y = 1 - (i / (N - 1)) * 2;
      const rad = Math.sqrt(1 - y * y);
      const th = golden * i;
      pts.push({ x: Math.cos(th) * rad * R, y: y * R, z: Math.sin(th) * rad * R });
    }

    const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    const tiltX = -0.35;
    let angle = 0.6;
    let raf = 0;

    const project = (p: { x: number; y: number; z: number }) => {
      // rotate around Y, then tilt around X
      const cx = Math.cos(angle);
      const sx = Math.sin(angle);
      const x1 = p.x * cx - p.z * sx;
      const z1 = p.x * sx + p.z * cx;
      const ct = Math.cos(tiltX);
      const st = Math.sin(tiltX);
      const y2 = p.y * ct - z1 * st;
      const z2 = p.y * st + z1 * ct;
      const s = FOV / (FOV + z2);
      return { x: SIZE / 2 + x1 * s, y: SIZE / 2 + y2 * s, z: z2, s };
    };

    const draw = () => {
      ctx.clearRect(0, 0, SIZE, SIZE);

      // halo
      const halo = ctx.createRadialGradient(SIZE / 2, SIZE / 2, R * 0.4, SIZE / 2, SIZE / 2, R * 1.4);
      halo.addColorStop(0, "rgba(79,140,255,0.10)");
      halo.addColorStop(1, "rgba(79,140,255,0)");
      ctx.fillStyle = halo;
      ctx.fillRect(0, 0, SIZE, SIZE);

      // orbital rings (screen-space ellipses)
      ctx.strokeStyle = "rgba(123,97,255,0.35)";
      ctx.lineWidth = 1;
      for (const [rx, ry, rot] of [[R * 1.25, R * 0.42, -0.5], [R * 1.35, R * 0.34, 0.65]] as const) {
        ctx.beginPath();
        ctx.ellipse(SIZE / 2, SIZE / 2, rx, ry, rot, 0, Math.PI * 2);
        ctx.stroke();
      }

      // sphere points, back-to-front
      const projected = pts.map(project).sort((a, b) => b.z - a.z);
      for (const q of projected) {
        const depth = 1 - (q.z + R) / (2 * R); // 0 back .. 1 front
        const alpha = 0.15 + depth * 0.65;
        ctx.fillStyle = depth > 0.55 ? `rgba(79,140,255,${alpha})` : `rgba(123,97,255,${alpha})`;
        ctx.beginPath();
        ctx.arc(q.x, q.y, 0.8 + depth * 1.1, 0, Math.PI * 2);
        ctx.fill();
      }

      angle += 0.004;
      if (!reduced) raf = requestAnimationFrame(draw);
    };
    draw();

    return () => cancelAnimationFrame(raf);
  }, []);

  return (
    <canvas
      ref={ref}
      width={SIZE}
      height={SIZE}
      style={{ width: SIZE, height: SIZE, filter: "drop-shadow(0 0 18px rgba(79,140,255,0.35))" }}
      role="img"
      aria-label="Global transaction monitor"
    />
  );
}
