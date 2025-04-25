<script setup>
import { ref, onMounted, watch } from 'vue'
import { sponsorService } from '../../services/api'
import { RouterLink } from 'vue-router'

// State
const loading = ref(true)
const adRequests = ref([])
const filteredRequests = ref([])
const error = ref('')
const statusFilter = ref('all')
const searchQuery = ref('')

// Status options
const statusOptions = [
  { value: 'all', label: 'All Statuses' },
  { value: 'Pending', label: 'Pending' },
  { value: 'Negotiating', label: 'Negotiating' },
  { value: 'Accepted', label: 'Accepted' },
  { value: 'Rejected', label: 'Rejected' }
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
  return new Date(dateString).toLocaleDateString('en-US', {
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

// Delete ad request
const deleteAdRequest = async (id) => {
  if (!confirm('Are you sure you want to delete this ad request?')) return
  
  try {
    await sponsorService.deleteAdRequest(id)
    // Remove from local state
    adRequests.value = adRequests.value.filter(r => r.id !== id)
    applyFilters()
  } catch (err) {
    console.error('Failed to delete ad request:', err)
    error.value = 'Failed to delete ad request. Please try again later.'
  }
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
                    <th>Influencer</th>
                    <th>Campaign</th>
                    <th>Payment</th>
                    <th>Status</th>
                    <th>Updated</th>
                    <th>Last Action By</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="request in filteredRequests" :key="request.id">
                    <td>{{ request.influencer_name }}</td>
                    <td>{{ request.campaign_name }}</td>
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
                    </td>
                    <td>{{ formatDate(request.updated_at) }}</td>
                    <td>{{ request.last_offer_by }}</td>
                    <td>
                      <div class="btn-group">
                        <RouterLink :to="`/sponsor/ad-requests/${request.id}`" class="btn btn-sm btn-outline-primary">
                          View
                        </RouterLink>
                        <button 
                          v-if="request.status === 'Pending' || request.status === 'Rejected'" 
                          @click="deleteAdRequest(request.id)" 
                          class="btn btn-sm btn-outline-danger"
                        >
                          Delete
                        </button>
                      </div>
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