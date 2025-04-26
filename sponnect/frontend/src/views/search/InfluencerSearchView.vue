<script setup>
import { ref, reactive, onMounted, watch } from 'vue'
import { useRouter, RouterLink } from 'vue-router'
import { searchService } from '../../services/api'

const router = useRouter()

// State
const loading = ref(false)
const influencers = ref([])
const error = ref('')
const searchQuery = ref('')
const searching = ref(false)
let searchTimeout = null

// Advanced search filters
const searchFilters = reactive({
  category: '',
  niche: '',
  minReach: '',
  maxReach: ''
})

// Available categories for filtering
const categories = [
  { id: '', name: 'All Categories' },
  { id: 'beauty', name: 'Beauty & Cosmetics' },
  { id: 'fashion', name: 'Fashion & Apparel' },
  { id: 'food', name: 'Food & Beverage' },
  { id: 'technology', name: 'Technology' },
  { id: 'travel', name: 'Travel & Lifestyle' },
  { id: 'gaming', name: 'Gaming' },
  { id: 'fitness', name: 'Health & Fitness' },
  { id: 'other', name: 'Other' }
]

// Load initial influencers
const loadInfluencers = async () => {
  loading.value = true
  error.value = ''
  
  try {
    const response = await searchService.searchInfluencers({ limit: 12 })
    influencers.value = response.data || []
  } catch (err) {
    console.error('Failed to load influencers:', err)
    error.value = 'Failed to load influencers. Please try again later.'
  } finally {
    loading.value = false
  }
}

// Search for influencers
const searchInfluencers = async () => {
  searching.value = true
  error.value = ''
  
  try {
    const response = await searchService.searchInfluencers({ 
      query: searchQuery.value,
      category: searchFilters.category,
      niche: searchFilters.niche,
      minReach: searchFilters.minReach || undefined,
      maxReach: searchFilters.maxReach || undefined,
      limit: 20
    })
    influencers.value = response.data || []
    
    if (influencers.value.length === 0) {
      error.value = 'No influencers found matching your criteria. Try adjusting your filters.'
    }
  } catch (err) {
    console.error('Failed to search influencers:', err)
    error.value = 'Failed to search influencers. Please try again.'
  } finally {
    searching.value = false
  }
}

// Handle creating a new ad request with the selected influencer
const createAdRequest = (influencerId) => {
  router.push({
    name: 'sponsor-campaigns',
    query: { 
      action: 'create-request',
      influencer_id: influencerId
    }
  })
}

// Reset filters
const resetFilters = () => {
  searchQuery.value = ''
  searchFilters.category = ''
  searchFilters.niche = ''
  searchFilters.minReach = ''
  searchFilters.maxReach = ''
  loadInfluencers()
}

// Watch for search query changes
watch(searchQuery, (newValue) => {
  if (searchTimeout) {
    clearTimeout(searchTimeout)
  }
  
  if (newValue.length >= 3) {
    searchTimeout = setTimeout(() => {
      searchInfluencers()
    }, 500)
  } else if (newValue.length === 0) {
    // If search field is cleared, reset to initial state
    loadInfluencers()
  }
})

onMounted(() => {
  loadInfluencers()
})
</script>

<template>
  <div class="influencer-search-view py-5">
    <div class="container">
      <!-- Header with breadcrumb -->
      <div class="d-flex justify-content-between align-items-center mb-4">
        <h1>Find Influencers</h1>
        <nav aria-label="breadcrumb">
          <ol class="breadcrumb mb-0">
            <li class="breadcrumb-item">
              <RouterLink to="/sponsor/dashboard">Dashboard</RouterLink>
            </li>
            <li class="breadcrumb-item active">Find Influencers</li>
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
          <h5 class="card-title mb-3">Search Influencers</h5>
          
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
                  placeholder="Search by name, category, or niche..."
                />
              </div>
            </div>
            
            <!-- Advanced filters -->
            <div class="col-md-3">
              <label class="form-label">Category</label>
              <select v-model="searchFilters.category" class="form-select">
                <option value="">All Categories</option>
                <option v-for="category in categories" :key="category.id" :value="category.id">
                  {{ category.name }}
                </option>
              </select>
            </div>
            
            <div class="col-md-3">
              <label class="form-label">Niche</label>
              <input 
                type="text" 
                class="form-control" 
                v-model="searchFilters.niche"
                placeholder="Enter niche"
              />
            </div>
            
            <div class="col-md-3">
              <label class="form-label">Min Reach</label>
              <input 
                type="number" 
                class="form-control" 
                v-model="searchFilters.minReach"
                placeholder="Min followers"
              />
            </div>
            
            <div class="col-md-3">
              <label class="form-label">Max Reach</label>
              <input 
                type="number" 
                class="form-control" 
                v-model="searchFilters.maxReach"
                placeholder="Max followers"
              />
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
                @click="searchInfluencers"
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
      
      <!-- Search Results Header -->
      <div class="d-flex justify-content-between align-items-center mb-4">
        <h5>Search Results</h5>
        <div>
          <span class="text-muted me-2">{{ influencers.length || 0 }} influencers found</span>
        </div>
      </div>
      
      <!-- Loading state -->
      <div v-if="loading" class="text-center py-5">
        <div class="spinner-border text-primary" role="status">
          <span class="visually-hidden">Loading...</span>
        </div>
        <p class="mt-3">Loading influencers...</p>
      </div>
      
      <!-- Results -->
      <div v-else>
        <!-- No results state -->
        <div v-if="influencers.length === 0" class="text-center py-5">
          <div class="mb-4">
            <i class="bi bi-people display-1 text-muted"></i>
          </div>
          <h3 class="mb-3">No influencers found</h3>
          <p class="text-muted mb-4">Try adjusting your search criteria or filters</p>
          <button class="btn btn-outline-secondary" @click="resetFilters">
            Reset All Filters
          </button>
        </div>
        
        <!-- Influencer cards -->
        <div v-else class="row row-cols-1 row-cols-md-2 row-cols-lg-3 g-4">
          <div v-for="influencer in influencers" :key="influencer.id" class="col">
            <div class="card h-100 border-0 shadow-sm">
              <div class="card-body">
                <div class="d-flex justify-content-between align-items-start mb-3">
                  <h5 class="card-title mb-0">{{ influencer.influencer_name }}</h5>
                  <span class="badge bg-primary rounded-pill">
                    {{ influencer.reach.toLocaleString() }} reach
                  </span>
                </div>
                
                <div class="mb-3">
                  <span class="badge bg-light text-dark me-2 mb-2">{{ influencer.category }}</span>
                  <span v-if="influencer.niche" class="badge bg-light text-dark me-2 mb-2">{{ influencer.niche }}</span>
                </div>
                
                <p class="card-text text-muted small">
                  {{ influencer.bio || 'No bio available' }}
                </p>
              </div>
              <div class="card-footer bg-white border-0 pt-0 pb-3">
                <button 
                  @click="createAdRequest(influencer.id)" 
                  class="btn btn-primary w-100"
                >
                  <i class="bi bi-plus-circle me-2"></i>Create Ad Request with This Influencer
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
.influencer-search-view {
  animation: fadeIn 0.5s ease-in-out;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}
</style> 
  animation: fadeIn 0.5s ease-in-out;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}
</style> 