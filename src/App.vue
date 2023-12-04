<template>
  <PanelMap  :src="url" :map="map"/>
</template>

<script>


import  PanelMap from './PanelMap/PanelMap.vue';
import images from './images';
import docs from './docs';


var panelAreas = [
    {
      name: 'g52',
      shape: 'rect',
      coords: [352,194,524,355],
      fillColor: 'rgb(255,100,0,0.0)',
      id: '1',
      img: images.imgDemo,
      title: 'Garmin G5 EFIS (as HSI)',
      href: docs.docDemo,
      width: "18rem",
      text: "Example description: this is a Garmin G5 EFIS"
    },
    {
      name: 'avidyne',
      shape: 'rect',
      coords: [898,66,1194,198],
      fillColor: 'rgb(100,255,0,0.0)',
      id: '2',
      title: 'Avidyne IFD440 navigator',
      img: images.imgDemo,
      href: docs.docDemo,
      width: "18rem",
      text: "Example description: this is an Avidyne IFD440 navigator"
    }
  ];

  export default {
  name: 'App',
  components: {
    PanelMap,
  },
  computed: {
    url() {
      return images.imgCockpitPanel
    },
    map(){
      return {
        areas: panelAreas,
        name: 'panel-dexpl',
      };
    },
  }
}
</script>
