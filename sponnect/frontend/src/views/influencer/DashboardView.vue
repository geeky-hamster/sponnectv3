<script setup>
import { ref, onMounted } from 'vue'
import { influencerService, searchService } from '../../services/api'
import { formatDate } from '../../utils/dateUtils'

const loading = ref(true)
const adRequests = ref([])
const publicCampaigns = ref([])
const error = ref('')

onMounted(async () => {
  try {
    loading.value = true
    
    // Fetch influencer data
    const [requestsResponse, campaignsResponse] = await Promise.all([
      influencerService.getAdRequests(),
      searchService.searchCampaigns() // Get public campaigns
    ])
    
    adRequests.value = Array.isArray(requestsResponse.data) ? requestsResponse.data : []
    publicCampaigns.value = Array.isArray(campaignsResponse.data) ? campaignsResponse.data.slice(0, 5) : [] // Limit to 5 campaigns
    
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
      
      <div v-if="loading" class="text-center py-5">
        <div class="spinner-border text-primary" role="status">
          <span class="visually-hidden">Loading...</span>
        </div>
        <p class="mt-3">Loading your dashboard...</p>
      </div>
      
      <div v-else-if="error" class="alert alert-danger">
        {{ error }}
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
              <router-link to="/influencer/campaigns/browse" class="btn btn-primary btn-sm">
                Browse All
              </router-link>
            </div>
          </div>
          <div class="card-body">
            <div v-if="!publicCampaigns.length" class="text-center">
              <p>No public campaigns available at the moment.</p>
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
