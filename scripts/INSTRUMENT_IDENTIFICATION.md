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
- **Placement** — every box must sit **on the instrument it names**. Before
  emitting an area, confirm the box actually covers that unit, not an empty panel
  area, a placard, or a neighbouring instrument. A named unit floating over blank
  panel, or two areas landing on the same spot, are red flags — and a misplaced
  box usually means the *real* instrument got missed too.

Always eyeball the map — in the editor (`panelmap_editor.html`), or from an
`--overlay` render — before it is used downstream.

## Titling rule: read, don't guess — function over model

`title` is the catalog-matching key, so a wrong model name is worse than a
generic one. Apply this two-tier rule:

**Faceplate-named units → brand/model title.** Radios, navigators,
transponders, audio panels and similar avionics carry their model name printed
on the bezel ("GNS 430", "KX 155 TSO", "TT31", "KMA 24"). Here the title is
*read* from the photo, not inferred — use it verbatim.

**Indicator-class instruments → functional title.** Mechanical CDIs, HSIs,
RMIs and ADF indicators from different makers (Garmin GI-106A, King KI
203/204/206/525, …) are near-indistinguishable at panel-photo resolution, and
model guesses are the most common vision-pass error. Title them by function
instead:

- `CDI` — vertical needle, OBS knob, TO/FR flag, **no** glideslope needle
- `CDI/Glideslope` — as above **plus** a horizontal GS needle / GS flags
- `HSI` — course needle integrated with a heading compass card
- `ADF Indicator` — plain pointer on a card, **no** TO/FR flag and no
  deviation dots

The glideslope needle, TO/FR flag and compass-card integration are reliably
visible in a zoomed crop; the manufacturer logo often is not. If a model can
be read or is otherwise known, put it in the optional `text` field
("Garmin GI-106A") — there a wrong guess breaks nothing downstream.

**Autopilots:** don't infer the model from capabilities alone; use the
control-head form factor first. An S-TEC with no standalone head (controls in
the turn coordinator) is a System 20/30; a separate rectangular programmer
with mode annunciator window, HDG/NAV/APR/REV and trim UP/DN is a System
40/50 (ALT hold ⇒ 50). When unsure, `S-TEC Autopilot` alone still matches the
catalog — prefer that over a specific wrong number.

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

## Completeness — find every round instrument

Missing instruments is a common first-shot failure. Round gauges are easy to
under-count because clusters are dense and yokes hide some. Work systematically:

- **Read the cluster as a grid.** Instruments sit in a regular row×column layout.
  Enumerate **every cell** and account for each — an instrument box, or a clear
  reason it is empty (a blank/plugged hole). Don't stop at the obvious "six".
- **A six-pack is 2×3, but panels often add columns.** Extra columns commonly
  hold a second altimeter, an HSI, a VOR/CDI, an RMI/ADF, or engine gauges — so
  a left cluster can be 2×4 or more. Count the columns in each row.
- **Map round gauges hidden behind the control yokes/columns.** A yoke crossing a
  gauge leaves a partial bezel arc on each side — treat it as one full circle and
  box it through the occlusion. These are the most-often-missed instruments.
- **Zoom in to catch them.** Crop and magnify each cluster (3–4×); gauges and
  faint bezels invisible at full-frame become obvious.
