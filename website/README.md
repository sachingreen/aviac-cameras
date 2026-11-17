# Aviac Technologies website (demo)

A static site: the landing page plus the two interactive 3D showcases.

    website/
      src/index.html     landing page (edit this)
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

The contact button uses a placeholder address (hello@example.com): change it in `src/index.html`.
