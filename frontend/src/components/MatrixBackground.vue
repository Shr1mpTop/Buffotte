<template>
  <div class="matrix-bg">
    <div class="scan-line" aria-hidden="true"></div>
  </div>
</template>

<script>
export default { name: 'MatrixBackground' }
</script>

<style scoped>
.matrix-bg { position: fixed; inset: 0; z-index: -1; pointer-events: none; }
.scan-line { position:absolute; left:0; top:-20%; width:100%; height:3px; background:linear-gradient(90deg, transparent, rgba(0,255,127,0.18), transparent); animation: scan 6s linear infinite; }
@keyframes scan { 0% { top:-10%; } 50% { top:50%; } 100% { top:110%; } }
</style>
