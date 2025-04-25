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

// Active tab state
const activeTab = ref('details')

// Progress updates state
const progressUpdates = ref([])
const loadingProgress = ref(false)
const submittingProgress = ref(false)
const progressForm = reactive({
  content: '',
  media_urls: [],
  metrics: {
    views: 0,
    likes: 0,
    comments: 0,
    shares: 0
  }
})

// Progress badge count - updates that need revision
const progressBadgeCount = computed(() => {
  return progressUpdates.value.filter(update => update.status === 'Revision Requested').length
})

// Payments state
const payments = ref([])
const loadingPayments = ref(false)

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

// Load progress updates
const loadProgressUpdates = async () => {
  if (!adRequest.value || adRequest.value.status !== 'Accepted') return
  
  try {
    loadingProgress.value = true
    const response = await influencerService.getProgressUpdates(adRequest.value.id)
    progressUpdates.value = response.data || []
  } catch (err) {
    console.error('Failed to load progress updates:', err)
    error.value = 'Failed to load progress updates'
  } finally {
    loadingProgress.value = false
  }
}

// Submit progress update
const submitProgressUpdate = async () => {
  try {
    submittingProgress.value = true
    
    // Format metrics to JSON string
    const metricsData = JSON.stringify(progressForm.metrics)
    
    // Filter out empty media URLs
    const mediaUrls = progressForm.media_urls.filter(url => url.trim() !== '')
    
    const payload = {
      content: progressForm.content,
      media_urls: mediaUrls,
      metrics_data: metricsData
    }
    
    await influencerService.addProgressUpdate(adRequest.value.id, payload)
    
    // Reset form
    progressForm.content = ''
    progressForm.media_urls = []
    progressForm.metrics = { views: 0, likes: 0, comments: 0, shares: 0 }
    
    // Reload updates
    await loadProgressUpdates()
    
    successMessage.value = 'Progress update submitted successfully!'
    
    // Clear success message after 3 seconds
    setTimeout(() => {
      successMessage.value = ''
    }, 3000)
    
  } catch (err) {
    console.error('Failed to submit progress update:', err)
    error.value = 'Failed to submit progress update'
  } finally {
    submittingProgress.value = false
  }
}

// Load payments
const loadPayments = async () => {
  if (!adRequest.value || adRequest.value.status !== 'Accepted') return
  
  try {
    loadingPayments.value = true
    const response = await influencerService.getPayments(adRequest.value.id)
    payments.value = response.data || []
  } catch (err) {
    console.error('Failed to load payments:', err)
    error.value = 'Failed to load payments'
  } finally {
    loadingPayments.value = false
  }
}

// Enhanced loadAdRequest to also load progress updates and payments if relevant
const enhancedLoadAdRequest = async () => {
  await loadAdRequest()
  
  // If request is accepted, load additional data
  if (adRequest.value && adRequest.value.status === 'Accepted') {
    await loadProgressUpdates()
    await loadPayments()
  }
}

