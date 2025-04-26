<template>
  <div class="button-with-confirmation">
    <button 
      :class="buttonClass" 
      @click="showConfirmation = true"
      :disabled="disabled"
    >
      <slot></slot>
    </button>

    <!-- Confirmation Modal -->
    <div v-if="showConfirmation" class="confirmation-modal-backdrop" @click="cancelAction">
      <div class="confirmation-modal" @click.stop>
        <div class="confirmation-header">
          <h5>{{ title }}</h5>
          <button type="button" class="btn-close" @click="cancelAction" aria-label="Close"></button>
        </div>
        <div class="confirmation-body">
          <p>{{ message }}</p>
        </div>
        <div class="confirmation-footer">
          <button 
            type="button" 
            class="btn btn-secondary" 
            @click="cancelAction"
          >
            Cancel
          </button>
          <button 
            type="button" 
            class="btn btn-danger" 
            @click="confirmAction"
            :disabled="loading"
          >
            <span v-if="loading" class="spinner-border spinner-border-sm me-2" role="status"></span>
            Confirm
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';

const props = defineProps({
  title: {
    type: String,
    default: 'Confirm Action'
  },
  message: {
    type: String,
    default: 'Are you sure you want to perform this action?'
  },
  buttonClass: {
    type: String,
    default: 'btn btn-danger'
  },
  disabled: {
    type: Boolean,
    default: false
  },
  loading: {
    type: Boolean,
    default: false
  }
});

const emit = defineEmits(['confirm', 'cancel']);

const showConfirmation = ref(false);

const confirmAction = () => {
  emit('confirm');
  showConfirmation.value = false;
};

const cancelAction = () => {
  emit('cancel');
  showConfirmation.value = false;
};
</script>

<style scoped>
.confirmation-modal-backdrop {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1050;
}

.confirmation-modal {
  background-color: white;
  border-radius: 4px;
  max-width: 400px;
  width: 100%;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
}

.confirmation-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem;
  border-bottom: 1px solid #dee2e6;
}

.confirmation-header h5 {
  margin: 0;
}

.confirmation-body {
  padding: 1rem;
}

.confirmation-footer {
  display: flex;
  justify-content: flex-end;
  gap: 0.5rem;
  padding: 1rem;
  border-top: 1px solid #dee2e6;
}
</style> 