<script setup>
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { influencerService } from '../../services/api'

const router = useRouter()
const route = useRoute()

// Check if a campaign ID is provided in the route
const selectedCampaignId = computed(() => route.params.id ? parseInt(route.params.id) : null)

// State
const loading = ref(true)
const applyLoading = ref(false)
const campaigns = ref([])
const error = ref('')
const successMessage = ref('')
const selectedCampaign = ref(null)
const showApplyModal = ref(false)

// Placeholder image as data URL
const campaignPlaceholder = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDAwIiBoZWlnaHQ9IjIyNSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iNDAwIiBoZWlnaHQ9IjIyNSIgZmlsbD0iI2VlZWVlZSIvPjx0ZXh0IHg9IjUwJSIgeT0iNTAlIiBmb250LWZhbWlseT0iQXJpYWwsIHNhbnMtc2VyaWYiIGZvbnQtc2l6ZT0iMThweCIgdGV4dC1hbmNob3I9Im1pZGRsZSIgZG9taW5hbnQtYmFzZWxpbmU9Im1pZGRsZSIgZmlsbD0iIzU1NTU1NSI+Q2FtcGFpZ24gSW1hZ2U8L3RleHQ+PC9zdmc+'

// Search and filter
const filters = reactive({
  search: '',
  category: '',
  minBudget: null,
  maxBudget: null,
  sort: 'latest'
})

// Categories (to be replaced with actual categories from backend)
const categories = [
  { id: 'beauty', name: 'Beauty & Cosmetics' },
  { id: 'fashion', name: 'Fashion & Apparel' },
  { id: 'food', name: 'Food & Beverage' },
  { id: 'technology', name: 'Technology' },
  { id: 'travel', name: 'Travel & Lifestyle' },
  { id: 'gaming', name: 'Gaming' },
  { id: 'fitness', name: 'Health & Fitness' },
  { id: 'other', name: 'Other' }
]

// Sort options
const sortOptions = [
  { id: 'latest', name: 'Newest First' },
  { id: 'oldest', name: 'Oldest First' },
  { id: 'budget_high', name: 'Budget: High to Low' },
  { id: 'budget_low', name: 'Budget: Low to High' }
]

// Application form
const applicationForm = reactive({
  message: '',
  proposedAmount: null
})

// Form errors
const formErrors = reactive({
  message: '',
  proposedAmount: ''
})

// Computed property for filtered campaigns
const filteredCampaigns = computed(() => {
  if (!campaigns.value.length) return []
  
  return campaigns.value.filter(campaign => {
    // Search filter
    const searchMatch = !filters.search || 
      campaign.name.toLowerCase().includes(filters.search.toLowerCase()) ||
      (campaign.description && campaign.description.toLowerCase().includes(filters.search.toLowerCase()))
    
    // Category filter
    const categoryMatch = !filters.category || campaign.category === filters.category
    
    // Budget filters
    const minBudgetMatch = !filters.minBudget || campaign.budget >= filters.minBudget
    const maxBudgetMatch = !filters.maxBudget || campaign.budget <= filters.maxBudget
    
    return searchMatch && categoryMatch && minBudgetMatch && maxBudgetMatch
  }).sort((a, b) => {
    // Sort based on selected option
    switch (filters.sort) {
      case 'latest':
        return new Date(b.created_at) - new Date(a.created_at)
      case 'oldest':
        return new Date(a.created_at) - new Date(b.created_at)
      case 'budget_high':
        return b.budget - a.budget
      case 'budget_low':
        return a.budget - b.budget
      default:
        return 0
    }
  })
})

// Load available campaigns
const loadCampaigns = async () => {
  try {
    loading.value = true
    error.value = ''
    
    const response = await influencerService.getAvailableCampaigns()
    campaigns.value = response.data || []
    
    // If a specific campaign ID was provided, open that campaign automatically
    if (selectedCampaignId.value && campaigns.value.length) {
      const campaign = campaigns.value.find(c => c.id === selectedCampaignId.value)
      if (campaign) {
        openApplyModal(campaign)
      }
    }
    
  } catch (err) {
    console.error('Failed to load campaigns:', err)
    error.value = 'Failed to load available campaigns. Please try again later.'
  } finally {
    loading.value = false
  }
}

// Format currency
const formatCurrency = (amount) => {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 0
  }).format(amount || 0)
}

// Format date
const formatDate = (dateString) => {
  if (!dateString) return 'N/A'
  
  const date = new Date(dateString)
  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric'
  })
}

// Open apply modal
const openApplyModal = (campaign) => {
  selectedCampaign.value = campaign
  
  // Pre-fill the proposed amount with the campaign budget if available
  if (campaign.budget) {
    applicationForm.proposedAmount = campaign.budget
  }
  
  showApplyModal.value = true
}

