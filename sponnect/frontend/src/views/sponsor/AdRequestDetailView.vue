<script setup>
import { ref, onMounted, computed, reactive } from 'vue'
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

// Active tab state
const activeTab = ref('details')

// Progress updates state
const progressUpdates = ref([])
const loadingProgress = ref(false)
const submittingReview = ref(false)
const reviewForm = reactive({
  status: 'Approved',
  feedback: ''
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
    const errorMsg = err.response?.data?.message || 'Failed to load ad request details. Please try again later.'
    error.value = errorMsg
    adRequest.value = null // Reset adRequest to prevent null reference errors
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
  
  // Show action buttons when it's the sponsor's turn to respond
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
  loadAdRequest().then(() => {
    if (adRequest.value) {
      // Initialize payment amount for counter-offers
      newMessage.payment_amount = adRequest.value.payment_amount
    }
  })
})

// Map actions to display text
const mapActionToDisplay = (action) => {
  switch (action) {
    case 'accept': return 'Accepted Offer';
    case 'reject': return 'Rejected Offer';
    case 'negotiate': return 'Made Counter-offer';
    case 'propose': return 'Initial Proposal';
    default: return action;
  }
}

// New message state
const newMessage = reactive({
  action: 'negotiate',
  message: '',
  payment_amount: null
})

const sendingMessage = ref(false)

// Send message function
const sendMessage = async () => {
  if (!validateMessage()) return
  
  try {
    sendingMessage.value = true
    
    const payload = {
      action: newMessage.action,
      message: newMessage.message,
      payment_amount: newMessage.action === 'negotiate' ? newMessage.payment_amount : adRequest.value.payment_amount
    }
    
    await sponsorService.negotiateAdRequest(adRequest.value.id, payload)
    
    // Reset form
    newMessage.message = ''
    if (newMessage.action === 'accept' || newMessage.action === 'reject') {
      // Reload ad request to get updated status
      await loadAdRequest()
    } else {
      // Just reload to get new messages
      await loadAdRequest()
    }
    
  } catch (err) {
    console.error('Failed to send message:', err)
    error.value = 'Failed to send your message. Please try again.'
  } finally {
    sendingMessage.value = false
  }
}

// Validate message
const validateMessage = () => {
  if (newMessage.action === 'negotiate' && (!newMessage.payment_amount || newMessage.payment_amount <= 0)) {
    error.value = 'Please enter a valid payment amount'
    return false
  }
  
  if ((newMessage.action === 'negotiate' || newMessage.action === 'reject') && !newMessage.message.trim()) {
    error.value = `Please provide a message explaining your ${newMessage.action === 'negotiate' ? 'counter offer' : 'rejection'}`
    return false
  }
  
  return true
}

// Computed property for pending updates count
const pendingUpdatesCount = computed(() => {
  return progressUpdates.value.filter(update => update.status === 'Pending').length
})

// Format metrics for display
const formatMetrics = (metricsString) => {
  try {
    const metrics = JSON.parse(metricsString)
    return Object.entries(metrics)
      .map(([key, value]) => `${key.charAt(0).toUpperCase() + key.slice(1)}: ${value}`)
      .join('\n')
  } catch (e) {
    return metricsString
  }
}

// Review an update
const reviewUpdate = async (updateId, status, feedback) => {
  try {
    submittingReview.value = true
    
    const payload = {
      status: status,
      feedback: status === 'Revision Requested' ? feedback : ''
    }
    
    await sponsorService.reviewProgressUpdate(adRequest.value.id, updateId, payload)
    
    // Reset the form
    reviewForm.status = 'Approved'
    reviewForm.feedback = ''
    
    // Reload updates
    await loadProgressUpdates()
    
    // Show success message
    success.value = `Progress update ${status === 'Approved' ? 'approved' : 'sent back for revision'} successfully!`
    
    // Clear success message after 3 seconds
    setTimeout(() => {
      success.value = ''
    }, 3000)
    
  } catch (err) {
    console.error('Failed to review progress update:', err)
    error.value = 'Failed to review progress update'
  } finally {
    submittingReview.value = false
  }
}

// Load progress updates
const loadProgressUpdates = async () => {
  if (!adRequest.value || adRequest.value.status !== 'Accepted') return
  
  try {
    loadingProgress.value = true
    const response = await sponsorService.getProgressUpdates(adRequest.value.id)
    progressUpdates.value = response.data || []
  } catch (err) {
    console.error('Failed to load progress updates:', err)
    error.value = 'Failed to load progress updates'
  } finally {
    loadingProgress.value = false
  }
}

