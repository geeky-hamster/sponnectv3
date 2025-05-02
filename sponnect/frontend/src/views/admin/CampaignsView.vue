<script setup>
import { ref, onMounted, watch, computed } from 'vue'
import { adminService } from '../../services/api'
import { formatCurrency } from '../../utils/formatters'
import { formatDate, formatDateWithTime } from '../../utils/dateUtils'

// State
const campaigns = ref([])
const pagination = ref({
  page: 1,
  per_page: 10,
  total_pages: 1,
  total_items: 0
})
const loading = ref(true)
const applyingFilters = ref(false)
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
  budget_max: '',
  flagged: false, // Add flagged filter for admin
  sort: 'created_at_desc' // default sort
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

// Additional filter options
const dateRangeOptions = [
  { value: '', text: 'All Time' },
  { value: 'today', text: 'Today' },
  { value: 'yesterday', text: 'Yesterday' },
  { value: 'this_week', text: 'This Week' },
  { value: 'last_week', text: 'Last Week' },
  { value: 'this_month', text: 'This Month' },
  { value: 'last_month', text: 'Last Month' },
  { value: 'last_3_months', text: 'Last 3 Months' },
  { value: 'last_6_months', text: 'Last 6 Months' },
  { value: 'this_year', text: 'This Year' }
]

const sortOptions = [
  { value: 'created_at_desc', text: 'Newest First', field: 'created_at', order: 'desc' },
  { value: 'created_at_asc', text: 'Oldest First', field: 'created_at', order: 'asc' },
  { value: 'budget_desc', text: 'Budget (High to Low)', field: 'budget', order: 'desc' },
  { value: 'budget_asc', text: 'Budget (Low to High)', field: 'budget', order: 'asc' },
  { value: 'name_asc', text: 'Name (A-Z)', field: 'name', order: 'asc' },
  { value: 'name_desc', text: 'Name (Z-A)', field: 'name', order: 'desc' }
]

// Watch for filter changes with debounce
let debounceTimer
watch(filters, () => {
  clearTimeout(debounceTimer)
  debounceTimer = setTimeout(() => {
    console.log('Filters changed, reloading campaigns with filters:', filters.value);
    loadCampaigns(1) // Reset to page 1 when filters change
  }, 500) // Slightly longer debounce for better UX
}, { deep: true })

const loadCampaigns = async (page = 1) => {
  try {
    loading.value = true;
    error.value = '';
    
    // Prepare query parameters - only include non-empty values
    const params = { page };
    
    if (pagination.value.per_page) {
      params.per_page = pagination.value.per_page;
    }
    
    // Add filter parameters with validation
    if (filters.value.search && filters.value.search.trim()) {
      params.search = filters.value.search.trim();
    }
    
    if (filters.value.status) {
      params.status = filters.value.status;
    }
    
    if (filters.value.sponsor_id && filters.value.sponsor_id.trim()) {
      params.sponsor_id = filters.value.sponsor_id.trim();
    }
    
    if (filters.value.date_range) {
      params.date_range = filters.value.date_range;
    }
    
    // Add flagged filter if true
    if (filters.value.flagged) {
      params.flagged = true;
    }
    
    // Ensure numeric parameters are actually numbers
    if (filters.value.budget_min && !isNaN(parseFloat(filters.value.budget_min))) {
      params.budget_min = parseFloat(filters.value.budget_min);
    }
    
    if (filters.value.budget_max && !isNaN(parseFloat(filters.value.budget_max))) {
      params.budget_max = parseFloat(filters.value.budget_max);
    }
    
    // Add sorting
    if (filters.value.sort) {
      const selectedSort = sortOptions.find(opt => opt.value === filters.value.sort);
      if (selectedSort) {
        params.sort_by = selectedSort.field;
        params.sort_order = selectedSort.order;
      }
    }
    
    console.log('Fetching admin campaigns with params:', params);
    
    // Make API call with all filters applied
    const response = await adminService.getCampaigns(params);
    
    // Process response data
    handleCampaignsResponse(response, page);
    
    console.log(`Loaded ${campaigns.value.length} campaigns after applying filters:`, filters.value);
  } catch (err) {
    handleCampaignsError(err);
  } finally {
    loading.value = false;
  }
}

