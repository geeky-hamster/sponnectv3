<script setup>
import { ref, onMounted, computed, watch, reactive } from 'vue'
import { useRoute, useRouter, RouterLink } from 'vue-router'
import { sponsorService, searchService } from '../../services/api'

const route = useRoute()
const router = useRouter()
const campaignId = computed(() => route.params.id)

// State
const loading = ref(true)
const submitting = ref(false)
const campaign = ref(null)
const influencers = ref([])
const searchResults = ref([])
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

// Form state
const form = ref({
  influencer_id: route.query.influencer_id || '',
  payment_amount: '',
  requirements: '',
  message: ''
})

// Load campaign data and initial influencer list
const loadData = async () => {
  loading.value = true
  error.value = ''
  
  try {
    // Get campaign details and search for influencers
    const [campaignResponse, influencersResponse] = await Promise.all([
      sponsorService.getCampaign(campaignId.value),
      searchService.searchInfluencers({ limit: 10 }) // Get some initial influencers
    ])
    
    campaign.value = campaignResponse.data
    influencers.value = influencersResponse.data || []
    
    // Set initial payment amount suggestion from campaign budget
    if (campaign.value) {
      form.value.payment_amount = Math.round(campaign.value.budget * 0.1) // Suggest 10% of budget as default
      
      // Set default requirements based on campaign goals if available
      if (campaign.value.goals) {
        form.value.requirements = `Based on our campaign goals: ${campaign.value.goals}`
      }
    }
    
    // If influencer_id was provided in the URL, set it
    if (route.query.influencer_id) {
      form.value.influencer_id = route.query.influencer_id
    }
  } catch (err) {
    console.error('Failed to load data:', err)
    error.value = 'Failed to load campaign or influencer data. Please try again later.'
  } finally {
    loading.value = false
  }
}

