<template>
  <PanelMap  :src="url" :map="map"/>
</template>

<style>

body {
  padding: 1rem;
}

</style>

<script>
import 'bootstrap/dist/css/bootstrap.min.css';
import  PanelMap from '@staski/panel-map';
import * as panel from './panelAreas';
import images from './images';

export default {
  name: 'App',
  components: {
    PanelMap,
  },
  computed: {
    url() {
      return images.imgcockpitpanel
    },
    map(){
      return {
        areas: panel.panelAreas,
        name: 'demo-panel',
      };
    },
  }
}

</script>
