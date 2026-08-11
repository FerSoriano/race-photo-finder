import type { PhotoDownloadLink } from '@/types/api'

// Signed URLs are short-lived and single-use in intent -- fire them off as
// soon as the bulk-download response arrives, staggered so the browser
// doesn't treat a burst of simultaneous downloads as a popup flood.
export function triggerDownloads(links: PhotoDownloadLink[]) {
  links.forEach((link, i) => {
    setTimeout(() => {
      const a = document.createElement('a')
      a.href = link.url
      a.download = link.filename
      a.rel = 'noopener'
      document.body.appendChild(a)
      a.click()
      a.remove()
    }, i * 300)
  })
}
