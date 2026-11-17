# Aviac Technologies website (demo)

A static site on the structure of aviac.in (Home, Analytics, Sensors, Contact; the Terrain platform),
with the Aviac MS and Aviac Duo built in: 3D product viewers and the two flying showcases.

    website/
      src/               page templates: index.html, analytics/, sensors/, contact/, assets/site.css + site.js
                         ({{HEAD}}, {{NAV}}, {{FOOT}}, {{CARD}}, {{VIEWER}} are filled in by build.py)
      viewer/            source of the 3D product viewer (node build.mjs writes src/viewer.js)
      build.py           assembles public/ from the repo: brand files, renders, the two showcases
      vercel.json        trailing slashes on, caching for the models and images
      public/            the deployable site (generated; committed so Vercel needs no build)

## Rebuild

```bash
cd cameras/6band/showcase && node build.mjs
```

```bash
cd cameras/duo/showcase && node build.mjs
```

```bash
python3 website/build.py
```

## Deploy on Vercel

1. vercel.com → Add New → Project → import `sachingreen/aviac-cameras`.
2. Root Directory: `website/public`. Framework preset: Other. Build command: none. Output directory: leave empty.
3. Deploy. The landing page is `/`, the showcases are `/ms/` and `/duo/`.

Or from a terminal:

```bash
cd website/public && npx vercel --prod
```

The contact form opens the visitor's mail app addressed to aviactech@gmail.com (a static site has no server to receive forms).
