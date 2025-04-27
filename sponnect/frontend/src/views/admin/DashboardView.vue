<script setup>
import { ref, onMounted, computed, onUnmounted } from 'vue'
import { adminService } from '../../services/api'
import { formatCurrency, formatDate, formatDateTime } from '../../utils/formatters'

const loading = ref(true)
const error = ref('')
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
  flagged_campaigns: 0,
  payment_stats: {
    total_payments: 0,
    total_platform_fees: 0,
    total_payment_count: 0,
    recent_fees: 0,
    currency_symbol: '₹'
  }
})
const pendingSponsors = ref([])
const pendingInfluencers = ref([])
const pendingUsers = ref([])
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
  },
  currencySymbol: '₹'
})
// Add auto-refresh interval
let refreshInterval = null

// Calculate the percentage for ad request status
const getStatusPercentage = (status) => {
  if (!stats.value || !stats.value.ad_requests_by_status) return 0
  
  const total = Object.values(stats.value.ad_requests_by_status).reduce((sum, val) => sum + val, 0)
  if (total === 0) return 0
  
  return (stats.value.ad_requests_by_status[status] || 0) / total * 100
}

// Format a number with commas
const formatNumber = (num) => {
  return new Intl.NumberFormat('en-IN').format(num)
}

// Calculate percentage for ad request statuses
const calculatePercentage = (status) => {
  const total = Object.values(stats.value.ad_requests_by_status || {}).reduce((sum, val) => sum + val, 0)
  if (total === 0) return 0
  return Math.round((stats.value.ad_requests_by_status?.[status] || 0) / total * 100)
}

// Function to load admin data
const loadAdminData = async () => {
  try {
    loading.value = true;
    error.value = '';
    
    // Make all API calls in parallel
    const [statsResponse, pendingSponsorsResponse, pendingInfluencersResponse, pendingUsersResponse, dashboardSummaryResponse] = await Promise.all([
      adminService.getStats(),
      adminService.getPendingSponsors(),
      adminService.getPendingInfluencers(),
      adminService.getPendingUsers(),
      adminService.getDashboardSummary()
    ]);
    
    stats.value = statsResponse.data;
    pendingSponsors.value = pendingSponsorsResponse.data;
    pendingInfluencers.value = pendingInfluencersResponse.data;
    pendingUsers.value = pendingUsersResponse.data;
    dashboardSummary.value = dashboardSummaryResponse.data;
  } catch (err) {
    console.error('Error loading admin data:', err);
    error.value = 'Failed to load admin dashboard data. Please refresh the page or try again later.';
  } finally {
    loading.value = false;
  }
}

onMounted(() => {
  // Load data immediately
  loadAdminData()
  
  // Set up auto-refresh every 30 seconds
  refreshInterval = setInterval(loadAdminData, 30000)
})

// Clean up interval when component unmounts
onUnmounted(() => {
  if (refreshInterval) {
    clearInterval(refreshInterval)
  }
})

const approveSponsor = async (sponsorId) => {
  try {
    await adminService.approveSponsor(sponsorId)
    // Remove approved sponsor from the list
    pendingSponsors.value = pendingSponsors.value.filter(sponsor => sponsor.id !== sponsorId)
    // Refresh data to update stats
    loadAdminData()
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
    // Refresh data to update stats
    loadAdminData()
  } catch (err) {
    console.error('Error rejecting sponsor:', err)
    error.value = 'Failed to reject sponsor. Please try again.'
  }
}

// Handle approving a user (sponsor or influencer)
const approveUser = async (user) => {
  try {
    if (user.role === 'sponsor') {
      await adminService.approveSponsor(user.id)
    } else if (user.role === 'influencer') {
      await adminService.approveInfluencer(user.id)
    }
    
    // Remove from pending lists
    if (user.role === 'sponsor') {
      const index = pendingSponsors.value.findIndex(s => s.id === user.id)
      if (index !== -1) pendingSponsors.value.splice(index, 1)
    } else if (user.role === 'influencer') {
      const index = pendingInfluencers.value.findIndex(i => i.id === user.id)
      if (index !== -1) pendingInfluencers.value.splice(index, 1)
    }
    
    // Remove from combined list
    const index = pendingUsers.value.findIndex(u => u.id === user.id)
    if (index !== -1) pendingUsers.value.splice(index, 1)
    
    // Update stats
    if (user.role === 'sponsor') {
      stats.value.pending_sponsors--
      stats.value.active_sponsors++
    } else if (user.role === 'influencer') {
      stats.value.pending_influencers--
      stats.value.active_influencers++
    }
  } catch (err) {
    console.error('Error approving user:', err)
    error.value = `Failed to approve ${user.role}. Please try again.`
  }
}

