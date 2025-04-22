<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { RouterLink } from 'vue-router'
import { influencerService } from '../../services/api'

// State
const loading = ref(true)
const adRequests = ref([])
const error = ref('')

// Filters
const filters = reactive({
  status: '',
  search: ''
})

// Available statuses for filter
const statusOptions = [
  { value: '', label: 'All Requests' },
  { value: 'Pending', label: 'Pending' },
  { value: 'Negotiating', label: 'Negotiating' },
  { value: 'Accepted', label: 'Accepted' },
  { value: 'Rejected', label: 'Rejected' }
]

// Computed property for filtered requests
const filteredRequests = computed(() => {
  return adRequests.value.filter(request => {
    // Status filter
    const statusMatch = !filters.status || request.status === filters.status
    
    // Search filter (case insensitive)
    const searchMatch = !filters.search || 
      request.campaign_name?.toLowerCase().includes(filters.search.toLowerCase()) ||
      request.message?.toLowerCase().includes(filters.search.toLowerCase()) ||
      request.requirements?.toLowerCase().includes(filters.search.toLowerCase())
      
    return statusMatch && searchMatch
  })
})

// Load all ad requests
const loadAdRequests = async () => {
  try {
    loading.value = true
    error.value = ''
    
    const response = await influencerService.getAdRequests()
    adRequests.value = response.data || []
  } catch (err) {
    console.error('Failed to load ad requests:', err)
    error.value = 'Failed to load ad requests. Please try again later.'
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
    day: 'numeric'
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

// Get badge class based on status
const getStatusBadgeClass = (status) => {
  switch (status) {
    case 'Pending': return 'bg-warning'
    case 'Negotiating': return 'bg-info'
    case 'Accepted': return 'bg-success'
    case 'Rejected': return 'bg-danger'
    default: return 'bg-secondary'
  }
}

// Clear filters
const clearFilters = () => {
  filters.status = ''
  filters.search = ''
}

// Load data on component mount
onMounted(() => {
  loadAdRequests()
})
</script>

<template>
  <div class="ad-requests-view py-5">
    <div class="container">
      <div class="d-flex justify-content-between align-items-center mb-4">
        <h1>Ad Requests</h1>
        <nav aria-label="breadcrumb">
          <ol class="breadcrumb mb-0">
            <li class="breadcrumb-item">
              <RouterLink to="/influencer/dashboard">Dashboard</RouterLink>
            </li>
            <li class="breadcrumb-item active">Ad Requests</li>
          </ol>
        </nav>
      </div>
      
      <!-- Error Alert -->
      <div v-if="error" class="alert alert-danger alert-dismissible fade show mb-4" role="alert">
        {{ error }}
        <button type="button" class="btn-close" @click="error = ''"></button>
      </div>
      
      <!-- Filters -->
      <div class="card border-0 shadow-sm mb-4">
        <div class="card-body">
          <h5 class="card-title mb-3">
            <i class="bi bi-funnel me-2"></i>Filter Requests
          </h5>
          <div class="row g-3">
            <div class="col-md-8">
              <div class="input-group">
                <span class="input-group-text">
                  <i class="bi bi-search"></i>
                </span>
                <input 
                  type="text" 
                  class="form-control" 
                  v-model="filters.search" 
                  placeholder="Search by campaign name or content"
                >
              </div>
            </div>
            <div class="col-md-4">
              <select class="form-select" v-model="filters.status">
                <option v-for="option in statusOptions" :key="option.value" :value="option.value">
                  {{ option.label }}
                </option>
              </select>
            </div>
          </div>
          <div class="d-flex justify-content-end mt-3">
            <button class="btn btn-outline-secondary" @click="clearFilters">
              <i class="bi bi-x-circle me-2"></i>Clear Filters
            </button>
          </div>
        </div>
      </div>
      
      <!-- Loading Spinner -->
      <div v-if="loading" class="text-center py-5">
        <div class="spinner-border text-primary" role="status">
          <span class="visually-hidden">Loading...</span>
        </div>
        <p class="mt-3">Loading ad requests...</p>
      </div>
      
      <!-- Empty State -->
      <div v-else-if="adRequests.length === 0" class="card border-0 shadow-sm">
        <div class="card-body text-center py-5">
          <i class="bi bi-inbox fs-1 text-muted mb-3"></i>
          <h3>No Ad Requests</h3>
          <p class="text-muted mb-4">You don't have any ad requests yet.</p>
          <RouterLink to="/influencer/campaigns/browse" class="btn btn-primary">
            Browse Campaigns
          </RouterLink>
        </div>
      </div>
      
      <!-- No Results After Filtering -->
      <div v-else-if="filteredRequests.length === 0" class="card border-0 shadow-sm">
        <div class="card-body text-center py-5">
          <i class="bi bi-search fs-1 text-muted mb-3"></i>
          <h3>No Results Found</h3>
          <p class="text-muted mb-4">No ad requests match your filters.</p>
          <button class="btn btn-primary" @click="clearFilters">
            Clear Filters
          </button>
        </div>
      </div>
      
      <!-- Request List -->
      <div v-else class="row g-4">
        <div v-for="request in filteredRequests" :key="request.id" class="col-md-6">
          <div class="card border-0 shadow-sm h-100">
            <div class="card-header bg-white border-0 py-3">
              <div class="d-flex justify-content-between align-items-center">
                <h5 class="card-title mb-0">{{ request.campaign_name }}</h5>
                <span :class="`badge ${getStatusBadgeClass(request.status)}`">
                  {{ request.status }}
                </span>
              </div>
            </div>
            <div class="card-body">
              <div class="mb-3">
                <div class="row mb-2">
                  <div class="col-6">
                    <span class="text-muted">Offer Amount:</span>
                  </div>
                  <div class="col-6 text-end">
                    <span class="fw-bold">{{ formatCurrency(request.payment_amount) }}</span>
                  </div>
                </div>
                <div class="row mb-2">
                  <div class="col-6">
                    <span class="text-muted">Last Updated:</span>
                  </div>
                  <div class="col-6 text-end">
                    <span>{{ formatDate(request.updated_at) }}</span>
                  </div>
                </div>
                <div class="row">
                  <div class="col-6">
                    <span class="text-muted">Last Action By:</span>
                  </div>
                  <div class="col-6 text-end">
                    <span class="fst-italic">{{ request.last_offer_by || 'N/A' }}</span>
                  </div>
                </div>
              </div>
              
              <h6 class="fw-bold">Requirements:</h6>
              <p class="mb-4">{{ request.requirements?.substring(0, 100) }}{{ request.requirements?.length > 100 ? '...' : '' }}</p>
              
              <div class="d-grid">
                <RouterLink :to="`/influencer/ad-requests/${request.id}`" class="btn btn-primary">
                  View Details
                </RouterLink>
              </div>
            </div>
            <div class="card-footer bg-white text-muted small py-2">
              <i class="bi bi-calendar me-1"></i> Created: {{ formatDate(request.created_at) }}
            </div>
          </div>
        </div>
      </div>
      
      <!-- Help Box (Always visible) -->
      <div class="card bg-light border-0 mt-4">
        <div class="card-body">
          <h5><i class="bi bi-info-circle me-2"></i>Understanding Ad Request Status</h5>
          <div class="row mt-3">
            <div class="col-md-3 mb-2">
              <div class="d-flex align-items-center">
                <span class="badge bg-warning me-2 p-2">&nbsp;</span>
                <div>
                  <strong>Pending</strong>
                  <p class="mb-0 small">Awaiting response</p>
                </div>
              </div>
            </div>
            <div class="col-md-3 mb-2">
              <div class="d-flex align-items-center">
                <span class="badge bg-info me-2 p-2">&nbsp;</span>
                <div>
                  <strong>Negotiating</strong>
                  <p class="mb-0 small">In discussion</p>
                </div>
              </div>
            </div>
            <div class="col-md-3 mb-2">
              <div class="d-flex align-items-center">
                <span class="badge bg-success me-2 p-2">&nbsp;</span>
                <div>
                  <strong>Accepted</strong>
                  <p class="mb-0 small">Ready to proceed</p>
                </div>
              </div>
            </div>
            <div class="col-md-3 mb-2">
              <div class="d-flex align-items-center">
                <span class="badge bg-danger me-2 p-2">&nbsp;</span>
                <div>
                  <strong>Rejected</strong>
                  <p class="mb-0 small">Not moving forward</p>
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
.ad-requests-view {
  animation: fadeIn 0.5s ease-in-out;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}
</style> 