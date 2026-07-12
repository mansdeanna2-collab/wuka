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
  background: var(--admin-bg);
}
</style>