// Close apply modal
const closeApplyModal = () => {
  showApplyModal.value = false
  selectedCampaign.value = null
  
  // Reset form
  applicationForm.message = ''
  applicationForm.proposedAmount = null
  
  // Reset form errors
  formErrors.message = ''
  formErrors.proposedAmount = ''
}

// Validate application form
const validateForm = () => {
  let isValid = true
  
  // Reset errors
  formErrors.message = ''
  formErrors.proposedAmount = ''
  
  // Validate message
  if (!applicationForm.message.trim()) {
    formErrors.message = 'Please enter a message to the sponsor'
    isValid = false
  }
  
  // Validate proposed amount
  if (!applicationForm.proposedAmount) {
    formErrors.proposedAmount = 'Please enter your proposed payment amount'
    isValid = false
  } else if (applicationForm.proposedAmount <= 0) {
    formErrors.proposedAmount = 'Amount must be greater than zero'
    isValid = false
  }
  
  return isValid
}

// Submit application
const submitApplication = async () => {
  if (!validateForm()) return
  
  try {
    applyLoading.value = true
    error.value = ''
    successMessage.value = ''
    
    const payload = {
      campaign_id: selectedCampaign.value.id,
      message: applicationForm.message,
      payment_amount: applicationForm.proposedAmount
    }
    
    await influencerService.applyCampaign(payload)
    
    // Show success message
    successMessage.value = `Application sent successfully for ${selectedCampaign.value.name}!`
    
    // Close modal
    closeApplyModal()
    
    // Refresh campaigns list after a short delay
    setTimeout(() => {
      loadCampaigns()
    }, 2000)
    
  } catch (err) {
    console.error('Failed to apply for campaign:', err)
    
    // Handle duplicate ad request case (409 Conflict)
    if (err.response && err.response.status === 409) {
      const adRequestId = err.response.data.ad_request_id
      
      if (adRequestId) {
        // Close the modal
        closeApplyModal()
        // Set error with link to existing request
        error.value = `${err.response.data.message}. <a href="/influencer/ad-requests/${adRequestId}" class="alert-link">View existing request</a>`
      } else {
        error.value = err.response.data.message || 'You already have a request for this campaign'
      }
    } else {
      error.value = 'Failed to submit your application. Please try again later.'
    }
  } finally {
    applyLoading.value = false
  }
}

// Reset filters
const resetFilters = () => {
  filters.search = ''
  filters.category = ''
  filters.minBudget = null
  filters.maxBudget = null
  filters.sort = 'latest'
}

// View campaign details
const viewCampaignDetails = (campaign) => {
  // Update the URL without reloading the page
  router.push(`/campaigns/${campaign.id}`)
  openApplyModal(campaign)
}

// Watch for changes in the route params
watch(() => route.params.id, (newId) => {
  if (newId && campaigns.value.length) {
    const campaignId = parseInt(newId)
    const campaign = campaigns.value.find(c => c.id === campaignId)
    if (campaign) {
      openApplyModal(campaign)
    }
  }
})

// Load data on component mount
onMounted(() => {
  loadCampaigns()
})
</script>