// Payments state
const payments = ref([])
const loadingPayments = ref(false)
const showPaymentModal = ref(false)
const processingPayment = ref(false)
const paymentForm = reactive({
  amount: 0,
  payment_method: '',
  transaction_id: ''
})

// Computed property to check if payment can be made
const canMakePayment = computed(() => {
  return adRequest.value && adRequest.value.status === 'Accepted'
})

// Close payment modal
const closePaymentModal = () => {
  showPaymentModal.value = false
  
  // Reset form
  paymentForm.amount = adRequest.value ? adRequest.value.payment_amount : 0
  paymentForm.payment_method = ''
  paymentForm.transaction_id = ''
}

// Submit payment
const submitPayment = async () => {
  try {
    processingPayment.value = true
    
    const payload = {
      amount: paymentForm.amount,
      payment_method: paymentForm.payment_method,
      transaction_id: paymentForm.transaction_id || null
    }
    
    await sponsorService.createPayment(adRequest.value.id, payload)
    
    // Close modal and reset form
    closePaymentModal()
    
    // Reload payments
    await loadPayments()
    
    // Show success message
    success.value = 'Payment processed successfully!'
    
    // Clear success message after 3 seconds
    setTimeout(() => {
      success.value = ''
    }, 3000)
    
  } catch (err) {
    console.error('Failed to process payment:', err)
    error.value = 'Failed to process payment'
  } finally {
    processingPayment.value = false
  }
}

// Navigate to Razorpay payment page
const goToRazorpayPayment = () => {
  // Validate amount
  if (!paymentForm.amount || paymentForm.amount <= 0) {
    error.value = 'Please enter a valid payment amount'
    return
  }
  
  // Check if payment method is Razorpay
  if (paymentForm.payment_method !== 'Razorpay') {
    // For non-Razorpay methods, use the regular payment process
    submitPayment()
    return
  }
  
  // Navigate to Razorpay payment page with parameters
  router.push({
    name: 'razorpay-payment',
    params: { adRequestId: adRequest.value.id },
    query: { amount: paymentForm.amount }
  })
}

// Load payments
const loadPayments = async () => {
  if (!adRequest.value || adRequest.value.status !== 'Accepted') return
  
  try {
    loadingPayments.value = true
    const response = await sponsorService.getPayments(adRequest.value.id)
    payments.value = response.data || []
  } catch (err) {
    console.error('Failed to load payments:', err)
    error.value = 'Failed to load payments'
  } finally {
    loadingPayments.value = false
  }
}

// Initialize payment form when ad request loads
const initializePaymentForm = () => {
  if (adRequest.value) {
    paymentForm.amount = adRequest.value.payment_amount
  }
}

