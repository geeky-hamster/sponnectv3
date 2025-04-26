<template>
  <div 
    class="profile-icon" 
    :class="[`bg-${bgColor || 'primary'}`, size]"
    :style="customStyle"
  >
    {{ initial }}
  </div>
</template>

<script setup>
import { computed } from 'vue';

const props = defineProps({
  name: {
    type: String,
    default: 'User'
  },
  size: {
    type: String,
    default: 'md',
    validator: (value) => ['sm', 'md', 'lg', 'xl'].includes(value)
  },
  bgColor: {
    type: String,
    default: 'primary'
  },
  customStyle: {
    type: Object,
    default: () => ({})
  }
});

const initial = computed(() => {
  if (!props.name) return 'U';
  return props.name.charAt(0).toUpperCase();
});
</script>

<style scoped>
.profile-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  color: white;
  font-weight: bold;
}

.sm {
  width: 30px;
  height: 30px;
  font-size: 14px;
}

.md {
  width: 40px;
  height: 40px;
  font-size: 18px;
}

.lg {
  width: 60px;
  height: 60px;
  font-size: 24px;
}

.xl {
  width: 100px;
  height: 100px;
  font-size: 40px;
}
</style> 