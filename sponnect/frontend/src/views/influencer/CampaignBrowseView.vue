<script setup>
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { influencerService, searchService } from '../../services/api'
import { formatDate } from '../../utils/dateUtils'

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
let searchTimeout = null

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

// Categories
const categories = [
  { id: 'technology', name: 'Technology' },
  { id: 'fashion', name: 'Fashion & Apparel' },
  { id: 'beauty', name: 'Beauty & Cosmetics' },
  { id: 'food', name: 'Food & Beverage' },
  { id: 'travel', name: 'Travel & Lifestyle' },
  { id: 'gaming', name: 'Gaming' },
  { id: 'fitness', name: 'Health & Fitness' },
  { id: 'automotive', name: 'Automotive' },
  { id: 'finance', name: 'Finance' },
  { id: 'entertainment', name: 'Entertainment' },
  { id: 'education', name: 'Education' },
  { id: 'lifestyle', name: 'Lifestyle' },
  { id: 'sports', name: 'Sports' },
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
    
    console.log('Loading campaigns for influencer...');
    const response = await influencerService.getAvailableCampaigns()
    
    // Handle different response formats
    if (response.data && Array.isArray(response.data)) {
      // Direct array format
      campaigns.value = response.data
      console.log(`Loaded ${response.data.length} campaigns (array format)`);
    } else if (response.data && Array.isArray(response.data.campaigns)) {
      // Object with campaigns field
      campaigns.value = response.data.campaigns
      console.log(`Loaded ${response.data.campaigns.length} campaigns (object.campaigns format)`);
    } else {
      console.error('Unexpected response format:', response.data)
      campaigns.value = []
      error.value = 'Error: Received unexpected data format from server'
    }
    
    // Log the first few campaigns for debugging
    if (campaigns.value.length > 0) {
      console.log('First campaign data:', JSON.stringify(campaigns.value[0], null, 2));
      
      // Verify all required fields are present
      let missingFields = [];
      campaigns.value.forEach((campaign, index) => {
        if (!campaign.name) missingFields.push(`Campaign ${index} missing name`);
        if (!campaign.description) missingFields.push(`Campaign ${index} missing description`);
        if (campaign.budget === undefined) missingFields.push(`Campaign ${index} missing budget`);
        
        // Ensure dates are properly formatted
        if (campaign.start_date && campaign.start_date.includes('NaN')) {
          console.error(`Invalid start_date in campaign ${index}:`, campaign.start_date);
          // Use ISO date if available
          if (campaign.start_date_iso) {
            campaign.start_date = formatDate(campaign.start_date_iso);
          }
        }
        
        if (campaign.end_date && campaign.end_date.includes('NaN')) {
          console.error(`Invalid end_date in campaign ${index}:`, campaign.end_date);
          // Use ISO date if available
          if (campaign.end_date_iso) {
            campaign.end_date = formatDate(campaign.end_date_iso);
          }
        }
      });
      
      if (missingFields.length > 0) {
        console.warn('Missing campaign fields:', missingFields);
      }
    } else {
      console.log('No campaigns returned');
      error.value = 'No active campaigns found. Please check back later.';
    }
    
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

// Search campaigns with all filters applied
const searchCampaigns = async () => {
  try {
    loading.value = true;
    error.value = '';
    
    // Log which filters we're using for debugging purposes
    console.log('Searching campaigns with filters:', {
      query: filters.search || 'none',
      category: filters.category || 'any',
      minBudget: filters.minBudget || 'not specified',
      maxBudget: filters.maxBudget || 'not specified',
      sort: filters.sort || 'default'
    });
    
    // Prepare search parameters - only include non-empty values
    const searchParams = {};
    
    // Only add parameters that have valid values
    if (filters.search && filters.search.trim()) {
      searchParams.query = filters.search.trim();
    }
    
    if (filters.category) {
      searchParams.category = filters.category;
    }
    
    // Handle numeric parameters carefully
    if (filters.minBudget && !isNaN(parseFloat(filters.minBudget))) {
      searchParams.min_budget = parseFloat(filters.minBudget);
    }
    
    if (filters.maxBudget && !isNaN(parseFloat(filters.maxBudget))) {
      searchParams.max_budget = parseFloat(filters.maxBudget);
    }
    
    // Add sort parameters that match backend expectations
    if (filters.sort) {
      switch (filters.sort) {
        case 'latest':
          searchParams.sort_by = 'created_at';
          searchParams.sort_order = 'desc';
          break;
        case 'oldest':
          searchParams.sort_by = 'created_at';
          searchParams.sort_order = 'asc';
          break;
        case 'budget_high':
          searchParams.sort_by = 'budget';
          searchParams.sort_order = 'desc';
          break;
        case 'budget_low':
          searchParams.sort_by = 'budget';
          searchParams.sort_order = 'asc';
          break;
      }
    }
    
    console.log('Calling API with search params:', searchParams);
    
    const response = await searchService.searchCampaigns(searchParams);
    console.log('Search API response received:', response);
    
    // Extract campaigns from the response, handling different response formats
    let campaignData = [];
    
    if (response.data) {
      if (Array.isArray(response.data)) {
        // Direct array format
        campaignData = response.data;
      } else if (response.data.campaigns && Array.isArray(response.data.campaigns)) {
        // Object with campaigns field
        campaignData = response.data.campaigns;
      } else if (typeof response.data === 'object' && !Array.isArray(response.data)) {
        // Check if it's a single campaign object (has id and name)
        if (response.data.id && response.data.name) {
          campaignData = [response.data];
        }
      }
    }
    
    // Ensure all required fields are present with fallbacks
    campaignData = campaignData.map(campaign => {
      return {
        ...campaign,
        name: campaign.name || 'Unnamed Campaign',
        description: campaign.description || 'No description provided',
        budget: campaign.budget || 0,
        category: campaign.category || 'other',
        created_at: campaign.created_at || new Date().toISOString()
      };
    });
    
    // Update campaigns
    campaigns.value = campaignData;
    
    // Display appropriate message based on results
    if (campaignData.length === 0) {
      error.value = 'No campaigns found matching your criteria. Try adjusting your filters.';
    } else {
      console.log(`Successfully found ${campaignData.length} matching campaigns`);
      // Log first campaign for debugging
      if (campaignData.length > 0) {
        console.log('First campaign sample:', {
          id: campaignData[0].id,
          name: campaignData[0].name,
          category: campaignData[0].category,
          budget: campaignData[0].budget
        });
      }
    }
  } catch (err) {
    console.error('Failed to search campaigns:', err);
    handleSearchError(err);
  } finally {
    loading.value = false;
  }
};

// Handle search errors in a consistent way
const handleSearchError = (err) => {
  if (err.response) {
    const status = err.response.status;
    if (status === 401) {
      error.value = 'Your session has expired. Please login again.';
    } else if (status === 403) {
      error.value = 'You do not have permission to access these campaigns.';
    } else if (err.response.data && err.response.data.message) {
      error.value = err.response.data.message;
    } else {
      error.value = `Error ${status}: Failed to search campaigns. Please try again.`;
    }
  } else if (err.request) {
    error.value = 'Server did not respond. Please check your connection and try again.';
  } else {
    error.value = 'Failed to search campaigns. Please try again later.';
  }
  
  // Ensure campaigns is empty when there's an error
  campaigns.value = [];
};

// Format currency
const formatCurrency = (amount) => {
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    minimumFractionDigits: 0
  }).format(amount || 0)
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

