# Instrument identification reference

A guide for identifying instruments in a cockpit panel photo when producing an
`areas.json` (see `PANELMAP_WORKFLOW.md`). It captures the domain knowledge that
a fresh session — or a different person — would otherwise lack, so labeling
quality does not depend on who is driving.

This is a **living document**. Add rules as they are learned; the more specific
the recognition cues, the better the results.

## How to use it

Detecting a panel has two parts with very different reliability:

- **Geometry (boxes)** — read directly from the image and usually accurate. Round
  gauges → `shape: "circle"` = `[cx, cy, r]`; rectangular screens/radios →
  `shape: "rect"` = `[x1, y1, x2, y2]`, in the image's natural pixel space.
- **Labels (what each box *is*)** — an educated guess. Recognition cues below help,
  but **model numbers and ambiguous glass should be human-confirmed.** When in
  doubt, read the branding/label text printed on the unit itself.

Always generate the `overlay.png` and have a human eyeball it before the map is
used downstream.

## Shape-based disambiguation rules

Some instruments are told apart primarily by outline:

| Rule | Detail |
|------|--------|
| **Garmin G5 = square** | The G5 is a square/quadratic glass display. |
| **Garmin GI-275 = round** | The GI-275 is a round glass display (fits a 3⅛" round cutout). |

So a *square* Garmin glass screen is a G5; a *round* one is a GI-275. In a dual-G5
install the upper unit is typically the attitude indicator (PFD) and the lower one
the HSI/DG — but confirm, as configurations vary. A dual-**GI-275** install (two
round glass displays: attitude + HSI) is equally common.

> **Caution — don't let mounting screws fool the shape call.** A round GI-275 is
> often held by four screws arranged in a *square* pattern around the bezel. The
> square screw layout can make a round instrument read as "square" at a glance.
> Judge the shape from the **display/bezel outline**, not the screw positions —
> if the glass itself is round, it's a GI-275.

## Common GA instruments — recognition cues

### The "six-pack" (round analog gauges)

- **Airspeed Indicator** — round; arc of numbers with `KNOTS` (or `MPH`); colored
  arcs (white/green/yellow) and a red line; single needle.
- **Attitude Indicator / Artificial Horizon** — round; blue (sky) over brown
  (ground) with a horizon line and miniature aircraft. *Often replaced by a G5.*
- **Altimeter** — round; marked `FEET`; one or more hands plus a Kollsman
  (pressure) window; may say `ENCODING` on an encoding altimeter.
- **Turn Coordinator** — round; miniature aircraft symbol; `2 MIN`, `L`/`R`, and
  usually `NO PITCH INFORMATION`.
- **Heading Indicator / Directional Gyro** — round; compass card with `N E S W`
  and a fixed aircraft/lubber line.
- **Vertical Speed Indicator (VSI)** — round; `VERTICAL SPEED`, `UP`/`DOWN`,
  `100 FT PER MIN`; needle rests at zero (9 o'clock).

### Navigation indicators (round)

- **CDI / VOR indicator** — round; vertical course-deviation needle; `TO`/`FROM`
  flag. **Key tell: a small circular `OBS` course-selector knob in the lower-left
  corner of the bezel** — the presence of that knob reliably marks a CDI (vs. a
  plain heading/compass display, which has no OBS knob).
- **CDI with Glideslope** — as above plus a **horizontal** glideslope needle for
  ILS approaches (two needles forming a cross).
- **HSI (Horizontal Situation Indicator)** — round; combines heading card and
  course-deviation needle in one instrument.
- **Magnetic Compass** — round wet compass, usually top-center of the panel or on
  the windscreen post; a panel-mounted *repeater* can appear elsewhere.

### Engine & fuel gauges

- **Tachometer** — round; `RPM`, usually `x100`.
- **Oil Temperature / Pressure**, **Fuel Quantity (L/R)**, **EGT/CHT**,
  **Manifold Pressure**, **Fuel Flow** — often small round or bar gauges, labeled;
  frequently grouped in a column or cluster.

### Avionics stack (rectangular units)

- **Audio Panel** — row of `COM`/`NAV` selector buttons, `MIC`/`PHONE`; e.g.
  Bendix/King **KMA24**.
- **Nav/Com Radio** — active/standby frequency displays with a flip-flop swap
  knob; e.g. King **KX155**.
- **GPS Navigator** — a screen with soft-key labels; Garmin **GNS/GTN** or Avidyne
  **IFD** (the IFD540 shows `AVIDYNE` and `FMS  MAP  AUX` soft-keys).
- **Transponder** — 4-digit squawk-code display with `IDENT` and
  `ALT`/`STBY`/`ON`/`GND` mode keys (these are the reliable, model-independent
  cues). **Some models add a quadratic numeric keypad (`0`–`9`) for entering the
  code — when present, that number-pad block is a strong positive marker for a
  transponder** (adjacent radios have knobs/soft-keys but no full number pad).
  This is model-specific, though: the **Garrecht VT2000** has the keypad, whereas
  the **Trig TT31** uses a rotary knob plus a few buttons and has *no* keypad — so
  a keypad's *absence* does not rule out a transponder; fall back to the squawk
  display + IDENT/mode keys.
- **Autopilot** — amber/segmented mode display with a row of mode buttons
  (`AP`, `HDG`, `NAV`, `APR`, `REV`, `ALT`) and often `UP`/`DN` trim keys; e.g.
  Bendix/King KAP-series.
- **ADF Receiver** and **DME** — frequency/distance displays; e.g. King **KN62A**
  DME.

### Splitting a stacked avionics column (avoid over-lumping)

Radios and navigators are stacked as separate **line-replaceable units (LRUs)**,
each in its **own rectangular bezel**. Map **one box per unit**, not one box for
the whole stack. The most common over-lumping mistake is a single box that
swallows a screen *plus* the radio/keypad below it.

How to find the boundary between two stacked units:

- **Bezel seams.** Each LRU has its own bezel; there is a visible horizontal
  seam / mounting rail / gap between units. Split there.
- **Control-type changes mark a new unit.** A jump from a screen, to a row of
  tuning knobs, to a `0`–`9` keypad almost always crosses an LRU boundary.
- **A touchscreen navigator has no separate keypad below it.** All-in-one
  touchscreen GPS/NAV/COM units (e.g. **Avidyne IFD540**, **Garmin GTN** series)
  carry their soft-keys and knobs on their *own* bezel. A distinct unit *below*
  such a screen — with its own bezel, display and keypad/knobs — is a
  **different** radio. (On the D-EGPS panel a **Garmin GNC255A** nav/com sat
  under the IFD540 and was wrongly merged into it, because the keypad was assumed
  to belong to the IFD.)
- **But one continuous bezel = one unit.** An integrated navigator whose screen
  and keypad share a single unbroken bezel (e.g. a **Garmin GNS430/530**) is one
  LRU — do not split it.
- **Per-unit branding / screws.** Separate brand-model text, or a row of mounting
  screws bordering a sub-region, is strong evidence it is its own unit.

When unsure, prefer splitting at a clear bezel seam over lumping: an over-lumped
box makes several instruments respond as one blob and mislabels all but one.

## Notes for extension

- Add new instruments and brand/model cues under the sections above.
- When a photo yields a confident model number (from branding text), prefer the
  specific label (e.g. "Avidyne IFD540") over the generic one ("GPS Navigator").
- Record any panel-specific quirks (unusual layouts, non-standard installs) that
  helped disambiguate — future sessions benefit from them.
