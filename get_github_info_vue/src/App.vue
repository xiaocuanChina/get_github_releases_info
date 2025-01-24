<template>
  <div id="app">
    <StarredReleases />
  </div>
</template>

<script>
import StarredReleases from './main/StarredReleases.vue'

export default {
  name: 'App',
  components: {
    StarredReleases
  }
}
</script>

<style>
#app {
  font-family: Avenir, Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  color: #2c3e50;
}
</style>
