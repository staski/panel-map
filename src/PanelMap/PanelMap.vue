<template>
  <div class="pm-root">
    <div class="pm-stage">
      <!-- panel image with an SVG hotspot overlay (coords are in the image's
           natural pixel space; the viewBox scales them to any display size) -->
      <div class="pm-imgwrap">
        <img class="pm-img" :src="src" alt="" @load="onImgLoad">
        <svg v-if="imgW" class="pm-overlay" :viewBox="`0 0 ${imgW} ${imgH}`"
             preserveAspectRatio="xMidYMid meet" :style="{ '--pm-sw': strokeW }">
          <!-- background: a tap/click on empty panel dismisses the card -->
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

      <!-- info card: appears beside the panel (desktop) or as a bottom sheet (mobile) -->
      <div v-if="current" class="pm-card">
        <div class="card">
          <div class="card-header d-flex justify-content-between align-items-center">
            <span class="fw-semibold">{{ current.title }}</span>
            <button type="button" class="btn-close" aria-label="Close" @click="closeCard"></button>
          </div>
          <div v-if="current.img" class="d-flex justify-content-center my-3">
            <img :src="current.img" :style="{ width: cardImgWidth }" :alt="current.title">
          </div>
          <div class="card-body">
            <p class="card-text" v-html="current.text"></p>
          </div>
          <div v-if="current.href" class="card-footer">
            <a :href="current.href" target="_blank" rel="noopener"
               class="btn btn-primary btn-sm w-100">Open manual</a>
          </div>
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
.pm-hot { fill: rgba(0, 0, 0, 0); stroke: rgba(70, 150, 245, .4);
  stroke-width: var(--pm-sw, 3); pointer-events: all; cursor: pointer;
  transition: fill .1s, stroke .1s; }
.pm-hot:hover, .pm-hot.pm-active { fill: rgba(57, 160, 255, .18); stroke: #2b8aef; }
.pm-card { flex: 0 0 320px; }
.pm-card .card { max-width: 100%; }

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

// Interaction model
//   * hover (mouse)      -> show the instrument's card
//   * click / tap        -> pin the card (stays until dismissed)
//   * "Open manual"      -> opens the linked document (works everywhere)
//   * long-press (touch) -> shortcut to open the manual directly
//   * tap empty / ✕      -> dismiss
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
      pinnedArea: null, // shown after a click/tap, until dismissed
    };
  },
  computed: {
    areas() { return (this.map && this.map.areas) || []; },
    current() { return this.pinnedArea || this.hoverArea; },
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
    onClick(a) {
      if (this._suppressClick) { this._suppressClick = false; return; }  // long-press handled it
      if (a.nodisplay) return;
      this.pinnedArea = a;
    },
    closeCard() { this.pinnedArea = null; this.hoverArea = null; },
    openManual(a) { if (a && a.href) window.open(a.href, '_blank', 'noopener'); },

    // --- long-press detection (touch) ---
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
      if (this._lpReady) {                 // held long enough -> open manual (in a user gesture)
        this._lpReady = false;
        this._suppressClick = true;        // don't let the synthesized click also pin the card
        this.openManual(this._touchArea);
      }
    },
  },
});
</script>
