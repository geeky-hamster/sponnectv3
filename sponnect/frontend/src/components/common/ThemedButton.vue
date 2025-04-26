<template>
  <button 
    :class="buttonClasses"
    :disabled="disabled || loading"
    @click="$emit('click', $event)"
  >
    <span v-if="loading" class="spinner-border spinner-border-sm me-2" role="status"></span>
    <slot></slot>
  </button>
</template>

<script setup>
import { computed } from 'vue';

const props = defineProps({
  variant: {
    type: String,
    default: 'primary',
    validator: (value) => [
      'primary', 'secondary', 'success', 
      'danger', 'warning', 'info', 
      'light', 'dark', 'link'
    ].includes(value)
  },
  size: {
    type: String,
    default: '',
    validator: (value) => ['', 'sm', 'lg'].includes(value)
  },
  outline: {
    type: Boolean,
    default: false
  },
  block: {
    type: Boolean,
    default: false
  },
  disabled: {
    type: Boolean,
    default: false
  },
  loading: {
    type: Boolean,
    default: false
  },
  rounded: {
    type: Boolean,
    default: false
  },
  customClass: {
    type: String,
    default: ''
  }
});

defineEmits(['click']);

const buttonClasses = computed(() => {
  const classes = ['btn'];
  
  // Add variant
  classes.push(props.outline ? `btn-outline-${props.variant}` : `btn-${props.variant}`);
  
  // Add size
  if (props.size) {
    classes.push(`btn-${props.size}`);
  }
  
  // Add block display
  if (props.block) {
    classes.push('d-block w-100');
  }
  
  // Add rounded style
  if (props.rounded) {
    classes.push('rounded-pill');
  }
  
  // Add custom classes
  if (props.customClass) {
    classes.push(props.customClass);
  }
  
  return classes.join(' ');
});
</script>

<style scoped>
button {
  transition: all 0.2s ease-in-out;
}

button:disabled {
  cursor: not-allowed;
}
</style> 