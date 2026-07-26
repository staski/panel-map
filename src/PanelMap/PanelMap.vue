<template>
  <div class="pm-root">
    <div class="pm-stage">
      <!-- panel image with an SVG hotspot overlay (coords are in the image's
           natural pixel space; the viewBox scales them to any display size) -->
      <div class="pm-imgwrap">
        <img class="pm-img" :src="src" alt="" @load="onImgLoad">
        <svg v-if="imgW" class="pm-overlay" :viewBox="`0 0 ${imgW} ${imgH}`"
             preserveAspectRatio="xMidYMid meet" :style="{ '--pm-sw': strokeW }">
          <!-- background: a tap/click on empty panel dismisses a pinned card -->
          <rect class="pm-bg" x="0" y="0" :width="imgW" :height="imgH" @click="closeCard" />
          <template v-for="(a, i) in areas" :key="i">
            <circle v-if="a.shape === 'circle'"
              :cx="a.coords[0]" :cy="a.coords[1]" :r="a.coords[2]"
              class="pm-hot" :class="{ 'pm-active': a === current }"
              @mouseenter="onEnter(a)" @mouseleave="onLeave(a)" @click="onClick(a)"
              @touchstart.passive="onTouchStart(a, $event)"
              @touchmove.passive="onTouchMove($event)" @touchend="onTouchEnd()" />
            <rect v-else
              :x="rectX(a)" :y="rectY(a)" :width="rectW(a)" :height="rectH(a)"
              class="pm-hot" :class="{ 'pm-active': a === current }"
              @mouseenter="onEnter(a)" @mouseleave="onLeave(a)" @click="onClick(a)"
              @touchstart.passive="onTouchStart(a, $event)"
              @touchmove.passive="onTouchMove($event)" @touchend="onTouchEnd()" />
          </template>
        </svg>
      </div>

      <!-- info card — its column is always reserved (desktop), so showing the
           card never resizes the panel; on mobile it's a bottom sheet -->
      <div class="pm-card">
        <div v-if="current" class="card">
          <div class="card-header d-flex justify-content-between align-items-center">
            <span class="fw-semibold">{{ current.title }}</span>
            <button v-if="isPinned" type="button" class="btn-close" aria-label="Close" @click="closeCard"></button>
          </div>
          <div v-if="current.img" class="d-flex justify-content-center my-3">
            <img :src="current.img" :style="{ width: cardImgWidth }" :alt="current.title">
          </div>
          <div class="card-body">
            <p class="card-text" v-html="current.text"></p>
          </div>
          <div v-if="current.href" class="card-footer">
            <a v-if="isPinned" :href="current.href" target="_blank" rel="noopener"
               class="btn btn-primary btn-sm w-100">Open manual</a>
            <span v-else class="text-muted small">Click the instrument to open its manual.</span>
          </div>
        </div>
        <div v-else class="pm-hint d-none d-md-block text-muted small p-2">
          Hover an instrument to see its details.
        </div>
      </div>
    </div>
  </div>
</template>

<style>
.pm-root { width: 100%; }
.pm-stage { display: flex; gap: 1rem; align-items: flex-start; }
.pm-imgwrap { position: relative; flex: 1 1 auto; min-width: 0; }
.pm-img { display: block; width: 100%; height: auto; }
.pm-overlay { position: absolute; inset: 0; width: 100%; height: 100%;
  -webkit-touch-callout: none; -webkit-user-select: none; user-select: none; }
.pm-bg { fill: transparent; pointer-events: all; }
.pm-hot { fill: rgba(0, 0, 0, 0); stroke: transparent; stroke-width: var(--pm-sw, 3);
  pointer-events: all; cursor: pointer; transition: fill .1s, stroke .1s; }
