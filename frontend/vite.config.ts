import path from 'node:path'
import { defineConfig, loadEnv, type Plugin } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// Open Graph needs an absolute `og:image` -- WhatsApp, the only channel that
// matters here, refuses to build a preview card from a relative one. The
// deploy domain is only known at build time, so it is substituted into
// index.html from VITE_SITE_URL, with a dev-server fallback so a plain
// `npm run build` never emits a raw placeholder.
function siteUrl(mode: string): Plugin {
  const env = loadEnv(mode, process.cwd(), '')
  const url = (env.VITE_SITE_URL || 'http://localhost:5173').replace(/\/$/, '')
  return {
    name: 'rpf-site-url',
    transformIndexHtml: (html) => html.replaceAll('%SITE_URL%', url),
  }
}

// https://vite.dev/config/
export default defineConfig(({ mode }) => ({
  plugins: [react(), tailwindcss(), siteUrl(mode)],
  resolve: {
    alias: {
      '@': path.resolve(import.meta.dirname, './src'),
    },
  },
}))
