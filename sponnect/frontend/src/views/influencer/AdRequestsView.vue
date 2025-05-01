<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { RouterLink } from 'vue-router'
import { influencerService } from '../../services/api'
import { formatDate, formatCurrency } from '../../utils/formatters'
import { formatDateWithTime } from '../../utils/dateUtils'

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
  { value: '', label: 'All Statuses' },
  { value: 'Pending', label: 'Pending' },
  { value: 'Negotiating', label: 'Negotiating' },
  { value: 'Accepted', label: 'Accepted' },
  { value: 'Rejected', label: 'Rejected' }
]

// Computed property for filtered requests
const filteredRequests = computed(() => {
  if (!adRequests.value.length) return []
  
  return adRequests.value.filter(request => {
    // Status filter
    const statusMatch = !filters.status || request.status === filters.status
    
    // Search filter
    const searchTerm = filters.search.toLowerCase()
    const searchMatch = !searchTerm || 
      (request.campaign_name && request.campaign_name.toLowerCase().includes(searchTerm)) || 
      (request.message && request.message.toLowerCase().includes(searchTerm))
    
    return statusMatch && searchMatch
  })
})

// Load all ad requests
const loadAdRequests = async () => {
  try {
    loading.value = true
    error.value = ''
    
    const response = await influencerService.getAdRequests()
    
    // For the influencer endpoint, the response is a direct array (not nested in an object)
    // Make sure we always have an array
    if (Array.isArray(response.data)) {
      adRequests.value = response.data
    } else {
      console.warn('Expected array response from adRequests endpoint, got:', typeof response.data)
      adRequests.value = []
    }
    
    // Debug log: Check first request's structure and fields
    if (adRequests.value.length > 0) {
      console.log('First ad request data:', adRequests.value[0])
    }
  } catch (err) {
    console.error('Failed to load ad requests:', err)
    error.value = 'Failed to load ad requests. Please try again later.'
  } finally {
    loading.value = false
  }
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

// Format currency
const formatCurrency = (amount) => {
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    minimumFractionDigits: 0
  }).format(amount || 0)
}
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
      
      <!-- Ad Requests Table -->
      <div v-if="filteredRequests.length" class="table-responsive">
        <table class="table table-hover align-middle mb-0">
          <thead class="table-light">
            <tr>
              <th>Campaign</th>
              <th>Offer Amount</th>
              <th>Status</th>
              <th>Last Updated</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="request in filteredRequests" :key="request.id">
              <td>{{ request.campaign_name || 'Unknown Campaign' }}</td>
              <td>{{ formatCurrency(request.payment_amount) }}</td>
              <td>
                <span 
                  :class="`badge rounded-pill ${getStatusBadgeClass(request.status)}`"
                >
                  {{ request.status }}
                </span>
              </td>
              <td>{{ formatDateWithTime(request.updated_at) }}</td>
              <td>
                <router-link 
                  :to="`/influencer/ad-requests/${request.id}`" 
                  class="btn btn-sm btn-outline-primary"
                >
                  View Details
                </router-link>
              </td>
            </tr>
          </tbody>
        </table>
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