<template>
  <div class="campaign-browse-view py-5">
    <div class="container">
      <h1 class="mb-4">{{ selectedCampaignId ? 'Campaign Details' : 'Browse Campaigns' }}</h1>
      
      <!-- Breadcrumbs navigation -->
      <nav v-if="selectedCampaignId" aria-label="breadcrumb" class="mb-4">
        <ol class="breadcrumb">
          <li class="breadcrumb-item"><router-link to="/influencer/dashboard">Dashboard</router-link></li>
          <li class="breadcrumb-item"><router-link to="/influencer/campaigns/browse">Browse Campaigns</router-link></li>
          <li class="breadcrumb-item active">Campaign Details</li>
        </ol>
      </nav>
      
      <!-- Error Alert -->
      <div v-if="error" class="alert alert-danger alert-dismissible fade show mb-4" role="alert">
        <span v-html="error"></span>
        <button type="button" class="btn-close" @click="error = ''"></button>
      </div>
      
      <!-- Success Alert -->
      <div v-if="successMessage" class="alert alert-success alert-dismissible fade show mb-4" role="alert">
        {{ successMessage }}
        <button type="button" class="btn-close" @click="successMessage = ''"></button>
      </div>
      
      <!-- Filters (only show when not viewing a specific campaign) -->
      <div v-if="!selectedCampaignId" class="card border-0 shadow-sm mb-4">
        <div class="card-body">
          <h5 class="card-title mb-3">Find Campaigns</h5>
          <div class="row g-3">
            <!-- Search -->
            <div class="col-md-6">
              <label for="search" class="form-label">Search</label>
              <div class="input-group">
                <span class="input-group-text">
                  <i class="bi bi-search"></i>
                </span>
                <input 
                  type="text" 
                  id="search" 
                  class="form-control" 
                  v-model="filters.search"
                  placeholder="Search by campaign name or description"
                >
              </div>
            </div>
            
            <!-- Category -->
            <div class="col-md-6">
              <label for="category" class="form-label">Category</label>
              <select id="category" class="form-select" v-model="filters.category">
                <option value="">All Categories</option>
                <option v-for="category in categories" :key="category.id" :value="category.id">
                  {{ category.name }}
                </option>
              </select>
            </div>
            
            <!-- Budget Range -->
            <div class="col-md-6">
              <div class="row g-2">
                <div class="col-6">
                  <label for="minBudget" class="form-label">Min Budget</label>
                  <div class="input-group">
                    <span class="input-group-text">$</span>
                    <input 
                      type="number" 
                      id="minBudget" 
                      class="form-control" 
                      v-model="filters.minBudget"
                      min="0"
                      placeholder="Min"
                    >
                  </div>
                </div>
                <div class="col-6">
                  <label for="maxBudget" class="form-label">Max Budget</label>
                  <div class="input-group">
                    <span class="input-group-text">$</span>
                    <input 
                      type="number" 
                      id="maxBudget" 
                      class="form-control" 
                      v-model="filters.maxBudget"
                      min="0"
                      placeholder="Max"
                    >
                  </div>
                </div>
              </div>
            </div>
            
            <!-- Sort -->
            <div class="col-md-6">
              <label for="sort" class="form-label">Sort By</label>
              <select id="sort" class="form-select" v-model="filters.sort">
                <option v-for="option in sortOptions" :key="option.id" :value="option.id">
                  {{ option.name }}
                </option>
              </select>
            </div>
            
            <!-- Actions -->
            <div class="col-12 d-flex justify-content-end">
              <button class="btn btn-outline-secondary me-2" @click="resetFilters">
                Reset Filters
              </button>
            </div>
          </div>
        </div>
      </div>
      
      <!-- Loading Spinner -->
      <div v-if="loading" class="text-center py-5">
        <div class="spinner-border text-primary" role="status">
          <span class="visually-hidden">Loading...</span>
        </div>
        <p class="mt-3">Loading available campaigns...</p>
      </div>
      
      <!-- No Campaigns -->
      <div v-else-if="!filteredCampaigns.length" class="text-center py-5">
        <div class="mb-3">
          <i class="bi bi-clipboard-x fs-1 text-muted"></i>
        </div>
        <h3>No Campaigns Found</h3>
        <p class="text-muted mb-4">
          {{ campaigns.length ? 'No campaigns match your current filters.' : 'There are no campaigns available right now.' }}
        </p>
        <button 
          v-if="campaigns.length && Object.values(filters).some(v => v !== '' && v !== null && v !== 'latest')" 
          class="btn btn-primary" 
          @click="resetFilters"
        >
          Reset Filters
        </button>
      </div>
      
      <!-- Campaign List -->
      <div v-else class="row row-cols-1 row-cols-md-2 row-cols-lg-3 g-4">
        <div v-for="campaign in filteredCampaigns" :key="campaign.id" class="col">
          <div class="card h-100 border-0 shadow-sm campaign-card" :title="campaign.name">
            <!-- Campaign Image -->
            <div class="campaign-card-img" 
                 :style="{ backgroundImage: `url(${campaign.image_url || campaignPlaceholder})` }">
              <div class="campaign-card-category">
                {{ categories.find(c => c.id === campaign.category)?.name || 'Uncategorized' }}
              </div>
            </div>
            
            <div class="card-body">
              <h5 class="card-title">{{ campaign.name }}</h5>
              
              <div class="mb-3">
                <span class="text-primary fw-bold">{{ formatCurrency(campaign.budget) }}</span>
                <span class="text-muted"> budget</span>
              </div>
              
              <p class="card-text campaign-description">
                {{ campaign.description || 'No description provided.' }}
              </p>
            </div>
            
            <div class="card-footer bg-white border-top-0 pt-0">
              <div class="d-flex justify-content-between align-items-center">
                <small class="text-muted">Posted: {{ formatDate(campaign.created_at) }}</small>
                <button class="btn btn-primary" @click="openApplyModal(campaign)">
                  Apply Now
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <!-- Apply Modal - Using Bootstrap's modal classes -->
      <div v-if="showApplyModal" class="modal-overlay" @click.self="closeApplyModal">
        <div class="modal show d-block" tabindex="-1" role="dialog">
          <div class="modal-dialog modal-dialog-centered" role="document">
            <div class="modal-content">
              <div class="modal-header">
                <h5 class="modal-title">Apply for Campaign</h5>
                <button type="button" class="btn-close" @click="closeApplyModal" aria-label="Close"></button>
              </div>
              
              <div class="modal-body">
                <div v-if="selectedCampaign" class="mb-4">
                  <h4 class="text-dark">{{ selectedCampaign.name }}</h4>
                  
                  <div class="campaign-details mb-3 p-3 border rounded">
                    <div class="row g-3">
                      <div class="col-6">
                        <label class="text-muted d-block mb-1 fw-bold">Budget</label>
                        <div class="fs-5 fw-bold text-primary">{{ formatCurrency(selectedCampaign.budget) }}</div>
                      </div>
                      <div class="col-6">
                        <label class="text-muted d-block mb-1 fw-bold">Category</label>
                        <div class="fw-medium">{{ categories.find(c => c.id === selectedCampaign.category)?.name || 'Uncategorized' }}</div>
                      </div>
                    </div>
                  </div>
                  
                  <div class="bg-light p-3 rounded mb-4 border">
                    <h6 class="mb-2 fw-bold">Description</h6>
                    <p class="mb-0 whitespace-pre-wrap text-dark">{{ selectedCampaign.description || 'No description provided.' }}</p>
                  </div>
                  
                  <div class="bg-light p-3 rounded border">
                    <h6 class="mb-2 fw-bold">Requirements</h6>
                    <p class="mb-0 whitespace-pre-wrap text-dark">{{ selectedCampaign.requirements || 'No specific requirements provided.' }}</p>
                  </div>
                </div>
                
                <hr class="my-4" />
                
                <form @submit.prevent="submitApplication" class="bg-white p-3 rounded border">
                  <h5 class="mb-3">Your Application</h5>
                  <!-- Proposed Amount -->
                  <div class="mb-3">
                    <label for="proposedAmount" class="form-label fw-bold">Your Proposed Amount</label>
                    <div class="input-group">
                      <span class="input-group-text">$</span>
                      <input 
                        type="number" 
                        id="proposedAmount" 
                        class="form-control" 
                        v-model="applicationForm.proposedAmount"
                        min="1"
                        placeholder="Enter your proposed payment amount"
                        required
                      >
                    </div>
                    <div v-if="formErrors.proposedAmount" class="text-danger small mt-1">{{ formErrors.proposedAmount }}</div>
                    <small class="form-text text-muted">This amount can be negotiated later.</small>
                  </div>
                  
                  <!-- Message -->
                  <div class="mb-3">
                    <label for="message" class="form-label fw-bold">Message to Sponsor</label>
                    <textarea 
                      id="message" 
                      class="form-control" 
                      v-model="applicationForm.message"
                      rows="4"
                      placeholder="Explain why you're a good fit for this campaign..."
                      required
                    ></textarea>
                    <div v-if="formErrors.message" class="text-danger small mt-1">{{ formErrors.message }}</div>
                  </div>
                </form>
              </div>
              
              <div class="modal-footer">
                <button type="button" class="btn btn-outline-secondary" @click="closeApplyModal">
                  Cancel
                </button>
                <button 
                  type="button" 
                  class="btn btn-primary" 
                  @click="submitApplication"
                  :disabled="applyLoading"
                >
                  <span v-if="applyLoading" class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
                  Submit Application
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
.campaign-browse-view {
  animation: fadeIn 0.5s ease-in-out;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

.campaign-card {
  transition: transform 0.2s, box-shadow 0.2s;
  cursor: pointer;
}

.campaign-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 10px 15px rgba(0, 0, 0, 0.1) !important;
}

.campaign-card-img {
  height: 180px;
  background-size: cover;
  background-position: center;
  background-repeat: no-repeat;
  position: relative;
  border-top-left-radius: 0.375rem;
  border-top-right-radius: 0.375rem;
}

.campaign-card-category {
  position: absolute;
  bottom: 10px;
  left: 10px;
  background-color: rgba(0, 0, 0, 0.7);
  color: white;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 0.75rem;
}

.campaign-description {
  overflow: hidden;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  max-height: 4.5rem; /* Approx 3 lines */
}

/* For Bootstrap modal in Vue */
.modal-backdrop {
  opacity: 0.5;
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 1040;
}

.modal {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 1050;
  overflow-x: hidden;
  overflow-y: auto;
}

.modal-dialog {
  margin: 1.75rem auto;
  max-width: 600px;
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

.whitespace-pre-wrap {
  white-space: pre-wrap;
}

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
</style> 