// Handle successful campaign response
const handleCampaignsResponse = (response, page) => {
  // Log response for debugging
  console.log('Campaign response received:', {
    status: response.status,
    hasData: !!response.data,
    hasCampaigns: response.data && Array.isArray(response.data.campaigns),
    campaignCount: response.data && response.data.campaigns ? response.data.campaigns.length : 0
  });
  
  // Extract campaigns from different response formats
  let campaignData = [];
  let paginationData = null;
  
  if (response.data) {
    if (Array.isArray(response.data)) {
      // Direct array format
      campaignData = response.data;
    } else if (response.data.campaigns && Array.isArray(response.data.campaigns)) {
      // Object with campaigns field (most likely format)
      campaignData = response.data.campaigns;
      if (response.data.pagination) {
        paginationData = response.data.pagination;
      }
    } else if (typeof response.data === 'object' && !Array.isArray(response.data) && response.data.id) {
      // Single campaign object
      campaignData = [response.data];
    } else {
      console.warn('Invalid response format:', response.data);
      campaignData = [];
    }
  }
  
  // Ensure required fields are present with fallbacks
  campaignData = campaignData.map(campaign => {
    return {
      ...campaign,
      name: campaign.name || 'Unnamed Campaign',
      description: campaign.description || '',
      budget: campaign.budget || 0,
      status: campaign.status || 'unknown',
      created_at: campaign.created_at || new Date().toISOString()
    };
  });
  
  // Update state
  campaigns.value = campaignData;
  console.log('Updated campaigns list with filtered results:', campaignData.length);
  
  // Update pagination
  if (paginationData) {
    pagination.value = paginationData;
  } else {
    // Fallback pagination
    pagination.value = {
      page,
      per_page: 10,
      total_pages: Math.ceil(campaignData.length / 10),
      total_items: campaignData.length
    };
  }
  
  // Log the first campaign for debugging
  if (campaignData.length > 0) {
    console.log('Sample campaign data:', campaignData[0]);
  } else {
    console.log('No campaigns returned with the current filters');
  }
}

// Handle campaign loading errors
const handleCampaignsError = (err) => {
  console.error('Error loading campaigns:', err);
  
  // Provide more specific error messages
  if (err.response) {
    const status = err.response.status;
    const errorData = err.response.data;
    
    if (status === 403) {
      error.value = 'You do not have permission to view these campaigns.';
    } else if (status === 400 && errorData && errorData.message) {
      error.value = `Invalid search parameters: ${errorData.message}`;
    } else if (errorData && errorData.message) {
      error.value = errorData.message;
    } else {
      error.value = `Failed to load campaigns (Error ${status}). Please try again.`;
    }
  } else if (err.request) {
    error.value = 'Server did not respond. Please check your connection and try again.';
  } else {
    error.value = `Failed to load campaigns: ${err.message}`;
  }
  
  // Reset data on error
  campaigns.value = [];
  pagination.value = { page: 1, per_page: 10, total_pages: 1, total_items: 0 };
}

onMounted(() => {
  loadCampaigns()
})

const applyFilters = async () => {
  console.log('Explicitly applying filters:', filters.value);
  applyingFilters.value = true;
  
  // Force reload with current filters by passing page 1
  await loadCampaigns(1); 
  
  applyingFilters.value = false;
  console.log('Filters applied, loaded campaigns count:', campaigns.value.length);
}