.pm-hot:hover, .pm-hot.pm-active { fill: rgba(57, 160, 255, .18); stroke: #2b8aef; }
/* the card column is reserved so hovering never reflows the panel (no flicker) */
.pm-card { flex: 0 0 20rem; }
.pm-card .card { max-width: 100%; }

/* touch devices (no hover): hint the hotspots so they're discoverable by tap */
@media (hover: none) {
  .pm-hot { stroke: rgba(70, 150, 245, .45); }
}

/* narrow screens: panel goes full width, card becomes a bottom sheet */
@media (max-width: 768px) {
  .pm-stage { flex-direction: column; }
  .pm-card { position: fixed; left: 0; right: 0; bottom: 0; z-index: 1050;
    flex: none; max-height: 60vh; overflow: auto; }
  .pm-card .card { border-radius: 12px 12px 0 0; box-shadow: 0 -6px 20px rgba(0, 0, 0, .25); }
}
</style>

<script>
import { defineComponent } from 'vue';
import 'bootstrap/dist/css/bootstrap.min.css';

// Device-adaptive interaction:
//   Desktop (has hover): hover an instrument -> info card; click it -> open manual.
//   Touch (no hover):    tap -> pin the card; long-press or the "Open manual"
//                        button -> open the manual; tap empty / ✕ -> dismiss.
export default defineComponent({
  name: 'PanelMap',
  props: {
    src: String,
    map: Object,
  },
  data() {
    return {
      imgW: 0,          // natural image size -> drives the SVG viewBox
      imgH: 0,
      hoverArea: null,  // shown while hovering (desktop)
      pinnedArea: null, // shown after a tap, until dismissed (touch)
    };
  },
  computed: {
    areas() { return (this.map && this.map.areas) || []; },
    current() { return this.pinnedArea || this.hoverArea; },
    isPinned() { return !!this.pinnedArea && this.current === this.pinnedArea; },
    strokeW() { return Math.max(1, this.imgW / 400); },
    cardImgWidth() { return (this.current && this.current.width) || '10rem'; },
  },
  beforeUnmount() { clearTimeout(this._lpTimer); },
  methods: {
    onImgLoad(e) { this.imgW = e.target.naturalWidth; this.imgH = e.target.naturalHeight; },
    rectX(a) { return Math.min(a.coords[0], a.coords[2]); },
    rectY(a) { return Math.min(a.coords[1], a.coords[3]); },
    rectW(a) { return Math.abs(a.coords[2] - a.coords[0]); },
    rectH(a) { return Math.abs(a.coords[3] - a.coords[1]); },

    onEnter(a) { if (!a.nodisplay) this.hoverArea = a; },
    onLeave(a) { if (this.hoverArea === a) this.hoverArea = null; },
    onClick(a) {                              // fires for mouse click AND after a tap
      if (this._suppressClick) { this._suppressClick = false; return; }  // touch handled it
      this.openManual(a);                     // desktop: click opens the manual
    },
    closeCard() { this.pinnedArea = null; this.hoverArea = null; },
    openManual(a) { if (a && a.href) window.open(a.href, '_blank', 'noopener'); },

    // --- touch: tap pins the card, long-press opens the manual ---
    onTouchStart(a, ev) {
      this._touchArea = a;
      this._lpReady = false;
      const t = ev.touches[0];
      this._touchStart = { x: t.clientX, y: t.clientY };
      clearTimeout(this._lpTimer);
      this._lpTimer = setTimeout(() => { this._lpReady = true; }, 500);
    },
    onTouchMove(ev) {
      if (!this._touchStart) return;
      const t = ev.touches[0];
      if (Math.hypot(t.clientX - this._touchStart.x, t.clientY - this._touchStart.y) > 12) {
        clearTimeout(this._lpTimer);
        this._lpReady = false;
      }
    },
    onTouchEnd() {
      clearTimeout(this._lpTimer);
      this._suppressClick = true;             // don't let the synthesized click open the manual
      const a = this._touchArea;
      if (this._lpReady) { this._lpReady = false; this.openManual(a); }  // long-press -> manual
      else if (a && !a.nodisplay) { this.pinnedArea = a; }               // tap -> pin the card
    },
  },
});
</script>
