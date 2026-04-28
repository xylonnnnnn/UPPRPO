<template>
  <!-- 🔥 Это "окошко", куда Vue Router будет подставлять страницы -->
  <router-view />
</template>

<script setup>
// Скрипт тут пока не нужен. Вся логика живёт в роутере и страницах.
</script>

<style>
#app {
  font-family: Avenir, Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-align: center;
  color: #2c3e50;
  margin-top: 0; /* убрал 60px, чтобы страницы занимали весь экран */
  min-height: 100vh;
  background: #f0f0f0;
}
</style>