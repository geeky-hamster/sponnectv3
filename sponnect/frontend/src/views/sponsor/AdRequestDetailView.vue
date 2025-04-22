<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter, RouterLink } from 'vue-router'
import { sponsorService, negotiationService } from '../../services/api'

const route = useRoute()
const router = useRouter()
const adRequestId = computed(() => route.params.id)

// State
const loading = ref(true)
const submitting = ref(false)
const adRequest = ref(null)
const negotiationHistory = ref([])
const error = ref('')
const success = ref('')

// Negotiation form
const negotiationForm = ref({
  action: '',
  payment_amount: '',
  message: ''
})

// Load ad request data
const loadAdRequest = async () => {
  loading.value = true
  error.value = ''
  
  try {
    // Get ad request details and negotiation history in parallel
    const [adRequestResponse, historyResponse] = await Promise.all([
      sponsorService.getAdRequest(adRequestId.value),
      negotiationService.getHistory(adRequestId.value)
    ])
    
    adRequest.value = adRequestResponse.data
    negotiationHistory.value = historyResponse.data.history || []
    
    // Pre-fill negotiation form with current payment amount
    if (adRequest.value) {
      negotiationForm.value.payment_amount = adRequest.value.payment_amount
    }
  } catch (err) {
    console.error('Failed to load ad request details:', err)
    error.value = 'Failed to load ad request details. Please try again later.'
  } finally {
    loading.value = false
  }
}

