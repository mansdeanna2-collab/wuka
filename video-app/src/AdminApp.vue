<template>
  <div class="admin-app">
    <router-view />
  </div>
</template>

<script>
export default {
  name: 'AdminApp'
}
</script>

<style>
/* Admin app wrapper styles */
.admin-app {
  min-height: 100vh;
  background: #0f0f1a;
}
</style>
