<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { influencerService } from '../../services/api'

const route = useRoute()
const router = useRouter()
const requestId = route.params.id

// State
const loading = ref(true)
const submitLoading = ref(false)
const adRequest = ref(null)
const error = ref('')
const successMessage = ref('')

// Negotiation form
const form = reactive({
  action: '',
  counterOffer: null,
  message: ''
})

// Form validation
const formErrors = reactive({
  action: '',
  counterOffer: '',
  message: ''
})

// Available actions
const actions = [
  { value: 'accept', label: 'Accept Offer', description: 'Accept the current offer and proceed with the partnership' },
  { value: 'negotiate', label: 'Make Counter Offer', description: 'Propose a different amount or terms' },
  { value: 'reject', label: 'Decline Offer', description: 'Reject this offer and end negotiations' }
]

// Computed property for disabled actions based on current status
const disabledActions = computed(() => {
  if (!adRequest.value) return []
  
  const status = adRequest.value.status
  if (status === 'Accepted' || status === 'Rejected') {
    return ['accept', 'negotiate', 'reject']
  }
  return []
})

// Load ad request details
const loadAdRequest = async () => {
  try {
    loading.value = true
    error.value = ''
    
    // Since we're using the getAdRequests endpoint that returns all requests,
    // we need to filter for the specific one based on the ID
    const response = await influencerService.getAdRequests()
    const foundRequest = (response.data || []).find(req => req.id === parseInt(requestId))
    
    if (foundRequest) {
      adRequest.value = foundRequest
      
      // Pre-fill counter offer with current amount
      if (foundRequest.payment_amount) {
        form.counterOffer = foundRequest.payment_amount
      }
    } else {
      error.value = 'Ad request not found'
    }
  } catch (err) {
    console.error('Failed to load ad request:', err)
    error.value = 'Failed to load ad request details. Please try again later.'
  } finally {
    loading.value = false
  }
}

// Format date for better display
const formatDate = (dateString) => {
  if (!dateString) return 'N/A'
  
  const date = new Date(dateString)
  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

// Format currency
const formatCurrency = (amount) => {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 0
  }).format(amount || 0)
}

// Validate form
const validateForm = () => {
  let isValid = true
  
  // Reset errors
  formErrors.action = ''
  formErrors.counterOffer = ''
  formErrors.message = ''
  
  // Validate action
  if (!form.action) {
    formErrors.action = 'Please select an action'
    isValid = false
  }
  
  // Validate counter offer if negotiating
  if (form.action === 'negotiate') {
    if (!form.counterOffer) {
      formErrors.counterOffer = 'Please enter your counter offer amount'
      isValid = false
    } else if (form.counterOffer <= 0) {
      formErrors.counterOffer = 'Amount must be greater than zero'
      isValid = false
    }
  }
  
  // Validate message for negotiate or reject
  if (['negotiate', 'reject'].includes(form.action) && !form.message.trim()) {
    formErrors.message = `Please provide a message explaining your ${form.action === 'negotiate' ? 'counter offer' : 'rejection'}`
    isValid = false
  }
  
  return isValid
}

// Handle form submission
const handleSubmit = async () => {
  if (!validateForm()) return
  
  try {
    submitLoading.value = true
    error.value = ''
    successMessage.value = ''
    
    // Build the payload based on the action
    const payload = {
      status: form.action === 'accept' ? 'Accepted' : form.action === 'reject' ? 'Rejected' : 'Negotiating',
      message: form.message,
      payment_amount: form.action === 'negotiate' ? form.counterOffer : adRequest.value.payment_amount
    }
    
    // Send the response to the ad request
    await influencerService.respondToAdRequest(adRequest.value.id, payload)
    
    // Update success message
    successMessage.value = form.action === 'accept' 
      ? 'Offer accepted successfully! The sponsor will be notified.' 
      : form.action === 'reject'
        ? 'Offer rejected. The sponsor will be notified.' 
        : 'Counter offer sent. Waiting for the sponsor to respond.'
    
    // Reload ad request to get updated status
    await loadAdRequest()
    
    // Reset form
    form.action = ''
    form.message = ''
    
  } catch (err) {
    console.error('Failed to respond to ad request:', err)
    error.value = 'Failed to submit your response. Please try again later.'
  } finally {
    submitLoading.value = false
  }
}

// Get status badge class
const getStatusBadgeClass = (status) => {
  switch (status) {
    case 'Pending': return 'bg-warning'
    case 'Negotiating': return 'bg-info'
    case 'Accepted': return 'bg-success'
    case 'Rejected': return 'bg-danger'
    default: return 'bg-secondary'
  }
}