// Watch for search query changes to implement auto-search
watch(() => filters.search, (newValue) => {
  if (searchTimeout) {
    clearTimeout(searchTimeout)
  }
  
  if (newValue.length >= 3) {
    // Debounce search for better UX
    searchTimeout = setTimeout(() => {
      searchCampaigns()
    }, 500)
  }
})

// Load data on component mount
onMounted(() => {
  loadCampaigns()
})

// Helper function to get category name
const getCategoryName = (categoryId) => {
  const category = categories.find(c => c.id === categoryId)
  return category ? category.name : categoryId
}
</script>

<template>
  <div class="campaign-browse-view py-5">
    <div class="container">
      <!-- Header with breadcrumb -->
      <div class="d-flex justify-content-between align-items-center mb-4">
        <h1>{{ selectedCampaignId ? 'Campaign Details' : 'Browse & Search Campaigns' }}</h1>
        <nav v-if="!selectedCampaignId" aria-label="breadcrumb">
          <ol class="breadcrumb mb-0">
            <li class="breadcrumb-item"><router-link to="/influencer/dashboard">Dashboard</router-link></li>
            <li class="breadcrumb-item active">Browse & Search Campaigns</li>
          </ol>
        </nav>
      </div>
      
      <!-- Breadcrumbs navigation for campaign detail view -->
      <nav v-if="selectedCampaignId" aria-label="breadcrumb" class="mb-4">
        <ol class="breadcrumb">
          <li class="breadcrumb-item"><router-link to="/influencer/dashboard">Dashboard</router-link></li>
          <li class="breadcrumb-item"><router-link to="/influencer/campaigns/browse">Browse & Search Campaigns</router-link></li>
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
                    <span class="input-group-text">₹</span>
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
                    <span class="input-group-text">₹</span>
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
              <button class="btn btn-primary" @click="searchCampaigns">
                <i class="bi bi-search me-1"></i> Search
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
            <div class="card-body">
              <div class="d-flex justify-content-between align-items-start mb-3">
                <h5 class="card-title">{{ campaign.name }}</h5>
                <span class="badge bg-primary">{{ getCategoryName(campaign.category) }}</span>
              </div>
              
              <div class="mb-3">
                <span class="text-primary fw-bold">{{ formatCurrency(campaign.budget) }}</span>
                <span class="text-muted"> budget</span>
              </div>
              
              <div class="mb-3">
                <span class="text-muted">By: </span>
                <span>{{ campaign.sponsor_name || 'Unknown' }}</span>
                <span v-if="campaign.sponsor_company"> ({{ campaign.sponsor_company }})</span>
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
                        <div class="fw-medium">{{ getCategoryName(selectedCampaign.category) }}</div>
                      </div>
                      <div class="col-12">
                        <label class="text-muted d-block mb-1 fw-bold">Sponsor</label>
                        <div class="fw-medium">
                          {{ selectedCampaign.sponsor_name || 'Unknown' }}
                          <span v-if="selectedCampaign.sponsor_company">({{ selectedCampaign.sponsor_company }})</span>
                        </div>
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
                      <span class="input-group-text">₹</span>
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
