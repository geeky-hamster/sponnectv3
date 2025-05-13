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
  { id: 'beauty', name: 'Beauty' },
  { id: 'fashion', name: 'Fashion' },
  { id: 'food', name: 'Food' },
  { id: 'technology', name: 'Technology' },
  { id: 'travel', name: 'Travel' },
  { id: 'gaming', name: 'Gaming' },
  { id: 'fitness', name: 'Fitness' },
  { id: 'business', name: 'Business' },
  { id: 'education', name: 'Education' },
  { id: 'entertainment', name: 'Entertainment' },
  { id: 'health', name: 'Health' },
  { id: 'sports', name: 'Sports' },
  { id: 'parenting', name: 'Parenting' },
  { id: 'lifestyle', name: 'Lifestyle' },  
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
    // Get campaign details and search for popular influencers
    const [campaignResponse, influencersResponse] = await Promise.all([
      sponsorService.getCampaign(campaignId.value),
      searchService.searchInfluencers({ 
        category: '', 
        limit: 20, 
        sort: 'popularity' 
      }) // Get some initial popular influencers
    ])
    
    campaign.value = campaignResponse.data
    influencers.value = influencersResponse.data || []
    
    // Set initial payment amount suggestion from campaign budget
    if (campaign.value) {
      form.value.payment_amount = Math.round(campaign.value.budget * 0.1) // Suggest 10% of budget as default
      
      // Set default requirements based on campaign category and goals if available
      if (campaign.value.goals) {
        form.value.requirements = `Based on our campaign goals: ${campaign.value.goals}\n\nOur campaign is in the ${campaign.value.category || 'marketing'} category and we're looking for engaging content that resonates with your audience.`
      }

      // Pre-filter influencers based on campaign category if possible
      if (campaign.value.category) {
        searchFilters.category = campaign.value.category
        searchInfluencers() // Auto-search based on campaign category
      }
    }
    
    // If influencer_id was provided in the URL, set it and show the selection
    if (route.query.influencer_id) {
      form.value.influencer_id = route.query.influencer_id
      
      // If the influencer isn't in our list yet, fetch their details
      if (!influencers.value.find(i => i.id.toString() === form.value.influencer_id.toString())) {
        try {
          const response = await searchService.searchInfluencers({ 
            query: form.value.influencer_id 
          })
          
          // If we found the influencer, add them to our list
          const foundInfluencer = response.data?.find(i => i.id.toString() === form.value.influencer_id.toString())
          if (foundInfluencer) {
            influencers.value.unshift(foundInfluencer) // Add to start of list
          }
        } catch (err) {
          console.error('Failed to fetch influencer details:', err)
        }
      }
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
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
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
    
    console.log(`Submitting ad request for campaign ${campaignId.value} to influencer ${requestData.influencer_id}`)
    
    // Add debug information to help trace issues
    const selectedInfluencerData = selectedInfluencer.value || {}
    console.log('Selected influencer data:', 
      { 
        id: selectedInfluencerData.id,
        name: selectedInfluencerData.influencer_name,
        approved: selectedInfluencerData.influencer_approved,
        active: selectedInfluencerData.is_active
      }
    )
    
    const response = await sponsorService.createAdRequest(campaignId.value, requestData)
    console.log('Ad request created successfully:', response.data)
    
    // Redirect to campaign details page
    router.push(`/sponsor/campaigns/${campaignId.value}?tab=requests`)
  } catch (err) {
    console.error('Failed to create ad request:', err)
    
    // Handle specific error cases
    if (err.response) {
      const statusCode = err.response.status
      const responseData = err.response.data
      
      console.log(`Server response: ${statusCode}`, responseData)
      
      // Handle duplicate ad request case (409 Conflict)
      if (statusCode === 409) {
        const adRequestId = responseData.ad_request_id
        
        if (adRequestId) {
          error.value = `${responseData.message}. <a href="/sponsor/ad-requests/${adRequestId}" class="alert-link">View existing request</a>` 
        } else {
          error.value = responseData.message || 'A request for this influencer already exists'
        }
      } 
      // Handle influencer not found/approved issues
      else if (statusCode === 404) {
        error.value = responseData.message || 'The selected influencer is not available. They may be pending approval or inactive.'
      }
      // Handle server errors
      else if (statusCode === 500) {
        error.value = responseData.message || 'A server error occurred. Please try again later or contact support.'
      }
      // Handle any other error
      else {
        error.value = responseData.message || `Error ${statusCode}: Failed to create ad request`
      }
    } else if (err.message) {
      // Handle client-side errors or custom error messages
      error.value = err.message
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

// New function to select an influencer
const selectInfluencer = (influencer) => {
  form.value.influencer_id = influencer.id.toString()
}
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
                  <label class="form-label fw-bold">Select Influencer</label>
                  
                  <div class="input-group mb-3">
                    <span class="input-group-text bg-light border-end-0">
                      <i class="bi bi-search"></i>
                    </span>
                    <input 
                      type="text" 
                      v-model="searchQuery" 
                      class="form-control border-start-0" 
                      placeholder="Search for influencers by name, category, or niche..."
                    />
                    <button 
                      class="btn btn-primary"
                      type="button"
                      @click="searchInfluencers"
                      :disabled="searching"
                    >
                      <i class="bi bi-search"></i>
                    </button>
                  </div>
                  
                  <!-- Advanced search filters -->
                  <div class="card bg-light border-0 mt-2 mb-3">
                    <div class="card-body">
                      <div class="d-flex justify-content-between align-items-center mb-2">
                        <h6 class="mb-0 fw-bold">Advanced Filters</h6>
                        <button type="button" class="btn btn-sm btn-outline-secondary" 
                                @click="searchFilters.category = ''; searchFilters.niche = ''; searchFilters.minReach = ''; searchFilters.maxReach = ''">
                          Reset
                        </button>
                      </div>
                      <div class="row g-2">
                        <div class="col-md-6">
                          <label class="form-label small">Category</label>
                          <select class="form-select" v-model="searchFilters.category">
                            <option v-for="category in categories" :key="category.id" :value="category.id">
                              {{ category.name }}
                            </option>
                          </select>
                        </div>
                        <div class="col-md-6">
                          <label class="form-label small">Niche</label>
                          <input 
                            type="text" 
                            class="form-control" 
                            placeholder="E.g., cooking, fitness, tech reviews" 
                            v-model="searchFilters.niche"
                          />
                        </div>
                        <div class="col-md-6">
                          <label class="form-label small">Min Reach</label>
                          <div class="input-group">
                            <input 
                              type="number" 
                              class="form-control" 
                              v-model="searchFilters.minReach"
                              min="0"
                              placeholder="1000"
                            />
                            <span class="input-group-text">followers</span>
                          </div>
                        </div>
                        <div class="col-md-6">
                          <label class="form-label small">Max Reach</label>
                          <div class="input-group">
                            <input 
                              type="number" 
                              class="form-control" 
                              v-model="searchFilters.maxReach"
                              min="0"
                              placeholder="100000"
                            />
                            <span class="input-group-text">followers</span>
                          </div>
                        </div>
                      </div>
                      <div class="d-grid mt-3">
                        <button type="button" class="btn btn-primary" @click="searchInfluencers()">
                          <i class="bi bi-filter-circle me-1"></i> Apply Filters
                        </button>
                      </div>
                    </div>
                  </div>
                  
                  <!-- Influencer search results -->
                  <div class="list-group mb-3">
                    <div v-if="searching" class="text-center p-3">
                      <div class="spinner-border spinner-border-sm text-primary" role="status">
                        <span class="visually-hidden">Searching...</span>
                      </div>
                      <span class="ms-2">Searching for influencers...</span>
                    </div>
                    
                    <div v-else-if="searchResults.length === 0 && searchQuery" class="alert alert-info">
                      No influencers found matching your search criteria.
                    </div>
                    
                    <div v-for="influencer in searchResults" :key="influencer.id" 
                         class="list-group-item list-group-item-action d-flex justify-content-between align-items-center"
                         :class="{'active': form.influencer_id === influencer.id.toString()}"
                         @click="selectInfluencer(influencer)">
                      <div>
                        <div class="d-flex align-items-center">
                          <strong class="me-2">{{ influencer.influencer_name || influencer.username }}</strong>
                          <!-- Add status indicator to help sponsors verify that influencers are approved and active -->
                          <span v-if="influencer.influencer_approved" class="badge bg-success me-2">
                            <i class="bi bi-check-circle-fill me-1"></i>Verified
                          </span>
                        </div>
                        <small>
                          {{ influencer.category }}
                          <span v-if="influencer.niche">• {{ influencer.niche }}</span>
                          <span v-if="influencer.reach">• {{ influencer.reach.toLocaleString() }} followers</span>
                        </small>
                      </div>
                      <button type="button" class="btn btn-sm" 
                              :class="form.influencer_id === influencer.id.toString() ? 'btn-light' : 'btn-primary'"
                              @click.stop="selectInfluencer(influencer)">
                        {{ form.influencer_id === influencer.id.toString() ? 'Selected' : 'Select' }}
                      </button>
                    </div>
                  </div>
                  
                  <!-- Top Influencers - when no search has been performed -->
                  <div v-if="!selectedInfluencer && !searchQuery && influencers.length > 0 && searchResults.length === 0" class="mb-4">
                    <h6 class="form-label mb-3">
                      <i class="bi bi-stars me-1"></i> Recommended Influencers
                    </h6>
                    
                    <div class="row row-cols-1 row-cols-md-2 g-3">
                      <div 
                        v-for="influencer in influencers" 
                        :key="influencer.id"
                        class="col"
                      >
                        <div 
                          class="card h-100 border"
                          :class="{ 'border-primary': form.influencer_id.toString() === influencer.id.toString() }"
                          style="cursor: pointer;"
                          @click="form.influencer_id = influencer.id.toString()"
                        >
                          <div class="card-body p-3">
                            <div class="d-flex justify-content-between align-items-center mb-2">
                              <h6 class="card-title mb-0 fw-bold">{{ influencer.influencer_name }}</h6>
                              <span class="badge bg-primary rounded-pill">{{ influencer.reach.toLocaleString('en-IN', ) }}</span>
                            </div>
                            <div class="mb-2">
                              <span class="badge bg-light text-dark me-1">{{ influencer.category }}</span>
                              <span v-if="influencer.niche" class="badge bg-light text-dark">{{ influencer.niche }}</span>
                            </div>
                            <div class="d-grid">
                              <button 
                                @click.stop="form.influencer_id = influencer.id.toString()" 
                                class="btn btn-sm"
                                :class="form.influencer_id.toString() === influencer.id.toString() ? 'btn-success' : 'btn-outline-primary'"
                              >
                                <i 
                                  :class="form.influencer_id.toString() === influencer.id.toString() ? 'bi bi-check-circle-fill' : 'bi bi-person-plus-fill'"
                                  class="me-1"
                                ></i>
                                {{ form.influencer_id.toString() === influencer.id.toString() ? 'Selected' : 'Select' }}
                              </button>
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                  
                  <!-- No results state -->
                  <div v-if="searchQuery && searchResults.length === 0 && !searching" class="alert alert-info">
                    <i class="bi bi-info-circle-fill me-2"></i> 
                    No influencers found matching your search criteria. Try adjusting your filters or search terms.
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
                    <div class="badge bg-primary rounded-pill">{{ selectedInfluencer.reach.toLocaleString('en-IN', ) }} reach</div>
                  </div>
                </div>
                
                <!-- Payment amount -->
                <div class="mb-4">
                  <label for="paymentAmount" class="form-label">Payment Amount (₹)</label>
                  <input
                    type="number"
                    class="form-control"
                    id="paymentAmount"
                    v-model="form.payment_amount"
                    placeholder="Enter amount in INR"
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