// Format date
const formatDate = (dateString) => {
  if (!dateString) return 'N/A'
  return new Date(dateString).toLocaleDateString('en-US', {
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

// Can sponsor respond to negotiation
const canRespond = computed(() => {
  if (!adRequest.value) return false
  
  return adRequest.value.status === 'Negotiating' && 
         adRequest.value.last_offer_by === 'influencer'
})

// Can delete request
const canDelete = computed(() => {
  if (!adRequest.value) return false
  
  return adRequest.value.status === 'Pending' || 
         adRequest.value.status === 'Rejected'
})

// Handle negotiation response
const handleNegotiation = async () => {
  if (!negotiationForm.value.action) {
    error.value = 'Please select an action'
    return
  }
  
  if (negotiationForm.value.action === 'negotiate' && !negotiationForm.value.payment_amount) {
    error.value = 'Please enter a payment amount'
    return
  }
  
  submitting.value = true
  error.value = ''
  success.value = ''
  
  try {
    const payload = {
      action: negotiationForm.value.action,
      message: negotiationForm.value.message || undefined
    }
    
    if (negotiationForm.value.action === 'negotiate') {
      payload.payment_amount = parseFloat(negotiationForm.value.payment_amount)
    }
    
    await sponsorService.negotiateAdRequest(adRequestId.value, payload)
    
    success.value = 'Response submitted successfully'
    
    // Reset form and reload data
    negotiationForm.value = {
      action: '',
      payment_amount: '',
      message: ''
    }
    
    loadAdRequest()
  } catch (err) {
    console.error('Failed to submit response:', err)
    error.value = 'Failed to submit response. Please try again.'
  } finally {
    submitting.value = false
  }
}

// Delete ad request
const deleteAdRequest = async () => {
  if (!confirm('Are you sure you want to delete this ad request?')) return
  
  submitting.value = true
  error.value = ''
  
  try {
    await sponsorService.deleteAdRequest(adRequestId.value)
    router.push('/sponsor/ad-requests')
  } catch (err) {
    console.error('Failed to delete ad request:', err)
    error.value = 'Failed to delete ad request. Please try again.'
    submitting.value = false
  }
}

// Load data on component mount
onMounted(() => {
  loadAdRequest()
})
</script>

<template>
  <div class="ad-request-detail-view py-5">
    <div class="container">
      <!-- Breadcrumb -->
      <nav aria-label="breadcrumb" class="mb-4">
        <ol class="breadcrumb">
          <li class="breadcrumb-item">
            <RouterLink to="/sponsor/dashboard">Dashboard</RouterLink>
          </li>
          <li class="breadcrumb-item">
            <RouterLink to="/sponsor/ad-requests">Ad Requests</RouterLink>
          </li>
          <li class="breadcrumb-item active">Ad Request Details</li>
        </ol>
      </nav>
      
      <!-- Loading state -->
      <div v-if="loading" class="text-center py-5">
        <div class="spinner-border text-primary" role="status">
          <span class="visually-hidden">Loading...</span>
        </div>
        <p class="mt-3">Loading ad request details...</p>
      </div>
      
      <!-- Error state -->
      <div v-else-if="error" class="alert alert-danger alert-dismissible fade show" role="alert">
        {{ error }}
        <button type="button" class="btn-close" @click="error = ''"></button>
      </div>
      
      <!-- Success message -->
      <div v-if="success" class="alert alert-success alert-dismissible fade show" role="alert">
        {{ success }}
        <button type="button" class="btn-close" @click="success = ''"></button>
      </div>
      
      <!-- Ad request details -->
      <div v-if="adRequest" class="mb-5">
        <div class="d-flex justify-content-between align-items-start mb-4">
          <div>
            <h1 class="mb-2">Ad Request for {{ adRequest.campaign_name }}</h1>
            <div class="d-flex align-items-center">
              <span 
                :class="{
                  'badge rounded-pill bg-warning me-2': adRequest.status === 'Pending',
                  'badge rounded-pill bg-info me-2': adRequest.status === 'Negotiating',
                  'badge rounded-pill bg-success me-2': adRequest.status === 'Accepted',
                  'badge rounded-pill bg-danger me-2': adRequest.status === 'Rejected'
                }"
              >
                {{ adRequest.status }}
              </span>
              <span class="text-muted">Last updated on {{ formatDate(adRequest.updated_at) }}</span>
            </div>
          </div>
          <div v-if="canDelete">
            <button @click="deleteAdRequest" class="btn btn-outline-danger" :disabled="submitting">
              <i class="bi bi-trash me-1"></i>Delete
            </button>
          </div>
        </div>
        
        <div class="row">
          <div class="col-lg-8">
            <!-- Request Details -->
            <div class="card border-0 shadow-sm mb-4">
              <div class="card-body">
                <h4 class="card-title mb-4">Request Details</h4>
                
                <div class="row mb-4">
                  <div class="col-md-6">
                    <h6 class="text-muted mb-1">Influencer</h6>
                    <p class="mb-0">{{ adRequest.influencer_name }}</p>
                  </div>
                  <div class="col-md-6">
                    <h6 class="text-muted mb-1">Campaign</h6>
                    <p class="mb-0">
                      <RouterLink :to="`/sponsor/campaigns/${adRequest.campaign_id}`">
                        {{ adRequest.campaign_name }}
                      </RouterLink>
                    </p>
                  </div>
                </div>
                
                <div class="row mb-4">
                  <div class="col-md-6">
                    <h6 class="text-muted mb-1">Payment Amount</h6>
                    <p class="mb-0 fs-5 fw-bold text-success">{{ formatCurrency(adRequest.payment_amount) }}</p>
                  </div>
                  <div class="col-md-6">
                    <h6 class="text-muted mb-1">Last Action By</h6>
                    <p class="mb-0">{{ adRequest.last_offer_by }}</p>
                  </div>
                </div>
                
                <div class="mb-4">
                  <h6 class="text-muted mb-1">Requirements</h6>
                  <p class="mb-0">{{ adRequest.requirements || 'No specific requirements provided.' }}</p>
                </div>
                
                <div>
                  <h6 class="text-muted mb-1">Message</h6>
                  <p class="mb-0">{{ adRequest.message || 'No message provided.' }}</p>
                </div>
              </div>
            </div>
            
            <!-- Negotiation History -->
            <div class="card border-0 shadow-sm mb-4">
              <div class="card-body">
                <h4 class="card-title mb-4">Negotiation History</h4>
                
                <div v-if="negotiationHistory.length === 0" class="text-center py-3">
                  <p class="text-muted mb-0">No negotiation history available.</p>
                </div>
                
                <div v-else class="timeline">
                  <div v-for="(item, index) in negotiationHistory" :key="item.id" class="timeline-item">
                    <div :class="[
                      'timeline-badge',
                      item.user_role === 'sponsor' ? 'bg-primary' : 'bg-success'
                    ]">
                      <i :class="[
                        'bi',
                        item.action === 'propose' ? 'bi-chat-left-text' :
                        item.action === 'negotiate' ? 'bi-arrow-left-right' :
                        item.action === 'accept' ? 'bi-check-lg' : 'bi-x-lg'
                      ]"></i>
                    </div>
                    <div class="timeline-panel">
                      <div class="timeline-heading">
                        <div class="d-flex justify-content-between">
                          <h5 class="mb-1">
                            {{ item.user_role === 'sponsor' ? 'You' : item.username }}
                            {{ item.action === 'propose' ? 'proposed' :
                               item.action === 'negotiate' ? 'counter-offered' :
                               item.action === 'accept' ? 'accepted' : 'rejected' }}
                          </h5>
                          <small class="text-muted">{{ formatDate(item.created_at) }}</small>
                        </div>
                      </div>
                      <div class="timeline-body mt-2">
                        <div v-if="item.payment_amount" class="mb-2">
                          <strong>Payment Amount:</strong> {{ formatCurrency(item.payment_amount) }}
                        </div>
                        <div v-if="item.message" class="mb-2">
                          <strong>Message:</strong> {{ item.message }}
                        </div>
                        <div v-if="item.requirements">
                          <strong>Requirements:</strong> {{ item.requirements }}
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            
            <!-- Response Form (Only shown if it's sponsor's turn) -->
            <div v-if="canRespond" class="card border-0 shadow-sm">
              <div class="card-body">
                <h4 class="card-title mb-4">Your Response</h4>
                
                <form @submit.prevent="handleNegotiation">
                  <div class="mb-3">
                    <label class="form-label">Action</label>
                    <div class="d-flex gap-3">
                      <div class="form-check">
                        <input
                          class="form-check-input"
                          type="radio"
                          id="actionAccept"
                          value="accept"
                          v-model="negotiationForm.action"
                        >
                        <label class="form-check-label" for="actionAccept">
                          Accept
                        </label>
                      </div>
                      <div class="form-check">
                        <input
                          class="form-check-input"
                          type="radio"
                          id="actionNegotiate"
                          value="negotiate"
                          v-model="negotiationForm.action"
                        >
                        <label class="form-check-label" for="actionNegotiate">
                          Counter-offer
                        </label>
                      </div>
                      <div class="form-check">
                        <input
                          class="form-check-input"
                          type="radio"
                          id="actionReject"
                          value="reject"
                          v-model="negotiationForm.action"
                        >
                        <label class="form-check-label" for="actionReject">
                          Reject
                        </label>
                      </div>
                    </div>
                  </div>
                  
                  <div v-if="negotiationForm.action === 'negotiate'" class="mb-3">
                    <label for="paymentAmount" class="form-label">Your Counter-offer Amount ($)</label>
                    <input
                      type="number"
                      class="form-control"
                      id="paymentAmount"
                      v-model="negotiationForm.payment_amount"
                      placeholder="Enter amount in USD"
                      min="1"
                      step="1"
                    >
                  </div>
                  
                  <div class="mb-3">
                    <label for="message" class="form-label">Message (Optional)</label>
                    <textarea
                      class="form-control"
                      id="message"
                      v-model="negotiationForm.message"
                      rows="3"
                      placeholder="Add a message to the influencer"
                    ></textarea>
                  </div>
                  
                  <div class="d-flex justify-content-end">
                    <button
                      type="submit"
                      class="btn btn-primary"
                      :disabled="submitting || !negotiationForm.action"
                    >
                      <span v-if="submitting" class="spinner-border spinner-border-sm me-1" role="status" aria-hidden="true"></span>
                      Send Response
                    </button>
                  </div>
                </form>
              </div>
            </div>
          </div>
          
          <div class="col-lg-4">
            <!-- Status Card -->
            <div class="card border-0 shadow-sm mb-4">
              <div class="card-body">
                <h5 class="card-title mb-4">Status</h5>
                
                <div class="mb-3 pb-3 border-bottom">
                  <h6 class="text-muted mb-1">Current Status</h6>
                  <div 
                    :class="{
                      'text-warning': adRequest.status === 'Pending',
                      'text-info': adRequest.status === 'Negotiating',
                      'text-success': adRequest.status === 'Accepted',
                      'text-danger': adRequest.status === 'Rejected'
                    }"
                    class="fw-bold"
                  >
                    {{ adRequest.status }}
                  </div>
                </div>
                
                <div class="mb-3 pb-3 border-bottom">
                  <h6 class="text-muted mb-1">Initiated By</h6>
                  <div>{{ adRequest.initiator_id === adRequest.influencer_id ? 'Influencer' : 'You' }}</div>
                </div>
                
                <div v-if="adRequest.status === 'Negotiating'" class="mb-3 pb-3 border-bottom">
                  <h6 class="text-muted mb-1">Next Action</h6>
                  <div class="fw-bold">
                    {{ adRequest.last_offer_by === 'influencer' ? 'Your Turn' : 'Waiting for Influencer' }}
                  </div>
                </div>
                
                <div>
                  <h6 class="text-muted mb-1">Created On</h6>
                  <div>{{ formatDate(adRequest.created_at) }}</div>
                </div>
              </div>
            </div>
            
            <!-- Actions Card -->
            <div class="card border-0 shadow-sm">
              <div class="card-body">
                <h5 class="card-title mb-4">Actions</h5>
                
                <div class="d-grid gap-2">
                  <RouterLink 
                    :to="`/sponsor/campaigns/${adRequest.campaign_id}`" 
                    class="btn btn-outline-primary"
                  >
                    <i class="bi bi-arrow-left me-1"></i>Back to Campaign
                  </RouterLink>
                  
                  <RouterLink 
                    to="/sponsor/ad-requests" 
                    class="btn btn-outline-secondary"
                  >
                    View All Requests
                  </RouterLink>
                </div>
              </div>
            </div>
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

/* Timeline styling */
.timeline {
  position: relative;
  padding: 20px 0;
}

.timeline:before {
  content: '';
  position: absolute;
  top: 0;
  bottom: 0;
  left: 20px;
  width: 3px;
  background: #e9ecef;
}

.timeline-item {
  position: relative;
  margin-bottom: 30px;
}

.timeline-item:last-child {
  margin-bottom: 0;
}

.timeline-badge {
  position: absolute;
  left: 0;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  text-align: center;
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1;
}

.timeline-badge i {
  font-size: 1.2rem;
}

.timeline-panel {
  position: relative;
  margin-left: 60px;
  background: #f8f9fa;
  border-radius: 0.25rem;
  padding: 15px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

.timeline-panel:before {
  content: '';
  position: absolute;
  top: 10px;
  left: -10px;
  width: 0;
  height: 0;
  border-top: 10px solid transparent;
  border-bottom: 10px solid transparent;
  border-right: 10px solid #f8f9fa;
}
</style> 