// Enhanced loadAdRequest to also load progress updates and payments if relevant
const enhancedLoadAdRequest = async () => {
  try {
    await loadAdRequest()
    
    // If request is accepted, load additional data
    if (adRequest.value && adRequest.value.status === 'Accepted') {
      await Promise.all([
        loadProgressUpdates(),
        loadPayments()
      ])
      initializePaymentForm()
    }
  } catch (err) {
    console.error('Error in enhanced load:', err)
    // Error already handled in loadAdRequest
  }
}
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
      
      <!-- Add a new tab navigation for different sections -->
      <div v-if="adRequest" class="mb-4">
        <ul class="nav nav-tabs">
          <li class="nav-item">
            <a class="nav-link" :class="{ active: activeTab === 'details' }" href="#" @click.prevent="activeTab = 'details'">
              <i class="bi bi-info-circle me-1"></i>Details
            </a>
          </li>
          <li class="nav-item">
            <a class="nav-link" :class="{ active: activeTab === 'negotiations' }" href="#" @click.prevent="activeTab = 'negotiations'">
              <i class="bi bi-chat-dots me-1"></i>Negotiations
            </a>
          </li>
          <li class="nav-item" v-if="adRequest.status === 'Accepted'">
            <a class="nav-link" :class="{ active: activeTab === 'progress' }" href="#" @click.prevent="activeTab = 'progress'">
              <i class="bi bi-clipboard-check me-1"></i>Progress Updates
              <span v-if="pendingUpdatesCount" class="badge bg-warning ms-1">{{ pendingUpdatesCount }}</span>
            </a>
          </li>
          <li class="nav-item" v-if="adRequest.status === 'Accepted'">
            <a class="nav-link" :class="{ active: activeTab === 'payments' }" href="#" @click.prevent="activeTab = 'payments'">
              <i class="bi bi-credit-card me-1"></i>Payments
            </a>
          </li>
        </ul>
      </div>
      
      <!-- Ad Request Details Section -->
      <div v-if="activeTab === 'details' && adRequest" class="card border-0 shadow-sm mb-4">
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
      
      <!-- Update the negotiation tab to include action buttons -->
      <div v-if="activeTab === 'negotiations' && adRequest" class="card border-0 shadow-sm mb-4">
        <div class="card-body">
          <h5 class="card-title border-bottom pb-2 mb-3">Negotiation History</h5>

          <!-- Add Negotiation Actions Section - This is what was missing -->
          <div v-if="canRespond" class="alert alert-info mb-4">
            <h6 class="alert-heading font-weight-bold">Respond to Offer</h6>
            <p>The influencer has made a counter-offer of <strong>{{ formatCurrency(adRequest.payment_amount) }}</strong></p>
            <p v-if="adRequest.message" class="mt-2">
              <strong>Message:</strong> {{ adRequest.message }}
            </p>
            
            <hr>
            
            <div class="mt-3">
              <div class="mb-3 btn-group w-100">
                <button 
                  @click="newMessage.action = 'accept'" 
                  :class="['btn', newMessage.action === 'accept' ? 'btn-success' : 'btn-outline-success']"
                >
                  Accept
                </button>
                <button 
                  @click="newMessage.action = 'negotiate'" 
                  :class="['btn', newMessage.action === 'negotiate' ? 'btn-primary' : 'btn-outline-primary']"
                >
                  Counter Offer
                </button>
                <button 
                  @click="newMessage.action = 'reject'" 
                  :class="['btn', newMessage.action === 'reject' ? 'btn-danger' : 'btn-outline-danger']"
                >
                  Reject
                </button>
              </div>
              
              <div v-if="newMessage.action === 'negotiate'" class="form-group mb-3">
                <label for="payment" class="form-label">Your Counter Offer (USD)</label>
                <div class="input-group">
                  <span class="input-group-text">$</span>
                  <input
                    id="payment"
                    type="number"
                    v-model="newMessage.payment_amount"
                    class="form-control"
                    placeholder="Enter amount"
                    min="1"
                  />
                </div>
              </div>
              
              <div v-if="newMessage.action !== 'accept'" class="form-group mb-3">
                <label class="form-label">Message {{ newMessage.action === 'reject' ? '(Required)' : '' }}</label>
                <textarea
                  v-model="newMessage.message"
                  class="form-control"
                  rows="3"
                  :placeholder="newMessage.action === 'negotiate' ? 'Explain your counter offer' : 'Explain why you are rejecting'"
                ></textarea>
              </div>
              
              <div class="d-flex justify-content-end">
                <button 
                  @click="sendMessage"
                  class="btn btn-primary"
                  :disabled="sendingMessage"
                >
                  <span v-if="sendingMessage">
                    <i class="fas fa-spinner fa-spin me-2"></i> Sending...
                  </span>
                  <span v-else>
                    Send Response
                  </span>
                </button>
              </div>
            </div>
          </div>

          <!-- Negotiation Timeline -->
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
      
      <!-- Progress Updates Tab Content -->
      <div v-if="activeTab === 'progress' && adRequest" class="card border-0 shadow-sm mb-4">
        <div class="card-header bg-white border-0 py-3">
          <h5 class="card-title mb-0">Progress Updates</h5>
        </div>
        
        <div class="card-body">
          <!-- Loading state -->
          <div v-if="loadingProgress" class="text-center py-4">
            <div class="spinner-border text-primary" role="status">
              <span class="visually-hidden">Loading...</span>
            </div>
            <p class="mt-3">Loading progress updates...</p>
          </div>
          
          <!-- Empty state -->
          <div v-else-if="!progressUpdates.length" class="text-center py-4">
            <i class="bi bi-clipboard-x text-muted display-4"></i>
            <p class="mt-3 text-muted">No progress updates have been submitted yet.</p>
          </div>
          
          <!-- Progress updates list -->
          <div v-else>
            <div v-for="update in progressUpdates" :key="update.id" class="progress-update mb-4 p-3 border rounded">
              <div class="d-flex justify-content-between align-items-center mb-2">
                <h6 class="mb-0">Update on {{ formatDate(update.created_at) }}</h6>
                <span class="badge" :class="{
                  'bg-warning': update.status === 'Pending',
                  'bg-success': update.status === 'Approved',
                  'bg-danger': update.status === 'Revision Requested'
                }">{{ update.status }}</span>
              </div>
              
              <p class="mb-3">{{ update.content }}</p>
              
              <!-- Media links if any -->
              <div v-if="update.media_urls && update.media_urls.length" class="mb-3">
                <h6 class="mb-2 small text-muted">Attached Media:</h6>
                <div class="d-flex flex-wrap gap-2">
                  <a v-for="(url, index) in update.media_urls" :key="index" 
                     :href="url" target="_blank" class="btn btn-sm btn-outline-primary">
                    <i class="bi bi-link-45deg me-1"></i>Media {{ index + 1 }}
                  </a>
                </div>
              </div>
              
              <!-- Metrics if any -->
              <div v-if="update.metrics_data" class="mb-3">
                <h6 class="mb-2 small text-muted">Performance Metrics:</h6>
                <div class="bg-light p-2 rounded">
                  <pre class="mb-0 small">{{ formatMetrics(update.metrics_data) }}</pre>
                </div>
              </div>
              
              <!-- Review form for pending updates -->
              <div v-if="update.status === 'Pending'" class="mt-3 pt-3 border-top">
                <h6 class="mb-3 text-primary">Review This Update</h6>
                <form @submit.prevent="reviewUpdate(update.id, reviewForm.status, reviewForm.feedback)">
                  <div class="mb-3">
                    <label class="form-label">Review Decision</label>
                    <div class="d-flex gap-2">
                      <button 
                        type="button" 
                        class="btn btn-outline-success flex-grow-1" 
                        :class="{ active: reviewForm.status === 'Approved' }"
                        @click="reviewForm.status = 'Approved'"
                      >
                        <i class="bi bi-check-circle me-1"></i>Approve
                      </button>
                      <button 
                        type="button" 
                        class="btn btn-outline-danger flex-grow-1" 
                        :class="{ active: reviewForm.status === 'Revision Requested' }"
                        @click="reviewForm.status = 'Revision Requested'"
                      >
                        <i class="bi bi-x-circle me-1"></i>Request Revision
                      </button>
                    </div>
                  </div>
                  
                  <div v-if="reviewForm.status === 'Revision Requested'" class="mb-3">
                    <label for="reviewFeedback" class="form-label">Feedback for Influencer</label>
                    <textarea 
                      id="reviewFeedback" 
                      v-model="reviewForm.feedback" 
                      class="form-control" 
                      rows="3" 
                      placeholder="Explain what needs to be improved or changed..."
                      required
                    ></textarea>
                  </div>
                  
                  <div class="d-flex justify-content-end">
                    <button 
                      type="submit" 
                      class="btn btn-primary" 
                      :disabled="submittingReview"
                    >
                      <span v-if="submittingReview" class="spinner-border spinner-border-sm me-2"></span>
                      Submit Review
                    </button>
                  </div>
                </form>
              </div>
              
              <!-- Feedback if status is Revision Requested -->
              <div v-if="update.status === 'Revision Requested' && update.feedback" class="alert alert-danger mt-3">
                <h6 class="mb-1"><i class="bi bi-exclamation-triangle-fill me-2"></i>Revision Requested:</h6>
                <p class="mb-0">{{ update.feedback }}</p>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <!-- Payments Tab Content -->
      <div v-if="activeTab === 'payments' && adRequest" class="card border-0 shadow-sm mb-4">
        <div class="card-header bg-white border-0 py-3 d-flex justify-content-between align-items-center">
          <h5 class="card-title mb-0">Payment History</h5>
          <button 
            class="btn btn-primary" 
            @click="showPaymentModal = true" 
            :disabled="!canMakePayment"
          >
            <i class="bi bi-plus-circle me-1"></i>Make Payment
          </button>
        </div>
        
        <div class="card-body">
          <!-- Loading state -->
          <div v-if="loadingPayments" class="text-center py-4">
            <div class="spinner-border text-primary" role="status">
              <span class="visually-hidden">Loading...</span>
            </div>
            <p class="mt-3">Loading payments...</p>
          </div>
          
          <!-- Empty state -->
          <div v-else-if="!payments.length" class="text-center py-4">
            <i class="bi bi-cash-stack text-muted display-4"></i>
            <p class="mt-3 text-muted">No payments made yet.</p>
            <p v-if="canMakePayment" class="text-muted">Click "Make Payment" to pay the influencer.</p>
          </div>
          
          <!-- Payments list -->
          <div v-else>
            <div class="table-responsive">
              <table class="table table-hover">
                <thead>
                  <tr>
                    <th>Date</th>
                    <th>Amount</th>
                    <th>Status</th>
                    <th>Payment Method</th>
                    <th>Transaction ID</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="payment in payments" :key="payment.id">
                    <td>{{ formatDate(payment.created_at) }}</td>
                    <td>{{ formatCurrency(payment.amount) }}</td>
                    <td>
                      <span class="badge" :class="{
                        'bg-warning': payment.status === 'Pending',
                        'bg-success': payment.status === 'Completed',
                        'bg-danger': payment.status === 'Failed'
                      }">{{ payment.status }}</span>
                    </td>
                    <td>{{ payment.payment_method }}</td>
                    <td><code>{{ payment.transaction_id }}</code></td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
      
      <!-- Payment Modal -->
      <div v-if="showPaymentModal" class="modal fade show d-block" tabindex="-1" style="background-color: rgba(0,0,0,0.5)">
        <div class="modal-dialog modal-dialog-centered">
          <div class="modal-content">
            <div class="modal-header">
              <h5 class="modal-title">Make Payment</h5>
              <button type="button" class="btn-close" @click="closePaymentModal" aria-label="Close"></button>
            </div>
            <div class="modal-body">
              <form @submit.prevent="submitPayment">
                <div class="mb-3">
                  <label for="paymentAmount" class="form-label">Payment Amount ($)</label>
                  <input 
                    type="number" 
                    id="paymentAmount" 
                    v-model="paymentForm.amount" 
                    class="form-control" 
                    min="1" 
                    step="0.01" 
                    required 
                    :placeholder="'Agreed amount: $' + adRequest?.payment_amount"
                  >
                  <div class="form-text">
                    Agreed payment amount: {{ formatCurrency(adRequest?.payment_amount) }}
                  </div>
                </div>
                
                <div class="mb-3">
                  <label for="paymentMethod" class="form-label">Payment Method</label>
                  <select id="paymentMethod" v-model="paymentForm.payment_method" class="form-select" required>
                    <option value="" disabled>Select a payment method</option>
                    <option value="Razorpay">Razorpay</option>
                    <option value="Bank Transfer">Bank Transfer</option>
                    <option value="Other">Other</option>
                  </select>
                </div>
                
                <div class="mb-3">
                  <label for="transactionId" class="form-label">Transaction ID (Optional)</label>
                  <input 
                    type="text" 
                    id="transactionId" 
                    v-model="paymentForm.transaction_id" 
                    class="form-control" 
                    placeholder="Enter transaction reference if available"
                  >
                </div>
              </form>
            </div>
            <div class="modal-footer">
              <button type="button" class="btn btn-secondary" @click="closePaymentModal">Cancel</button>
              <button 
                type="button" 
                class="btn btn-primary" 
                @click="goToRazorpayPayment" 
                :disabled="processingPayment"
              >
                <span v-if="processingPayment" class="spinner-border spinner-border-sm me-2"></span>
                Proceed to Payment
              </button>
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

.chat-container {
  max-height: 400px;
  overflow-y: auto;
  padding-right: 10px;
}

.chat-message {
  max-width: 80%;
}

.sponsor-message {
  margin-left: auto;
}

.influencer-message {
  margin-right: auto;
}

.sponsor-message .message-content {
  background-color: rgba(var(--bs-primary-rgb), 0.1);
  border-top-right-radius: 0 !important;
}

.influencer-message .message-content {
  background-color: rgba(var(--bs-info-rgb), 0.1);
  border-top-left-radius: 0 !important;
}

/* Scrollbar styling */
.chat-container::-webkit-scrollbar {
  width: 6px;
}

.chat-container::-webkit-scrollbar-track {
  background: #f1f1f1;
}

.chat-container::-webkit-scrollbar-thumb {
  background: #ccc;
  border-radius: 3px;
}

/* Tab navigation styles */
.nav-tabs .nav-link {
  color: #6c757d;
}

.nav-tabs .nav-link.active {
  color: var(--bs-primary);
  font-weight: 500;
}

.nav-tabs .nav-link:hover:not(.active) {
  color: #343a40;
}

/* Modal styles */
.modal {
  background-color: rgba(0, 0, 0, 0.5);
}
</style> 