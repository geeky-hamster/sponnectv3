<script setup>
import { ref, onMounted, computed } from 'vue'
import { adminService } from '../../services/api'

const loading = ref(true)
const stats = ref({
  total_users: 0,
  active_sponsors: 0,
  active_influencers: 0,
  public_campaigns: 0,
  private_campaigns: 0,
  ad_requests_by_status: {
    Pending: 0,
    Negotiating: 0,
    Accepted: 0,
    Rejected: 0
  },
  flagged_users: 0,
  flagged_campaigns: 0
})
const pendingSponsors = ref([])
const dashboardSummary = ref({
  userSummary: {
    labels: [],
    datasets: []
  },
  campaignVisibility: {
    labels: [],
    datasets: []
  },
  adRequestStatus: {
    labels: [],
    datasets: []
  },
  conversionRate: {
    value: 0,
    label: 'Acceptance Rate'
  }
})
const error = ref('')

// Calculate the percentage for ad request status
const getStatusPercentage = (status) => {
  if (!stats.value || !stats.value.ad_requests_by_status) return 0
  
  const total = Object.values(stats.value.ad_requests_by_status).reduce((sum, val) => sum + val, 0)
  if (total === 0) return 0
  
  return (stats.value.ad_requests_by_status[status] || 0) / total * 100
}

onMounted(async () => {
  try {
    loading.value = true
    
    // Fetch admin data
    const [statsResponse, pendingResponse] = await Promise.all([
      adminService.getStats(),
      adminService.getPendingSponsors()
    ])
    
    stats.value = statsResponse.data
    pendingSponsors.value = pendingResponse.data
    
    // Initialize dashboard summary with empty data
    dashboardSummary.value = {
      userSummary: {
        labels: [],
        datasets: []
      },
      campaignVisibility: {
        labels: ['Public', 'Private'],
        datasets: [{
          data: [stats.value.public_campaigns || 0, stats.value.private_campaigns || 0]
        }]
      },
      adRequestStatus: {
        labels: Object.keys(stats.value.ad_requests_by_status || {}),
        datasets: [{
          data: Object.values(stats.value.ad_requests_by_status || {})
        }]
      },
      conversionRate: {
        value: stats.value.ad_requests_by_status?.Accepted / 
               Object.values(stats.value.ad_requests_by_status || {}).reduce((sum, val) => sum + val, 0) * 100 || 0,
        label: 'Acceptance Rate'
      }
    }
    
  } catch (err) {
    console.error('Error loading admin dashboard:', err)
    error.value = 'Failed to load dashboard data. Please try again.'
  } finally {
    loading.value = false
  }
})

const approveSponsor = async (sponsorId) => {
  try {
    await adminService.approveSponsor(sponsorId)
    // Remove approved sponsor from the list
    pendingSponsors.value = pendingSponsors.value.filter(sponsor => sponsor.id !== sponsorId)
  } catch (err) {
    console.error('Error approving sponsor:', err)
    error.value = 'Failed to approve sponsor. Please try again.'
  }
}

const rejectSponsor = async (sponsorId) => {
  try {
    await adminService.rejectSponsor(sponsorId)
    // Remove rejected sponsor from the list
    pendingSponsors.value = pendingSponsors.value.filter(sponsor => sponsor.id !== sponsorId)
  } catch (err) {
    console.error('Error rejecting sponsor:', err)
    error.value = 'Failed to reject sponsor. Please try again.'
  }
}
</script>