const resetFilters = () => {
  // Reset all filters to default values
  filters.value = {
    search: '',
    status: '',
    sponsor_id: '',
    date_range: '',
    budget_min: '',
    budget_max: '',
    flagged: false,
    sort: 'created_at_desc' // default sort
  };
  
  // Reload campaigns without filters
  loadCampaigns(1);
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
      return `Are you sure you want to approve the campaign "${campaign.name}"? This will make it visible to influencers.`
    case 'reject': 
      return `Are you sure you want to reject the campaign "${campaign.name}"? The sponsor will be notified.`
    case 'pause': 
      return `Are you sure you want to pause the campaign "${campaign.name}"? This will temporarily hide it from influencers.`
    case 'activate': 
      return `Are you sure you want to activate the campaign "${campaign.name}"? This will make it visible to influencers.`
    case 'feature': 
      return `Are you sure you want to feature the campaign "${campaign.name}"? This will show it prominently to influencers.`
    case 'unfeature': 
      return `Are you sure you want to remove the featured status from "${campaign.name}"?`
    default: 
      return 'Are you sure you want to perform this action?'
  }
}

const cancelAction = () => {
  confirmAction.value = null
}

function getCampaignStatusBadge(status) {
  // Convert status to lowercase string for more robust comparison
  const statusLower = String(status || '').toLowerCase();
  
  // Map of status values to display text and badge classes
  const statusMap = {
    'draft': { text: 'Draft', class: 'bg-secondary' },
    'pending_approval': { text: 'Pending Approval', class: 'bg-warning' },
    'pending': { text: 'Pending Approval', class: 'bg-warning' },
    'active': { text: 'Active', class: 'bg-success' },
    'paused': { text: 'Paused', class: 'bg-info' },
    'completed': { text: 'Completed', class: 'bg-primary' },
    'rejected': { text: 'Rejected', class: 'bg-danger' }
  };
  
  // Return mapped value or default
  return statusMap[statusLower] || {
    text: status ? (String(status).charAt(0).toUpperCase() + String(status).slice(1)) : 'Unknown',
    class: 'bg-secondary'
  };
}

// Helper function to check if campaign can be paused
function canPauseCampaign(campaign) {
  return campaign && campaign.status && 
    (campaign.status.toLowerCase() === 'active' || 
     campaign.status.toLowerCase() === 'pending_approval');
}

// Helper function to check if campaign can be activated
function canActivateCampaign(campaign) {
  return campaign && campaign.status && 
    (campaign.status.toLowerCase() === 'paused' || 
     campaign.status.toLowerCase() === 'rejected' ||
     campaign.status.toLowerCase() === 'draft');
}

// Helper function to check if campaign can be featured
function canFeatureCampaign(campaign) {
  return campaign && campaign.status && 
    campaign.status.toLowerCase() === 'active' && 
    !campaign.is_featured;
}

// Helper function to check if campaign can be unfeatured
function canUnfeatureCampaign(campaign) {
  return campaign && campaign.is_featured;
}

