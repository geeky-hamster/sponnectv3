<script setup>
import { ref, onMounted, watch, reactive } from 'vue'
import { sponsorService, negotiationService } from '../../services/api'
import { RouterLink } from 'vue-router'

// State
const loading = ref(true)
const adRequests = ref([])
const filteredRequests = ref([])
const error = ref('')
const successMessage = ref('')
const statusFilter = ref('all')
const searchQuery = ref('')

// Modal state
const showAdRequestModal = ref(false)
const selectedRequest = ref(null)
const negotiationHistory = ref([])
const loadingHistory = ref(false)
const submitting = ref(false)

// Negotiation form
const negotiationForm = reactive({
  action: '',
  payment_amount: '',
  message: ''
})

// Form validation
const formErrors = reactive({
  action: '',
  payment_amount: '',
  message: ''
})

// Status options
const statusOptions = [
  { value: 'all', label: 'All Statuses' },
  { value: 'Pending', label: 'Pending' },
  { value: 'Negotiating', label: 'Negotiating' },
  { value: 'Accepted', label: 'Accepted' },
  { value: 'Rejected', label: 'Rejected' }
]

// Action options
const actionOptions = [
  { value: 'accept', label: 'Accept Offer', description: 'Accept the current offer and proceed with the partnership' },
  { value: 'negotiate', label: 'Make Counter Offer', description: 'Propose a different amount or terms' },
  { value: 'reject', label: 'Decline Offer', description: 'Reject this offer and end negotiations' }
]

// Load ad requests
const loadAdRequests = async () => {
  loading.value = true
  error.value = ''
  
  try {
    const response = await sponsorService.getAdRequests()
    // Backend returns data in the format { ad_requests: [...] }
    adRequests.value = response.data?.ad_requests || []
    applyFilters()
  } catch (err) {
    console.error('Failed to load ad requests:', err)
    error.value = 'Failed to load ad requests. Please try again later.'
  } finally {
    loading.value = false
  }
}

// Filter ad requests
const applyFilters = () => {
  filteredRequests.value = adRequests.value.filter(request => {
    // Apply status filter
    const matchesStatus = statusFilter.value === 'all' || request.status === statusFilter.value
    
    // Apply search filter (check influencer name or campaign name)
    const matchesSearch = searchQuery.value === '' || 
      (request.influencer_name && request.influencer_name.toLowerCase().includes(searchQuery.value.toLowerCase())) ||
      (request.campaign_name && request.campaign_name.toLowerCase().includes(searchQuery.value.toLowerCase()))
    
    return matchesStatus && matchesSearch
  })
}

// Format date for display
const formatDate = (dateString) => {
  if (!dateString) return 'N/A'
  
  try {
    const date = new Date(dateString)
    if (isNaN(date.getTime())) return 'N/A'
    
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    })
  } catch (e) {
    console.error('Error formatting date:', e)
    return 'N/A'
  }
}

// Format currency
const formatCurrency = (amount) => {
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    minimumFractionDigits: 0
  }).format(amount || 0)
}

// Delete ad request
const deleteAdRequest = async (id) => {
  if (!confirm('Are you sure you want to delete this ad request?')) return
  
  try {
    await sponsorService.deleteAdRequest(id)
    // Remove from local state
    adRequests.value = adRequests.value.filter(r => r.id !== id)
    applyFilters()
    successMessage.value = 'Ad request deleted successfully'
  } catch (err) {
    console.error('Failed to delete ad request:', err)
    error.value = 'Failed to delete ad request. Please try again later.'
  }
}

// Open ad request modal
const openAdRequestModal = async (request) => {
  selectedRequest.value = request
  
  // Reset form and pre-fill payment amount
  negotiationForm.action = ''
  negotiationForm.payment_amount = request.payment_amount
  negotiationForm.message = ''
  
  // Reset form errors
  formErrors.action = ''
  formErrors.payment_amount = ''
  formErrors.message = ''
  
  showAdRequestModal.value = true
  
  // Load negotiation history
  await loadNegotiationHistory(request.id)
}

