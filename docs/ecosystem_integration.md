# Vaishnava Calendar — Ecosystem Integration Specification

## Overview

Vaishnava Calendar acts as the authoritative calculation engine for calendrical observances and astronomical events within the Bhaktilib Ecosystem.

---

## Dynamic Ecosystem Cross-Discovery

- `loadEcosystemCrossDiscovery()` in `web/js/app.js` queries `https://api.bhaktilib.com/v1/entities` dynamically.
- Resolves calendar event subjects to canonical ecosystem entity URNs (`event`, `person`, `concept`, `place`).
- Connects Ekadasi fasting events to exact chapter CFI locations in BhaktiLib's EPUB reader.
- Preserves legacy `EKADASI_MAPPING` and `SEMANTIC_ENTITIES` arrays as offline fallbacks.
