# Checking whether spraying worked: what the Duo can and cannot show

A camera cannot weigh the liquid that landed on a leaf. What it can do is check four things that
together answer "was this field sprayed properly". Ordered from most to least proven:

## 1. Coverage: did every part of the field get sprayed?

- The Duo logs every frame with GNSS position and time, and logs the drone's spray-on signal on its
  trigger input (connector J9; the pump or nozzle PWM from the flight controller).
- From those it draws the sprayed swath on a map and flags gaps between passes, missed headlands and
  stretches where the pump was off.
- The frames are the evidence: each strip of the map links to the images taken there.

Proven approach; the only new work is reading the spray-on signal and drawing the map.

## 2. Deposit, using water-sensitive cards

- Water-sensitive paper is the field standard: yellow cards that turn blue where droplets land.
- Put cards in the crop before spraying. At 3 m the Duo resolves 2.1 mm per pixel, so a 26 x 76 mm
  card covers about 12 x 36 pixels: enough to read the blue fraction of the card (coverage %),
  not enough to count individual droplets.
- The software finds the cards in the frames and reports coverage per card on the map, so there is no
  walking out to collect them for a first reading.

Cards are proven; reading them from the air at this resolution is **plausible but not yet tested**.

## 3. Effect, days later

- Fly the field again 3-10 days after spraying. Camera A's red and near-infrared give NDVI per pixel.
- Compare against the earlier flight: herbicide-treated weeds lose vigour, fungicide-treated patches
  stop spreading, untreated strips stand out.
- For fair comparisons between days, the light must be corrected (a reference panel in the first
  frames, or the light sensor the 6-band camera uses).

Proven approach in crop monitoring; needs repeat flights.

## 4. Drift and wetness at the moment of spraying

- With the camera tilted back, the mist cloud behind the boom is visible in the frames; heavy drift
  sideways can be flagged.
- Wet leaves look slightly different right after spraying, but the effect is small and fades within
  minutes. **Unproven**; worth a test, not something to promise.

## What this needs from the drone

- Spray-on signal to J9 (or over MAVLink), GNSS (the carrier has its own receiver; the drone's RTK
  position over MAVLink is better), and power (see the power note in `01-stereo-design.md`).
