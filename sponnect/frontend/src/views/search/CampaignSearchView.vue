<script setup>
import { ref, reactive, onMounted, watch } from 'vue'
import { useRouter, RouterLink } from 'vue-router'
import { searchService } from '../../services/api'

const router = useRouter()

// State
const loading = ref(false)
const campaigns = ref([])
const error = ref('')
const searchQuery = ref('')
const searching = ref(false)
let searchTimeout = null

// Search filters
const filters = reactive({
  category: '',
  minBudget: '',
  maxBudget: '',
  sort: 'latest'
})

// Categories
const categories = [
  { id: '', name: 'All Categories' },
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

// Load initial campaigns
const loadCampaigns = async () => {
  loading.value = true
  error.value = ''
  
  try {
    const response = await searchService.searchCampaigns({ limit: 12 })
    campaigns.value = response.data || []
  } catch (err) {
    console.error('Failed to load campaigns:', err)
    error.value = 'Failed to load campaigns. Please try again later.'
  } finally {
    loading.value = false
  }
}

// Search for campaigns
const searchCampaigns = async () => {
  searching.value = true
  error.value = ''
  
  try {
    const response = await searchService.searchCampaigns({ 
      query: searchQuery.value,
      category: filters.category,
      minBudget: filters.minBudget || undefined,
      maxBudget: filters.maxBudget || undefined,
      sort: filters.sort,
      limit: 20
    })
    campaigns.value = response.data || []
    
    if (campaigns.value.length === 0) {
      error.value = 'No campaigns found matching your criteria. Try adjusting your filters.'
    }
  } catch (err) {
    console.error('Failed to search campaigns:', err)
    error.value = 'Failed to search campaigns. Please try again.'
  } finally {
    searching.value = false
  }
}

// View campaign details
const viewCampaignDetails = (campaignId) => {
  router.push({
    name: 'campaign-detail',
    params: { id: campaignId }
  })
}

// Add a link to browse all campaigns
const browseAllCampaigns = () => {
  router.push('/influencer/campaigns/browse')
}

// Reset filters
const resetFilters = () => {
  searchQuery.value = ''
  filters.category = ''
  filters.minBudget = ''
  filters.maxBudget = ''
  filters.sort = 'latest'
  loadCampaigns()
}

// Format currency
const formatCurrency = (amount) => {
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    minimumFractionDigits: 0
  }).format(amount || 0)
}

// Format date
const formatDate = (dateString) => {
  if (!dateString) return 'N/A'
  return new Date(dateString).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric'
  })
}

// Helper function to get category name
const getCategoryName = (categoryId) => {
  const category = categories.find(c => c.id === categoryId)
  return category ? category.name : categoryId
}

// Watch for search query changes
watch(searchQuery, (newValue) => {
  if (searchTimeout) {
    clearTimeout(searchTimeout)
  }
  
  if (newValue.length >= 3) {
    searchTimeout = setTimeout(() => {
      searchCampaigns()
    }, 500)
  } else if (newValue.length === 0) {
    // If search field is cleared, reset to initial state
    loadCampaigns()
  }
})

onMounted(() => {
  loadCampaigns()
})
</script>

