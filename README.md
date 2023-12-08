# panel-map

A simple Vue component that enbables popups over highlighted areas of an image map. The popup will appear on the rightmost column of the screen. Main pupose is for displaying a virtual airplane instrument panel and provide information about the instruments once you hover over them on the image. The component is reactive in the sense that it resizes the main picture when resizing the screen. Please note however, that this component will not produce meaningful results on mobile devies (phones or tablets)
## Dependencies

panel-map depends only on [bootstrap](https://getbootstrap.com) for display of the info card on the right side. 
## Usage

Import the component as you normally do, and add it wherever you like in your JSX views as below:

```javascript           
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
```
## Properties


|Props|Type|Description|Default|        
|---|---|---|---| 
|***map***|*Object*|object containing a unique name and an array of `areas`, for a description of these `areas`, see below |*required*|
|***src***|*String*|the URL pointing to the image of the cockpit panel|*required*|

The `areas` attribute of the `map` prop has to be an array of objects describing the highlighted areas with the following elements:

```javascript
{
  name: String // describing the instrument in questions. This string is the anchor for the text element displayed in the popup
  shape: String // either 'rect' or 'circle'
  coords: [Number] // the coordinates of the shape as in area map
  fillColor: Color // the color of the shape when highlighted
  id: Number // a unique ID
  width: String // the width of the image. Used for scaling images to a common size
  title: String // displayed as title of the popup
  img: Image // displayed in the popup
  doc: Document // opened in a new browser tab when clicking the instrument
  text: String // the description of the instrument displayed in the card 
}
```

## Getting started

The easiest way to getting started is cloning this repository and then filling the images, docs, texts with your corresponding data.

```sh
git clone git@github.com:staski/panel-map.git
cd vpanel
npm install
npm run dev
```

this will bring up a local server with the demo panel. Bring your own images and docs for your instruments. See https://github.com/staski/panel-map for advanced options. The demo should look like this.


![image](https://github.com/staski/vpanel/assets/25439303/4d77bb57-dc7c-4ee6-afee-0064a4921405)
## License

Distributed with an MIT License. See LICENSE.txt for more details!

Copyright (c) 2023 Carl Philipp Staszkiewicz
