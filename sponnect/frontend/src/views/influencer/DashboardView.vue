<script setup>
import { ref, onMounted, computed } from 'vue'
import { influencerService, searchService } from '../../services/api'
import { formatDate } from '../../utils/dateUtils'

const loading = ref(true)
const adRequests = ref([])
const publicCampaigns = ref([])
const error = ref('')
const showDebugInfo = ref(false)
const debugMessages = ref([])

// Helper function to add debug messages
const addDebugMessage = (message) => {
  const timestamp = new Date().toLocaleTimeString()
  debugMessages.value.unshift(`${timestamp}: ${message}`)
  // Limit debug history to 10 messages
  if (debugMessages.value.length > 10) {
    debugMessages.value.pop()
  }
}

// Manual refresh function
const refreshDashboard = async () => {
  try {
    addDebugMessage('Manually refreshing dashboard...')
    loading.value = true
    error.value = ''
    
    // Fetch influencer data
    const [requestsResponse, campaignsResponse] = await Promise.all([
      influencerService.getAdRequests(),
      searchService.searchCampaigns({
        _t: Date.now() // Add timestamp to prevent caching
      })
    ])
    
    adRequests.value = Array.isArray(requestsResponse.data) ? requestsResponse.data : []
    addDebugMessage(`Loaded ${adRequests.value.length} ad requests`)
    
    // Properly extract campaigns from the response
    if (campaignsResponse.data) {
      addDebugMessage(`Campaign response type: ${typeof campaignsResponse.data}`)
      
      if (campaignsResponse.data.campaigns && Array.isArray(campaignsResponse.data.campaigns)) {
        // Response with pagination object format
        publicCampaigns.value = campaignsResponse.data.campaigns.slice(0, 5)
        addDebugMessage(`Extracted ${publicCampaigns.value.length} campaigns from pagination format`)
      } else if (Array.isArray(campaignsResponse.data)) {
        // Direct array format 
        publicCampaigns.value = campaignsResponse.data.slice(0, 5)
        addDebugMessage(`Extracted ${publicCampaigns.value.length} campaigns from array format`)
      } else {
        console.error('Unexpected campaigns response format:', campaignsResponse.data)
        addDebugMessage(`Error: Unexpected response format - ${JSON.stringify(campaignsResponse.data).substring(0, 100)}...`)
        publicCampaigns.value = []
      }
    } else {
      console.error('No data in campaigns response')
      addDebugMessage('Error: No data in campaigns response')
      publicCampaigns.value = []
    }
    
  } catch (err) {
    console.error('Error refreshing dashboard:', err)
    addDebugMessage(`Error refreshing: ${err.message}`)
    error.value = 'Failed to refresh dashboard data. Please try again.'
  } finally {
    loading.value = false
  }
}

// Toggle debug info
const toggleDebugInfo = () => {
  showDebugInfo.value = !showDebugInfo.value
}

// Development mode check
const isDevelopmentMode = computed(() => {
  try {
    return import.meta.env.DEV === true
  } catch (e) {
    return false
  }
})