const executeAction = async () => {
  if (!confirmAction.value) return;
  
  const { type, campaign } = confirmAction.value;
  
  try {
    loading.value = true;
    error.value = '';
    success.value = '';
    
    console.log(`Executing action ${type} on campaign ID ${campaign.id}`);
    
    let response;
    let newStatus;
    let newFeatured;
    
    switch (type) {
      case 'approve':
        response = await adminService.approveCampaign(campaign.id);
        success.value = `Campaign "${campaign.name}" has been approved`;
        newStatus = 'active';
        break;
      case 'reject':
        response = await adminService.rejectCampaign(campaign.id);
        success.value = `Campaign "${campaign.name}" has been rejected`;
        newStatus = 'rejected';
        break;
      case 'pause':
        response = await adminService.pauseCampaign(campaign.id);
        success.value = `Campaign "${campaign.name}" has been paused`;
        newStatus = 'paused';
        break;
      case 'activate':
        response = await adminService.activateCampaign(campaign.id);
        success.value = `Campaign "${campaign.name}" has been activated`;
        newStatus = 'active';
        break;
      case 'feature':
        response = await adminService.featureCampaign(campaign.id);
        success.value = `Campaign "${campaign.name}" has been featured`;
        newFeatured = true;
        break;
      case 'unfeature':
        response = await adminService.unfeatureCampaign(campaign.id);
        success.value = `Campaign "${campaign.name}" has been unfeatured`;
        newFeatured = false;
        break;
    }
    
    console.log(`Action ${type} response:`, response);
    
    // Apply optimistic update for immediate feedback
    const campaignIndex = campaigns.value.findIndex(c => c.id === campaign.id);
    if (campaignIndex !== -1) {
      if (newStatus) {
        campaigns.value[campaignIndex].status = newStatus;
      }
      if (newFeatured !== undefined) {
        campaigns.value[campaignIndex].is_featured = newFeatured;
      }
    }
    
    // Refresh the list after a short delay
    setTimeout(() => {
      loadCampaigns(pagination.page);
    }, 500);
  } catch (err) {
    console.error(`Error executing action ${type}:`, err);
    
    // Provide more specific error messages based on error type
    if (err.response) {
      const status = err.response.status;
      const errorData = err.response.data;
      
      if (status === 403) {
        error.value = 'You do not have permission to perform this action.';
      } else if (status === 404) {
        error.value = 'The campaign could not be found.';
      } else if (errorData && errorData.message) {
        error.value = errorData.message;
      } else {
        error.value = `Failed to ${type} campaign (Error ${status}). Please try again.`;
      }
    } else if (err.request) {
      error.value = 'No response from server. Please check your connection and try again.';
    } else {
      error.value = `Failed to ${type} campaign: ${err.message}`;
    }
  } finally {
    loading.value = false;
    confirmAction.value = null;
  }
}

const viewCampaignDetails = (campaign) => {
  selectedCampaign.value = campaign
  showDetailsModal.value = true
}

