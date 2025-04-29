<script setup>
import { ref, onMounted, watch } from 'vue'
import { adminService } from '../../services/api'
import { formatCurrency, formatDate } from '../../utils/formatters'

// State
const campaigns = ref([])
const pagination = ref({
  page: 1,
  per_page: 10,
  total_pages: 1,
  total_items: 0
})
const loading = ref(true)
const error = ref('')
const success = ref('')
const confirmAction = ref(null)
const selectedCampaign = ref(null)
const showDetailsModal = ref(false)

// Filters
const filters = ref({
  search: '',
  status: '',
  sponsor_id: '',
  date_range: '',
  budget_min: '',
  budget_max: ''
})

const campaignStatusOptions = [
  { value: '', text: 'All Statuses' },
  { value: 'draft', text: 'Draft' },
  { value: 'pending_approval', text: 'Pending Approval' },
  { value: 'active', text: 'Active' },
  { value: 'paused', text: 'Paused' },
  { value: 'completed', text: 'Completed' },
  { value: 'rejected', text: 'Rejected' }
]

const loadCampaigns = async (page = 1) => {
  try {
    loading.value = true
    error.value = ''
    
    // Prepare query parameters
    const params = {
      page,
      per_page: pagination.value.per_page,
      ...filters.value
    }
    
    // Remove empty filters
    Object.keys(params).forEach(key => {
      if (params[key] === '') {
        delete params[key]
      }
    })
    
    const response = await adminService.getCampaigns(params)
    campaigns.value = response.data.campaigns
    pagination.value = response.data.pagination
  } catch (err) {
    console.error('Error loading campaigns:', err)
    error.value = 'Failed to load campaigns. Please try again.'
  } finally {
    loading.value = false
  }
}

// Watch for filter changes with debounce
let debounceTimer
watch(filters, () => {
  clearTimeout(debounceTimer)
  debounceTimer = setTimeout(() => {
    loadCampaigns(1) // Reset to page 1 when filters change
  }, 300)
}, { deep: true })

onMounted(() => {
  loadCampaigns()
})

const clearFilters = () => {
  filters.value = {
    search: '',
    status: '',
    sponsor_id: '',
    date_range: '',
    budget_min: '',
    budget_max: ''
  }
}

// Campaign actions
const showConfirmation = (action, campaign) => {
  confirmAction.value = {
    type: action,
    campaign,
    title: getActionTitle(action),
    message: getActionMessage(action, campaign)
  }
}

const getActionTitle = (action) => {
  switch (action) {
    case 'approve': return 'Approve Campaign'
    case 'reject': return 'Reject Campaign'
    case 'pause': return 'Pause Campaign'
    case 'activate': return 'Activate Campaign'
    case 'feature': return 'Feature Campaign'
    case 'unfeature': return 'Unfeature Campaign'
    default: return 'Confirm Action'
  }
}

const getActionMessage = (action, campaign) => {
  switch (action) {
    case 'approve': 
      return `Are you sure you want to approve the campaign "${campaign.title || campaign.name}"? This will make it visible to influencers.`
    case 'reject': 
      return `Are you sure you want to reject the campaign "${campaign.title || campaign.name}"? The sponsor will be notified.`
    case 'pause': 
      return `Are you sure you want to pause the campaign "${campaign.title || campaign.name}"? This will temporarily hide it from influencers.`
    case 'activate': 
      return `Are you sure you want to activate the campaign "${campaign.title || campaign.name}"? This will make it visible to influencers.`
    case 'feature': 
      return `Are you sure you want to feature the campaign "${campaign.title || campaign.name}"? This will show it prominently to influencers.`
    case 'unfeature': 
      return `Are you sure you want to remove the featured status from "${campaign.title || campaign.name}"?`
    default: 
      return 'Are you sure you want to perform this action?'
  }
}

const cancelAction = () => {
  confirmAction.value = null
}

const executeAction = async () => {
  if (!confirmAction.value) return
  
  const { type, campaign } = confirmAction.value
  
  try {
    loading.value = true
    error.value = ''
    success.value = ''
    
    switch (type) {
      case 'approve':
        await adminService.approveCampaign(campaign.id)
        success.value = `Campaign "${campaign.title || campaign.name}" has been approved`
        break
      case 'reject':
        await adminService.rejectCampaign(campaign.id)
        success.value = `Campaign "${campaign.title || campaign.name}" has been rejected`
        break
      case 'pause':
        await adminService.pauseCampaign(campaign.id)
        success.value = `Campaign "${campaign.title || campaign.name}" has been paused`
        break
      case 'activate':
        await adminService.activateCampaign(campaign.id)
        success.value = `Campaign "${campaign.title || campaign.name}" has been activated`
        break
      case 'feature':
        await adminService.featureCampaign(campaign.id)
        success.value = `Campaign "${campaign.title || campaign.name}" has been featured`
        break
      case 'unfeature':
        await adminService.unfeatureCampaign(campaign.id)
        success.value = `Campaign "${campaign.title || campaign.name}" has been unfeatured`
        break
    }
    
    // Refresh the list
    loadCampaigns(pagination.value.page)
  } catch (err) {
    console.error(`Error executing action ${type}:`, err)
    error.value = `Failed to ${type} campaign. Please try again.`
  } finally {
    loading.value = false
    confirmAction.value = null
  }
}

