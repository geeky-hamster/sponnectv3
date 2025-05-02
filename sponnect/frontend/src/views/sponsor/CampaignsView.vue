<script setup>
import { ref, onMounted, watch } from 'vue'
import { sponsorService } from '../../services/api'
import { RouterLink } from 'vue-router'

// State
const loading = ref(true)
const campaigns = ref([])
const filteredCampaigns = ref([])
const error = ref('')
const searchQuery = ref('')
const visibilityFilter = ref('all')
const statusFilter = ref('all')

// Load campaigns
const loadCampaigns = async () => {
  loading.value = true
  error.value = ''
  
  try {
    const response = await sponsorService.getCampaigns()
    campaigns.value = response.data || []
    applyFilters()
  } catch (err) {
    console.error('Failed to load campaigns:', err)
    error.value = 'Failed to load campaigns. Please try again later.'
  } finally {
    loading.value = false
  }
}

// Check if campaign is expired
const isExpired = (campaign) => {
  if (!campaign || !campaign.end_date_iso) return false
  
  const endDate = new Date(campaign.end_date_iso)
  const now = new Date()
  
  return endDate < now && campaign.status !== 'completed'
}

// Get status display text
const getStatusText = (campaign) => {
  if (!campaign) return ''
  
  if (isExpired(campaign) && campaign.status === 'active') {
    return 'Expired'
  }
  
  switch (campaign.status) {
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
      return campaign.status
  }
}