- **Cross-check right-side / engine clusters too** (manifold pressure, tach, EGT,
  OAT, fuel/oil) — not just the primary flight group.

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
  `100 FT PER MIN`; needle rests at zero (9 o'clock). **Key tell: the scale `0`
  sits at the 9 o'clock position with short curved up/down arrows radiating from
  that zero** (climb above, descent below). Those arrows disambiguate a VSI from
  a compass/nav gauge even when it is largely hidden behind a yoke — don't
  mislabel a yoke-occluded VSI as a VOR/CDI.

### Navigation indicators (round)

- **CDI / VOR indicator** — round; a **fixed vertical lubber line** with a
  **horizontal scale** the needle moves across to show lateral course / cross-track
  deviation; often a `TO`/`FROM` flag. **Key tell: a small circular `OBS`
  course-selector knob in the lower-left corner of the bezel** — that knob
  reliably marks a CDI (vs. a plain heading/compass display, which has no OBS
  knob). Do **not** mistake a CDI for an **RMI**: an RMI has a *rotating* compass
  card with bearing pointer(s) to a station; a fixed vertical line + horizontal
  cross-track scale is a CDI.
- **CDI with Glideslope** — as above plus a **horizontal** glideslope needle for
  ILS approaches (two needles forming a cross).
- **HSI (Horizontal Situation Indicator)** — round; combines heading card and
  course-deviation needle in one instrument. Only call it an HSI if the compass
  card actually **rotates/slaves to heading**; a fixed-card course indicator —
  even one with a glideslope needle — is a plain **CDI**, not an HSI.
- **Magnetic Compass** — round wet compass, usually top-center of the panel or on
  the windscreen post; a panel-mounted *repeater* can appear elsewhere.

### Engine & fuel gauges

- **Tachometer** — round; `RPM`, usually `x100`.
- **Oil Temperature / Pressure**, **Fuel Quantity (L/R)**, **EGT/CHT**,
  **Manifold Pressure**, **Fuel Flow** — often small round or bar gauges, labeled;
  frequently grouped in a column or cluster.

### Avionics stack (rectangular units)

- **Audio Panel** — row of `COM`/`NAV` selector buttons, `MIC`/`PHONE`; e.g.
  Bendix/King **KMA24**. KMA24 layout specifically: marker-beacon buttons
  (`A`/`O`/`M` = airway/outer/middle) on the **left**, a rotary audio-source
  selector knob on the **right**, and **two rows of push-buttons** in the middle.
- **Nav/Com Radio** — active/standby frequency displays with a flip-flop swap
  knob; e.g. King **KX155**.
- **GPS Navigator** — a screen with soft-key labels; Garmin **GNS/GTN** or Avidyne
  **IFD** (the IFD540 shows `AVIDYNE` and `FMS  MAP  AUX` soft-keys). Note some
  units are **GPS + COM only, with no NAV/VOR/ILS receiver** — e.g. the Garmin
  **GNC355** (GPS + COM). It shows a COM frequency but no VLOC/NAV frequency and
  no VOR/CDI function, unlike a GNS430/530 or GTN650/750 (which include NAV).
  **Check the brand:** the same `FMS/MAP/AUX` unit branded **Bendix/King** (not
  Avidyne) is a **Bendix/King AeroNav 900** — a Honeywell/Bendix-King-licensed
  rebrand of the Avidyne IFD540. Label it AeroNav 900 when the bezel reads
  Bendix/King, IFD540 when it reads Avidyne.
- **Transponder** — 4-digit squawk-code display with `IDENT` and
  `ALT`/`STBY`/`ON`/`GND` mode keys (these are the reliable, model-independent
  cues). **Some models add a quadratic numeric keypad (`0`–`9`) for entering the
  code — when present, that number-pad block is a strong positive marker for a
  transponder** (adjacent radios have knobs/soft-keys but no full number pad).
  This is model-specific, though: the **Garrecht VT2000** has the keypad, whereas
  the **Trig TT31** uses a rotary knob plus a few buttons and has *no* keypad — so
  a keypad's *absence* does not rule out a transponder; fall back to the squawk
  display + IDENT/mode keys.
- **Autopilot** — a row of mode buttons (`ON/OFF`, `HDG`, `NAV`, `APR`, `REV`,
  `ALT`) with a display and often `UP`/`DN` trim keys; e.g. Bendix/King
  KAP-series, or **S-TEC** (e.g. the **S-TEC 50**, identifiable by its `ON/OFF`,
  `ALT`, `NAV` buttons). The mode-button row is the reliable cue — a lone knob is
  not (see Placement pitfalls).
- **ADF Receiver** and **DME** — frequency/distance displays; e.g. King **KN62A**
  DME. The **KN62A** layout specifically: an LED display spanning from the left
  edge to about the centre, a white 3-way source/mode switch
  (remote-frequency / groundspeed-time) just left of a **frequency-selector knob
  on the far right**.
- **Traffic / awareness display** — a small screen showing nearby traffic
  (FLARM / ADS-B / transponder-based). Frequently an **octagonal** (or square)
  bezel mounted *among the flight instruments* (e.g. right next to the altimeter),
  not in the radio stack; e.g. **Garrecht TRX 2000**. The octagonal outline is a
  strong shape cue.

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

## Placement & mislabel pitfalls

Things that are commonly boxed by mistake, or boxed in the wrong place:

- **Warning / annunciator panels are not instruments.** A block of small coloured
  (red/amber) segment lights — often top-centre, with labels like `OIL P`, low
  volts, low vacuum — is an annunciator, not a gauge or a clock. Do **not** map it
  as the chronometer. The **chronometer** is a *separate round instrument* with a
  digital time readout in a round bezel, commonly top-left. (On the D-EGPS panel
  the top-centre red annunciator was wrongly boxed as "Chronometer / OAT" while
  the real round chronometer top-left was missed.)
- **Do not name an autopilot from a lone knob.** Call a unit an autopilot only
  when you can see its **mode-button row** (`AP`, `HDG`, `NAV`, `APR`, `REV`,
  `ALT`). A round selector knob plus a small display describes many things (OAT
  probe, fuel selector, dimmer, encoder) — a lone knob is not enough, and the
  real autopilot usually lives in the avionics stack. (On the D-EGPS panel an
  autopilot box was placed on a centre-panel knob far from the actual autopilot.)
- **Skip placards, switches, breakers, vents, and registration text.** "SMOKING
  PROHIBITED", "REMOVE CONTROL LOCK", lighting/master switch rows, circuit
  breakers, air vents, and the aircraft registration are not instruments.
- **Empty / plugged instrument holes** (a blank round cutout or a covered hole)
  are not instruments — do not map them.
- **A round bezel can be a switch, not a gauge.** Backup/standby-power switches
  for glass displays sit in round holes among the flight instruments — e.g. a
  **GI-275 backup switch** (engages the GI-275's standby battery if ship power
  fails). It has a switch/knob and often a small tape, not a dial with a needle;
  don't call it an ADF/gauge. (Map it as a control only if mapping everything.)

## Notes for extension

- Add new instruments and brand/model cues under the sections above.
- When a photo yields a confident model number (from branding text), prefer the
  specific label (e.g. "Avidyne IFD540") over the generic one ("GPS Navigator").
- Record any panel-specific quirks (unusual layouts, non-standard installs) that
  helped disambiguate — future sessions benefit from them.