// Close ad request modal
const closeAdRequestModal = () => {
  showAdRequestModal.value = false
  selectedRequest.value = null
  negotiationHistory.value = []
}

// Load negotiation history
const loadNegotiationHistory = async (requestId) => {
  loadingHistory.value = true
  
  try {
    const response = await negotiationService.getHistory(requestId)
    negotiationHistory.value = response.data.history || []
  } catch (err) {
    console.error('Failed to load negotiation history:', err)
  } finally {
    loadingHistory.value = false
  }
}

// Validate form
const validateForm = () => {
  let isValid = true
  
  // Reset errors
  formErrors.action = ''
  formErrors.payment_amount = ''
  formErrors.message = ''
  
  // Validate action
  if (!negotiationForm.action) {
    formErrors.action = 'Please select an action'
    isValid = false
  }
  
  // Validate counter offer if negotiating
  if (negotiationForm.action === 'negotiate') {
    if (!negotiationForm.payment_amount) {
      formErrors.payment_amount = 'Please enter your counter offer amount'
      isValid = false
    } else if (negotiationForm.payment_amount <= 0) {
      formErrors.payment_amount = 'Amount must be greater than zero'
      isValid = false
    }
  }
  
  // Validate message for negotiate or reject
  if (['negotiate', 'reject'].includes(negotiationForm.action) && !negotiationForm.message.trim()) {
    formErrors.message = `Please provide a message explaining your ${negotiationForm.action === 'negotiate' ? 'counter offer' : 'rejection'}`
    isValid = false
  }
  
  return isValid
}

// Submit negotiation
const submitNegotiation = async () => {
  if (!validateForm()) return
  
  try {
    submitting.value = true
    error.value = ''
    successMessage.value = ''
    
    // Build the payload based on the action
    const payload = {
      action: negotiationForm.action,
      message: negotiationForm.message || undefined
    }
    
    if (negotiationForm.action === 'negotiate') {
      payload.payment_amount = parseFloat(negotiationForm.payment_amount)
    }
    
    await sponsorService.negotiateAdRequest(selectedRequest.value.id, payload)
    
    // Update success message
    successMessage.value = negotiationForm.action === 'accept' 
      ? 'Offer accepted successfully!' 
      : negotiationForm.action === 'reject'
        ? 'Offer rejected successfully.' 
        : 'Counter offer sent successfully.'
    
    // Close modal
    closeAdRequestModal()
    
    // Reload requests
    await loadAdRequests()
    
  } catch (err) {
    console.error('Failed to submit negotiation:', err)
    error.value = 'Failed to submit your response. Please try again later.'
  } finally {
    submitting.value = false
  }
}

// Check if sponsor can respond
const canRespond = (request) => {
  return (request.status === 'Pending') || 
         (request.status === 'Negotiating' && request.last_offer_by === 'influencer')
}

// Watch for filter changes
watch([statusFilter, searchQuery], () => {
  applyFilters()
})

// Load data on component mount
onMounted(() => {
  loadAdRequests()
})
</script>

