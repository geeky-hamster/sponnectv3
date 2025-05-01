<script setup>
import { ref, onMounted } from 'vue'
import { sponsorService } from '../../services/api'
import { formatDate } from '../../utils/dateUtils'

const loading = ref(true)
const campaigns = ref([])
const adRequests = ref([])
const error = ref('')
const stats = ref({})

onMounted(async () => {
  try {
    loading.value = true
    
    // Fetch sponsor data
    const [campaignsResponse, requestsResponse] = await Promise.all([
      sponsorService.getCampaigns(),
      sponsorService.getAdRequests()
    ])
    
    campaigns.value = campaignsResponse.data
    adRequests.value = requestsResponse.data.ad_requests || requestsResponse.data || []
    
  } catch (err) {
    console.error('Error loading sponsor dashboard:', err)
    error.value = 'Failed to load dashboard data. Please try again.'
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div class="sponsor-dashboard py-5">
    <div class="container">
      <h1 class="mb-4">Sponsor Dashboard</h1>
      
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
            <div class="card border-0 shadow-sm h-100">
              <div class="card-body p-4">
                <h5 class="card-title">Total Campaigns</h5>
                <div class="d-flex align-items-center mt-3">
                  <div class="bg-primary rounded-circle p-3 me-3">
                    <i class="bi bi-megaphone text-white fs-4"></i>
                  </div>
                  <h3 class="mb-0">{{ campaigns.length }}</h3>
                </div>
              </div>
            </div>
          </div>
          
          <div class="col-md-4 mb-3">
            <div class="card border-0 shadow-sm h-100">
              <div class="card-body p-4">
                <h5 class="card-title">Active Requests</h5>
                <div class="d-flex align-items-center mt-3">
                  <div class="bg-success rounded-circle p-3 me-3">
                    <i class="bi bi-chat-dots text-white fs-4"></i>
                  </div>
                  <h3 class="mb-0">{{ adRequests.filter ? adRequests.filter(r => r.status === 'Pending' || r.status === 'Negotiating').length : 0 }}</h3>
                </div>
              </div>
            </div>
          </div>
          
          <div class="col-md-4 mb-3">
            <div class="card border-0 shadow-sm h-100">
              <div class="card-body p-4">
                <h5 class="card-title">Accepted Partnerships</h5>
                <div class="d-flex align-items-center mt-3">
                  <div class="bg-info rounded-circle p-3 me-3">
                    <i class="bi bi-handshake text-white fs-4"></i>
                  </div>
                  <h3 class="mb-0">{{ adRequests.filter ? adRequests.filter(r => r.status === 'Accepted').length : 0 }}</h3>
                </div>
              </div>
            </div>
          </div>
        </div>
        
        <!-- Recent Campaigns -->
        <div class="card border-0 shadow-sm mb-4">
          <div class="card-header bg-white border-0 py-3">
            <div class="d-flex justify-content-between align-items-center">
              <h4 class="mb-0">Recent Campaigns</h4>
              <router-link to="/sponsor/campaigns" class="btn btn-primary btn-sm">
                View All
              </router-link>
            </div>
          </div>
          <div class="card-body p-0">
            <div v-if="campaigns.length === 0" class="p-4 text-center">
              <p class="mb-3">You haven't created any campaigns yet.</p>
              <router-link to="/sponsor/campaigns/create" class="btn btn-primary">
                Create Your First Campaign
              </router-link>
            </div>
            <div v-else class="table-responsive">
              <table class="table table-hover align-middle mb-0">
                <thead class="table-light">
                  <tr>
                    <th>Name</th>
                    <th>Budget</th>
                    <th>Status</th>
                    <th>Created</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="campaign in campaigns.slice(0, 5)" :key="campaign.id">
                    <td>{{ campaign.name }}</td>
                    <td>₹{{ campaign.budget.toLocaleString('en-IN', ) }}</td>
                    <td>
                      <span :class="{
                        'badge rounded-pill bg-success': campaign.is_visible,
                        'badge rounded-pill bg-secondary': !campaign.is_visible
                      }">
                        {{ campaign.is_visible ? 'Public' : 'Draft' }}
                      </span>
                    </td>
                    <td>{{ formatDate(campaign.created_at) }}</td>
                    <td>
                      <router-link :to="`/sponsor/campaigns/${campaign.id}`" class="btn btn-sm btn-outline-primary">
                        View
                      </router-link>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
        
        <!-- Recent Requests -->
        <div class="card border-0 shadow-sm">
          <div class="card-header bg-white border-0 py-3">
            <div class="d-flex justify-content-between align-items-center">
              <h4 class="mb-0">Recent Requests</h4>
              <router-link to="/sponsor/ad-requests" class="btn btn-primary btn-sm">
                View All
              </router-link>
            </div>
          </div>
          <div class="card-body p-0">
            <div v-if="!adRequests.length" class="p-4 text-center">
              <p>No ad requests found.</p>
            </div>
            <div v-else class="table-responsive">
              <table class="table table-hover align-middle mb-0">
                <thead class="table-light">
                  <tr>
                    <th>Campaign</th>
                    <th>Influencer</th>
                    <th>Payment</th>
                    <th>Status</th>
                    <th>Updated</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="request in adRequests.slice(0, 5)" :key="request.id">
                    <td>{{ request.campaign_name }}</td>
                    <td>{{ request.influencer_name }}</td>
                    <td>₹{{ request.payment_amount.toLocaleString('en-IN', ) }}</td>
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
                      <router-link :to="`/sponsor/ad-requests/${request.id}`" class="btn btn-sm btn-outline-primary">
                        View
                      </router-link>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template> 
