// Cover art fallback for events with no `cover_url`.
//
// Hue comes from the slug so a given race always looks the same, but chroma
// and lightness are pinned low on purpose: a saturated random hue would sooner
// or later fight the Volt accent for the eye, and the accent has to win.
export function coverGradient(slug: string): string {
  let hue = 0
  for (const ch of slug) hue = (hue * 31 + ch.codePointAt(0)!) % 360
  const shifted = (hue + 28) % 360

  return [
    'linear-gradient(152deg,',
    `oklch(0.38 0.062 ${hue}) 0%,`,
    `oklch(0.27 0.045 ${shifted}) 58%,`,
    `oklch(0.2 0.028 ${shifted}) 100%)`,
  ].join(' ')
}
