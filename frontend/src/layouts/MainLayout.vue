<template>
  <div class="main-layout">
    <Sidebar @collapse-change="onCollapseChange" />
    <div class="content-area" :class="{ collapsed }">
      <router-view />
    </div>
  </div>
</template>

<script>
import Sidebar from '../components/Sidebar.vue'
import { ref } from 'vue'

export default {
  name: 'MainLayout',
  components: { Sidebar },
  setup() {
    const collapsed = ref(false)
    const onCollapseChange = (val) => { collapsed.value = val }
    return { collapsed, onCollapseChange }
  }
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
  transition: margin-left 0.3s cubic-bezier(0.4, 0, 0.2, 1);

  &::-webkit-scrollbar { width: 6px; }
  &::-webkit-scrollbar-track { background: #0a0e0a; }
  &::-webkit-scrollbar-thumb {
    background: rgba(0, 255, 127, 0.3);
    border-radius: 3px;
    &:hover { background: #00ff7f; box-shadow: 0 0 8px rgba(0, 255, 127, 0.6); }
  }
  scrollbar-width: thin;
  scrollbar-color: rgba(0, 255, 127, 0.3) #0a0e0a;
}

.content-area.collapsed {
  margin-left: 56px;
}

@media (max-width: 900px) {
  .content-area { margin-left: 56px !important; }
}
</style>
