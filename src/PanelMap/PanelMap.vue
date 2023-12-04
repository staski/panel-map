<template>
  <div class="container-fluid">
      <div class="row">
        <div class="col">
          <img  ref="img" :src="src" @load="initValues()" :useMap="`#${map.name}`" :width="width"/>
        <map
          :name="map.name"
        >
          <area
            v-for="(area) in map.areas"
            :key="area.id"
            :id="area.id"
            :coords="extendedArea(area).scaledCoords.join(',')"
            :shape="area.shape"
            :href="area.href"
            @mouseenter="handleMouseEnter(extendedArea(area), $event)"
            @mouseleave="handleMouseLeave(extendedArea(area), $event)"
            alt="map"
            target="_blank"
          />
        </map>
        </div>
        <div class="col p-3" v-show="hoveron">
          <div class="card" >
            <h5 class="card-header">{{ this.title }}</h5>
            <div class="d-flex justify-content-center my-4" v-if="this.instrumentImage">
            <img :src="this.instrumentImage" :style="{ width: this.cardImgWidth }" :alt="this.title">
            </div>
            <div class="card-body">
              <p class="card-text"><span v-html="this.description"></span></p>
            </div>
            <h6 class="card-footer" v-if="displayFooter"> Click to open the manual</h6>
          </div>      
        </div>
    </div>
  </div>
</template>

<style>

.card {
    display: block;
    max-width: 26rem;
}

</style>

<script>
import { defineComponent } from 'vue';
import 'bootstrap/dist/css/bootstrap.min.css';

export default defineComponent({
  name: 'PanelMap',
  props: {  src: String,
            map: Object,
  },
  data () {
    return {
      hoveron: false,
      displayFooter: false,
      instrumentImage : null,
      description: undefined,
      title: "",
      imgWidth: 0, //the natural image width
      width: 0, // the image width as displayed
      cardImgWidth: "",
      cardImgDefaultWidth: "10rem",
    }
  },
  mounted () {
    this.width = window.innerWidth - 480;
    window.addEventListener('resize', this.onResize);
  },
  beforeDestroy() {
    window.removeEventListener('resize', this.onResize);
  },
  methods: { 
    initValues() {
      this.imgWidth = this.$refs.img.naturalWidth;
    },
    onResize() {
      this.width = window.innerWidth - 480;
    },
    extendedArea(area) {
      const scaledCoords = this.scaleCoords(area.coords);
      return { ...area, scaledCoords};
    },
    scaleCoords(coords) {
      const scale =
        this.width && this.imgWidth && this.imgWidth > 0 ? this.width / this.imgWidth : 1;
      return coords.map(coord => coord * scale);
    },
    handleMouseEnter(area, event) {
      if (arguments.length < 2) {
        return;
      }
      if (area.nodisplay == true){
        return;
      }
      if (area.img === undefined){
        this.instrumentImage = undefined;
      }
      if (area.href !== undefined){
        this.displayFooter = true;
      }
      this.hoveron = true;
      this.instrumentImage = area.img;
      this.description = area.text;
      this.title = area.title;
      if (area.width) {
        this.cardImgWidth = area.width;
      } else {
        this.cardImgWidth = this.cardImgDefaultWidth;
      }
     },
    handleMouseLeave(area, event) {
      this.hoveron = false;
      this.displayFooter = false;
    },
  },  
});
</script>
