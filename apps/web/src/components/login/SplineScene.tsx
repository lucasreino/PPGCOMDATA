"use client";

import Spline from "@splinetool/react-spline";

const SPLINE_SCENE =
  "https://prod.spline.design/Slk6b8kz3LRlKiyk/scene.splinecode";

export default function SplineScene() {
  return <Spline scene={SPLINE_SCENE} className="w-full h-full" />;
}
