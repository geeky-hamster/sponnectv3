<script setup>
import { RouterView } from 'vue-router'
import Navbar from './components/Navbar.vue'
import { useAuthStore } from './stores/auth'
import Footer from './components/Footer.vue'
import { ref, onErrorCaptured } from 'vue'

const authStore = useAuthStore()

// Add error handling for route loading errors
const routeError = ref(null)

onErrorCaptured((err, instance, info) => {
  // Handle route loading errors gracefully
  console.error('App error captured:', err, info)
  if (err.message && err.message.includes('error loading dynamically imported module')) {
    routeError.value = {
      message: 'Failed to load page. Try refreshing the browser.',
      details: err.message,
      time: new Date().toISOString()
    }
    return false // prevent error from propagating
  }
  return true // let other errors propagate
})
</script>

<template>
  <header>
    <Navbar />
  </header>

  <main>
    <!-- Error boundary for route loading errors -->
    <div v-if="routeError" class="container mt-5">
      <div class="alert alert-danger">
        <h4 class="alert-heading">Page Loading Error</h4>
        <p>{{ routeError.message }}</p>
        <hr>
        <div class="d-flex justify-content-between align-items-center">
          <small class="text-muted">{{ routeError.time }}</small>
          <button @click="window.location.reload()" class="btn btn-outline-danger">Refresh Page</button>
        </div>
      </div>
    </div>
    
    <!-- Normal route view when no errors -->
    <RouterView v-else />
  </main>

  <Footer />
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

<style>
/* Fix dropdown z-index issues globally */
.dropdown-menu {
  z-index: 9999 !important;
}

/* Make sure the Bootstrap dropdowns work correctly */
.dropdown-toggle.show {
  z-index: 1000 !important;
}

/* Add additional styles for better dropdown appearance */
.dropdown-menu {
  box-shadow: 0 0.5rem 1rem rgba(0, 0, 0, 0.15);
  border: none;
  border-radius: 0.5rem;
}

/* Fix bootstrap modal z-index */
.modal-backdrop {
  z-index: 1040 !important;
}
.modal {
  z-index: 1045 !important;
}

/* Make sure text-truncate works properly */
.text-truncate {
  max-width: 100%;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  display: inline-block;
}
</style>
