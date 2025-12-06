<template>
  <div class="main-layout">
    <Sidebar />
    <div class="content-area">
      <router-view />
    </div>
  </div>
</template>

<script>
import Sidebar from '../components/Sidebar.vue'

export default {
  name: 'MainLayout',
  components: { Sidebar }
}
</script>

<style scoped>
.main-layout {
  display: flex;
  min-height: 100vh;
  background: #000;
  overflow: hidden;
}

.content-area {
  flex: 1;
  padding: 0;
  margin: 0 0 0 220px;
  height: 100vh;
  overflow: hidden;
  display: flex;
  align-items: flex-start;
  justify-content: center;
  background: #000;
}
</style>
