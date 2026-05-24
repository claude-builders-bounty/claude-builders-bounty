### Summary of Changes
This pull request introduces Wayland support for `autokey` by implementing an `EvdevInterface` to directly monitor input devices and using a D-Bus monitor to detect active windows. It also updates the setup configuration to include the `evdev` dependency.

### Identified Risks
- Directly accessing `/dev/input/` devices via `evdev` typically requires root privileges or membership in the `input` group, which could complicate installation and pose security concerns if misconfigured.
- D-Bus based active window detection relies on specific desktop environments exposing window metadata over D-Bus, which may not be standardized across all Wayland compositors (e.g. Sway vs GNOME).

### Improvement Suggestions
- Provide documentation or a post-install script warning users about adding themselves to the `input` group.
- Add robust error handling when the D-Bus interface is unavailable, falling back gracefully rather than crashing.
- Add unit tests for `EvdevInterface` device enumeration and event parsing.

### Confidence Score
Medium
