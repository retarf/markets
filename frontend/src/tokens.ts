// JS-side access to the design tokens (mirrors design-tokens.json / theme.css)
// for chart geometry where CSS variables are inconvenient (SVG scales, series
// colors). Keep in sync with theme.css.
export const tokens = {
  primary: "#4c8dff",
  primarySubtle: "#86b0ff",
  bg: "#0b0e14",
  surface: "#131722",
  elev: "#1c2230",
  border: "#2a3242",
  text: "#e6e9ef",
  dim: "#8a93a6",
  danger: "#f0524b",
  ok: "#3fb950",
  space: 8,
  radius: 8,
} as const;