// Load data on component mount
onMounted(() => {
  enhancedLoadAdRequest()
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
                    <span v-if="progressBadgeCount" class="badge bg-danger ms-1">{{ progressBadgeCount }}</span>
                  </a>
                </li>
                <li class="nav-item" v-if="adRequest.status === 'Accepted'">
                  <a class="nav-link" :class="{ active: activeTab === 'payments' }" href="#" @click.prevent="activeTab = 'payments'">
                    <i class="bi bi-credit-card me-1"></i>Payments
                  </a>
                </li>
              </ul>
            </div>
            
            <!-- Details Tab Content -->
            <div v-if="activeTab === 'details'" class="card border-0 shadow-sm mb-4">
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
            
            <!-- Negotiations Tab Content -->
            <div v-if="activeTab === 'negotiations'" class="card border-0 shadow-sm mb-4">
              <!-- Existing negotiation content -->
              <!-- ... existing code ... -->
            </div>
            
            <!-- Progress Updates Tab Content -->
            <div v-if="activeTab === 'progress'" class="card border-0 shadow-sm mb-4">
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
                  <i class="bi bi-clipboard-plus text-muted display-4"></i>
                  <p class="mt-3 text-muted">No progress updates yet. Add your first update!</p>
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
                    
                    <!-- Feedback if status is Revision Requested -->
                    <div v-if="update.status === 'Revision Requested' && update.feedback" class="alert alert-danger mt-3">
                      <h6 class="mb-1"><i class="bi bi-exclamation-triangle-fill me-2"></i>Revision Required:</h6>
                      <p class="mb-0">{{ update.feedback }}</p>
                    </div>
                  </div>
                </div>
                
                <!-- Add new progress update form -->
                <div class="card mt-4">
                  <div class="card-header">
                    <h6 class="mb-0">Add New Progress Update</h6>
                  </div>
                  <div class="card-body">
                    <form @submit.prevent="submitProgressUpdate">
                      <div class="mb-3">
                        <label for="progressContent" class="form-label">Update Content</label>
                        <textarea 
                          id="progressContent" 
                          v-model="progressForm.content" 
                          class="form-control" 
                          rows="4" 
                          placeholder="Describe your progress, accomplishments, and next steps..."
                          required
                        ></textarea>
                      </div>
                      
                      <div class="mb-3">
                        <label class="form-label">Media URLs (Optional)</label>
                        <div v-for="(url, index) in progressForm.media_urls" :key="index" class="input-group mb-2">
                          <input 
                            type="url" 
                            class="form-control" 
                            v-model="progressForm.media_urls[index]" 
                            placeholder="Enter URL to image, video, or social media post"
                          >
                          <button 
                            type="button" 
                            class="btn btn-outline-danger" 
                            @click="progressForm.media_urls.splice(index, 1)"
                          >
                            <i class="bi bi-trash"></i>
                          </button>
                        </div>
                        <button 
                          type="button" 
                          class="btn btn-sm btn-outline-secondary mt-1" 
                          @click="progressForm.media_urls.push('')"
                        >
                          <i class="bi bi-plus-circle me-1"></i>Add Media URL
                        </button>
                      </div>
                      
                      <div class="mb-3">
                        <label class="form-label">Performance Metrics (Optional)</label>
                        <div class="row g-2 mb-2">
                          <div class="col-6">
                            <div class="input-group">
                              <span class="input-group-text">Views</span>
                              <input type="number" class="form-control" v-model="progressForm.metrics.views" min="0">
                            </div>
                          </div>
                          <div class="col-6">
                            <div class="input-group">
                              <span class="input-group-text">Likes</span>
                              <input type="number" class="form-control" v-model="progressForm.metrics.likes" min="0">
                            </div>
                          </div>
                          <div class="col-6">
                            <div class="input-group">
                              <span class="input-group-text">Comments</span>
                              <input type="number" class="form-control" v-model="progressForm.metrics.comments" min="0">
                            </div>
                          </div>
                          <div class="col-6">
                            <div class="input-group">
                              <span class="input-group-text">Shares</span>
                              <input type="number" class="form-control" v-model="progressForm.metrics.shares" min="0">
                            </div>
                          </div>
                        </div>
                      </div>
                      
                      <div class="d-flex justify-content-end">
                        <button 
                          type="submit" 
                          class="btn btn-primary" 
                          :disabled="submittingProgress"
                        >
                          <span v-if="submittingProgress" class="spinner-border spinner-border-sm me-2"></span>
                          Submit Progress Update
                        </button>
                      </div>
                    </form>
                  </div>
                </div>
              </div>
            </div>
            
            <!-- Payments Tab Content -->
            <div v-if="activeTab === 'payments'" class="card border-0 shadow-sm mb-4">
              <div class="card-header bg-white border-0 py-3">
                <h5 class="card-title mb-0">Payment History</h5>
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
                  <p class="mt-3 text-muted">No payments received yet.</p>
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
</style> 