// Navigate back to ad requests list
const goBack = () => {
  router.push('/influencer/ad-requests')
}

// Load data on component mount
onMounted(() => {
  loadAdRequest()
})
</script>

<template>
  <div class="ad-request-detail-view py-5">
    <div class="container">
      <!-- Back Button and Breadcrumbs -->
      <div class="d-flex justify-content-between align-items-center mb-4">
        <button class="btn btn-outline-secondary" @click="goBack">
          <i class="bi bi-arrow-left me-2"></i>Back to Ad Requests
        </button>
        <nav aria-label="breadcrumb">
          <ol class="breadcrumb mb-0">
            <li class="breadcrumb-item">
              <router-link to="/influencer/dashboard">Dashboard</router-link>
            </li>
            <li class="breadcrumb-item">
              <router-link to="/influencer/ad-requests">Ad Requests</router-link>
            </li>
            <li class="breadcrumb-item active">Request Details</li>
          </ol>
        </nav>
      </div>
      
      <!-- Error Alert -->
      <div v-if="error" class="alert alert-danger alert-dismissible fade show mb-4" role="alert">
        {{ error }}
        <button type="button" class="btn-close" @click="error = ''"></button>
      </div>
      
      <!-- Success Alert -->
      <div v-if="successMessage" class="alert alert-success alert-dismissible fade show mb-4" role="alert">
        {{ successMessage }}
        <button type="button" class="btn-close" @click="successMessage = ''"></button>
      </div>
      
      <!-- Loading Spinner -->
      <div v-if="loading" class="text-center py-5">
        <div class="spinner-border text-primary" role="status">
          <span class="visually-hidden">Loading...</span>
        </div>
        <p class="mt-3">Loading ad request details...</p>
      </div>
      
      <!-- Ad Request Not Found -->
      <div v-else-if="!adRequest" class="card border-0 shadow-sm">
        <div class="card-body text-center py-5">
          <i class="bi bi-exclamation-circle fs-1 text-muted mb-3"></i>
          <h3>Ad Request Not Found</h3>
          <p class="text-muted mb-4">The requested ad request could not be found.</p>
          <button class="btn btn-primary" @click="goBack">
            Back to Ad Requests
          </button>
        </div>
      </div>
      
      <!-- Ad Request Details -->
      <div v-else>
        <div class="card border-0 shadow-sm mb-4">
          <div class="card-header bg-white border-0 py-3">
            <div class="d-flex justify-content-between align-items-center">
              <h1 class="h3 mb-0">{{ adRequest.campaign_name }}</h1>
              <span :class="`badge ${getStatusBadgeClass(adRequest.status)} px-3 py-2 fs-6`">
                {{ adRequest.status }}
              </span>
            </div>
          </div>
          
          <div class="card-body">
            <!-- Request Details -->
            <div class="row mb-4">
              <div class="col-md-6">
                <div class="mb-3">
                  <label class="text-muted d-block mb-1">Sponsor</label>
                  <div class="fs-5">{{ adRequest.sponsor_name || 'Unknown Sponsor' }}</div>
                </div>
                <div class="mb-3">
                  <label class="text-muted d-block mb-1">Campaign</label>
                  <div class="fs-5">{{ adRequest.campaign_name }}</div>
                </div>
                <div class="mb-3">
                  <label class="text-muted d-block mb-1">Created</label>
                  <div>{{ formatDate(adRequest.created_at) }}</div>
                </div>
              </div>
              <div class="col-md-6">
                <div class="mb-3">
                  <label class="text-muted d-block mb-1">Last Updated</label>
                  <div>{{ formatDate(adRequest.updated_at) }}</div>
                </div>
                <div class="mb-3">
                  <label class="text-muted d-block mb-1">Last Action By</label>
                  <div>{{ adRequest.last_offer_by || 'N/A' }}</div>
                </div>
                <div class="mb-3">
                  <label class="text-muted d-block mb-1">Current Offer</label>
                  <div class="fs-4 fw-bold text-primary">{{ formatCurrency(adRequest.payment_amount) }}</div>
                </div>
              </div>
            </div>
            
            <hr class="my-4" />
            
            <!-- Requirements Section -->
            <div class="mb-4">
              <h5 class="mb-3">Requirements</h5>
              <div class="p-3 bg-light rounded">
                <p class="mb-0 whitespace-pre-wrap">{{ adRequest.requirements || 'No specific requirements provided.' }}</p>
              </div>
            </div>
            
            <!-- Message/Note Section -->
            <div class="mb-4">
              <h5 class="mb-3">Message</h5>
              <div class="p-3 bg-light rounded">
                <p class="mb-0 whitespace-pre-wrap">{{ adRequest.message || 'No message provided.' }}</p>
              </div>
            </div>
            
            <!-- History Section (could be expanded to show negotiation history) -->
            <div class="mb-0">
              <h5 class="mb-3">Status</h5>
              <div class="p-3 bg-light rounded d-flex align-items-center">
                <span :class="`badge ${getStatusBadgeClass(adRequest.status)} me-3 px-3 py-2`">
                  {{ adRequest.status }}
                </span>
                <span class="text-muted">Last updated: {{ formatDate(adRequest.updated_at) }}</span>
              </div>
            </div>
          </div>
        </div>
        
        <!-- Response Form -->
        <div class="card border-0 shadow-sm mb-4">
          <div class="card-header bg-white border-0 py-3">
            <h5 class="card-title mb-0">Respond to Request</h5>
          </div>
          
          <div class="card-body">
            <!-- If request is already finalized -->
            <div v-if="adRequest.status === 'Accepted' || adRequest.status === 'Rejected'" class="alert alert-info">
              <i class="bi bi-info-circle me-2"></i>
              This request is already 
              <strong>{{ adRequest.status.toLowerCase() }}</strong>. 
              No further action is needed.
            </div>
            
            <!-- Response form -->
            <form v-else @submit.prevent="handleSubmit">
              <!-- Action Selection -->
              <div class="mb-4">
                <label class="form-label fw-bold">Choose an Action</label>
                <div class="action-options">
                  <div v-for="action in actions" :key="action.value" class="action-option mb-3">
                    <div class="form-check">
                      <input 
                        class="form-check-input" 
                        type="radio" 
                        :id="`action-${action.value}`" 
                        :value="action.value" 
                        v-model="form.action"
                        :disabled="disabledActions.includes(action.value)"
                      >
                      <label class="form-check-label" :for="`action-${action.value}`">
                        <span class="d-block fw-bold">{{ action.label }}</span>
                        <small class="text-muted">{{ action.description }}</small>
                      </label>
                    </div>
                  </div>
                </div>
                <div v-if="formErrors.action" class="text-danger small mt-1">{{ formErrors.action }}</div>
              </div>
              
              <!-- Counter Offer Input (only shown when negotiating) -->
              <div v-if="form.action === 'negotiate'" class="mb-4">
                <label for="counterOffer" class="form-label">Counter Offer Amount</label>
                <div class="input-group">
                  <span class="input-group-text">$</span>
                  <input 
                    type="number" 
                    id="counterOffer" 
                    class="form-control" 
                    v-model="form.counterOffer"
                    min="1"
                    placeholder="Enter your counter offer amount"
                  >
                </div>
                <div v-if="formErrors.counterOffer" class="text-danger small mt-1">{{ formErrors.counterOffer }}</div>
              </div>
              
              <!-- Message Input -->
              <div v-if="['negotiate', 'reject'].includes(form.action)" class="mb-4">
                <label for="message" class="form-label">Message to Sponsor</label>
                <textarea 
                  id="message" 
                  class="form-control" 
                  v-model="form.message"
                  rows="4"
                  :placeholder="form.action === 'negotiate' 
                    ? 'Explain your counter offer and any additional requirements...' 
                    : 'Provide a reason for declining this offer...'"
                ></textarea>
                <div v-if="formErrors.message" class="text-danger small mt-1">{{ formErrors.message }}</div>
              </div>
              
              <!-- Submit Button -->
              <div class="d-grid gap-2 d-md-flex justify-content-md-end">
                <button 
                  type="button" 
                  class="btn btn-outline-secondary me-md-2" 
                  @click="goBack"
                >
                  Cancel
                </button>
                <button 
                  type="submit" 
                  class="btn btn-primary" 
                  :disabled="submitLoading || !form.action"
                >
                  <span v-if="submitLoading" class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
                  <span v-if="form.action === 'accept'">Accept Offer</span>
                  <span v-else-if="form.action === 'negotiate'">Send Counter Offer</span>
                  <span v-else-if="form.action === 'reject'">Decline Offer</span>
                  <span v-else>Submit Response</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.ad-request-detail-view {
  animation: fadeIn 0.5s ease-in-out;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

.action-option {
  border: 1px solid #eee;
  border-radius: 8px;
  padding: 1rem;
  transition: all 0.2s ease;
}

.action-option:hover {
  border-color: #ccc;
  background-color: #f9f9f9;
}

.form-check-input:checked + .form-check-label + .action-option,
.form-check-input:checked ~ .action-option {
  border-color: var(--bs-primary);
  background-color: rgba(var(--bs-primary-rgb), 0.05);
}

.whitespace-pre-wrap {
  white-space: pre-wrap;
}
</style> 