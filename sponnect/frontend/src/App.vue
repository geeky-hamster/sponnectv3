<script setup>
import { RouterView } from 'vue-router'
import Navbar from './components/Navbar.vue'
import { useAuthStore } from './stores/auth'

const authStore = useAuthStore()
</script>

<template>
  <header>
    <Navbar />
  </header>

  <main>
    <RouterView />
  </main>

  <footer class="py-4 bg-dark text-white mt-5">
    <div class="container text-center">
      <p class="mb-0">© 2023 Sponnect - Connecting Sponsors & Influencers</p>
    </div>
  </footer>
</template>

<style scoped>

.logo {
  height: 6em;
  padding: 1.5em;
  will-change: filter;
  transition: filter 300ms;
}
.logo:hover {
  filter: drop-shadow(0 0 2em #646cffaa);
}
.logo.vue:hover {
  filter: drop-shadow(0 0 2em #42b883aa);
}
</style>
