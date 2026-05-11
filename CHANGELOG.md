# Changelog

All notable changes to this project will be documented in this file.

## [Initial Release] - 2026-05-11

### Added
- feat(iOS): magical UX — color wheel picker, ambient glow, animated counters, scene pulse
- feat(iOS): god-level room assignment with drag-drop, batch mode, color picker, inline rename, search, haptics
- feat: granular room assignment across backend, web dashboard, CLI, and iOS
- Add comprehensive README with architecture, API docs, and god-level connection reliability details
- feat: TV Screen Sync — remote device capture on same WiFi
- feat: accurate screen sync — vibrant/edge sampling, HSV delta, smoothing, FPS counter
- feat: screen sync — mirror display colors onto lights in real time
- feat: improved reconnect UX + keyboard shortcut
- feat: panic button + disconnect control (god level)
- feat: 5 god-level cutting-edge features (v3.0.0-ultra)
- feat: 20 new ambient effects (34 total)
- feat: 10 new ambient effects (14 total)
- feat: robust universal auto-discovery — works in any house, any bulbs
- feat: universal auto-discovery + 10 new dynamic scenes
- feat: 23 dynamic scenes with color palette animations
- feat: 5 god-level features - circadian, vacation, effects, music reactive, photo-to-scene
- Add custom light names

### Fixed
- Fix remaining medium/lingering issues
- fix(iOS): restore missing guard in Color.toHex() — prevents garbage RGB on color-space failure
- fix(iOS): revert List minHeight experiment — .fixedSize() is correct, .ambientGlow was the real culprit
- fix(iOS): god-level bug sweep — 7 critical/high issues fixed
- fix(iOS): prevent polling from reverting optimistic toggle updates
- fix(iOS): give List explicit minHeight to prevent zero-height collapse in ScrollView
- fix(iOS): remove ambientGlow from RoomCard to fix List layout
- Fix build: remove mutating triggerPulse, deduplicate ToastStyle, add showToast extension
- fix(iOS): remove duplicate ViewModel methods that broke compilation
- Fix build: add ToastStyle, showToast, turnOnRoom, turnOffRoom for GitHub sync compatibility
- fix(critical): resolve infinite recursion in get_latest_lights, deadlock in effect_runner, room API races, XSS in drag-drop, iOS data races and duplicate room crashes
- Fix duplicate RoomCard declaration in RoomAssignView
- security & stability: fix XSS, injection, race conditions, and UI bugs across backend, web, and iOS
- Fix inflated light count and motion sensor reliability
- fix: server.py couldn't start — syntax error + broken/duplicate Fire TV block
- fix: deep bug sweep — Kasa asyncio, SSE broadcast, serialization, voice parser, reconnect, memory leaks, paused checks
- fix: reconnect button click blocked by CSS
- fix: stop constant full-page re-renders
- Fix room names + add room editor UI
- Fix toggle flicker in Rooms view
- Fix all critical and serious bugs from deep audit
- fix: optimistic toggle updates + selective DOM rendering for Rooms

### Changed
- docs: add CLAUDE.md with current architecture overview

### Other
- Revert web dashboard changes — iOS app only
- ux: god-level UX improvements — skeleton loaders, haptics, toasts, swipe actions, context menus, keyboard shortcuts, empty states, animations
- SmartLights iOS app — complete build
- SpaceSense v3.1: Router sensor + trigonometric body tracking — multilateration with WiFi gateway and bulb fusion
- SpaceSense v3.0: Military-grade motion detection — Kalman filter, FFT, body tracking, micro-movement, direction estimation, cross-correlation, adaptive thresholds, 6 motion signatures
- SpaceSense: 5 god-level features - heatmap, spectrogram, prediction, presence, gestures
- SpaceSense: god-level precision + real-time SSE updates
- 🎮 Samsung TV control page + nav links
- 📱 iOS: PWA + Native App — God Level
- 📱 Samsung TV + iOS PWA + Native App + CLI
- 📱 Samsung TV + iOS PWA + Native App
- 🔥 Fire TV god level — auto-discovery + full ADB control
- 🔥 Fire TV Stick god level takeover — ADB integration
- 🏠 Smart Lights God Mode v2.0

