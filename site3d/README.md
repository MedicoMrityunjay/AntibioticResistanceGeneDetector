# 3D Showcase — Antibiotic Resistance Gene Detector

This directory contains a lightweight Three.js-based showcase for the project.

Quick local preview

1. Open the `site3d/index.html` file in a modern browser (Chrome/Edge/Firefox).
2. The page uses CDN-hosted Three.js; no build step is required.

Notes
- Designed to be fast and mobile-friendly; the main scene renders a rotating DNA helix with clickable hotspots.
- Each hotspot opens an interactive 3D module (Input, Processing, Output, Error Handling, Demo Notebook).

If you want a production-ready build (minification, bundling), set up a small npm project and bundle with esbuild/rollup. This is intentionally dependency-light so you can preview quickly.
