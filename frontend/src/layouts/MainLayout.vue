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
  overflow-y: auto;
  overflow-x: hidden;
  background: #000;

  /* 隐藏滚动条 */
  &::-webkit-scrollbar {
    width: 6px;
  }
  
  &::-webkit-scrollbar-track {
    background: #0a0e0a;
  }
  
  &::-webkit-scrollbar-thumb {
    background: rgba(0, 255, 127, 0.3);
    border-radius: 3px;
    
    &:hover {
      background: #00ff7f;
      box-shadow: 0 0 8px rgba(0, 255, 127, 0.6);
    }
  }

  /* Firefox */
  scrollbar-width: thin;
  scrollbar-color: rgba(0, 255, 127, 0.3) #0a0e0a;
}
</style>
