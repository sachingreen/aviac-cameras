AVIAC WEBSITE - HOSTING
=======================

This folder is the complete website: plain HTML, CSS, JavaScript, images, films and 3D models.
No server code and no build step are needed. Upload the CONTENTS of this folder to the web root.

Where to host
- Vercel / Netlify / Cloudflare Pages: drag this folder in, or point the project at it.
  vercel.json (Vercel) and _headers (Netlify, Cloudflare) set caching; 404.html is the not-found page.
- cPanel / Apache (e.g. Hostinger, GoDaddy): upload into public_html. .htaccess sets caching and the 404 page.
- Any other static host (S3, GitHub Pages, nginx): upload as is; set 404.html as the error page.

Before going live
1. Domain: links for search engines and link previews point to https://aviac.in
   (sitemap.xml, robots.txt, and the canonical / og tags in each page). If the site lives on another
   domain, rebuild with:  SITE=https://your-domain python3 website/build.py
2. Contact form: it sends to info@aviac.in through FormSubmit (formsubmit.co). The FIRST time someone
   submits it, FormSubmit emails info@aviac.in an activation link - click it once, and every request
   after that arrives in the inbox. If FormSubmit cannot be reached, the visitor's mail app opens instead.
3. HTTPS: turn it on at your host (the 3D viewers and films need a normal https page).
4. Security headers: vercel.json, _headers and .htaccess send the same set (a Content Security Policy, nosniff,
   frame and referrer rules). The policy allows this site, Google Fonts and FormSubmit only; if you add another
   service (analytics, a chat widget), add its host to Content-Security-Policy in all three files.

Pages
  /                         home
  /solutions/<market>/      crop-monitoring, spraying, solar, industrial, construction
  /product/<camera>/        multispectral, duos, thermal, swir
  /dashboard/               sign-in placeholder for the Aviac dashboard (nothing is sent or stored yet)

Editing
  The source is in the repository under website/src and website/tools; build.py writes this folder.
  New or changed photos: run  python3 website/tools/webp.py  before build.py; it writes the WebP versions
  (40 to 70 % lighter) that the pages serve, with the JPEG kept as the fallback.