<template>
  <div class="admin-dashboard py-5">
    <div class="container">
      <h1 class="mb-4">Admin Dashboard</h1>
      
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
        <!-- Stats Overview -->
        <div class="row mb-4">
          <div class="col-md-3 mb-3">
            <div class="card border-0 shadow-sm h-100">
              <div class="card-body p-4">
                <h5 class="card-title">Total Users</h5>
                <div class="d-flex align-items-center mt-3">
                  <div class="bg-primary rounded-circle p-3 me-3">
                    <i class="bi bi-people text-white fs-4"></i>
                  </div>
                  <h3 class="mb-0">{{ stats.total_users }}</h3>
                </div>
              </div>
            </div>
          </div>
          
          <div class="col-md-3 mb-3">
            <div class="card border-0 shadow-sm h-100">
              <div class="card-body p-4">
                <h5 class="card-title">Active Sponsors</h5>
                <div class="d-flex align-items-center mt-3">
                  <div class="bg-success rounded-circle p-3 me-3">
                    <i class="bi bi-briefcase text-white fs-4"></i>
                  </div>
                  <h3 class="mb-0">{{ stats.active_sponsors }}</h3>
                </div>
              </div>
            </div>
          </div>
          
          <div class="col-md-3 mb-3">
            <div class="card border-0 shadow-sm h-100">
              <div class="card-body p-4">
                <h5 class="card-title">Active Influencers</h5>
                <div class="d-flex align-items-center mt-3">
                  <div class="bg-info rounded-circle p-3 me-3">
                    <i class="bi bi-person-badge text-white fs-4"></i>
                  </div>
                  <h3 class="mb-0">{{ stats.active_influencers }}</h3>
                </div>
              </div>
            </div>
          </div>
          
          <div class="col-md-3 mb-3">
            <div class="card border-0 shadow-sm h-100">
              <div class="card-body p-4">
                <h5 class="card-title">Total Campaigns</h5>
                <div class="d-flex align-items-center mt-3">
                  <div class="bg-warning rounded-circle p-3 me-3">
                    <i class="bi bi-megaphone text-white fs-4"></i>
                  </div>
                  <h3 class="mb-0">{{ stats.public_campaigns + stats.private_campaigns }}</h3>
                </div>
              </div>
            </div>
          </div>
        </div>
        
        <!-- Pending Sponsors Approval -->
        <div class="card border-0 shadow-sm mb-4">
          <div class="card-header bg-white border-0 py-3">
            <div class="d-flex justify-content-between align-items-center">
              <h4 class="mb-0">
                Pending Sponsor Approvals
                <span class="badge bg-warning ms-2">{{ pendingSponsors.length }}</span>
              </h4>
              <router-link to="/admin/users" class="btn btn-primary btn-sm">
                Manage All Users
              </router-link>
            </div>
          </div>
          <div class="card-body p-0">
            <div v-if="pendingSponsors.length === 0" class="p-4 text-center">
              <p>No pending sponsor approvals.</p>
            </div>
            <div v-else class="table-responsive">
              <table class="table table-hover align-middle mb-0">
                <thead class="table-light">
                  <tr>
                    <th>Username</th>
                    <th>Company</th>
                    <th>Industry</th>
                    <th>Registered On</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="sponsor in pendingSponsors" :key="sponsor.id">
                    <td>{{ sponsor.username }}</td>
                    <td>{{ sponsor.company_name }}</td>
                    <td>{{ sponsor.industry }}</td>
                    <td>{{ new Date(sponsor.created_at).toLocaleDateString() }}</td>
                    <td>
                      <div class="btn-group" role="group">
                        <button @click="approveSponsor(sponsor.id)" class="btn btn-sm btn-success me-2">
                          <i class="bi bi-check-circle me-1"></i> Approve
                        </button>
                        <button @click="rejectSponsor(sponsor.id)" class="btn btn-sm btn-danger">
                          <i class="bi bi-x-circle me-1"></i> Reject
                        </button>
                      </div>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
        
        <!-- Platform Statistics -->
        <div class="row mb-4">
          <div class="col-md-6 mb-3">
            <div class="card border-0 shadow-sm h-100">
              <div class="card-header bg-white border-0 py-3">
                <h4 class="mb-0">Ad Request Status</h4>
              </div>
              <div class="card-body">
                <div v-if="stats && stats.ad_requests_by_status" class="mb-3">
                  <div class="progress" style="height: 2rem;">
                    <div class="progress-bar bg-warning" 
                         :style="`width: ${getStatusPercentage('Pending')}%`" 
                         role="progressbar">
                      Pending
                    </div>
                    <div class="progress-bar bg-info" 
                         :style="`width: ${getStatusPercentage('Negotiating')}%`" 
                         role="progressbar">
                      Negotiating
                    </div>
                    <div class="progress-bar bg-success" 
                         :style="`width: ${getStatusPercentage('Accepted')}%`" 
                         role="progressbar">
                      Accepted
                    </div>
                    <div class="progress-bar bg-danger" 
                         :style="`width: ${getStatusPercentage('Rejected')}%`" 
                         role="progressbar">
                      Rejected
                    </div>
                  </div>
                  
                  <div class="row mt-4">
                    <div class="col-6 col-md-3 mb-2">
                      <div class="d-flex align-items-center">
                        <span class="badge bg-warning p-2 me-2"></span>
                        <div>
                          <div>Pending</div>
                          <div class="fw-bold">{{ stats.ad_requests_by_status.Pending || 0 }}</div>
                        </div>
                      </div>
                    </div>
                    <div class="col-6 col-md-3 mb-2">
                      <div class="d-flex align-items-center">
                        <span class="badge bg-info p-2 me-2"></span>
                        <div>
                          <div>Negotiating</div>
                          <div class="fw-bold">{{ stats.ad_requests_by_status.Negotiating || 0 }}</div>
                        </div>
                      </div>
                    </div>
                    <div class="col-6 col-md-3 mb-2">
                      <div class="d-flex align-items-center">
                        <span class="badge bg-success p-2 me-2"></span>
                        <div>
                          <div>Accepted</div>
                          <div class="fw-bold">{{ stats.ad_requests_by_status.Accepted || 0 }}</div>
                        </div>
                      </div>
                    </div>
                    <div class="col-6 col-md-3 mb-2">
                      <div class="d-flex align-items-center">
                        <span class="badge bg-danger p-2 me-2"></span>
                        <div>
                          <div>Rejected</div>
                          <div class="fw-bold">{{ stats.ad_requests_by_status.Rejected || 0 }}</div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
          
          <div class="col-md-6 mb-3">
            <div class="card border-0 shadow-sm h-100">
              <div class="card-header bg-white border-0 py-3">
                <h4 class="mb-0">Flagged Content</h4>
              </div>
              <div class="card-body">
                <div class="row">
                  <div class="col-md-6 mb-3">
                    <div class="card border-0 bg-light h-100">
                      <div class="card-body p-3">
                        <div class="d-flex align-items-center">
                          <div class="bg-danger rounded-circle p-2 me-3">
                            <i class="bi bi-exclamation-triangle text-white"></i>
                          </div>
                          <div>
                            <h6 class="mb-0">Flagged Users</h6>
                            <h3 class="mb-0">{{ stats.flagged_users }}</h3>
                          </div>
                        </div>
                        <div class="mt-3">
                          <router-link to="/admin/users?flagged=true" class="btn btn-sm btn-outline-danger">
                            <i class="bi bi-eye me-1"></i> View
                          </router-link>
                        </div>
                      </div>
                    </div>
                  </div>
                  
                  <div class="col-md-6 mb-3">
                    <div class="card border-0 bg-light h-100">
                      <div class="card-body p-3">
                        <div class="d-flex align-items-center">
                          <div class="bg-danger rounded-circle p-2 me-3">
                            <i class="bi bi-exclamation-triangle text-white"></i>
                          </div>
                          <div>
                            <h6 class="mb-0">Flagged Campaigns</h6>
                            <h3 class="mb-0">{{ stats.flagged_campaigns }}</h3>
                          </div>
                        </div>
                        <div class="mt-3">
                          <router-link to="/admin/campaigns?flagged=true" class="btn btn-sm btn-outline-danger">
                            <i class="bi bi-eye me-1"></i> View
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
        
        <!-- Quick Links -->
        <div class="card border-0 shadow-sm">
          <div class="card-header bg-white border-0 py-3">
            <h4 class="mb-0">Quick Actions</h4>
          </div>
          <div class="card-body">
            <div class="row g-3">
              <div class="col-md-4">
                <router-link to="/admin/users" class="btn btn-primary d-block py-3">
                  <i class="bi bi-people-fill me-2"></i>
                  Manage Users
                </router-link>
              </div>
              <div class="col-md-4">
                <router-link to="/admin/campaigns" class="btn btn-success d-block py-3">
                  <i class="bi bi-megaphone-fill me-2"></i>
                  Manage Campaigns
                </router-link>
              </div>
              <div class="col-md-4">
                <router-link to="/admin/statistics" class="btn btn-info d-block py-3 text-white">
                  <i class="bi bi-graph-up me-2"></i>
                  View Analytics
                </router-link>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
// Additional methods
export default {
  methods: {
    getStatusPercentage(status) {
      if (!this.stats || !this.stats.ad_requests_by_status) return 0
      
      const total = Object.values(this.stats.ad_requests_by_status).reduce((sum, count) => sum + count, 0)
      if (total === 0) return 0
      
      return Math.round((this.stats.ad_requests_by_status[status] || 0) / total * 100)
    }
  }
}
</script> 