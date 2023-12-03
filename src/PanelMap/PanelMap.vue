<template>
  <ImageMapper :src="src" :img-width="imgWidth" :width="width" :map="map" :active="true" :responsive="false" />
</template>

<script>

import { defineComponent } from 'vue';
import { nextTick } from 'vue';

import ImageMapper from '@staski/vue-img-mapper';

import 'bootstrap/dist/css/bootstrap.min.css';
import * as bootstrap from 'bootstrap/dist/js/bootstrap.bundle';


export default defineComponent({
  name: 'PanelMap',
  components: {
    ImageMapper,
  },
  props: {  src: String,
            imgWidth: Number,
            width: Number,
            panelAreas: Array,
            popImgW: Number,
            map: Object,
  },
  mounted() {
    nextTick(() => this.getPopList());
  },
  methods: {
    getPopList() {
      this.map.areas.forEach(element => {
        let scale = this.width / this.imgWidth;
        var placement = 'right';
        var el = document.getElementById(element.id);
        let d2 = "<img src=" + element.img + " width=" + this.popImgW + "></img>";
        let myvar = {
          title: element.title,
          content: function () {
            return document.getElementById(element.name).innerHTML;
          },
          trigger: 'hover',
          container: 'body',
          placement: placement,
          offset: function () {
            let x, y;
            if (element.shape === 'rect') {
              y = Math.floor(parseInt(element.coords[3]) * scale);
              x = Math.floor(parseInt(element.coords[2]) * scale) + 10;
            } else if (element.shape == 'circle') {
              let r = Math.floor(parseInt(element.coords[2]) * scale);
              y = Math.floor(parseInt(element.coords[1]) * scale);
              x = Math.floor(parseInt(element.coords[0]) * scale);
              x = x + r;
            }
            if (navigator.userAgent.toLowerCase().indexOf('firefox') > -1) {
              return [0,0];
            } 
            return [y,x];
          },
          html: true,
          template:
            '<div class="popover"><div class="arrow"></div><h3 class="popover-header"></h3><div class="popover-image">' + d2 + '</div><div class="popover-body"></div></div>',
        };
        console.log(this.$refs);
        new bootstrap.Popover(el, myvar);
      });
    },
    showPos(e) {
      console.log(e.screenX, e.screenY);
      console.log(e.x, e.y);
    },
  },
});

</script>
<style>
.popover {
  max-width: 600px;
}
img {
  display: block;
  padding: 0px;
  margin-left: auto;
  margin-right: auto;
}
.popover-image {
  display: block;
  padding: 20px;
  margin-left: auto;
  margin-right: auto;
}
popover-header {
  text-align: center;
}
</style>
