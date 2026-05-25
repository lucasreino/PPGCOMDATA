"use client";

import dynamic from "next/dynamic";

const SplineScene = dynamic(() => import("./SplineScene"), {
  ssr: false,
  loading: () => <div className="absolute inset-0 bg-hero-bg" />,
});

export function SplineHeroBackground() {
  return (
    <>
      <div className="absolute inset-0 pointer-events-none" aria-hidden>
        <SplineScene />
      </div>
      <div className="absolute inset-0 bg-black/30 z-[1] pointer-events-none" aria-hidden />
    </>
  );
}
