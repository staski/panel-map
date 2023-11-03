# panel-map

A simple Vue component that enbables popups over highlighted areas of an image map. Main pupose is for displaying a virtual airplane instrument panel and provide information about the instruments once you hover over them on the image.
## Usage

Import the component as you normally do, and add it wherever you like in your JSX views as below:

```javascript           
<template>
  <PanelMap  :src="url" :panel-areas="pas" :img-width="1280" :width="1280" :popImgW="500"/>
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

import  PanelMap from '@staski/panel-map';
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
    pas() {
      return panelAreas
    }
  }
}
```
## Properties

|Props|Type|Description|Default|        
|---|---|---|---| 
|***pas***|*Array*|see below|*required*|
|***img-width***|*Number*|width of the cockpit panel image|*required*|
|***width***|*Number*|width of the screen display of the cockpit panel|*required*|
|***popImgW***|*Number*|width of the instrument image displayed in the popup|*required*|

pas has to be provided by an array called panelAreas. panelAreas has to be an array of objects describing the highlighted areas with the following elements:

```javascript
{
  name: String // describing the instrument in questions. This string is the anchor for the text element displayed in the popup
  shape: String // either 'rect' or 'circle'
  coords: [Number] // the coordinates of the shape as in area map
  fillColor: Color // the color of the shape when highlighted
  id: Number // a unique ID
  title: String // displayed as title of the popup
  img: Image // displayed in the popup
  doc: Document // opened in a new browser tab when clicking the instrument
}
```

## License

Distributed with an MIT License. See LICENSE.txt for more details!

Copyright (c) 2023 Carl Philipp Staszkiewicz
