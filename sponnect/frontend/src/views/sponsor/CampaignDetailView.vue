<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter, RouterLink } from 'vue-router'
import { sponsorService } from '../../services/api'

const route = useRoute()
const router = useRouter()
const campaignId = computed(() => route.params.id)

// State
const loading = ref(true)
const campaign = ref(null)
const adRequests = ref([])
const applications = ref([])
const error = ref('')
const activeTab = ref('details')

// Load campaign data
const loadCampaign = async () => {
  loading.value = true
  error.value = ''
  
  try {
    // Fetch campaign details and its ad requests in parallel
    const [campaignResponse, adRequestsResponse, applicationsResponse] = await Promise.all([
      sponsorService.getCampaign(campaignId.value),
      sponsorService.getAdRequests({ campaign_id: campaignId.value }),
      sponsorService.getCampaignApplications(campaignId.value)
    ])
    
    campaign.value = campaignResponse.data
    adRequests.value = adRequestsResponse.data || []
    applications.value = applicationsResponse.data.applications || []
    
  } catch (err) {
    console.error('Failed to load campaign details:', err)
    error.value = 'Failed to load campaign details. Please try again later.'
  } finally {
    loading.value = false
  }
}

// Format date for display
const formatDate = (dateString) => {
  if (!dateString) return 'Not specified'
  return new Date(dateString).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'long',
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

// Handle campaign deletion
const deleteCampaign = async () => {
  if (!confirm('Are you sure you want to delete this campaign? This action cannot be undone.')) {
    return
  }
  
  try {
    await sponsorService.deleteCampaign(campaignId.value)
    router.push('/sponsor/campaigns')
  } catch (err) {
    console.error('Failed to delete campaign:', err)
    error.value = 'Failed to delete campaign. Please try again later.'
  }
}

// Accept an application
const acceptApplication = async (applicationId) => {
  if (!confirm('Are you sure you want to accept this application?')) return
  
  try {
    await sponsorService.acceptApplication(applicationId)
    // Refresh data
    loadCampaign()
  } catch (err) {
    console.error('Failed to accept application:', err)
    error.value = 'Failed to accept application. Please try again later.'
  }
}

// Reject an application
const rejectApplication = async (applicationId) => {
  if (!confirm('Are you sure you want to reject this application?')) return
  
  try {
    await sponsorService.rejectApplication(applicationId)
    // Refresh data
    loadCampaign()
  } catch (err) {
    console.error('Failed to reject application:', err)
    error.value = 'Failed to reject application. Please try again later.'
  }
}

// Load data on component mount
onMounted(() => {
  loadCampaign()
})
</script>

<template>
  <div class="campaign-detail-view py-5">
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
          <li class="breadcrumb-item active">Campaign Details</li>
        </ol>
      </nav>
      
      <!-- Loading state -->
      <div v-if="loading" class="text-center py-5">
        <div class="spinner-border text-primary" role="status">
          <span class="visually-hidden">Loading...</span>
        </div>
        <p class="mt-3">Loading campaign details...</p>
      </div>
      
      <!-- Error state -->
      <div v-else-if="error" class="alert alert-danger alert-dismissible fade show" role="alert">
        {{ error }}
        <button type="button" class="btn-close" @click="error = ''"></button>
      </div>
      
      <!-- Campaign details -->
      <div v-else-if="campaign">
        <!-- Header with actions -->
        <div class="d-flex justify-content-between align-items-start mb-4">
          <div>
            <h1 class="mb-2">{{ campaign.name }}</h1>
            <div class="d-flex align-items-center">
              <span 
                :class="{
                  'badge rounded-pill bg-success me-2': campaign.visibility === 'public',
                  'badge rounded-pill bg-secondary me-2': campaign.visibility === 'private'
                }"
              >
                {{ campaign.visibility }}
              </span>
              <span class="text-muted">Created on {{ formatDate(campaign.created_at) }}</span>
            </div>
          </div>
          <div class="d-flex">
            <RouterLink :to="`/sponsor/campaigns/${campaignId}/edit`" class="btn btn-outline-primary me-2">
              <i class="bi bi-pencil me-1"></i>Edit
            </RouterLink>
            <button @click="deleteCampaign" class="btn btn-outline-danger">
              <i class="bi bi-trash me-1"></i>Delete
            </button>
          </div>
        </div>
        
        <!-- Tabs -->
        <ul class="nav nav-tabs mb-4">
          <li class="nav-item">
            <a 
              class="nav-link" 
              :class="{ active: activeTab === 'details' }"
              href="#" 
              @click.prevent="activeTab = 'details'"
            >
              Campaign Details
            </a>
          </li>
          <li class="nav-item">
            <a 
              class="nav-link" 
              :class="{ active: activeTab === 'requests' }"
              href="#" 
              @click.prevent="activeTab = 'requests'"
            >
              Ad Requests 
              <span class="badge bg-primary rounded-pill ms-1">{{ adRequests.length }}</span>
            </a>
          </li>
          <li class="nav-item">
            <a 
              class="nav-link" 
              :class="{ active: activeTab === 'applications' }"
              href="#" 
              @click.prevent="activeTab = 'applications'"
            >
              Applications 
              <span class="badge bg-primary rounded-pill ms-1">{{ applications.length }}</span>
            </a>
          </li>
        </ul>
        
        <!-- Tab content -->
        <div class="tab-content">
          <!-- Campaign Details Tab -->
          <div v-if="activeTab === 'details'" class="tab-pane fade show active">
            <div class="row">
              <div class="col-lg-8">
                <div class="card border-0 shadow-sm mb-4">
                  <div class="card-body">
                    <h4 class="card-title mb-3">Description</h4>
                    <p class="card-text">{{ campaign.description || 'No description provided.' }}</p>
                    
                    <h4 class="card-title mt-4 mb-3">Goals</h4>
                    <p class="card-text">{{ campaign.goals || 'No goals specified.' }}</p>
                  </div>
                </div>
                
                <div class="card border-0 shadow-sm">
                  <div class="card-body">
                    <h4 class="card-title mb-3">Find Influencers</h4>
                    <p class="text-muted mb-4">Search for influencers to invite to this campaign.</p>
                    <RouterLink to="/search/influencers" class="btn btn-primary">
                      <i class="bi bi-search me-1"></i>Find Influencers
                    </RouterLink>
                  </div>
                </div>
              </div>
              
              <div class="col-lg-4">
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
                      <h6 class="text-muted mb-1">Start Date</h6>
                      <div>{{ formatDate(campaign.start_date) }}</div>
                    </div>
                    
                    <div class="mb-3 pb-3 border-bottom">
                      <h6 class="text-muted mb-1">End Date</h6>
                      <div>{{ formatDate(campaign.end_date) }}</div>
                    </div>
                    
                    <div>
                      <h6 class="text-muted mb-1">Visibility</h6>
                      <div
                        :class="{
                          'text-success': campaign.visibility === 'public',
                          'text-secondary': campaign.visibility === 'private'
                        }"
                      >
                        <i 
                          :class="{
                            'bi bi-eye-fill me-1': campaign.visibility === 'public',
                            'bi bi-eye-slash-fill me-1': campaign.visibility === 'private'
                          }"
                        ></i>
                        {{ campaign.visibility.charAt(0).toUpperCase() + campaign.visibility.slice(1) }}
                      </div>
                    </div>
                  </div>
                </div>
                
                <div class="card border-0 shadow-sm">
                  <div class="card-body">
                    <h5 class="card-title mb-3">Stats</h5>
                    
                    <div class="d-flex justify-content-between align-items-center mb-2">
                      <div>Total Ad Requests</div>
                      <div class="fw-bold">{{ adRequests.length }}</div>
                    </div>
                    
                    <div class="d-flex justify-content-between align-items-center mb-2">
                      <div>Pending Applications</div>
                      <div class="fw-bold">{{ applications.filter(a => a.status === 'Pending').length }}</div>
                    </div>
                    
                    <div class="d-flex justify-content-between align-items-center mb-2">
                      <div>Accepted Partnerships</div>
                      <div class="fw-bold">{{ adRequests.filter(r => r.status === 'Accepted').length }}</div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
          
          <!-- Ad Requests Tab -->
          <div v-if="activeTab === 'requests'" class="tab-pane fade show active">
            <div class="card border-0 shadow-sm">
              <div class="card-body">
                <div class="d-flex justify-content-between align-items-center mb-4">
                  <h4 class="mb-0">Ad Requests</h4>
                  <RouterLink :to="`/sponsor/campaigns/${campaignId}/create-request`" class="btn btn-primary btn-sm">
                    <i class="bi bi-plus-circle me-1"></i>Create Request
                  </RouterLink>
                </div>
                
                <div v-if="adRequests.length === 0" class="text-center py-4">
                  <i class="bi bi-inbox display-4 text-muted"></i>
                  <p class="mt-3 mb-1">No ad requests yet</p>
                  <p class="text-muted">Invite influencers to collaborate on this campaign.</p>
                </div>
                
                <div v-else class="table-responsive">
                  <table class="table table-hover align-middle">
                    <thead class="table-light">
                      <tr>
                        <th>Influencer</th>
                        <th>Payment</th>
                        <th>Status</th>
                        <th>Updated</th>
                        <th>Last Action By</th>
                        <th>Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr v-for="request in adRequests" :key="request.id">
                        <td>{{ request.influencer_name }}</td>
                        <td>{{ formatCurrency(request.payment_amount) }}</td>
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
                        <td>{{ request.last_offer_by }}</td>
                        <td>
                          <RouterLink :to="`/sponsor/ad-requests/${request.id}`" class="btn btn-sm btn-outline-primary">
                            View
                          </RouterLink>
                        </td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          </div>
          
          <!-- Applications Tab -->
          <div v-if="activeTab === 'applications'" class="tab-pane fade show active">
            <div class="card border-0 shadow-sm">
              <div class="card-body">
                <h4 class="mb-4">Influencer Applications</h4>
                
                <div v-if="applications.length === 0" class="text-center py-4">
                  <i class="bi bi-inbox display-4 text-muted"></i>
                  <p class="mt-3 mb-1">No applications yet</p>
                  <p class="text-muted">
                    If your campaign is public, influencers can apply to collaborate.
                  </p>
                </div>
                
                <div v-else class="table-responsive">
                  <table class="table table-hover align-middle">
                    <thead class="table-light">
                      <tr>
                        <th>Influencer</th>
                        <th>Requested Payment</th>
                        <th>Date Applied</th>
                        <th>Status</th>
                        <th>Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr v-for="application in applications" :key="application.id">
                        <td>{{ application.influencer_name }}</td>
                        <td>{{ formatCurrency(application.payment_amount) }}</td>
                        <td>{{ formatDate(application.created_at) }}</td>
                        <td>
                          <span 
                            :class="{
                              'badge rounded-pill bg-warning': application.status === 'Pending',
                              'badge rounded-pill bg-success': application.status === 'Accepted',
                              'badge rounded-pill bg-danger': application.status === 'Rejected'
                            }"
                          >
                            {{ application.status }}
                          </span>
                        </td>
                        <td>
                          <div v-if="application.status === 'Pending'" class="btn-group">
                            <button @click="acceptApplication(application.id)" class="btn btn-sm btn-success">
                              Accept
                            </button>
                            <button @click="rejectApplication(application.id)" class="btn btn-sm btn-danger">
                              Reject
                            </button>
                          </div>
                          <RouterLink v-else :to="`/sponsor/ad-requests/${application.id}`" class="btn btn-sm btn-outline-primary">
                            View
                          </RouterLink>
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
    </div>
  </div>
</template>

<style scoped>
.campaign-detail-view {
  animation: fadeIn 0.5s ease-in-out;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

.tab-content {
  padding-top: 1rem;
}
</style> 