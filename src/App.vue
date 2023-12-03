<template>
  <PanelMap  :src="url" :map="map" :img-width="1280" :width="800" :popImgW="200"/>
  <div id="g52" hidden>
    Garmin G5 Eletronic Flight Instrument System (EFIS), used as a Horizontal Situation Indicator
    (HSI). In this mode the G5 displays lateral deviation from a track selected by a GPS source or a
    VOR receiver as well as vertical glideslope.
    <hr>
    <p>Click on the instrument to open it's Pilot's Guide.</p>
  </div>
  <div id="avidyne" hidden>
    The Avidyne IFD440 navigator serves multipe functions.
    <ol>
      <li>a navigation receiver for analog navigation aids like VOR, ILS as well as a GPS receiver</li>
      <li>a VHF-communictation transceiver</li>
      <li>a flight management system, which allows to create and edit flightplans</li>
      <li>a moving map, displaying the current flight plan and the plane's current location</li>
    </ol>
    <hr>
    <p>Click on the instrument to open it's Pilot's Guide.</p>
  </div>
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
        name: 'panel-demcf',
      };
    },
  }
}
</script>
