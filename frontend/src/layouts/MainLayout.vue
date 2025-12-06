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
}

.content-area {
  margin-left: 220px;
  flex: 1;
  padding: 24px;
  overflow-y: auto;
}
</style>
