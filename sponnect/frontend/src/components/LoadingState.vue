<script setup>
defineProps({
  message: {
    type: String,
    default: 'Loading...'
  },
  size: {
    type: String,
    default: 'md', // 'sm', 'md', 'lg'
    validator: (value) => ['sm', 'md', 'lg'].includes(value)
  },
  fullPage: {
    type: Boolean,
    default: false
  },
  overlay: {
    type: Boolean,
    default: false
  }
});

// Size mappings
const spinnerSizeClass = {
  sm: 'spinner-border-sm',
  md: '',
  lg: 'spinner-border-lg'
};
</script>

<template>
  <div :class="[
    'loading-container', 
    { 'loading-fullpage': fullPage, 'loading-overlay': overlay }
  ]">
    <div class="loading-content">
      <div 
        class="spinner-border text-primary" 
        :class="spinnerSizeClass[size]" 
        role="status"
      >
        <span class="visually-hidden">Loading...</span>
      </div>
      <p v-if="message" class="loading-message mt-2">{{ message }}</p>
    </div>
  </div>
</template>

<style scoped>
.loading-container {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 2rem;
}

.loading-fullpage {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(255, 255, 255, 0.9);
  z-index: 9999;
}

.loading-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(255, 255, 255, 0.8);
  z-index: 100;
}

.loading-content {
  text-align: center;
}

.loading-message {
  color: #6c757d;
  margin-bottom: 0;
}

.spinner-border-lg {
  width: 3rem;
  height: 3rem;
  border-width: 0.25rem;
}
</style> 