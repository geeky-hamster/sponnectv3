<script setup>
import { ref, onMounted, computed, reactive } from 'vue'
import { useRoute, useRouter, RouterLink } from 'vue-router'
import { sponsorService, negotiationService } from '../../services/api'
import { formatDate } from '../../utils/dateUtils'

const route = useRoute()
const router = useRouter()
const campaignId = computed(() => route.params.id)

// State
const loading = ref(true)
const campaign = ref(null)
const adRequests = ref([])
const applications = ref([])
const error = ref('')
const successMessage = ref('')
const activeTab = ref('details')

// Modal states
const showAdRequestModal = ref(false)
const showApplicationModal = ref(false)
const selectedRequest = ref(null)
const selectedApplication = ref(null)
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

// Load campaign data
const loadCampaign = async () => {
  loading.value = true
  error.value = ''
  
  try {
    // Fetch campaign details and its ad requests in parallel
    const [campaignResponse, adRequestsResponse, applicationsResponse] = await Promise.all([
      sponsorService.getCampaign(campaignId.value),
      sponsorService.getAdRequests({ campaign_id: campaignId.value }),
      sponsorService.getCampaignApplications(campaignId.value)
    ])
    
    campaign.value = campaignResponse.data
    adRequests.value = Array.isArray(adRequestsResponse.data) ? adRequestsResponse.data : 
                       (adRequestsResponse.data?.ad_requests ? adRequestsResponse.data.ad_requests : [])
    applications.value = Array.isArray(applicationsResponse.data) ? applicationsResponse.data : 
                         (applicationsResponse.data?.applications ? applicationsResponse.data.applications : [])
    
  } catch (err) {
    console.error('Failed to load campaign details:', err)
    error.value = 'Failed to load campaign details. Please try again later.'
  } finally {
    loading.value = false
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

// Handle campaign deletion
const deleteCampaign = async () => {
  if (!confirm('Are you sure you want to delete this campaign? This action cannot be undone.')) {
    return
  }
  
  try {
    await sponsorService.deleteCampaign(campaignId.value)
    router.push('/sponsor/campaigns')
  } catch (err) {
    console.error('Failed to delete campaign:', err)
    error.value = 'Failed to delete campaign. Please try again later.'
  }
}

// Mark campaign as completed
const completeCampaign = async () => {
  if (!confirm('Are you sure you want to mark this campaign as completed? This action cannot be undone.')) {
    return
  }
  
  try {
    const response = await sponsorService.completeCampaign(campaignId.value)
    campaign.value = response.data.campaign
    successMessage.value = 'Campaign marked as completed successfully!'
    
    // Auto-dismiss success message after 3 seconds
    setTimeout(() => {
      successMessage.value = ''
    }, 3000)
  } catch (err) {
    console.error('Failed to complete campaign:', err)
    error.value = 'Failed to mark campaign as completed. Please try again later.'
  }
}

// Check if campaign is expired but not completed
const isExpired = computed(() => {
  if (!campaign.value || !campaign.value.end_date_iso) return false
  
  const endDate = new Date(campaign.value.end_date_iso)
  const now = new Date()
  
  return endDate < now && campaign.value.status !== 'completed'
})

// Get status badge color
const getStatusBadgeClass = computed(() => {
  if (!campaign.value) return 'bg-secondary'
  
  switch (campaign.value.status) {
    case 'active':
      return isExpired.value ? 'bg-warning' : 'bg-success'
    case 'completed':
      return 'bg-info'
    case 'paused':
      return 'bg-warning'
    case 'draft':
      return 'bg-secondary'
    case 'pending_approval':
      return 'bg-primary'
    case 'rejected':
      return 'bg-danger'
    default:
      return 'bg-secondary'
  }
})

// Get human readable status
const getStatusText = computed(() => {
  if (!campaign.value) return ''
  
  if (isExpired.value && campaign.value.status === 'active') {
    return 'Expired'
  }
  
  switch (campaign.value.status) {
    case 'active':
      return 'Active'
    case 'completed':
      return 'Completed'
    case 'paused':
      return 'Paused'
    case 'draft':
      return 'Draft'
    case 'pending_approval':
      return 'Pending Approval'
    case 'rejected':
      return 'Rejected'
    default:
      return campaign.value.status
  }
})

// Accept an application
const acceptApplication = async (applicationId) => {
  if (!confirm('Are you sure you want to accept this application?')) return
  
  try {
    await sponsorService.acceptApplication(applicationId)
    successMessage.value = 'Application accepted successfully!'
    // Refresh data
    loadCampaign()
  } catch (err) {
    console.error('Failed to accept application:', err)
    error.value = 'Failed to accept application. Please try again later.'
  }
}

// Reject an application
const rejectApplication = async (applicationId) => {
  if (!confirm('Are you sure you want to reject this application?')) return
  
  try {
    await sponsorService.rejectApplication(applicationId)
    successMessage.value = 'Application rejected successfully!'
    // Refresh data
    loadCampaign()
  } catch (err) {
    console.error('Failed to reject application:', err)
    error.value = 'Failed to reject application. Please try again later.'
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

// Open application modal
const openApplicationModal = async (application) => {
  selectedApplication.value = application
  showApplicationModal.value = true
  
  // If the application has an ad request ID, load its history
  if (application.ad_request_id) {
    await loadNegotiationHistory(application.ad_request_id)
  }
}

// Close application modal
const closeApplicationModal = () => {
  showApplicationModal.value = false
  selectedApplication.value = null
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
    
    // Refresh data
    await loadCampaign()
    
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

// Load data on component mount
onMounted(() => {
  loadCampaign()
})
</script>

<template>
  <div class="campaign-detail-view py-5">
    <div class="container">
      <!-- Breadcrumb -->
      <nav aria-label="breadcrumb" class="mb-4">
        <ol class="breadcrumb">
          <li class="breadcrumb-item">
            <RouterLink to="/sponsor/dashboard">Dashboard</RouterLink>
          </li>
          <li class="breadcrumb-item">
            <RouterLink to="/sponsor/campaigns">Campaigns</RouterLink>
          </li>
          <li class="breadcrumb-item active">Campaign Details</li>
        </ol>
      </nav>
      
      <!-- Loading state -->
      <div v-if="loading" class="text-center py-5">
        <div class="spinner-border text-primary" role="status">
          <span class="visually-hidden">Loading...</span>
        </div>
        <p class="mt-3">Loading campaign details...</p>
      </div>
      
      <!-- Error state -->
      <div v-else-if="error" class="alert alert-danger alert-dismissible fade show" role="alert">
        {{ error }}
        <button type="button" class="btn-close" @click="error = ''"></button>
      </div>
      
      <!-- Success message -->
      <div v-if="successMessage" class="alert alert-success alert-dismissible fade show" role="alert">
        {{ successMessage }}
        <button type="button" class="btn-close" @click="successMessage = ''"></button>
      </div>
      
      <!-- Campaign details -->
      <div v-else-if="campaign">
        <!-- Header with actions -->
        <div class="d-flex justify-content-between align-items-start mb-4">
          <div>
            <h1 class="mb-2">{{ campaign.name }}</h1>
            <div class="d-flex align-items-center">
              <span 
                :class="{
                  'badge rounded-pill bg-success me-2': campaign.visibility === 'public',
                  'badge rounded-pill bg-secondary me-2': campaign.visibility === 'private'
                }"
              >
                {{ campaign.visibility }}
              </span>
              <span 
                class="badge rounded-pill me-2"
                :class="getStatusBadgeClass"
              >
                {{ getStatusText }}
              </span>
              <span class="text-muted">Created on {{ formatDate(campaign.created_at) }}</span>
            </div>
          </div>
          <div class="d-flex">
            <RouterLink 
              v-if="campaign.status !== 'completed'" 
              :to="`/sponsor/campaigns/${campaignId}/edit`" 
              class="btn btn-outline-primary me-2"
            >
              <i class="bi bi-pencil me-1"></i>Edit
            </RouterLink>
            <button 
              v-if="campaign.status === 'active'" 
              @click="completeCampaign" 
              class="btn btn-outline-success me-2"
              :disabled="loading"
            >
              <i class="bi bi-check-circle me-1"></i>Complete
            </button>
            <button 
              v-if="isExpired" 
              @click="completeCampaign" 
              class="btn btn-warning me-2"
              :disabled="loading"
            >
              <i class="bi bi-check-circle me-1"></i>Mark as Completed
            </button>
            <button 
              v-if="campaign.status !== 'completed'" 
              @click="deleteCampaign" 
              class="btn btn-outline-danger"
            >
              <i class="bi bi-trash me-1"></i>Delete
            </button>
          </div>
        </div>
        
        <!-- Tabs -->
        <ul class="nav nav-tabs mb-4">
          <li class="nav-item">
            <a 
              class="nav-link" 
              :class="{ active: activeTab === 'details' }"
              href="#" 
              @click.prevent="activeTab = 'details'"
            >
              Campaign Details
            </a>
          </li>
          <li class="nav-item">
            <a 
              class="nav-link" 
              :class="{ active: activeTab === 'requests' }"
              href="#" 
              @click.prevent="activeTab = 'requests'"
            >
              Ad Requests 
              <span class="badge bg-primary rounded-pill ms-1">{{ Array.isArray(adRequests) ? adRequests.length : 0 }}</span>
            </a>
          </li>
          <li class="nav-item">
            <a 
              class="nav-link" 
              :class="{ active: activeTab === 'applications' }"
              href="#" 
              @click.prevent="activeTab = 'applications'"
            >
              Applications 
              <span class="badge bg-primary rounded-pill ms-1">{{ Array.isArray(applications) ? applications.length : 0 }}</span>
            </a>
          </li>
        </ul>
        
        <!-- Tab content -->
        <div class="tab-content">
          <!-- Campaign Details Tab -->
          <div v-if="activeTab === 'details'" class="tab-pane fade show active">
            <div class="row">
              <div class="col-lg-8">
                <div class="card border-0 shadow-sm mb-4">
                  <div class="card-body">
                    <h4 class="card-title mb-3">Description</h4>
                    <p class="card-text">{{ campaign.description || 'No description provided.' }}</p>
                    
                    <h4 class="card-title mt-4 mb-3">Goals</h4>
                    <p class="card-text">{{ campaign.goals || 'No goals specified.' }}</p>
                  </div>
                </div>
                
                <div class="card border-0 shadow-sm">
                  <div class="card-body">
                    <h4 class="card-title mb-3">Find Influencers</h4>
                    <p class="text-muted mb-4">Search for influencers to invite to this campaign.</p>
                    <RouterLink to="/search/influencers" class="btn btn-primary">
                      <i class="bi bi-search me-1"></i>Find Influencers
                    </RouterLink>
                  </div>
                </div>
              </div>
              
              <div class="col-lg-4">
                <div class="card border-0 shadow-sm mb-4">
                  <div class="card-body">
                    <h5 class="card-title mb-3">Campaign Details</h5>
                    
                    <div class="mb-3 pb-3 border-bottom">
                      <h6 class="text-muted mb-1">Budget</h6>
                      <div class="fs-4 fw-bold text-success">
                        {{ formatCurrency(campaign.budget) }}
                      </div>
                    </div>
                    
                    <div class="mb-3 pb-3 border-bottom">
                      <h6 class="text-muted mb-1">Start Date</h6>
                      <div>{{ formatDate(campaign.start_date) }}</div>
                    </div>
                    
                    <div class="mb-3 pb-3 border-bottom">
                      <h6 class="text-muted mb-1">End Date</h6>
                      <div>{{ formatDate(campaign.end_date) }}</div>
                    </div>
                    
                    <div class="mb-3 pb-3 border-bottom">
                      <h6 class="text-muted mb-1">Status</h6>
                      <div :class="{
                        'text-success': campaign.status === 'active' && !isExpired,
                        'text-warning': isExpired || campaign.status === 'paused',
                        'text-info': campaign.status === 'completed',
                        'text-danger': campaign.status === 'rejected',
                        'text-primary': campaign.status === 'pending_approval',
                        'text-secondary': campaign.status === 'draft'
                      }">
                        <i :class="{
                          'bi bi-check-circle-fill me-1': campaign.status === 'active' && !isExpired,
                          'bi bi-exclamation-circle-fill me-1': isExpired,
                          'bi bi-info-circle-fill me-1': campaign.status === 'completed',
                          'bi bi-x-circle-fill me-1': campaign.status === 'rejected',
                          'bi bi-clock-fill me-1': campaign.status === 'pending_approval',
                          'bi bi-pause-circle-fill me-1': campaign.status === 'paused',
                          'bi bi-file-earmark-fill me-1': campaign.status === 'draft'
                        }"></i>
                        {{ getStatusText }}
                      </div>
                    </div>
                    
                    <div>
                      <h6 class="text-muted mb-1">Visibility</h6>
                      <div
                        :class="{
                          'text-success': campaign.visibility === 'public',
                          'text-secondary': campaign.visibility === 'private'
                        }"
                      >
                        <i 
                          :class="{
                            'bi bi-eye-fill me-1': campaign.visibility === 'public',
                            'bi bi-eye-slash-fill me-1': campaign.visibility === 'private'
                          }"
                        ></i>
                        {{ campaign.visibility.charAt(0).toUpperCase() + campaign.visibility.slice(1) }}
                      </div>
                    </div>
                  </div>
                </div>
                
                <div class="card border-0 shadow-sm">
                  <div class="card-body">
                    <h5 class="card-title mb-3">Stats</h5>
                    
                    <div class="d-flex justify-content-between align-items-center mb-2">
                      <div>Total Ad Requests</div>
                      <div class="fw-bold">{{ Array.isArray(adRequests) ? adRequests.length : 0 }}</div>
                    </div>
                    
                    <div class="mb-3">
                      <div class="d-flex justify-content-between align-items-center mb-2">
                        <div>Pending Applications</div>
                        <div class="fw-bold">{{ Array.isArray(applications) ? applications.filter(a => a.status === 'Pending').length : 0 }}</div>
                      </div>
                      
                      <div class="d-flex justify-content-between align-items-center mb-2">
                        <div>Accepted Partnerships</div>
                        <div class="fw-bold">{{ Array.isArray(adRequests) ? adRequests.filter(r => r.status === 'Accepted').length : 0 }}</div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
          
          <!-- Ad Requests Tab -->
          <div v-if="activeTab === 'requests'" class="tab-pane fade show active">
            <div class="card border-0 shadow-sm">
              <div class="card-body">
                <div class="d-flex justify-content-between align-items-center mb-4">
                  <h4 class="mb-0">Ad Requests</h4>
                  <RouterLink :to="`/sponsor/campaigns/${campaignId}/create-request`" class="btn btn-primary btn-sm">
                    <i class="bi bi-plus-circle me-1"></i>Create Request
                  </RouterLink>
                </div>
                
                <div v-if="!Array.isArray(adRequests) || adRequests.length === 0" class="text-center py-4">
                  <i class="bi bi-inbox display-4 text-muted"></i>
                  <p class="mt-3 mb-1">No ad requests yet</p>
                  <p class="text-muted">Invite influencers to collaborate on this campaign.</p>
                </div>
                
                <div v-else class="table-responsive">
                  <table class="table table-hover align-middle">
                    <thead class="table-light">
                      <tr>
                        <th>Influencer</th>
                        <th>Payment</th>
                        <th>Status</th>
                        <th>Updated</th>
                        <th>Last Action By</th>
                        <th>Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr v-for="request in adRequests" :key="request.id">
                        <td>{{ request.influencer_name }}</td>
                        <td>{{ formatCurrency(request.payment_amount) }}</td>
                        <td>
                          <span 
                            :class="{
                              'badge rounded-pill bg-warning': request.status === 'Pending',
                              'badge rounded-pill bg-info': request.status === 'Negotiating',
                              'badge rounded-pill bg-success': request.status === 'Accepted',
                              'badge rounded-pill bg-danger': request.status === 'Rejected'
                            }"
                          >
                            {{ request.status }}
                          </span>
                          <i v-if="canRespond(request)" class="bi bi-exclamation-circle text-warning ms-1" 
                             title="Action required"></i>
                        </td>
                        <td>{{ formatDate(request.updated_at) }}</td>
                        <td>{{ request.last_offer_by }}</td>
                        <td>
                          <div class="btn-group">
                            <button @click="openAdRequestModal(request)" class="btn btn-sm btn-primary">
                              <i class="bi bi-eye me-1"></i> View & Respond
                            </button>
                            <RouterLink :to="`/sponsor/ad-requests/${request.id}`" class="btn btn-sm btn-outline-primary">
                              Details
                            </RouterLink>
                          </div>
                        </td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          </div>
          
          <!-- Applications Tab -->
          <div v-if="activeTab === 'applications'" class="tab-pane fade show active">
            <div class="card border-0 shadow-sm">
              <div class="card-body">
                <h4 class="mb-4">Influencer Applications</h4>
                
                <div v-if="!Array.isArray(applications) || applications.length === 0" class="text-center py-4">
                  <i class="bi bi-inbox display-4 text-muted"></i>
                  <p class="mt-3 mb-1">No applications yet</p>
                  <p class="text-muted">
                    If your campaign is public, influencers can apply to collaborate.
                  </p>
                </div>
                
                <div v-else class="table-responsive">
                  <table class="table table-hover align-middle">
                    <thead class="table-light">
                      <tr>
                        <th>Influencer</th>
                        <th>Requested Payment</th>
                        <th>Date Applied</th>
                        <th>Status</th>
                        <th>Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr v-for="application in applications" :key="application.id">
                        <td>{{ application.influencer_name }}</td>
                        <td>{{ formatCurrency(application.payment_amount) }}</td>
                        <td>{{ formatDate(application.created_at) }}</td>
                        <td>
                          <span 
                            :class="{
                              'badge rounded-pill bg-warning': application.status === 'Pending',
                              'badge rounded-pill bg-success': application.status === 'Accepted',
                              'badge rounded-pill bg-danger': application.status === 'Rejected'
                            }"
                          >
                            {{ application.status }}
                          </span>
                        </td>
                        <td>
                          <div v-if="application.status === 'Pending'" class="btn-group">
                            <button @click="openApplicationModal(application)" class="btn btn-sm btn-primary">
                              <i class="bi bi-eye me-1"></i> View & Respond
                            </button>
                            <button @click="acceptApplication(application.id)" class="btn btn-sm btn-success">
                              Accept
                            </button>
                            <button @click="rejectApplication(application.id)" class="btn btn-sm btn-danger">
                              Reject
                            </button>
                          </div>
                          <RouterLink v-else :to="`/sponsor/ad-requests/${application.ad_request_id}`" class="btn btn-sm btn-outline-primary">
                            View Details
                          </RouterLink>
                        </td>
                      </tr>
                    </tbody>
                  </table>
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
                          <div class="fw-bold">{{ campaign.name }}</div>
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
        
        <!-- Application Modal -->
        <div v-if="showApplicationModal && selectedApplication" class="modal-overlay" @click.self="closeApplicationModal">
          <div class="modal show d-block" tabindex="-1" role="dialog">
            <div class="modal-dialog modal-dialog-centered modal-lg" role="document">
              <div class="modal-content">
                <div class="modal-header">
                  <h5 class="modal-title">Application from {{ selectedApplication.influencer_name }}</h5>
                  <button type="button" class="btn-close" @click="closeApplicationModal" aria-label="Close"></button>
                </div>
                
                <div class="modal-body">
                  <div class="card mb-4">
                    <div class="card-header bg-light">
                      <h6 class="mb-0">Application Details</h6>
                    </div>
                    <div class="card-body">
                      <div class="row g-3">
                        <div class="col-md-6">
                          <label class="text-muted d-block mb-1">Campaign</label>
                          <div class="fw-bold">{{ campaign.name }}</div>
                        </div>
                        <div class="col-md-6">
                          <label class="text-muted d-block mb-1">Requested Payment</label>
                          <div class="fs-5 fw-bold text-primary">{{ formatCurrency(selectedApplication.payment_amount) }}</div>
                        </div>
                        <div class="col-md-6">
                          <label class="text-muted d-block mb-1">Date Applied</label>
                          <div>{{ formatDate(selectedApplication.created_at) }}</div>
                        </div>
                        <div class="col-md-6">
                          <label class="text-muted d-block mb-1">Status</label>
                          <span 
                            :class="{
                              'badge rounded-pill bg-warning': selectedApplication.status === 'Pending',
                              'badge rounded-pill bg-success': selectedApplication.status === 'Accepted',
                              'badge rounded-pill bg-danger': selectedApplication.status === 'Rejected'
                            }"
                          >
                            {{ selectedApplication.status }}
                          </span>
                        </div>
                        <div class="col-12">
                          <label class="text-muted d-block mb-1">Message</label>
                          <div class="p-3 bg-light rounded">
                            <p class="mb-0 whitespace-pre-wrap">{{ selectedApplication.message || 'No message provided.' }}</p>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                  
                  <!-- Action Buttons if application is pending -->
                  <div v-if="selectedApplication.status === 'Pending'" class="alert alert-info mb-4">
                    <div class="d-flex justify-content-between mb-2">
                      <h6 class="alert-heading fw-bold mb-0">Response Required</h6>
                      <span class="badge bg-warning">Action Required</span>
                    </div>
                    
                    <p>The influencer is requesting <strong>{{ formatCurrency(selectedApplication.payment_amount) }}</strong> for this collaboration.</p>
                    <p v-if="selectedApplication.message" class="mt-2">
                      <strong>Message:</strong> {{ selectedApplication.message }}
                    </p>
                    
                    <hr>
                    
                    <div class="d-flex justify-content-center gap-3">
                      <button 
                        @click="acceptApplication(selectedApplication.id)" 
                        class="btn btn-success" 
                        type="button"
                      >
                        <i class="bi bi-check-circle me-1"></i> Accept Application
                      </button>
                      <button 
                        @click="rejectApplication(selectedApplication.id)" 
                        class="btn btn-danger" 
                        type="button"
                      >
                        <i class="bi bi-x-circle me-1"></i> Reject Application
                      </button>
                    </div>
                  </div>
                  
                  <!-- Status Message if application is already processed -->
                  <div v-else class="alert mb-4" :class="{
                    'alert-success': selectedApplication.status === 'Accepted',
                    'alert-danger': selectedApplication.status === 'Rejected'
                  }">
                    <div class="d-flex justify-content-between">
                      <h6 class="alert-heading fw-bold mb-1">Status: {{ selectedApplication.status }}</h6>
                    </div>
                    <p class="mb-0" v-if="selectedApplication.status === 'Accepted'">
                      <i class="bi bi-check-circle me-1"></i> You have accepted this application at <strong>{{ formatCurrency(selectedApplication.payment_amount) }}</strong>.
                    </p>
                    <p class="mb-0" v-else-if="selectedApplication.status === 'Rejected'">
                      <i class="bi bi-x-circle me-1"></i> This application has been rejected.
                    </p>
                  </div>
                  
                  <!-- Display Negotiation History if available -->
                  <div v-if="negotiationHistory.length > 0" class="card">
                    <div class="card-header bg-light">
                      <h6 class="mb-0">Negotiation History</h6>
                    </div>
                    <div class="card-body">
                      <!-- Negotiation history timeline -->
                      <div class="timeline mt-3">
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
                  <button type="button" class="btn btn-outline-secondary" @click="closeApplicationModal">
                    Close
                  </button>
                  <RouterLink 
                    v-if="selectedApplication.ad_request_id" 
                    :to="`/sponsor/ad-requests/${selectedApplication.ad_request_id}`" 
                    class="btn btn-primary"
                  >
                    View Full Details
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
.campaign-detail-view {
  animation: fadeIn 0.5s ease-in-out;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

.tab-content {
  padding-top: 1rem;
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
