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

// Filter campaigns
const applyFilters = () => {
  filteredCampaigns.value = campaigns.value.filter(campaign => {
    // Apply search filter
    const matchesSearch = searchQuery.value === '' || 
      campaign.name.toLowerCase().includes(searchQuery.value.toLowerCase()) ||
      (campaign.description && campaign.description.toLowerCase().includes(searchQuery.value.toLowerCase()))
    
    // Apply status filter
    const matchesStatus = statusFilter.value === 'all' || 
      (statusFilter.value === 'public' && campaign.visibility === 'public') ||
      (statusFilter.value === 'private' && campaign.visibility === 'private')
    
    return matchesSearch && matchesStatus
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
watch([searchQuery, statusFilter], () => {
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
                  placeholder="Search campaigns..."
                />
              </div>
            </div>
            <div class="col-md-3">
              <select v-model="statusFilter" class="form-select">
                <option value="all">All Visibility</option>
                <option value="public">Public</option>
                <option value="private">Private</option>
              </select>
            </div>
            <div class="col-md-3 text-end">
              <RouterLink to="/sponsor/campaigns/create" class="btn btn-primary">
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
          <button class="btn btn-outline-secondary" @click="searchQuery = ''; statusFilter = 'all'">
            Clear Filters
          </button>
        </div>
      </div>
      
      <!-- Campaigns list -->
      <div v-else class="row row-cols-1 row-cols-md-2 g-4">
        <div v-for="campaign in filteredCampaigns" :key="campaign.id" class="col">
          <div class="card h-100 border-0 shadow-sm">
            <div class="card-body">
              <div class="d-flex justify-content-between mb-3">
                <h5 class="card-title mb-0">{{ campaign.name }}</h5>
                <span 
                  :class="{
                    'badge rounded-pill bg-success': campaign.visibility === 'public',
                    'badge rounded-pill bg-secondary': campaign.visibility === 'private'
                  }"
                >
                  {{ campaign.visibility }}
                </span>
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