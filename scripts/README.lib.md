# @staski/panel-map

A small **Vue 3** component that renders an interactive image map over a picture:
hover a highlighted area to show an info card (picture + description) beside it,
and click to open a linked document. Built for **virtual cockpit instrument
panels** — hover an instrument to read about it, click to open its manual.

Part of the [panel-map](https://github.com/staski/panel-map) project, which also
includes a toolchain for building whole panels from a cockpit photo.

> Designed for desktop displays (the info card sits beside the panel) — not
> intended for phones/tablets.

## Install

```sh
npm i @staski/panel-map      # peer dependency: vue ^3
```

## Usage

```vue
<template>
  <PanelMap :src="imageUrl" :map="map" />
</template>

<script>
import PanelMap from '@staski/panel-map'
import '@staski/panel-map/style.css'      // bundled Bootstrap-based card styles

export default {
  components: { PanelMap },
  data() {
    return {
      imageUrl: '/images/cockpit.jpg',
      map: {
        name: 'my-panel',
        areas: [
          { title: 'Airspeed Indicator', shape: 'circle', coords: [232, 100, 60],
            text: 'Indicated airspeed in knots.',
            img: '/images/airspeed.jpg', href: '/docs/airspeed.pdf' },
          { title: 'Garmin GNS430', shape: 'rect', coords: [893, 63, 1197, 202] }
        ]
      }
    }
  }
}
</script>
```

## Props

| Prop  | Type   | Description |
|-------|--------|-------------|
| `src` | String | URL of the panel image |
| `map` | Object | `{ name, areas }` |

Each **area**:

| Field    | Required | Description |
|----------|----------|-------------|
| `title`  | yes | instrument name, shown as the card heading |
| `shape`  | yes | `"rect"` or `"circle"` |
| `coords` | yes | `circle` = `[cx, cy, r]`, `rect` = `[x1, y1, x2, y2]` |
| `text`   | no  | description shown in the card (may contain HTML) |
| `img`    | no  | URL of a picture shown in the card |
| `href`   | no  | URL opened in a new tab when the area is clicked |

Coordinates are in the image's **natural pixel space**; the component scales them
to the displayed size, so the map tracks the served image at any width.

## License

MIT — © 2023–2026 Carl Philipp Staszkiewicz.