<template>
  <div class="campaign-search-view py-5">
    <div class="container">
      <!-- Header with breadcrumb -->
      <div class="d-flex justify-content-between align-items-center mb-4">
        <h1>Search Campaigns</h1>
        <nav aria-label="breadcrumb">
          <ol class="breadcrumb mb-0">
            <li class="breadcrumb-item">
              <RouterLink to="/influencer/dashboard">Dashboard</RouterLink>
            </li>
            <li class="breadcrumb-item active">Search Campaigns</li>
          </ol>
        </nav>
      </div>
      
      <!-- Error alert -->
      <div v-if="error" class="alert alert-danger alert-dismissible fade show" role="alert">
        {{ error }}
        <button type="button" class="btn-close" @click="error = ''"></button>
      </div>
      
      <!-- Search and Filters -->
      <div class="card border-0 shadow-sm mb-4">
        <div class="card-body p-4">
          <h5 class="card-title mb-3">Search Campaigns</h5>
          
          <div class="row g-3">
            <!-- Search input -->
            <div class="col-md-12 mb-3">
              <div class="input-group">
                <span class="input-group-text bg-light border-end-0">
                  <i class="bi bi-search"></i>
                </span>
                <input 
                  type="text" 
                  v-model="searchQuery" 
                  class="form-control border-start-0" 
                  placeholder="Search by campaign name or description..."
                />
              </div>
            </div>
            
            <!-- Filters -->
            <div class="col-md-3">
              <label class="form-label">Category</label>
              <select v-model="filters.category" class="form-select">
                <option value="">All Categories</option>
                <option v-for="category in categories" :key="category.id" :value="category.id">
                  {{ category.name }}
                </option>
              </select>
            </div>
            
            <div class="col-md-3">
              <label class="form-label">Min Budget</label>
              <div class="input-group">
                <span class="input-group-text">₹</span>
                <input 
                  type="number" 
                  class="form-control" 
                  v-model="filters.minBudget"
                  placeholder="Min"
                />
              </div>
            </div>
            
            <div class="col-md-3">
              <label class="form-label">Max Budget</label>
              <div class="input-group">
                <span class="input-group-text">₹</span>
                <input 
                  type="number" 
                  class="form-control" 
                  v-model="filters.maxBudget"
                  placeholder="Max"
                />
              </div>
            </div>
            
            <div class="col-md-3">
              <label class="form-label">Sort By</label>
              <select v-model="filters.sort" class="form-select">
                <option v-for="option in sortOptions" :key="option.id" :value="option.id">
                  {{ option.name }}
                </option>
              </select>
            </div>
            
            <!-- Action buttons -->
            <div class="col-12 d-flex justify-content-end gap-2 mt-2">
              <button 
                type="button" 
                class="btn btn-outline-secondary" 
                @click="resetFilters"
              >
                Reset Filters
              </button>
              <button 
                type="button" 
                class="btn btn-primary" 
                @click="searchCampaigns"
                :disabled="searching"
              >
                <span v-if="searching" class="spinner-border spinner-border-sm me-1" role="status"></span>
                <i v-else class="bi bi-filter me-1"></i>
                Apply Filters
              </button>
            </div>
          </div>
        </div>
      </div>
      
      <!-- Browse all campaigns link -->
      <div class="d-flex justify-content-between align-items-center mb-4">
        <h5>Search Results <span class="text-muted fs-6">({{ campaigns.length || 0 }} campaigns found)</span></h5>
        <button 
          type="button" 
          class="btn btn-outline-primary"
          @click="browseAllCampaigns"
        >
          <i class="bi bi-grid me-1"></i>Browse All Campaigns
        </button>
      </div>
      
      <!-- Loading state -->
      <div v-if="loading" class="text-center py-5">
        <div class="spinner-border text-primary" role="status">
          <span class="visually-hidden">Loading...</span>
        </div>
        <p class="mt-3">Loading campaigns...</p>
      </div>
      
      <!-- Results -->
      <div v-else>
        <!-- No results state -->
        <div v-if="campaigns.length === 0" class="text-center py-5">
          <div class="mb-4">
            <i class="bi bi-clipboard-x display-1 text-muted"></i>
          </div>
          <h3 class="mb-3">No campaigns found</h3>
          <p class="text-muted mb-4">Try adjusting your search criteria or filters</p>
          <button class="btn btn-outline-secondary" @click="resetFilters">
            Reset All Filters
          </button>
        </div>
        
        <!-- Campaign cards -->
        <div v-else class="row row-cols-1 row-cols-md-2 g-4">
          <div v-for="campaign in campaigns" :key="campaign.id" class="col">
            <div class="card h-100 border-0 shadow-sm">
              <div class="card-body">
                <div class="d-flex justify-content-between align-items-start mb-3">
                  <h5 class="card-title mb-0">{{ campaign.name }}</h5>
                  <span class="badge bg-primary rounded-pill">
                    {{ formatCurrency(campaign.budget) }}
                  </span>
                </div>
                
                <div class="mb-3">
                  <span class="badge bg-light text-dark me-2">{{ getCategoryName(campaign.category) }}</span>
                  <span class="badge bg-light text-dark">{{ formatDate(campaign.created_at) }}</span>
                </div>
                
                <p class="card-text text-muted">
                  {{ campaign.description ? 
                    (campaign.description.length > 100 ? 
                      campaign.description.substring(0, 100) + '...' : 
                      campaign.description) : 
                    'No description provided.' }}
                </p>
              </div>
              <div class="card-footer bg-white border-0 pt-0 pb-3">
                <button 
                  @click="viewCampaignDetails(campaign.id)" 
                  class="btn btn-outline-primary w-100"
                >
                  <i class="bi bi-eye me-2"></i>View Full Details & Apply
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
.campaign-search-view {
  animation: fadeIn 0.5s ease-in-out;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}
</style> 