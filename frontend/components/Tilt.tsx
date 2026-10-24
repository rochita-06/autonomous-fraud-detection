"use client";

import { useRef } from "react";

/** Mouse-tracking 3D tilt wrapper with a moving glare highlight. */
export default function Tilt({
  children,
  max = 6,
  className = "",
}: {
  children: React.ReactNode;
  max?: number;
  className?: string;
}) {
  const ref = useRef<HTMLDivElement | null>(null);

  const onMove = (e: React.MouseEvent) => {
    const el = ref.current;
    if (!el) return;
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    const r = el.getBoundingClientRect();
    const px = (e.clientX - r.left) / r.width; // 0..1
    const py = (e.clientY - r.top) / r.height;
    const rx = (0.5 - py) * max;
    const ry = (px - 0.5) * max;
    el.style.transform = `perspective(900px) rotateX(${rx.toFixed(2)}deg) rotateY(${ry.toFixed(2)}deg) translateZ(6px)`;
    el.style.setProperty("--glare-x", `${(px * 100).toFixed(1)}%`);
    el.style.setProperty("--glare-y", `${(py * 100).toFixed(1)}%`);
    el.style.setProperty("--glare-o", "1");
  };

  const onLeave = () => {
    const el = ref.current;
    if (!el) return;
    el.style.transform = "perspective(900px) rotateX(0deg) rotateY(0deg) translateZ(0)";
    el.style.setProperty("--glare-o", "0");
  };

  return (
    <div
      ref={ref}
      onMouseMove={onMove}
      onMouseLeave={onLeave}
      className={`tilt ${className}`}
    >
      {children}
      <div className="tilt-glare" aria-hidden />
    </div>
  );
}
