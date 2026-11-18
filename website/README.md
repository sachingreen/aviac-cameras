# Aviac Technologies website

Static site, light "Field Glass" theme taken from the Aviac dashboard.

    website/
      src/index.html                      home: hero, the problem, the systems, in the field, research, company, contact
      src/product/multispectral/          Aviac MS: 3D viewer with colourways, scroll-driven teardown
      src/product/duos/                   Aviac Duos: the same
      src/assets/                         site.css, site.js, web-sized renders
      src/models/                         packed CAD models (tools/pack_models.py)
      viewer/                             source of the 3D viewer (node build.mjs writes src/viewer.js)
      build.py                            fills the templates and writes public/
      public/                             the deployable site (committed, so Vercel needs no build)

## Rebuild

```bash
python3 website/tools/pack_models.py
```

```bash
cd website/viewer && npm install && node build.mjs
```

```bash
python3 website/build.py
```

## Deploy on Vercel

Import the repo, set Root Directory to `website/public`, framework Other, no build command.