// Get active filter count
const activeFilterCount = computed(() => {
  let count = 0;
  if (filters.value.search) count++;
  if (filters.value.status) count++;
  if (filters.value.sponsor_id) count++;
  if (filters.value.date_range) count++;
  if (filters.value.budget_min) count++;
  if (filters.value.budget_max) count++;
  if (filters.value.flagged) count++;
  if (filters.value.sort && filters.value.sort !== 'created_at_desc') count++;
  return count;
})
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
            <i class="bi bi-funnel me-2"></i>Filter Campaigns
            <span v-if="activeFilterCount > 0" class="badge rounded-pill bg-primary ms-2">
              {{ activeFilterCount }} active
            </span>
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
                  placeholder="Campaign name or description"
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
              <label for="sponsor" class="form-label">Sponsor ID</label>
              <input 
                type="text" 
                class="form-control" 
                id="sponsor" 
                v-model="filters.sponsor_id"
                placeholder="Enter sponsor ID"
              >
            </div>
            
            <div class="col-md-4">
              <label for="date-range" class="form-label">Date Range</label>
              <select class="form-select" id="date-range" v-model="filters.date_range">
                <option 
                  v-for="option in dateRangeOptions" 
                  :key="option.value" 
                  :value="option.value"
                >
                  {{ option.text }}
                </option>
              </select>
            </div>
            
            <div class="col-md-3">
              <label for="budget-min" class="form-label">Min Budget (₹)</label>
              <input 
                type="number" 
                class="form-control" 
                id="budget-min" 
                v-model="filters.budget_min"
                placeholder="Minimum"
                min="0"
              >
            </div>
            
            <div class="col-md-3">
              <label for="budget-max" class="form-label">Max Budget (₹)</label>
              <input 
                type="number" 
                class="form-control" 
                id="budget-max" 
                v-model="filters.budget_max"
                placeholder="Maximum"
                min="0"
              >
            </div>
            
            <div class="col-md-2">
              <label class="form-label d-block">Show Flagged</label>
              <div class="form-check form-switch mt-2">
                <input 
                  class="form-check-input" 
                  type="checkbox" 
                  id="flagged-filter"
                  v-model="filters.flagged"
                >
                <label class="form-check-label" for="flagged-filter">
                  <span v-if="filters.flagged" class="text-danger">Flagged Only</span>
                  <span v-else class="text-muted">All Campaigns</span>
                </label>
              </div>
            </div>
          </div>
          
          <div class="row mt-3">
            <div class="col-md-8">
              <label for="sort-by" class="form-label">Sort By</label>
              <select class="form-select" id="sort-by" v-model="filters.sort">
                <option 
                  v-for="option in sortOptions" 
                  :key="option.value" 
                  :value="option.value"
                >
                  {{ option.text }}
                </option>
              </select>
            </div>
            
            <div class="col-md-4 d-flex align-items-end">
              <div class="d-grid gap-2 d-md-flex">
                <button 
                  class="btn btn-primary" 
                  @click="applyFilters" 
                  :disabled="applyingFilters"
                >
                  <span v-if="applyingFilters">
                    <span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>
                    Applying...
                  </span>
                  <span v-else>
                    <i class="bi bi-funnel-fill me-1"></i>
                    Apply Filters
                  </span>
                </button>
                <button 
                  class="btn btn-outline-secondary" 
                  @click="resetFilters"
                  v-if="activeFilterCount > 0"
                >
                  <i class="bi bi-x-circle me-1"></i>
                  Clear Filters
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <!-- Campaign List -->
      <div class="card border-0 shadow-sm overflow-hidden">
        <div class="card-header bg-white d-flex justify-content-between align-items-center py-3">
          <h5 class="mb-0">
            Campaign List 
            <span v-if="activeFilterCount > 0" class="badge rounded-pill bg-primary ms-2">
              Filtered
            </span>
            <span class="text-muted fs-6 ms-2">
              <span v-if="loading">
                <div class="spinner-border spinner-border-sm text-primary me-1" role="status">
                  <span class="visually-hidden">Loading...</span>
                </div>
                Loading...
              </span>
              <span v-else-if="campaigns.length === 0">No campaigns found</span>
              <span v-else>
                Showing {{ campaigns.length }} of {{ pagination.total_items || 0 }} campaigns
                <span v-if="activeFilterCount > 0">
                  <i class="bi bi-funnel-fill text-primary ms-1"></i>
                </span>
              </span>
            </span>
          </h5>
          <div class="btn-group">
            <button 
              class="btn btn-outline-secondary btn-sm" 
              @click="loadCampaigns(pagination.page - 1)"
              :disabled="pagination.page <= 1 || loading"
            >
              <i class="bi bi-chevron-left"></i>
            </button>
            <button class="btn btn-outline-secondary btn-sm" disabled>
              Page {{ pagination.page }} of {{ pagination.total_pages || 1 }}
            </button>
            <button 
              class="btn btn-outline-secondary btn-sm" 
              @click="loadCampaigns(pagination.page + 1)"
              :disabled="pagination.page >= pagination.total_pages || loading"
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
            <div class="py-4">
              <i class="bi bi-search fs-1 text-muted"></i>
              <p class="mt-3 mb-0 text-muted">No campaigns found matching your filters.</p>
              <button class="btn btn-outline-primary mt-3" @click="resetFilters">
                <i class="bi bi-x-circle me-1"></i>Clear All Filters
              </button>
            </div>
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
                        <div class="bg-light rounded d-flex align-items-center justify-content-center" style="width: 40px; height: 40px;">
                          <i class="bi bi-briefcase text-secondary"></i>
                        </div>
                      </div>
                      <div>
                        <div class="fw-semibold text-truncate" style="max-width: 200px;">
                          {{ campaign.name }}
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
                    <button class="btn btn-sm btn-primary" @click="viewCampaignDetails(campaign)">
                      <i class="bi bi-eye me-2"></i>View
                    </button>
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
                    <h4>{{ selectedCampaign.name }}</h4>
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
                        <strong>Start:</strong> {{ formatDate(selectedCampaign.start_date) }}
                      </div>
                      <div>
                        <strong>End:</strong> {{ formatDate(selectedCampaign.end_date) }}
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
