<template>
  <PanelMap v-if="ready" :src="src" :map="map"/>
  <p v-else-if="error" class="text-danger">Failed to load panel config: {{ error }}</p>
  <p v-else>Loading panel…</p>
</template>

<style>

body {
  padding: 1rem;
}

</style>

<script>
import 'bootstrap/dist/css/bootstrap.min.css';
import PanelMap from '@staski/panel-map';

// The panel configuration and all its assets (panel image, instrument pictures,
// docs, texts) are loaded at RUNTIME from the server's public/ tree, not bundled
// at build time. To update a picture, doc or text, edit the served files under
// panel/ , images/ and docs/ — no rebuild of the app is required.
export default {
  name: 'App',
  components: { PanelMap },
  data() {
    return { src: '', mapName: 'panel', areas: [], ready: false, error: '' };
  },
  computed: {
    map() { return { areas: this.areas, name: this.mapName }; },
  },
  async mounted() {
    const base = import.meta.env.BASE_URL;              // works under any deploy sub-path
    const url = p => (p ? base + String(p).replace(/^\/+/, '') : undefined);
    try {
      const res = await fetch(url('panel/areas.json'), { cache: 'no-store' });
      if (!res.ok) throw new Error('HTTP ' + res.status + ' for panel/areas.json');
      const cfg = await res.json();
      this.src = url(cfg.image);
      this.mapName = cfg.name || 'panel';
      this.areas = (cfg.areas || []).map(a => ({
        ...a,
        img: url(a.img),          // popup picture (server-relative -> full URL)
        href: url(a.doc),         // component reads `href`; config stores `doc`
      }));
      this.ready = true;
    } catch (e) {
      this.error = e.message;
    }
  },
}

</script>