// Get status badge class
const getStatusBadgeClass = (campaign) => {
  if (!campaign) return 'bg-secondary'
  
  if (isExpired(campaign) && campaign.status === 'active') {
    return 'bg-warning'
  }
  
  switch (campaign.status) {
    case 'active':
      return 'bg-success'
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
}

// Filter campaigns
const applyFilters = () => {
  filteredCampaigns.value = campaigns.value.filter(campaign => {
    // Apply search filter
    const matchesSearch = searchQuery.value === '' || 
      campaign.name.toLowerCase().includes(searchQuery.value.toLowerCase()) ||
      (campaign.description && campaign.description.toLowerCase().includes(searchQuery.value.toLowerCase()))
    
    // Apply visibility filter
    const matchesVisibility = visibilityFilter.value === 'all' || 
      (visibilityFilter.value === 'public' && campaign.visibility === 'public') ||
      (visibilityFilter.value === 'private' && campaign.visibility === 'private')
    
    // Apply status filter
    let matchesStatus = true;
    if (statusFilter.value !== 'all') {
      if (statusFilter.value === 'expired') {
        matchesStatus = isExpired(campaign)
      } else if (statusFilter.value === 'active_current') {
        matchesStatus = campaign.status === 'active' && !isExpired(campaign)
      } else {
        matchesStatus = campaign.status === statusFilter.value
      }
    }
    
    return matchesSearch && matchesVisibility && matchesStatus
  })
}

// Format date for display
const formatDate = (dateString) => {
  if (!dateString) return "N/A"
  
  try {
    // Handle different date formats - try ISO string first
    let date;
    
    // If we have the ISO version, prefer using that
    if (typeof dateString === 'string') {
      // Add logging to debug
      console.log(`Formatting date string: ${dateString}`);
      
      // Try to handle DD-MM-YYYY format
      if (dateString.includes('-') && !dateString.includes('T')) {
        const parts = dateString.split('-');
        if (parts.length === 3) {
          // Check if it's DD-MM-YYYY format
          const firstPart = parseInt(parts[0], 10);
          if (firstPart <= 31) {
            // It's likely DD-MM-YYYY format
            const day = firstPart;
            const month = parseInt(parts[1], 10) - 1;
            const year = parseInt(parts[2], 10);
            date = new Date(year, month, day);
          } else {
            // It's likely YYYY-MM-DD format
            const year = firstPart;
            const month = parseInt(parts[1], 10) - 1;
            const day = parseInt(parts[2], 10);
            date = new Date(year, month, day);
          }
        } else {
          date = new Date(dateString);
        }
      } else {
        date = new Date(dateString);
      }
    } else {
      date = new Date(dateString);
    }
    
    // Check if date is valid
    if (isNaN(date.getTime())) {
      console.error(`Invalid date: ${dateString}`);
      return "Invalid date";
    }
    
    // Use explicit formatting to avoid locale differences
    const day = date.getDate().toString().padStart(2, "0");
    const month = (date.getMonth() + 1).toString().padStart(2, "0"); // Months are 0-indexed
    const year = date.getFullYear();
    
    // Format as DD-MM-YYYY
    return `${day}-${month}-${year}`;
  } catch (e) {
    console.error("Error formatting date:", e, dateString);
    return "Invalid date";
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

// Delete campaign
const deleteCampaign = async (id) => {
  if (!confirm('Are you sure you want to delete this campaign?')) return
  
  try {
    await sponsorService.deleteCampaign(id)
    // Remove from local state
    campaigns.value = campaigns.value.filter(c => c.id !== id)
    applyFilters()
  } catch (err) {
    console.error('Failed to delete campaign:', err)
    error.value = 'Failed to delete campaign. Please try again later.'
  }
}

// Watch for filter changes
watch([searchQuery, visibilityFilter, statusFilter], () => {
  applyFilters()
})

// Load data on component mount
onMounted(() => {
  loadCampaigns()
})
</script>

<template>
  <div class="campaigns-view py-5">
    <div class="container">
      <!-- Header with breadcrumb -->
      <div class="d-flex justify-content-between align-items-center mb-4">
        <h1>My Campaigns</h1>
        <nav aria-label="breadcrumb">
          <ol class="breadcrumb mb-0">
            <li class="breadcrumb-item">
              <RouterLink to="/sponsor/dashboard">Dashboard</RouterLink>
            </li>
            <li class="breadcrumb-item active">Campaigns</li>
          </ol>
        </nav>
      </div>
      
      <!-- Error alert -->
      <div v-if="error" class="alert alert-danger alert-dismissible fade show" role="alert">
        {{ error }}
        <button type="button" class="btn-close" @click="error = ''"></button>
      </div>
      
      <!-- Filters and action buttons -->
      <div class="card border-0 shadow-sm mb-4">
        <div class="card-body">
          <h5 class="card-title mb-3">
            <i class="bi bi-funnel me-2"></i>Search Campaigns
          </h5>
          <div class="row g-3">
            <div class="col-md-6">
              <label for="campaignSearch" class="form-label">Search</label>
              <div class="input-group">
                <span class="input-group-text bg-light border-end-0">
                  <i class="bi bi-search"></i>
                </span>
                <input 
                  type="text" 
                  id="campaignSearch"
                  v-model="searchQuery" 
                  class="form-control border-start-0" 
                  placeholder="Search campaigns..."
                />
              </div>
            </div>
            <div class="col-md-3">
              <label for="visibilityFilter" class="form-label">Visibility</label>
              <select id="visibilityFilter" v-model="visibilityFilter" class="form-select">
                <option value="all">All Visibility</option>
                <option value="public">Public</option>
                <option value="private">Private</option>
              </select>
            </div>
            <div class="col-md-3">
              <label for="statusFilter" class="form-label">Status</label>
              <select id="statusFilter" v-model="statusFilter" class="form-select">
                <option value="all">All Statuses</option>
                <option value="expired">Expired</option>
                <option value="active_current">Active</option>
                <option value="completed">Completed</option>
                <option value="paused">Paused</option>
                <option value="draft">Draft</option>
                <option value="pending_approval">Pending Approval</option>
                <option value="rejected">Rejected</option>
              </select>
            </div>
            <div class="col-md-3 d-flex align-items-end">
              <RouterLink to="/sponsor/campaigns/create" class="btn btn-primary w-100">
                <i class="bi bi-plus-circle me-1"></i>New Campaign
              </RouterLink>
            </div>
          </div>
        </div>
      </div>
      
      <!-- Loading state -->
      <div v-if="loading" class="text-center py-5">
        <div class="spinner-border text-primary" role="status">
          <span class="visually-hidden">Loading...</span>
        </div>
        <p class="mt-3">Loading campaigns...</p>
      </div>
      
      <!-- Empty state -->
      <div v-else-if="filteredCampaigns.length === 0" class="text-center py-5">
        <div class="mb-4">
          <i class="bi bi-clipboard-x display-1 text-muted"></i>
        </div>
        <h3 class="mb-3">No campaigns found</h3>
        <p class="text-muted mb-4">
          {{ campaigns.length === 0 
            ? "You haven't created any campaigns yet." 
            : "No campaigns match your current filters." }}
        </p>
        <div v-if="campaigns.length === 0">
          <RouterLink to="/sponsor/campaigns/create" class="btn btn-primary">
            Create Your First Campaign
          </RouterLink>
        </div>
        <div v-else>
          <button class="btn btn-outline-secondary" @click="searchQuery = ''; visibilityFilter = 'all'; statusFilter = 'all'">
            Clear Filters
          </button>
        </div>
      </div>
      
      <!-- Campaigns list -->
      <div v-else>
        <div class="d-flex justify-content-between align-items-center mb-3">
          <h5 class="mb-0">Your Campaigns <span class="text-muted fs-6">({{ filteredCampaigns.length }} of {{ campaigns.length }} campaigns)</span></h5>
        </div>
        <div class="row row-cols-1 row-cols-md-2 g-4">
          <div v-for="campaign in filteredCampaigns" :key="campaign.id" class="col">
            <div class="card h-100 border-0 shadow-sm">
              <div class="card-body">
                <div class="d-flex justify-content-between mb-3">
                  <h5 class="card-title mb-0">{{ campaign.name }}</h5>
                  <div>
                    <span 
                      class="badge rounded-pill me-1"
                      :class="getStatusBadgeClass(campaign)"
                    >
                      {{ getStatusText(campaign) }}
                    </span>
                    <span 
                      class="badge rounded-pill"
                      :class="{
                        'bg-success': campaign.visibility === 'public',
                        'bg-secondary': campaign.visibility === 'private'
                      }"
                    >
                      {{ campaign.visibility }}
                    </span>
                  </div>
                </div>
                
                <p class="card-text text-muted">
                  {{ campaign.description ? 
                    (campaign.description.length > 100 ? 
                      campaign.description.substring(0, 100) + '...' : 
                      campaign.description) : 
                    'No description provided.' }}
                </p>
                
                <div class="row g-2 mb-3">
                  <div class="col-6">
                    <div class="d-flex align-items-center">
                      <i class="bi bi-cash-stack text-success me-2"></i>
                      <span>{{ formatCurrency(campaign.budget) }}</span>
                    </div>
                  </div>
                  <div class="col-6">
                    <div class="d-flex align-items-center">
                      <i class="bi bi-calendar-event text-primary me-2"></i>
                      <span>{{ formatDate(campaign.start_date) }}</span>
                    </div>
                  </div>
                </div>
              </div>
              <div class="card-footer bg-white border-0 pt-0 pb-3">
                <div class="d-flex justify-content-between">
                  <div>
                    <RouterLink :to="`/sponsor/campaigns/${campaign.id}`" class="btn btn-sm btn-outline-primary me-2">
                      <i class="bi bi-eye me-1"></i>View
                    </RouterLink>
                    <RouterLink :to="`/sponsor/campaigns/${campaign.id}/edit`" class="btn btn-sm btn-outline-secondary me-2">
                      <i class="bi bi-pencil me-1"></i>Edit
                    </RouterLink>
                  </div>
                  <button @click="deleteCampaign(campaign.id)" class="btn btn-sm btn-outline-danger">
                    <i class="bi bi-trash me-1"></i>Delete
                  </button>
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
.campaigns-view {
  animation: fadeIn 0.5s ease-in-out;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}
</style> 