<template>
  <div class="ad-requests-view py-5">
    <div class="container">
      <!-- Header with breadcrumb -->
      <div class="d-flex justify-content-between align-items-center mb-4">
        <h1>Ad Requests</h1>
        <nav aria-label="breadcrumb">
          <ol class="breadcrumb mb-0">
            <li class="breadcrumb-item">
              <RouterLink to="/sponsor/dashboard">Dashboard</RouterLink>
            </li>
            <li class="breadcrumb-item active">Ad Requests</li>
          </ol>
        </nav>
      </div>
      
      <!-- Error alert -->
      <div v-if="error" class="alert alert-danger alert-dismissible fade show" role="alert">
        {{ error }}
        <button type="button" class="btn-close" @click="error = ''"></button>
      </div>
      
      <!-- Success alert -->
      <div v-if="successMessage" class="alert alert-success alert-dismissible fade show" role="alert">
        {{ successMessage }}
        <button type="button" class="btn-close" @click="successMessage = ''"></button>
      </div>
      
      <!-- Filters -->
      <div class="card border-0 shadow-sm mb-4">
        <div class="card-body">
          <div class="row g-3">
            <div class="col-md-6">
              <div class="input-group">
                <span class="input-group-text bg-light border-end-0">
                  <i class="bi bi-search"></i>
                </span>
                <input 
                  type="text" 
                  v-model="searchQuery" 
                  class="form-control border-start-0" 
                  placeholder="Search by influencer or campaign..."
                />
              </div>
            </div>
            <div class="col-md-6">
              <select v-model="statusFilter" class="form-select">
                <option v-for="option in statusOptions" :key="option.value" :value="option.value">
                  {{ option.label }}
                </option>
              </select>
            </div>
          </div>
        </div>
      </div>
      
      <!-- Loading state -->
      <div v-if="loading" class="text-center py-5">
        <div class="spinner-border text-primary" role="status">
          <span class="visually-hidden">Loading...</span>
        </div>
        <p class="mt-3">Loading ad requests...</p>
      </div>
      
      <!-- Empty state -->
      <div v-else-if="filteredRequests.length === 0" class="text-center py-5">
        <div class="mb-4">
          <i class="bi bi-inbox display-1 text-muted"></i>
        </div>
        <h3 class="mb-3">No ad requests found</h3>
        <p class="text-muted mb-4">
          {{ adRequests.length === 0 
            ? "You haven't created any ad requests yet." 
            : "No ad requests match your current filters." }}
        </p>
        <div v-if="adRequests.length === 0">
          <RouterLink to="/search/influencers" class="btn btn-primary">
            Find Influencers
          </RouterLink>
        </div>
        <div v-else>
          <button class="btn btn-outline-secondary" @click="searchQuery = ''; statusFilter = 'all'">
            Clear Filters
          </button>
        </div>
      </div>
      
      <!-- Ad requests list -->
      <div v-else>
        <div class="card border-0 shadow-sm">
          <div class="card-body p-0">
            <div class="table-responsive">
              <table class="table table-hover align-middle mb-0">
                <thead class="table-light">
                  <tr>
                    <th>Campaign</th>
                    <th>Influencer</th>
                    <th>Offer Amount</th>
                    <th>Status</th>
                    <th>Last Updated</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="request in filteredRequests" :key="request.id">
                    <td>{{ request.campaign_name }}</td>
                    <td>{{ request.influencer_name }}</td>
                    <td>{{ formatCurrency(request.payment_amount) }}</td>
                    <td>
                      <span class="badge rounded-pill" :class="{
                        'bg-warning': request.status === 'Pending',
                        'bg-info': request.status === 'Negotiating',
                        'bg-success': request.status === 'Accepted',
                        'bg-danger': request.status === 'Rejected'
                      }">{{ request.status }}</span>
                    </td>
                    <td>{{ formatDate(request.updated_at) }}</td>
                    <td>
                      <router-link :to="`/sponsor/ad-requests/${request.id}`" class="btn btn-sm btn-outline-primary me-1">
                        View
                      </router-link>
                      <button 
                        v-if="request.status === 'Pending' || request.status === 'Rejected'"
                        @click="deleteAdRequest(request.id)" 
                        class="btn btn-sm btn-outline-danger"
                      >
                        <i class="bi bi-trash"></i>
                      </button>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
        
        <!-- Status summary cards -->
        <div class="row row-cols-2 row-cols-md-4 g-4 mt-4">
          <div class="col">
            <div class="card border-0 shadow-sm h-100">
              <div class="card-body">
                <h6 class="text-muted mb-2">Pending</h6>
                <h3 class="text-warning mb-0">
                  {{ adRequests.filter(r => r.status === 'Pending').length }}
                </h3>
              </div>
            </div>
          </div>
          
          <div class="col">
            <div class="card border-0 shadow-sm h-100">
              <div class="card-body">
                <h6 class="text-muted mb-2">Negotiating</h6>
                <h3 class="text-info mb-0">
                  {{ adRequests.filter(r => r.status === 'Negotiating').length }}
                </h3>
              </div>
            </div>
          </div>
          
          <div class="col">
            <div class="card border-0 shadow-sm h-100">
              <div class="card-body">
                <h6 class="text-muted mb-2">Accepted</h6>
                <h3 class="text-success mb-0">
                  {{ adRequests.filter(r => r.status === 'Accepted').length }}
                </h3>
              </div>
            </div>
          </div>
          
          <div class="col">
            <div class="card border-0 shadow-sm h-100">
              <div class="card-body">
                <h6 class="text-muted mb-2">Rejected</h6>
                <h3 class="text-danger mb-0">
                  {{ adRequests.filter(r => r.status === 'Rejected').length }}
                </h3>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <!-- Ad Request Modal -->
      <div v-if="showAdRequestModal && selectedRequest" class="modal-overlay" @click.self="closeAdRequestModal">
        <div class="modal show d-block" tabindex="-1" role="dialog">
          <div class="modal-dialog modal-dialog-centered modal-lg" role="document">
            <div class="modal-content">
              <div class="modal-header">
                <h5 class="modal-title">Ad Request from {{ selectedRequest.influencer_name }}</h5>
                <button type="button" class="btn-close" @click="closeAdRequestModal" aria-label="Close"></button>
              </div>
              
              <div class="modal-body">
                <!-- Request Details -->
                <div class="card mb-4">
                  <div class="card-header bg-light">
                    <h6 class="mb-0">Request Details</h6>
                  </div>
                  <div class="card-body">
                    <div class="row g-3">
                      <div class="col-md-6">
                        <label class="text-muted d-block mb-1">Campaign</label>
                        <div class="fw-bold">{{ selectedRequest.campaign_name }}</div>
                      </div>
                      <div class="col-md-6">
                        <label class="text-muted d-block mb-1">Current Offer</label>
                        <div class="fs-5 fw-bold text-primary">{{ formatCurrency(selectedRequest.payment_amount) }}</div>
                      </div>
                      <div class="col-md-6">
                        <label class="text-muted d-block mb-1">Status</label>
                        <span 
                          :class="{
                            'badge rounded-pill bg-warning': selectedRequest.status === 'Pending',
                            'badge rounded-pill bg-info': selectedRequest.status === 'Negotiating',
                            'badge rounded-pill bg-success': selectedRequest.status === 'Accepted',
                            'badge rounded-pill bg-danger': selectedRequest.status === 'Rejected'
                          }"
                        >
                          {{ selectedRequest.status }}
                        </span>
                      </div>
                      <div class="col-md-6">
                        <label class="text-muted d-block mb-1">Last Action By</label>
                        <div>{{ selectedRequest.last_offer_by }}</div>
                      </div>
                      <div class="col-12">
                        <label class="text-muted d-block mb-1">Message</label>
                        <div class="p-3 bg-light rounded">
                          <p class="mb-0 whitespace-pre-wrap">{{ selectedRequest.message || 'No message provided.' }}</p>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
                
                <!-- Action Required Alert - When sponsor needs to respond -->
                <div v-if="canRespond(selectedRequest)" class="alert alert-info mb-4">
                  <div class="d-flex justify-content-between mb-2">
                    <h6 class="alert-heading fw-bold mb-0">Respond to Offer</h6>
                    <span class="badge bg-warning">Action Required</span>
                  </div>
                  
                  <p>The influencer has offered <strong>{{ formatCurrency(selectedRequest.payment_amount) }}</strong> for this collaboration.</p>
                  <p v-if="selectedRequest.message" class="mt-2">
                    <strong>Message:</strong> {{ selectedRequest.message }}
                  </p>
                  
                  <hr>
                  
                  <form @submit.prevent="submitNegotiation">
                    <div class="mb-3">
                      <label class="form-label"><strong>How would you like to respond?</strong></label>
                      <div class="response-options mb-3">
                        <div class="mb-3 btn-group w-100">
                          <button 
                            type="button"
                            @click="negotiationForm.action = 'accept'" 
                            :class="['btn', negotiationForm.action === 'accept' ? 'btn-success' : 'btn-outline-success']"
                          >
                            <i class="bi bi-check-circle me-1"></i> Accept Offer
                          </button>
                          <button 
                            type="button"
                            @click="negotiationForm.action = 'negotiate'" 
                            :class="['btn', negotiationForm.action === 'negotiate' ? 'btn-primary' : 'btn-outline-primary']"
                          >
                            <i class="bi bi-arrow-left-right me-1"></i> Counter Offer
                          </button>
                          <button 
                            type="button"
                            @click="negotiationForm.action = 'reject'" 
                            :class="['btn', negotiationForm.action === 'reject' ? 'btn-danger' : 'btn-outline-danger']"
                          >
                            <i class="bi bi-x-circle me-1"></i> Reject
                          </button>
                        </div>
                        <div v-if="formErrors.action" class="text-danger small mt-1 mb-3">{{ formErrors.action }}</div>
                      </div>
                      
                      <div v-if="negotiationForm.action === 'negotiate'" class="form-group mb-3 shadow-sm p-3 border rounded bg-light">
                        <label for="payment_amount" class="form-label">Your Counter Offer (₹)</label>
                        <div class="input-group">
                          <span class="input-group-text">₹</span>
                          <input
                            id="payment_amount"
                            type="number"
                            v-model="negotiationForm.payment_amount"
                            class="form-control"
                            placeholder="Enter amount"
                            min="1"
                          />
                        </div>
                        <div v-if="formErrors.payment_amount" class="text-danger small mt-1">{{ formErrors.payment_amount }}</div>
                        <small class="form-text text-muted">Current offer: {{ formatCurrency(selectedRequest.payment_amount) }}</small>
                      </div>
                      
                      <div v-if="negotiationForm.action !== 'accept'" class="form-group mb-3">
                        <label class="form-label">{{ negotiationForm.action === 'negotiate' ? 'Explanation' : 'Reason for Rejection' }} {{ negotiationForm.action === 'reject' ? '(Required)' : '' }}</label>
                        <textarea
                          v-model="negotiationForm.message"
                          class="form-control"
                          rows="3"
                          :placeholder="negotiationForm.action === 'negotiate' ? 'Explain your counter offer' : 'Explain why you are rejecting'"
                        ></textarea>
                        <div v-if="formErrors.message" class="text-danger small mt-1">{{ formErrors.message }}</div>
                      </div>
                      
                      <div class="d-flex justify-content-end">
                        <button 
                          type="submit" 
                          class="btn btn-primary"
                          :disabled="submitting"
                        >
                          <span v-if="submitting">
                            <i class="bi bi-hourglass-split me-2"></i> Sending...
                          </span>
                          <span v-else>
                            <i class="bi bi-send me-1"></i> Send Response
                          </span>
                        </button>
                      </div>
                    </div>
                  </form>
                </div>
                
                <!-- Current Status Alert when no action needed -->
                <div v-else class="alert mb-4" :class="{
                  'alert-success': selectedRequest.status === 'Accepted',
                  'alert-danger': selectedRequest.status === 'Rejected',
                  'alert-warning': selectedRequest.status === 'Negotiating' && selectedRequest.last_offer_by === 'sponsor',
                  'alert-info': selectedRequest.status === 'Pending'
                }">
                  <div class="d-flex justify-content-between">
                    <h6 class="alert-heading fw-bold mb-1">Status: {{ selectedRequest.status }}</h6>
                    <span v-if="selectedRequest.status === 'Negotiating' && selectedRequest.last_offer_by === 'sponsor'" class="badge bg-warning">Waiting for influencer</span>
                  </div>
                  <p class="mb-0" v-if="selectedRequest.status === 'Accepted'">
                    <i class="bi bi-check-circle me-1"></i> You have accepted the offer of <strong>{{ formatCurrency(selectedRequest.payment_amount) }}</strong>. The collaboration is now active.
                  </p>
                  <p class="mb-0" v-else-if="selectedRequest.status === 'Rejected'">
                    <i class="bi bi-x-circle me-1"></i> This offer has been rejected and the negotiation is closed.
                  </p>
                  <p class="mb-0" v-else-if="selectedRequest.status === 'Negotiating' && selectedRequest.last_offer_by === 'sponsor'">
                    <i class="bi bi-hourglass me-1"></i> You made an offer of <strong>{{ formatCurrency(selectedRequest.payment_amount) }}</strong>. Waiting for the influencer to respond.
                  </p>
                  <p class="mb-0" v-else-if="selectedRequest.status === 'Pending'">
                    <i class="bi bi-clock me-1"></i> This request is pending initial response from the influencer.
                  </p>
                </div>
                
                <!-- Negotiation History -->
                <div class="card">
                  <div class="card-header bg-light">
                    <h6 class="mb-0">Negotiation History</h6>
                  </div>
                  <div class="card-body">
                    <!-- Loading state -->
                    <div v-if="loadingHistory" class="text-center py-3">
                      <div class="spinner-border spinner-border-sm text-primary me-2" role="status"></div>
                      <span>Loading history...</span>
                    </div>
                    
                    <!-- Empty state -->
                    <div v-else-if="negotiationHistory.length === 0" class="text-center py-3">
                      <p class="text-muted mb-0">No negotiation history available.</p>
                    </div>
                    
                    <!-- Negotiation history timeline -->
                    <div v-else class="timeline mt-3">
                      <div v-for="(item, index) in negotiationHistory" :key="index" class="timeline-item mb-4">
                        <div class="d-flex">
                          <div :class="[
                            'timeline-badge me-3',
                            item.user_role === 'sponsor' ? 'bg-primary' : 'bg-success'
                          ]">
                            <i :class="[
                              'bi',
                              item.action === 'propose' ? 'bi-chat-left-text' :
                              item.action === 'negotiate' ? 'bi-arrow-left-right' :
                              item.action === 'accept' ? 'bi-check-lg' : 'bi-x-lg'
                            ]"></i>
                          </div>
                          <div class="timeline-content border p-3 rounded flex-grow-1">
                            <div class="d-flex justify-content-between mb-2">
                              <h6 class="mb-0">
                                {{ item.user_role === 'sponsor' ? 'You' : 'Influencer' }}
                                {{ item.action === 'propose' ? 'proposed' :
                                   item.action === 'negotiate' ? 'counter-offered' :
                                   item.action === 'accept' ? 'accepted' : 'rejected' }}
                              </h6>
                              <small class="text-muted">{{ formatDate(item.created_at) }}</small>
                            </div>
                            <div class="mb-2 fw-bold">
                              Amount: {{ formatCurrency(item.payment_amount) }}
                            </div>
                            <div v-if="item.message" class="text-muted">
                              "{{ item.message }}"
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
              
              <div class="modal-footer">
                <button type="button" class="btn btn-outline-secondary" @click="closeAdRequestModal">
                  Close
                </button>
                <RouterLink :to="`/sponsor/ad-requests/${selectedRequest.id}`" class="btn btn-primary">
                  View Full Details
                </RouterLink>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.ad-requests-view {
  animation: fadeIn 0.5s ease-in-out;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

/* Modal styles */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  z-index: 1040;
  display: flex;
  align-items: center;
  justify-content: center;
}

.modal-content {
  box-shadow: 0 5px 15px rgba(0, 0, 0, 0.5);
  border: none;
  border-radius: 8px;
  animation: modalFadeIn 0.3s ease-out;
}

@keyframes modalFadeIn {
  from {
    opacity: 0;
    transform: translateY(-20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* Timeline styling */
.timeline {
  position: relative;
}

.timeline-badge {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
}

.timeline-content {
  background-color: #fff;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.whitespace-pre-wrap {
  white-space: pre-wrap;
}
</style> 