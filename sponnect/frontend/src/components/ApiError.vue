<script setup>
import { ref, watch } from 'vue';

const props = defineProps({
  error: {
    type: [String, Object, Error],
    default: null
  },
  dismissible: {
    type: Boolean,
    default: true
  },
  retry: {
    type: Function,
    default: null
  }
});

const emit = defineEmits(['dismiss']);

const visible = ref(!!props.error);
const errorMessage = ref('');

// Handle error formatting
watch(() => props.error, (newError) => {
  visible.value = !!newError;
  
  if (!newError) {
    errorMessage.value = '';
    return;
  }
  
  // Format error message based on type
  if (typeof newError === 'string') {
    errorMessage.value = newError;
  } else if (newError instanceof Error) {
    errorMessage.value = newError.message;
  } else if (newError.response && newError.response.data) {
    // Axios error
    const responseData = newError.response.data;
    if (typeof responseData === 'string') {
      errorMessage.value = responseData;
    } else if (responseData.message) {
      errorMessage.value = responseData.message;
    } else if (responseData.error) {
      errorMessage.value = responseData.error;
    } else {
      errorMessage.value = `Request failed with status ${newError.response.status}`;
    }
  } else {
    errorMessage.value = 'An unexpected error occurred';
  }
}, { immediate: true });

const dismiss = () => {
  visible.value = false;
  emit('dismiss');
};

const handleRetry = () => {
  if (props.retry && typeof props.retry === 'function') {
    props.retry();
  }
};
</script>

<template>
  <div v-if="visible && errorMessage" class="api-error">
    <div class="alert alert-danger" role="alert">
      <div class="d-flex align-items-center">
        <i class="bi bi-exclamation-triangle-fill me-2"></i>
        <div class="flex-grow-1">{{ errorMessage }}</div>
        <div v-if="dismissible" class="ms-auto">
          <button type="button" class="btn-close" @click="dismiss"></button>
        </div>
      </div>
      
      <div v-if="retry" class="mt-2 text-end">
        <button class="btn btn-sm btn-outline-danger" @click="handleRetry">
          <i class="bi bi-arrow-repeat me-1"></i> Retry
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.api-error {
  margin-bottom: 1.5rem;
}
</style> 