// Handle rejecting a user (sponsor or influencer)
const rejectUser = async (user) => {
  try {
    if (user.role === 'sponsor') {
      await adminService.rejectSponsor(user.id)
    } else if (user.role === 'influencer') {
      await adminService.rejectInfluencer(user.id)
    }
    
    // Remove from pending lists
    if (user.role === 'sponsor') {
      const index = pendingSponsors.value.findIndex(s => s.id === user.id)
      if (index !== -1) pendingSponsors.value.splice(index, 1)
    } else if (user.role === 'influencer') {
      const index = pendingInfluencers.value.findIndex(i => i.id === user.id)
      if (index !== -1) pendingInfluencers.value.splice(index, 1)
    }
    
    // Remove from combined list
    const index = pendingUsers.value.findIndex(u => u.id === user.id)
    if (index !== -1) pendingUsers.value.splice(index, 1)
    
    // Update stats
    if (user.role === 'sponsor') {
      stats.value.pending_sponsors--
    } else if (user.role === 'influencer') {
      stats.value.pending_influencers--
    }
  } catch (err) {
    console.error('Error rejecting user:', err)
    error.value = `Failed to reject ${user.role}. Please try again.`
  }
}
</script>

<template>
  <div class="admin-dashboard py-5">
    <div class="container">
      <div class="d-flex justify-content-between align-items-center mb-4">
        <h1 class="text-primary">Admin Dashboard</h1>
        <button @click="loadAdminData" class="btn btn-outline-primary" title="Refresh Dashboard">
          <i class="bi bi-arrow-clockwise me-1"></i> Refresh
        </button>
      </div>
      
      <!-- Error Alert -->
      <div v-if="error" class="alert alert-danger alert-dismissible fade show mb-4" role="alert">
        {{ error }}
        <button type="button" class="btn-close" @click="error = ''"></button>
      </div>
      
      <!-- Loading Spinner -->
      <div v-if="loading" class="text-center py-5">
        <div class="spinner-border text-primary" role="status">
          <span class="visually-hidden">Loading...</span>
        </div>
        <p class="mt-3">Loading dashboard data...</p>
      </div>
      
      <div v-else>
        <!-- Stats Overview -->
        <div class="row mb-4">
          <div class="col-md-3 col-sm-6 mb-3">
            <div class="card border-0 shadow-sm h-100 card-hover">
              <div class="card-body p-4">
                <div class="d-flex justify-content-between">
                  <h5 class="card-title text-primary">Total Users</h5>
                  <div class="bg-primary bg-opacity-10 rounded-circle p-2">
                    <i class="bi bi-people text-primary fs-4"></i>
                  </div>
                </div>
                <h3 class="mt-3 mb-0 fw-bold">{{ stats.total_users }}</h3>
                <small class="text-muted">Active accounts on platform</small>
              </div>
            </div>
          </div>
          
          <div class="col-md-3 col-sm-6 mb-3">
            <div class="card border-0 shadow-sm h-100 card-hover">
              <div class="card-body p-4">
                <div class="d-flex justify-content-between">
                  <h5 class="card-title text-success">Active Sponsors</h5>
                  <div class="bg-success bg-opacity-10 rounded-circle p-2">
                    <i class="bi bi-briefcase text-success fs-4"></i>
                  </div>
                </div>
                <h3 class="mt-3 mb-0 fw-bold">{{ stats.active_sponsors }}</h3>
                <small class="text-muted">{{ pendingSponsors.length }} pending approval</small>
              </div>
            </div>
          </div>
          
          <div class="col-md-3 col-sm-6 mb-3">
            <div class="card border-0 shadow-sm h-100 card-hover">
              <div class="card-body p-4">
                <div class="d-flex justify-content-between">
                  <h5 class="card-title text-info">Active Influencers</h5>
                  <div class="bg-info bg-opacity-10 rounded-circle p-2">
                    <i class="bi bi-person-badge text-info fs-4"></i>
                  </div>
                </div>
                <h3 class="mt-3 mb-0 fw-bold">{{ stats.active_influencers }}</h3>
                <small class="text-muted">Content creators on platform</small>
              </div>
            </div>
          </div>
          
          <div class="col-md-3 col-sm-6 mb-3">
            <div class="card border-0 shadow-sm h-100 card-hover">
              <div class="card-body p-4">
                <div class="d-flex justify-content-between">
                  <h5 class="card-title text-warning">Platform Revenue</h5>
                  <div class="bg-warning bg-opacity-10 rounded-circle p-2">
                    <i class="bi bi-currency-rupee text-warning fs-4"></i>
                  </div>
                </div>
                <h3 class="mt-3 mb-0 fw-bold">{{ formatCurrency(stats.payment_stats?.total_platform_fees || 0) }}</h3>
                <small class="text-muted">{{ stats.payment_stats?.total_payment_count || 0 }} total payments</small>
              </div>
            </div>
          </div>
        </div>
        <div class="row g-4 mb-4">
          <div class="col-md-3 col-sm-6">
            <div class="card border-0 shadow-sm h-100">
              <div class="card-body">
                <div class="d-flex justify-content-between align-items-center mb-3">
                  <h6 class="card-subtitle text-muted">Pending Sponsors</h6>
                  <div class="icon-circle bg-primary bg-opacity-10">
                    <i class="bi bi-briefcase text-primary"></i>
                  </div>
                </div>
                <h2 class="display-6 fw-bold mb-0">{{ stats.pending_sponsors || 0 }}</h2>
                <router-link to="/admin/users?role=sponsor&status=pending" class="mt-3 d-inline-block text-decoration-none">
                  Manage
                  <i class="bi bi-arrow-right ms-1"></i>
                </router-link>
              </div>
            </div>
          </div>
          
          <div class="col-md-3 col-sm-6">
            <div class="card border-0 shadow-sm h-100">
              <div class="card-body">
                <div class="d-flex justify-content-between align-items-center mb-3">
                  <h6 class="card-subtitle text-muted">Pending Influencers</h6>
                  <div class="icon-circle bg-info bg-opacity-10">
                    <i class="bi bi-person-badge text-info"></i>
                  </div>
                </div>
                <h2 class="display-6 fw-bold mb-0">{{ stats.pending_influencers || 0 }}</h2>
                <router-link to="/admin/users?role=influencer&status=pending" class="mt-3 d-inline-block text-decoration-none">
                  Manage
                  <i class="bi bi-arrow-right ms-1"></i>
                </router-link>
              </div>
            </div>
          </div>
          
          <div class="col-md-3 col-sm-6">
            <div class="card border-0 shadow-sm h-100">
              <div class="card-body">
                <div class="d-flex justify-content-between align-items-center mb-3">
                  <h6 class="card-subtitle text-muted">Active Sponsors</h6>
                  <div class="icon-circle bg-success bg-opacity-10">
                    <i class="bi bi-building-check text-success"></i>
                  </div>
                </div>
                <h2 class="display-6 fw-bold mb-0">{{ stats.active_sponsors || 0 }}</h2>
              </div>
            </div>
          </div>
          
          <div class="col-md-3 col-sm-6">
            <div class="card border-0 shadow-sm h-100">
              <div class="card-body">
                <div class="d-flex justify-content-between align-items-center mb-3">
                  <h6 class="card-subtitle text-muted">Active Influencers</h6>
                  <div class="icon-circle bg-success bg-opacity-10">
                    <i class="bi bi-person-check text-success"></i>
                  </div>
                </div>
                <h2 class="display-6 fw-bold mb-0">{{ stats.active_influencers || 0 }}</h2>
              </div>
            </div>
          </div>
        </div>
        
        <!-- Campaigns & Ad Requests -->
        <div class="row mb-4">
          <div class="col-md-6 mb-3">
            <div class="card border-0 shadow-sm h-100">
              <div class="card-header bg-white border-0 py-3 d-flex justify-content-between align-items-center">
                <h4 class="mb-0 text-primary">Campaigns</h4>
                <router-link to="/admin/campaigns" class="btn btn-sm btn-outline-primary">View All</router-link>
              </div>
              <div class="card-body">
                <div class="d-flex align-items-center mb-4">
                  <div class="me-4">
                    <div class="position-relative d-inline-block">
                      <svg width="100" height="100" viewBox="0 0 100 100">
                        <circle cx="50" cy="50" r="45" fill="none" stroke="#e9ecef" stroke-width="10" />
                        <circle 
                          cx="50" 
                          cy="50" 
                          r="45" 
                          fill="none" 
                          stroke="#4361ee" 
                          stroke-width="10"
                          stroke-dasharray="283"
                          :stroke-dashoffset="283 - (283 * stats.public_campaigns / (stats.public_campaigns + stats.private_campaigns || 1))"
                          transform="rotate(-90 50 50)"
                        />
                      </svg>
                      <div class="position-absolute top-50 start-50 translate-middle text-center">
                        <h4 class="mb-0">{{ stats.public_campaigns + stats.private_campaigns }}</h4>
                        <small>Total</small>
                      </div>
                    </div>
                  </div>
                  <div>
                    <div class="mb-2">
                      <div class="d-flex align-items-center">
                        <span class="bg-primary rounded-circle me-2" style="width: 12px; height: 12px;"></span>
                        <span class="me-2">Public:</span>
                        <span class="fw-bold">{{ stats.public_campaigns || 0 }}</span>
                      </div>
                    </div>
                    <div>
                      <div class="d-flex align-items-center">
                        <span class="bg-secondary rounded-circle me-2" style="width: 12px; height: 12px;"></span>
                        <span class="me-2">Private:</span>
                        <span class="fw-bold">{{ stats.private_campaigns || 0 }}</span>
                      </div>
                    </div>
                  </div>
                </div>
                <div class="row text-center">
                  <div class="col-6">
                    <div class="card bg-light border-0">
                      <div class="card-body py-2">
                        <h6 class="text-muted mb-1">Flagged</h6>
                        <h4 class="mb-0">{{ stats.flagged_campaigns || 0 }}</h4>
                      </div>
                    </div>
                  </div>
                  <div class="col-6">
                    <div class="card bg-light border-0">
                      <div class="card-body py-2">
                        <h6 class="text-muted mb-1">Avg. Budget</h6>
                        <h4 class="mb-0">{{ formatCurrency(5000) }}</h4> <!-- Placeholder - replace with actual data if available -->
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
                <h4 class="mb-0 text-primary">Ad Request Status</h4>
              </div>
              <div class="card-body">
                <div v-if="stats && stats.ad_requests_by_status" class="mb-3">
                  <div class="progress rounded-pill mb-4" style="height: 1.5rem;">
                    <div class="progress-bar bg-warning text-dark" 
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
                    <div class="col-6 col-md-3 mb-3">
                      <div class="d-flex align-items-center">
                        <span class="badge bg-warning p-2 me-2"></span>
                        <div>
                          <div class="small text-muted">Pending</div>
                          <div class="fw-bold">{{ stats.ad_requests_by_status.Pending || 0 }}</div>
                        </div>
                      </div>
                    </div>
                    <div class="col-6 col-md-3 mb-3">
                      <div class="d-flex align-items-center">
                        <span class="badge bg-info p-2 me-2"></span>
                        <div>
                          <div class="small text-muted">Negotiating</div>
                          <div class="fw-bold">{{ stats.ad_requests_by_status.Negotiating || 0 }}</div>
                        </div>
                      </div>
                    </div>
                    <div class="col-6 col-md-3 mb-3">
                      <div class="d-flex align-items-center">
                        <span class="badge bg-success p-2 me-2"></span>
                        <div>
                          <div class="small text-muted">Accepted</div>
                          <div class="fw-bold">{{ stats.ad_requests_by_status.Accepted || 0 }}</div>
                        </div>
                      </div>
                    </div>
                    <div class="col-6 col-md-3 mb-3">
                      <div class="d-flex align-items-center">
                        <span class="badge bg-danger p-2 me-2"></span>
                        <div>
                          <div class="small text-muted">Rejected</div>
                          <div class="fw-bold">{{ stats.ad_requests_by_status.Rejected || 0 }}</div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
   
 
        
        
        <!-- Quick Actions Card -->
        <div class="card border-0 shadow-sm">
          <div class="card-header bg-white border-0 py-3">
            <h4 class="mb-0 text-primary">Quick Actions</h4>
          </div>
          <div class="card-body">
            <div class="row g-3">
              <div class="col-md-3 col-sm-6">
                <router-link to="/admin/users" class="card border-0 shadow-sm text-decoration-none card-hover h-100">
                  <div class="card-body text-center p-4">
                    <div class="bg-primary bg-opacity-10 rounded-circle p-3 mx-auto mb-3" style="width: fit-content">
                      <i class="bi bi-people-fill text-primary fs-3"></i>
                    </div>
                    <h5 class="text-primary">Manage Users</h5>
                    <p class="text-muted mb-0 small">View and manage platform users</p>
                  </div>
                </router-link>
              </div>
              <div class="col-md-3 col-sm-6">
                <router-link to="/admin/campaigns" class="card border-0 shadow-sm text-decoration-none card-hover h-100">
                  <div class="card-body text-center p-4">
                    <div class="bg-success bg-opacity-10 rounded-circle p-3 mx-auto mb-3" style="width: fit-content">
                      <i class="bi bi-megaphone-fill text-success fs-3"></i>
                    </div>
                    <h5 class="text-success">Campaigns</h5>
                    <p class="text-muted mb-0 small">Manage and moderate campaigns</p>
                  </div>
                </router-link>
              </div>
              <div class="col-md-3 col-sm-6">
                <router-link to="/admin/statistics" class="card border-0 shadow-sm text-decoration-none card-hover h-100">
                  <div class="card-body text-center p-4">
                    <div class="bg-info bg-opacity-10 rounded-circle p-3 mx-auto mb-3" style="width: fit-content">
                      <i class="bi bi-graph-up text-info fs-3"></i>
                    </div>
                    <h5 class="text-info">Analytics</h5>
                    <p class="text-muted mb-0 small">View detailed platform statistics</p>
                  </div>
                </router-link>
              </div>
              <div class="col-md-3 col-sm-6">
                <router-link to="/admin/platform-fees" class="card border-0 shadow-sm text-decoration-none card-hover h-100">
                  <div class="card-body text-center p-4">
                    <div class="bg-warning bg-opacity-10 rounded-circle p-3 mx-auto mb-3" style="width: fit-content">
                      <i class="bi bi-cash-stack text-warning fs-3"></i>
                    </div>
                    <h5 class="text-warning">Revenue</h5>
                    <p class="text-muted mb-0 small">Track platform earnings and fees</p>
                  </div>
                </router-link>
              </div>
            </div>
          </div>
        </div>
        
        <!-- Pending Approvals Panel -->
        <div class="card border-0 shadow-sm mb-4">
          <div class="card-header bg-white border-0 py-3 d-flex justify-content-between align-items-center">
            <h4 class="mb-0 text-primary">Pending Approvals</h4>
            <span class="badge bg-warning rounded-pill">{{ pendingUsers.length }} users</span>
          </div>
          <div class="card-body p-0">
            <div v-if="pendingUsers.length === 0" class="text-center py-4">
              <i class="bi bi-check-circle-fill text-success fs-1"></i>
              <p class="mt-2 text-muted">No pending approval requests</p>
            </div>
            <div v-else class="table-responsive">
              <table class="table mb-0">
                <thead class="table-light">
                  <tr>
                    <th>Name</th>
                    <th>Role</th>
                    <th>Email</th>
                    <th>Joined</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="user in pendingUsers.slice(0, 5)" :key="user.id">
                    <td>
                      <div class="d-flex align-items-center">
                        <div class="avatar-placeholder rounded-circle bg-light d-flex align-items-center justify-content-center me-2" 
                             style="width: 36px; height: 36px; font-size: 16px;">
                          {{ user.username.charAt(0).toUpperCase() }}
                        </div>
                        {{ user.username }}
                      </div>
                    </td>
                    <td>
                      <span :class="`badge ${user.role === 'sponsor' ? 'bg-primary' : 'bg-info'}`">
                        {{ user.role }}
                      </span>
                    </td>
                    <td>{{ user.email }}</td>
                    <td>{{ formatDate(user.created_at) }}</td>
                    <td>
                      <div class="btn-group btn-group-sm">
                        <router-link :to="`/admin/users?view=${user.id}`" class="btn btn-outline-primary">
                          <i class="bi bi-eye"></i>
                        </router-link>
                        <button class="btn btn-outline-success" @click="approveUser(user)">
                          <i class="bi bi-check-lg"></i>
                        </button>
                        <button class="btn btn-outline-danger" @click="rejectUser(user)">
                          <i class="bi bi-x-lg"></i>
                        </button>
                      </div>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
            <div v-if="pendingUsers.length > 5" class="text-center py-3 border-top">
              <router-link to="/admin/users?status=pending" class="btn btn-sm btn-outline-primary">
                View all {{ pendingUsers.length }} pending users
              </router-link>
            </div>
          </div>
        </div>

        <!-- Statistics Cards Row -->
        
      </div>
    </div>
  </div>
</template>

<style scoped>
.admin-dashboard {
  animation: fadeIn 0.5s ease-in-out;
}

.card-hover {
  transition: transform 0.2s, box-shadow 0.2s;
}

.card-hover:hover {
  transform: translateY(-5px);
  box-shadow: 0 10px 20px rgba(0, 0, 0, 0.1) !important;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}
</style> 