const getCampaignStatusBadge = (status) => {
  switch (status) {
    case 'draft':
      return { text: 'Draft', class: 'bg-secondary' }
    case 'pending_approval':
      return { text: 'Pending Approval', class: 'bg-warning' }
    case 'active':
      return { text: 'Active', class: 'bg-success' }
    case 'paused':
      return { text: 'Paused', class: 'bg-info' }
    case 'completed':
      return { text: 'Completed', class: 'bg-primary' }
    case 'rejected':
      return { text: 'Rejected', class: 'bg-danger' }
    default:
      return { text: status, class: 'bg-secondary' }
  }
}

const viewCampaignDetails = (campaign) => {
  selectedCampaign.value = campaign
  showDetailsModal.value = true
}

// Format date with time
const formatDateWithTime = (dateString) => {
  if (!dateString) return 'N/A';
  
  try {
    // For debugging
    console.log('Date string:', dateString);
    
    // Handle different date formats
    const date = new Date(dateString);
    
    // Check if date is valid
    if (isNaN(date.getTime())) {
      console.log('Invalid date:', dateString);
      return 'N/A';
    }
    
    return date.toLocaleString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  } catch (error) {
    console.error('Error formatting date:', error);
    return 'N/A';
  }
}
</script>

<template>
  <div class="admin-campaigns py-5">
    <div class="container">
      <div class="d-flex justify-content-between align-items-center mb-4">
        <h1>Manage Campaigns</h1>
        <nav aria-label="breadcrumb">
          <ol class="breadcrumb mb-0">
            <li class="breadcrumb-item">
              <router-link to="/admin/dashboard">Dashboard</router-link>
            </li>
            <li class="breadcrumb-item active">Campaigns</li>
          </ol>
        </nav>
      </div>
      
      <!-- Alert Messages -->
      <div v-if="error" class="alert alert-danger alert-dismissible fade show" role="alert">
        {{ error }}
        <button type="button" class="btn-close" @click="error = ''"></button>
      </div>
      
      <div v-if="success" class="alert alert-success alert-dismissible fade show" role="alert">
        {{ success }}
        <button type="button" class="btn-close" @click="success = ''"></button>
      </div>
      
      <!-- Filters -->
      <div class="card border-0 shadow-sm mb-4">
        <div class="card-body">
          <h5 class="card-title mb-3">
            <i class="bi bi-funnel me-2"></i>Search Campaigns
          </h5>
          
          <div class="row g-3">
            <div class="col-md-4">
              <label for="search" class="form-label">Search</label>
              <div class="input-group">
                <span class="input-group-text">
                  <i class="bi bi-search"></i>
                </span>
                <input 
                  type="text" 
                  class="form-control" 
                  id="search" 
                  v-model="filters.search"
                  placeholder="Campaign title, description..."
                >
              </div>
            </div>
            
            <div class="col-md-4">
              <label for="status" class="form-label">Status</label>
              <select class="form-select" id="status" v-model="filters.status">
                <option 
                  v-for="option in campaignStatusOptions" 
                  :key="option.value" 
                  :value="option.value"
                >
                  {{ option.text }}
                </option>
              </select>
            </div>
            
            <div class="col-md-4">
              <label for="sponsor" class="form-label">Sponsor</label>
              <input 
                type="text" 
                class="form-control" 
                id="sponsor" 
                v-model="filters.sponsor_id"
                placeholder="Sponsor ID"
              >
            </div>
            
            <div class="col-md-4">
              <label for="date-range" class="form-label">Date Range</label>
              <select class="form-select" id="date-range" v-model="filters.date_range">
                <option value="">All Time</option>
                <option value="today">Today</option>
                <option value="yesterday">Yesterday</option>
                <option value="this_week">This Week</option>
                <option value="last_week">Last Week</option>
                <option value="this_month">This Month</option>
                <option value="last_month">Last Month</option>
              </select>
            </div>
            
            <div class="col-md-4">
              <label for="budget-min" class="form-label">Min Budget</label>
              <div class="input-group">
                <span class="input-group-text">₹</span>
                <input 
                  type="number" 
                  class="form-control" 
                  id="budget-min" 
                  v-model="filters.budget_min"
                  placeholder="Min"
                >
              </div>
            </div>
            
            <div class="col-md-4">
              <label for="budget-max" class="form-label">Max Budget</label>
              <div class="input-group">
                <span class="input-group-text">₹</span>
                <input 
                  type="number" 
                  class="form-control" 
                  id="budget-max" 
                  v-model="filters.budget_max"
                  placeholder="Max"
                >
              </div>
            </div>
          </div>
          
          <div class="d-flex justify-content-end mt-3">
            <button class="btn btn-outline-secondary" @click="clearFilters">
              <i class="bi bi-x-circle me-2"></i>Clear Filters
            </button>
          </div>
        </div>
      </div>
      
      <!-- Campaign List -->
      <div class="card border-0 shadow-sm overflow-hidden">
        <div class="card-header bg-white d-flex justify-content-between align-items-center py-3">
          <h5 class="mb-0">Campaign List <span class="text-muted fs-6">({{ campaigns.length }} of {{ pagination.total_items || 0 }} campaigns)</span></h5>
          <div class="btn-group">
            <button 
              class="btn btn-outline-secondary btn-sm" 
              @click="loadCampaigns(pagination.page - 1)"
              :disabled="pagination.page === 1 || loading"
            >
              <i class="bi bi-chevron-left"></i>
            </button>
            <button class="btn btn-outline-secondary btn-sm" disabled>
              Page {{ pagination.page }} of {{ pagination.total_pages }}
            </button>
            <button 
              class="btn btn-outline-secondary btn-sm" 
              @click="loadCampaigns(pagination.page + 1)"
              :disabled="pagination.page === pagination.total_pages || loading"
            >
              <i class="bi bi-chevron-right"></i>
            </button>
          </div>
        </div>
        <div class="card-body p-0">
          <div v-if="loading && !campaigns.length" class="text-center py-5">
            <div class="spinner-border text-primary" role="status">
              <span class="visually-hidden">Loading...</span>
            </div>
            <p class="mt-3">Loading campaigns...</p>
          </div>
          
          <div v-else-if="!campaigns.length" class="p-4 text-center">
            <p class="mb-0">No campaigns found matching your filters.</p>
          </div>
          
          <div v-else class="table-responsive">
            <table class="table table-hover align-middle mb-0">
              <thead class="table-light">
                <tr>
                  <th>Title</th>
                  <th>Sponsor</th>
                  <th>Status</th>
                  <th>Budget</th>
                  <th>Created</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="campaign in campaigns" :key="campaign.id" :class="{ 'table-info': campaign.is_featured }">
                  <td>
                    <div class="d-flex align-items-center">
                      <div class="campaign-icon me-2">
                        <img 
                          v-if="campaign.image_url" 
                          :src="campaign.image_url" 
                          alt="Campaign" 
                          class="img-fluid rounded" 
                          style="width: 40px; height: 40px; object-fit: cover;"
                        >
                        <div v-else class="bg-light rounded d-flex align-items-center justify-content-center" style="width: 40px; height: 40px;">
                          <i class="bi bi-briefcase text-secondary"></i>
                        </div>
                      </div>
                      <div>
                        <div class="fw-semibold text-truncate" style="max-width: 200px;">
                          {{ campaign.title || campaign.name }}
                          <i v-if="campaign.is_featured" class="bi bi-star-fill text-warning ms-2" title="Featured"></i>
                        </div>
                        <small class="text-muted">ID: {{ campaign.id }}</small>
                      </div>
                    </div>
                  </td>
                  <td>
                    <div class="text-truncate" style="max-width: 150px;">
                      {{ campaign.sponsor_name || 'Unknown' }}
                    </div>
                    <small class="text-muted">ID: {{ campaign.sponsor_id }}</small>
                  </td>
                  <td>
                    <span 
                      class="badge rounded-pill" 
                      :class="getCampaignStatusBadge(campaign.status).class"
                    >
                      {{ getCampaignStatusBadge(campaign.status).text }}
                    </span>
                  </td>
                  <td>
                    <div>{{ formatCurrency(campaign.budget) }}</div>
                    <small class="text-muted">per influencer</small>
                  </td>
                  <td>{{ formatDateWithTime(campaign.created_at) }}</td>
                  <td>
                    <div class="dropdown">
                      <button class="btn btn-sm btn-outline-secondary dropdown-toggle" type="button" data-bs-toggle="dropdown">
                        Actions
                      </button>
                      <ul class="dropdown-menu">
                        <li>
                          <button class="dropdown-item" @click="viewCampaignDetails(campaign)">
                            <i class="bi bi-eye me-2"></i>View Details
                          </button>
                        </li>
                        
                        <!-- Status actions -->
                        <li v-if="campaign.status === 'pending_approval'">
                          <button class="dropdown-item" @click="showConfirmation('approve', campaign)">
                            <i class="bi bi-check-circle text-success me-2"></i>Approve
                          </button>
                          <button class="dropdown-item" @click="showConfirmation('reject', campaign)">
                            <i class="bi bi-x-circle text-danger me-2"></i>Reject
                          </button>
                        </li>
                        
                        <li v-if="campaign.status === 'active'">
                          <button class="dropdown-item" @click="showConfirmation('pause', campaign)">
                            <i class="bi bi-pause-circle text-warning me-2"></i>Pause
                          </button>
                        </li>
                        
                        <li v-if="campaign.status === 'paused' || campaign.status === 'rejected'">
                          <button class="dropdown-item" @click="showConfirmation('activate', campaign)">
                            <i class="bi bi-play-circle text-success me-2"></i>Activate
                          </button>
                        </li>
                      </ul>
                    </div>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
      
      <!-- Confirmation Modal -->
      <div 
        class="modal fade" 
        id="confirmationModal" 
        tabindex="-1" 
        role="dialog"
        :class="{ show: confirmAction }"
        :style="{ display: confirmAction ? 'block' : 'none', backgroundColor: confirmAction ? 'rgba(0,0,0,0.5)' : '' }"
        aria-hidden="true"
      >
        <div class="modal-dialog modal-dialog-centered">
          <div class="modal-content">
            <div class="modal-header">
              <h5 class="modal-title">{{ confirmAction?.title }}</h5>
              <button type="button" class="btn-close" @click="cancelAction"></button>
            </div>
            <div class="modal-body">
              <p>{{ confirmAction?.message }}</p>
            </div>
            <div class="modal-footer">
              <button type="button" class="btn btn-secondary" @click="cancelAction">
                Cancel
              </button>
              <button 
                type="button" 
                class="btn" 
                :class="confirmAction?.type.includes('reject') ? 'btn-danger' : 'btn-primary'"
                @click="executeAction"
              >
                Confirm
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Campaign Details Modal -->
      <div 
        class="modal fade" 
        tabindex="-1" 
        role="dialog"
        :class="{ show: showDetailsModal }"
        :style="{ display: showDetailsModal ? 'block' : 'none', backgroundColor: showDetailsModal ? 'rgba(0,0,0,0.5)' : '' }"
        aria-hidden="true"
      >
        <div class="modal-dialog modal-dialog-centered modal-lg">
          <div class="modal-content">
            <div class="modal-header">
              <h5 class="modal-title">Campaign Details</h5>
              <button type="button" class="btn-close" @click="showDetailsModal = false"></button>
            </div>
            <div class="modal-body" v-if="selectedCampaign">
              <div class="row">
                <div class="col-md-8">
                  <div class="mb-4">
                    <h4>{{ selectedCampaign.title || selectedCampaign.name }}</h4>
                    <span 
                      class="badge rounded-pill" 
                      :class="getCampaignStatusBadge(selectedCampaign.status).class"
                    >
                      {{ getCampaignStatusBadge(selectedCampaign.status).text }}
                    </span>
                    <span v-if="selectedCampaign.is_featured" class="badge bg-warning ms-2">Featured</span>
                  </div>
                  
                  <div class="mb-3">
                    <h6 class="text-muted">Description</h6>
                    <p>{{ selectedCampaign.description || 'No description provided.' }}</p>
                  </div>
                  
                  <div class="mb-3">
                    <h6 class="text-muted">Goals</h6>
                    <p>{{ selectedCampaign.goals || 'No goals specified.' }}</p>
                  </div>
                </div>
                
                <div class="col-md-4">
                  <div class="card mb-3">
                    <div class="card-body">
                      <h6 class="text-muted mb-2">Budget</h6>
                      <div class="fw-bold fs-4">{{ formatCurrency(selectedCampaign.budget) }}</div>
                      <div class="text-muted small">per influencer</div>
                    </div>
                  </div>
                  
                  <div class="card mb-3">
                    <div class="card-body">
                      <h6 class="text-muted mb-2">Sponsor</h6>
                      <div>{{ selectedCampaign.sponsor_name || 'Unknown' }}</div>
                      <div class="text-muted small">ID: {{ selectedCampaign.sponsor_id }}</div>
                    </div>
                  </div>
                  
                  <div class="card">
                    <div class="card-body">
                      <h6 class="text-muted mb-2">Dates</h6>
                      <div class="mb-1">
                        <strong>Created:</strong> {{ formatDateWithTime(selectedCampaign.created_at) }}
                      </div>
                      <div class="mb-1">
                        <strong>Start:</strong> {{ formatDate(selectedCampaign.start_date) || 'Not set' }}
                      </div>
                      <div>
                        <strong>End:</strong> {{ formatDate(selectedCampaign.end_date) || 'Not set' }}
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            <div class="modal-footer">
              <button type="button" class="btn btn-secondary" @click="showDetailsModal = false">
                Close
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template> 