onMounted(async () => {
  try {
    loading.value = true
    
    // Fetch influencer data
    const [requestsResponse, campaignsResponse] = await Promise.all([
      influencerService.getAdRequests(),
      searchService.searchCampaigns({
        _t: Date.now() // Add timestamp to prevent caching
      })
    ])
    
    adRequests.value = Array.isArray(requestsResponse.data) ? requestsResponse.data : []
    
    // Properly extract campaigns from the response
    if (campaignsResponse.data) {
      if (campaignsResponse.data.campaigns && Array.isArray(campaignsResponse.data.campaigns)) {
        // Response with pagination object format
        publicCampaigns.value = campaignsResponse.data.campaigns.slice(0, 5)
      } else if (Array.isArray(campaignsResponse.data)) {
        // Direct array format 
        publicCampaigns.value = campaignsResponse.data.slice(0, 5)
      } else {
        console.error('Unexpected campaigns response format:', campaignsResponse.data)
        publicCampaigns.value = []
      }
    } else {
      console.error('No data in campaigns response')
      publicCampaigns.value = []
    }
    
    // Add debug log
    console.log(`Loaded ${publicCampaigns.value.length} campaigns for dashboard`)
    
  } catch (err) {
    console.error('Error loading influencer dashboard:', err)
    error.value = 'Failed to load dashboard data. Please try again.'
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div class="influencer-dashboard py-5">
    <div class="container">
      <h1 class="mb-4 dashboard-title">Influencer Dashboard</h1>
      
      <!-- Debug panel (only visible in development mode) -->
      <div v-if="isDevelopmentMode" class="card mb-4 bg-light">
        <div class="card-body">
          <div class="d-flex justify-content-between align-items-center">
            <h5 class="card-title mb-0">Debug Tools</h5>
            <div>
              <button @click="refreshDashboard" class="btn btn-sm btn-primary me-2">
                <i class="bi bi-arrow-clockwise me-1"></i> Refresh Data
              </button>
              <button @click="toggleDebugInfo" class="btn btn-sm btn-secondary">
                {{ showDebugInfo ? 'Hide' : 'Show' }} Debug Info
              </button>
            </div>
          </div>
          
          <div v-if="showDebugInfo" class="mt-3">
            <div class="alert alert-info">
              <strong>Dashboard Status:</strong> 
              <span class="ms-2">Ad Requests: {{ adRequests.length }}</span> | 
              <span>Campaigns: {{ publicCampaigns.length }}</span>
            </div>
            <div class="mt-2">
              <strong>Debug Log:</strong>
              <div class="bg-dark text-light p-2 mt-1" style="max-height: 200px; overflow: auto; font-size: 12px;">
                <div v-for="(msg, idx) in debugMessages" :key="idx">{{ msg }}</div>
                <div v-if="!debugMessages.length">No debug messages yet</div>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <div v-if="loading" class="text-center py-5">
        <div class="spinner-border text-primary" role="status">
          <span class="visually-hidden">Loading...</span>
        </div>
        <p class="mt-3">Loading your dashboard...</p>
      </div>
      
      <div v-else-if="error" class="alert alert-danger">
        {{ error }}
        <button @click="refreshDashboard" class="btn btn-sm btn-outline-danger ms-3">Try Again</button>
      </div>
      
      <div v-else>
        <!-- Dashboard Summary -->
        <div class="row mb-4">
          <div class="col-md-4 mb-3">
            <div class="card border-0 dashboard-card gradient-purple h-100">
              <div class="card-body p-4">
                <h5 class="card-title text-white">Total Requests</h5>
                <div class="d-flex align-items-center mt-3">
                  <div class="icon-container me-3">
                    <i class="bi bi-collection text-white fs-4"></i>
                  </div>
                  <h3 class="mb-0 text-white">{{ adRequests.length || 0 }}</h3>
                </div>
              </div>
            </div>
          </div>
          
          <div class="col-md-4 mb-3">
            <div class="card border-0 dashboard-card gradient-orange h-100">
              <div class="card-body p-4">
                <h5 class="card-title text-white">Active Negotiations</h5>
                <div class="d-flex align-items-center mt-3">
                  <div class="icon-container me-3">
                    <i class="bi bi-chat-square-text text-white fs-4"></i>
                  </div>
                  <h3 class="mb-0 text-white">{{ adRequests.filter ? adRequests.filter(r => r.status === 'Negotiating').length : 0 }}</h3>
                </div>
              </div>
            </div>
          </div>
          
          <div class="col-md-4 mb-3">
            <div class="card border-0 dashboard-card gradient-green h-100">
              <div class="card-body p-4">
                <h5 class="card-title text-white">Active Partnerships</h5>
                <div class="d-flex align-items-center mt-3">
                  <div class="icon-container me-3">
                    <i class="bi bi-stars text-white fs-4"></i>
                  </div>
                  <h3 class="mb-0 text-white">{{ adRequests.filter ? adRequests.filter(r => r.status === 'Accepted').length : 0 }}</h3>
                </div>
              </div>
            </div>
          </div>
        </div>
        
        <!-- Ad Requests -->
        <div class="card border-0 content-card mb-4">
          <div class="card-header bg-white border-0 py-3">
            <div class="d-flex justify-content-between align-items-center">
              <h4 class="mb-0">Recent Ad Requests</h4>
              <router-link to="/influencer/ad-requests" class="btn btn-primary btn-sm">
                View All
              </router-link>
            </div>
          </div>
          <div class="card-body p-0">
            <div v-if="!adRequests.length" class="p-4 text-center">
              <p>You don't have any ad requests yet.</p>
            </div>
            <div v-else class="table-responsive">
              <table class="table table-hover align-middle mb-0">
                <thead class="table-light">
                  <tr>
                    <th>Campaign</th>
                    <th>Offer Amount</th>
                    <th>Status</th>
                    <th>Updated</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="request in adRequests.slice ? adRequests.slice(0, 5) : []" :key="request.id">
                    <td>{{ request.campaign_name }}</td>
                    <td>₹{{ request.payment_amount ? request.payment_amount.toLocaleString('en-IN', ) : '0' }}</td>
                    <td>
                      <span 
                        :class="{
                          'badge rounded-pill bg-warning': request.status === 'Pending',
                          'badge rounded-pill bg-info': request.status === 'Negotiating',
                          'badge rounded-pill bg-success': request.status === 'Accepted',
                          'badge rounded-pill bg-danger': request.status === 'Rejected'
                        }"
                      >
                        {{ request.status }}
                      </span>
                    </td>
                    <td>{{ formatDate(request.updated_at) }}</td>
                    <td>
                      <router-link :to="`/influencer/ad-requests/${request.id}`" class="btn btn-sm btn-outline-primary">
                        View
                      </router-link>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
        
        <!-- Available Campaigns -->
        <div class="card border-0 content-card">
          <div class="card-header bg-white border-0 py-3">
            <div class="d-flex justify-content-between align-items-center">
              <h4 class="mb-0">Available Campaigns</h4>
              <div>
                <button v-if="isDevelopmentMode" @click="refreshDashboard" class="btn btn-sm btn-outline-secondary me-2">
                  <i class="bi bi-arrow-clockwise"></i> Refresh
                </button>
                <router-link to="/influencer/campaigns/browse" class="btn btn-primary btn-sm">
                  Browse All
                </router-link>
              </div>
            </div>
          </div>
          <div class="card-body">
            <div v-if="!publicCampaigns.length" class="text-center">
              <p>No public campaigns available at the moment.</p>
              <button class="btn btn-sm btn-outline-primary mt-2" @click="refreshDashboard">
                <i class="bi bi-arrow-clockwise me-1"></i> Check Again
              </button>
            </div>
            <div v-else class="row g-4">
              <div v-for="campaign in publicCampaigns" :key="campaign.id" class="col-md-6">
                <div class="card h-100 campaign-card">
                  <div class="card-body">
                    <h5 class="card-title">{{ campaign.name }}</h5>
                    <div class="d-flex justify-content-between mb-2">
                      <span class="text-muted">Budget:</span>
                      <span class="fw-bold">₹{{ campaign.budget ? campaign.budget.toLocaleString('en-IN', ) : '0' }}</span>
                    </div>
                    <p class="card-text mb-3">{{ campaign.description?.substring(0, 120) }}{{ campaign.description?.length > 120 ? '...' : '' }}</p>
                    <router-link :to="`/campaigns/${campaign.id}`" class="btn btn-outline-primary btn-sm">
                      View Details & Apply
                    </router-link>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template> 

<style>
.influencer-dashboard {
  background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
}

.dashboard-title {
  font-weight: 700;
  margin-bottom: 1.5rem;
  border-bottom: 2px solid #7209B7;
  padding-bottom: 0.5rem;
  display: inline-block;
}

.dashboard-card {
  border-radius: 12px;
  box-shadow: 0 8px 16px rgba(0,0,0,0.1);
  transition: transform 0.3s, box-shadow 0.3s;
  overflow: hidden;
}

.dashboard-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 12px 20px rgba(0,0,0,0.15);
}

.gradient-purple {
  background: linear-gradient(135deg, #7209B7, #560BAD);
}

.gradient-orange {
  background: linear-gradient(135deg, #F48C06, #E85D04);
}

.gradient-green {
  background: linear-gradient(135deg, #38B000, #008000);
}

.icon-container {
  width: 50px;
  height: 50px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.2);
  display: flex;
  align-items: center;
  justify-content: center;
}

.content-card {
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.08);
  transition: box-shadow 0.3s;
}

.content-card:hover {
  box-shadow: 0 8px 16px rgba(0,0,0,0.12);
}

.campaign-card {
  border-radius: 10px;
  border: none;
  box-shadow: 0 4px 8px rgba(0,0,0,0.05);
  transition: transform 0.3s, box-shadow 0.3s;
}

.campaign-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 6px 12px rgba(0,0,0,0.1);
}
</style>  