// Search for influencers
const searchInfluencers = async () => {
  if (!searchQuery.value.trim() && !searchFilters.category && !searchFilters.niche && !searchFilters.minReach && !searchFilters.maxReach) {
    searchResults.value = []
    return
  }
  
  searching.value = true
  
  try {
    const response = await searchService.searchInfluencers({ 
      query: searchQuery.value,
      category: searchFilters.category,
      niche: searchFilters.niche,
      minReach: searchFilters.minReach || undefined,
      maxReach: searchFilters.maxReach || undefined,
      limit: 20
    })
    searchResults.value = response.data || []
    
    if (searchResults.value.length === 0) {
      error.value = 'No influencers found matching your criteria. Try adjusting your filters.'
      setTimeout(() => {
        error.value = ''
      }, 3000)
    }
  } catch (err) {
    console.error('Failed to search influencers:', err)
    error.value = 'Failed to search influencers. Please try again.'
    searchResults.value = []
  } finally {
    searching.value = false
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

// Handle form submission
const handleSubmit = async () => {
  if (!form.value.influencer_id) {
    error.value = 'Please select an influencer'
    return
  }
  
  if (!form.value.payment_amount) {
    error.value = 'Please enter a payment amount'
    return
  }
  
  if (!form.value.requirements) {
    error.value = 'Please specify requirements'
    return
  }
  
  submitting.value = true
  error.value = ''
  
  try {
    const requestData = {
      influencer_id: form.value.influencer_id,
      payment_amount: parseFloat(form.value.payment_amount),
      requirements: form.value.requirements,
      message: form.value.message
    }
    
    await sponsorService.createAdRequest(campaignId.value, requestData)
    
    // Redirect to campaign details page
    router.push(`/sponsor/campaigns/${campaignId.value}?tab=requests`)
  } catch (err) {
    console.error('Failed to create ad request:', err)
    
    // Handle duplicate ad request case (409 Conflict)
    if (err.response && err.response.status === 409) {
      const adRequestId = err.response.data.ad_request_id
      
      if (adRequestId) {
        error.value = `${err.response.data.message}. <a href="/sponsor/ad-requests/${adRequestId}" class="alert-link">View existing request</a>` 
      } else {
        error.value = err.response.data.message || 'A request for this influencer already exists'
      }
    } else {
      error.value = 'Failed to create ad request. Please check your inputs and try again.'
    }
  } finally {
    submitting.value = false
  }
}

// Get selected influencer details
const selectedInfluencer = computed(() => {
  const allInfluencers = [...influencers.value, ...searchResults.value]
  return allInfluencers.find(i => i.id.toString() === form.value.influencer_id.toString())
})

// Watch for search query changes
watch(searchQuery, () => {
  if (searchQuery.value.trim().length > 2) {
    // Debounce search
    if (searchTimeout) clearTimeout(searchTimeout)
    searchTimeout = setTimeout(() => {
      searchInfluencers()
    }, 500)
  } else {
    searchResults.value = []
  }
})

// Load data on component mount
onMounted(() => {
  loadData()
})
</script>

<template>
  <div class="create-request-view py-5">
    <div class="container">
      <!-- Breadcrumb -->
      <nav aria-label="breadcrumb" class="mb-4">
        <ol class="breadcrumb">
          <li class="breadcrumb-item">
            <RouterLink to="/sponsor/dashboard">Dashboard</RouterLink>
          </li>
          <li class="breadcrumb-item">
            <RouterLink to="/sponsor/campaigns">Campaigns</RouterLink>
          </li>
          <li class="breadcrumb-item">
            <RouterLink :to="`/sponsor/campaigns/${campaignId}`">Campaign Details</RouterLink>
          </li>
          <li class="breadcrumb-item active">Create Ad Request</li>
        </ol>
      </nav>
      
      <h1 class="mb-4">Create Ad Request</h1>
      
      <!-- Loading state -->
      <div v-if="loading" class="text-center py-5">
        <div class="spinner-border text-primary" role="status">
          <span class="visually-hidden">Loading...</span>
        </div>
        <p class="mt-3">Loading campaign details...</p>
      </div>
      
      <!-- Error alert -->
      <div v-else-if="error" class="alert alert-danger alert-dismissible fade show mb-4" role="alert">
        <span v-html="error"></span>
        <button type="button" class="btn-close" @click="error = ''"></button>
      </div>
      
      <!-- Create request form -->
      <div v-if="campaign && !loading" class="row">
        <div class="col-lg-8">
          <div class="card border-0 shadow-sm mb-4">
            <div class="card-body p-4">
              <div class="card-title h5 mb-4">
                Create Ad Request for "{{ campaign.name }}"
              </div>
              
              <form @submit.prevent="handleSubmit">
                <!-- Influencer selection -->
                <div class="mb-4">
                  <label class="form-label">Select Influencer</label>
                  
                  <div class="input-group mb-2">
                    <span class="input-group-text bg-light border-end-0">
                      <i class="bi bi-search"></i>
                    </span>
                    <input 
                      type="text" 
                      v-model="searchQuery" 
                      class="form-control border-start-0" 
                      placeholder="Search for influencers..."
                    />
                  </div>
                  
                  <!-- Advanced search filters -->
                  <div class="card bg-light border-0 mt-2 mb-3">
                    <div class="card-body">
                      <div class="d-flex justify-content-between align-items-center mb-2">
                        <h6 class="mb-0">Advanced Filters</h6>
                        <button type="button" class="btn btn-sm btn-outline-secondary" 
                                @click="searchFilters.category = ''; searchFilters.niche = ''; searchFilters.minReach = ''; searchFilters.maxReach = ''">
                          Reset
                        </button>
                      </div>
                      <div class="row g-2">
                        <div class="col-md-6">
                          <select class="form-select form-select-sm" v-model="searchFilters.category">
                            <option v-for="category in categories" :key="category.id" :value="category.id">
                              {{ category.name }}
                            </option>
                          </select>
                        </div>
                        <div class="col-md-6">
                          <input 
                            type="text" 
                            class="form-control form-control-sm" 
                            placeholder="Niche (e.g. cooking, fitness)" 
                            v-model="searchFilters.niche"
                          />
                        </div>
                        <div class="col-md-6">
                          <div class="input-group input-group-sm">
                            <span class="input-group-text">Min Reach</span>
                            <input 
                              type="number" 
                              class="form-control form-control-sm" 
                              v-model="searchFilters.minReach"
                              min="0"
                            />
                          </div>
                        </div>
                        <div class="col-md-6">
                          <div class="input-group input-group-sm">
                            <span class="input-group-text">Max Reach</span>
                            <input 
                              type="number" 
                              class="form-control form-control-sm" 
                              v-model="searchFilters.maxReach"
                              min="0"
                            />
                          </div>
                        </div>
                      </div>
                      <div class="d-grid mt-2">
                        <button type="button" class="btn btn-sm btn-primary" @click="searchInfluencers()">
                          Apply Filters
                        </button>
                      </div>
                    </div>
                  </div>
                  
                  <div v-if="searching" class="text-center py-3">
                    <div class="spinner-border spinner-border-sm text-primary" role="status">
                      <span class="visually-hidden">Searching...</span>
                    </div>
                    <span class="ms-2">Searching...</span>
                  </div>
                  
                  <div v-if="searchResults.length > 0" class="mb-3">
                    <div class="list-group">
                      <div 
                        v-for="influencer in searchResults" 
                        :key="influencer.id"
                        class="list-group-item list-group-item-action"
                        :class="{ 'active': form.influencer_id.toString() === influencer.id.toString() }"
                        @click="form.influencer_id = influencer.id.toString()"
                      >
                        <div class="d-flex justify-content-between align-items-center">
                          <div>
                            <div class="fw-bold">{{ influencer.influencer_name }}</div>
                            <small>{{ influencer.category }} • {{ influencer.niche }}</small>
                          </div>
                          <div class="badge bg-primary rounded-pill">{{ influencer.reach.toLocaleString() }} reach</div>
                        </div>
                      </div>
                    </div>
                  </div>
                  
                  <div v-if="influencers.length > 0 && !searchQuery" class="mb-3">
                    <div class="form-label">Top Influencers</div>
                    <select v-model="form.influencer_id" class="form-select">
                      <option value="">-- Select an influencer --</option>
                      <option v-for="influencer in influencers" :key="influencer.id" :value="influencer.id">
                        {{ influencer.influencer_name }} ({{ influencer.niche }}, {{ influencer.reach.toLocaleString() }} reach)
                      </option>
                    </select>
                  </div>
                </div>
                
                <!-- Selected Influencer Details -->
                <div v-if="selectedInfluencer" class="mb-4 p-3 border rounded bg-light">
                  <div class="mb-2 fw-bold">Selected Influencer:</div>
                  <div class="d-flex justify-content-between align-items-center">
                    <div>
                      <div class="fw-bold">{{ selectedInfluencer.influencer_name }}</div>
                      <div>{{ selectedInfluencer.category }} • {{ selectedInfluencer.niche }}</div>
                    </div>
                    <div class="badge bg-primary rounded-pill">{{ selectedInfluencer.reach.toLocaleString() }} reach</div>
                  </div>
                </div>
                
                <!-- Payment amount -->
                <div class="mb-4">
                  <label for="paymentAmount" class="form-label">Payment Amount ($)</label>
                  <input
                    type="number"
                    class="form-control"
                    id="paymentAmount"
                    v-model="form.payment_amount"
                    placeholder="Enter amount in USD"
                    min="1"
                    step="1"
                  >
                  <div class="form-text">
                    Suggested: {{ formatCurrency(campaign.budget * 0.1) }} - {{ formatCurrency(campaign.budget * 0.3) }}
                  </div>
                </div>
                
                <!-- Requirements -->
                <div class="mb-4">
                  <label for="requirements" class="form-label">Requirements</label>
                  <textarea
                    class="form-control"
                    id="requirements"
                    v-model="form.requirements"
                    rows="4"
                    placeholder="Specify what you require from the influencer"
                  ></textarea>
                </div>
                
                <!-- Message -->
                <div class="mb-4">
                  <label for="message" class="form-label">Message (Optional)</label>
                  <textarea
                    class="form-control"
                    id="message"
                    v-model="form.message"
                    rows="3"
                    placeholder="Add a personal message to the influencer"
                  ></textarea>
                </div>
                
                <!-- Form actions -->
                <div class="d-flex justify-content-end">
                  <RouterLink 
                    :to="`/sponsor/campaigns/${campaignId}`" 
                    class="btn btn-outline-secondary me-2"
                  >
                    Cancel
                  </RouterLink>
                  <button
                    type="submit"
                    class="btn btn-primary"
                    :disabled="submitting"
                  >
                    <span v-if="submitting" class="spinner-border spinner-border-sm me-1" role="status" aria-hidden="true"></span>
                    Create Ad Request
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
        
        <div class="col-lg-4">
          <!-- Campaign overview -->
          <div class="card border-0 shadow-sm mb-4">
            <div class="card-body">
              <h5 class="card-title mb-3">Campaign Details</h5>
              
              <div class="mb-3 pb-3 border-bottom">
                <h6 class="text-muted mb-1">Budget</h6>
                <div class="fs-4 fw-bold text-success">
                  {{ formatCurrency(campaign.budget) }}
                </div>
              </div>
              
              <div class="mb-3 pb-3 border-bottom">
                <h6 class="text-muted mb-1">Campaign Name</h6>
                <div>{{ campaign.name }}</div>
              </div>
              
              <div v-if="campaign.description" class="mb-3 pb-3 border-bottom">
                <h6 class="text-muted mb-1">Description</h6>
                <div>{{ campaign.description }}</div>
              </div>
              
              <div v-if="campaign.goals">
                <h6 class="text-muted mb-1">Goals</h6>
                <div>{{ campaign.goals }}</div>
              </div>
            </div>
          </div>
          
          <!-- Tips box -->
          <div class="card border-0 shadow-sm">
            <div class="card-body">
              <h5 class="card-title mb-3">Tips for Success</h5>
              
              <ul class="list-group list-group-flush">
                <li class="list-group-item px-0">
                  <i class="bi bi-check-circle-fill text-success me-2"></i>
                  Be clear about your expectations and requirements
                </li>
                <li class="list-group-item px-0">
                  <i class="bi bi-check-circle-fill text-success me-2"></i>
                  Offer competitive payment based on the influencer's reach
                </li>
                <li class="list-group-item px-0">
                  <i class="bi bi-check-circle-fill text-success me-2"></i>
                  Include a personalized message explaining why you're interested
                </li>
                <li class="list-group-item px-0">
                  <i class="bi bi-check-circle-fill text-success me-2"></i>
                  Be open to negotiation if the influencer makes a counter-offer
                </li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.create-request-view {
  animation: fadeIn 0.5s ease-in-out;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}
</style> 