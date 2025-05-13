<script setup>
import { ref, onMounted, computed, onUnmounted } from 'vue'
import { adminService } from '../../services/api'
import { formatCurrency, formatDate, formatDateTime } from '../../utils/formatters'

const loading = ref(true)
const error = ref('')
const refreshing = ref(false)
const refreshCount = ref(0)
const stats = ref({
  total_users: 0,
  active_sponsors: 0,
  active_influencers: 0,
  public_campaigns: 0,
  private_campaigns: 0,
  pending_sponsors: 0,
  pending_influencers: 0,
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
  avgCampaignBudget: 0
})
// Set auto-refresh interval (10 seconds for more real-time data)
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
const loadAdminData = async (isManualRefresh = false) => {
  try {
    if (isManualRefresh) {
      refreshing.value = true;
      refreshCount.value++;
    } else {
      loading.value = true;
    }
    error.value = '';
    
    // Make all API calls in parallel for real-time data
    const [statsResponse, pendingSponsorsResponse, pendingInfluencersResponse, pendingUsersResponse, dashboardSummaryResponse] = await Promise.all([
      adminService.getStats().catch(err => {
        console.error('Error loading stats:', err);
        return { 
          data: {
            total_users: 0,
            active_sponsors: 0,
            active_influencers: 0,
            pending_sponsors: 0,
            pending_influencers: 0,
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
          }
        };
      }),
      adminService.getPendingSponsors().catch(err => {
        console.error('Error loading pending sponsors:', err);
        return { data: [] };
      }),
      adminService.getPendingInfluencers().catch(err => {
        console.error('Error loading pending influencers:', err);
        return { data: [] };
      }),
      adminService.getPendingUsers().catch(err => {
        console.error('Error loading pending users:', err);
        return { data: [] };
      }),
      adminService.getDashboardSummary().catch(err => {
        console.error('Error loading dashboard summary:', err);
        return { data: {
          userSummary: { labels: [], datasets: [] },
          campaignVisibility: { labels: [], datasets: [] },
          adRequestStatus: { labels: [], datasets: [] },
          conversionRate: { value: 0, label: 'Acceptance Rate' },
          avgCampaignBudget: 0
        }};
      })
    ]);
    
    // Ensure stats data has all required properties
    stats.value = {
      total_users: 0,
      active_sponsors: 0,
      active_influencers: 0,
      pending_sponsors: 0,
      pending_influencers: 0,
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
      ...statsResponse.data
    };
    
    // Ensure we have arrays for pending data
    pendingSponsors.value = Array.isArray(pendingSponsorsResponse.data) ? pendingSponsorsResponse.data : [];
    pendingInfluencers.value = Array.isArray(pendingInfluencersResponse.data) ? pendingInfluencersResponse.data : [];
    pendingUsers.value = Array.isArray(pendingUsersResponse.data) ? pendingUsersResponse.data : [];
    
    // Clean pending users data to ensure all required fields are present
    pendingUsers.value = pendingUsers.value.map(user => ({
      id: user.id || 0,
      username: user.username || 'Unknown User',
      email: user.email || 'no-email@example.com',
      role: user.role || 'unknown',
      created_at: user.created_at || new Date().toISOString(),
      ...user
    }));
    
    // Ensure dashboard summary has valid structure before assigning
    if (dashboardSummaryResponse && dashboardSummaryResponse.data) {
      // Make sure conversionRate exists and has a valid value
      if (!dashboardSummaryResponse.data.conversionRate) {
        dashboardSummaryResponse.data.conversionRate = { value: 0, label: 'Acceptance Rate' };
      }
      
      // Ensure all required chart data structures exist
      const requiredCharts = ['userSummary', 'campaignVisibility', 'adRequestStatus'];
      requiredCharts.forEach(chart => {
        if (!dashboardSummaryResponse.data[chart]) {
          dashboardSummaryResponse.data[chart] = { labels: [], datasets: [] };
        }
      });
      
      dashboardSummary.value = dashboardSummaryResponse.data;
    }
  } catch (err) {
    console.error('Error loading admin data:', err);
    error.value = 'Failed to load admin dashboard data. Please refresh the page or try again later.';
  } finally {
    loading.value = false;
    refreshing.value = false;
  }
}

// Function for manual refresh
const refreshDashboard = () => {
  loadAdminData(true);
}

onMounted(() => {
  // Load data immediately
  loadAdminData()
  
  // Set up auto-refresh every 60 seconds instead of 10 seconds to reduce refresh frequency
  refreshInterval = setInterval(() => loadAdminData(false), 60000)
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
        <h1 class="dashboard-title">Admin Dashboard</h1>
        <div class="d-flex align-items-center">
          <div class="badge bg-success me-2 d-inline-flex align-items-center">
            <span class="me-1">Auto-refresh: 60s</span>
            <span class="pulse-dot"></span>
          </div>
          <button @click="refreshDashboard" class="btn btn-outline-primary" 
                  :disabled="refreshing" title="Manually refresh dashboard data">
            <i class="bi" :class="refreshing ? 'bi-arrow-repeat spin' : 'bi-arrow-clockwise'"></i>
            <span class="ms-1">{{ refreshing ? 'Refreshing...' : 'Refresh' }}</span>
            <small v-if="refreshCount > 0" class="ms-1">({{ refreshCount }})</small>
          </button>
        </div>
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
          <div class="col-md-4 col-sm-6 mb-3">
            <div class="card border-0 dashboard-card gradient-blue h-100">
              <div class="card-body p-4">
                <div class="d-flex justify-content-between">
                  <h5 class="card-title text-white">Total Users</h5>
                  <div class="icon-container">
                    <i class="bi bi-people-fill text-white fs-4"></i>
                  </div>
                </div>
                <h3 class="mt-3 mb-0 fw-bold text-white">{{ stats.total_users }}</h3>
                <small class="text-white opacity-75">Active accounts on platform</small>
              </div>
            </div>
          </div>
          
          <div class="col-md-4 col-sm-6 mb-3">
            <div class="card border-0 dashboard-card gradient-green h-100">
              <div class="card-body p-4">
                <div class="d-flex justify-content-between">
                  <h5 class="card-title text-white">Active Sponsors</h5>
                  <div class="icon-container">
                    <i class="bi bi-building text-white fs-4"></i>
                  </div>
                </div>
                <h3 class="mt-3 mb-0 fw-bold text-white">{{ stats.active_sponsors }}</h3>
                <small class="text-white opacity-75">{{ stats.pending_sponsors }} pending approval</small>
              </div>
            </div>
          </div>
          
          <div class="col-md-4 col-sm-6 mb-3">
            <div class="card border-0 dashboard-card gradient-purple h-100">
              <div class="card-body p-4">
                <div class="d-flex justify-content-between">
                  <h5 class="card-title text-white">Active Influencers</h5>
                  <div class="icon-container">
                    <i class="bi bi-person-video3 text-white fs-4"></i>
                  </div>
                </div>
                <h3 class="mt-3 mb-0 fw-bold text-white">{{ stats.active_influencers }}</h3>
                <small class="text-white opacity-75">{{ stats.pending_influencers }} pending approval</small>
              </div>
            </div>
          </div>
        </div>

        <div class="row mb-4">  
          <div class="col-md-4 col-sm-6 mb-3">
            <div class="card border-0 content-card h-100">
              <div class="card-body">
                <div class="d-flex justify-content-between align-items-center mb-3">
                  <h6 class="card-subtitle text-muted">Campaign Status</h6>
                  <div class="icon-circle bg-primary bg-opacity-10">
                    <i class="bi bi-bullseye text-primary"></i>
                  </div>
                </div>
                <div class="d-flex align-items-center justify-content-between">
                  <div>
                    <h2 class="display-6 fw-bold mb-0">{{ stats.public_campaigns + stats.private_campaigns }}</h2>
                    <small class="text-muted">Total Campaigns</small>
              </div>
                  <div>
                    <div class="d-flex align-items-center mb-1">
                      <span class="bg-success rounded-circle me-2" style="width: 8px; height: 8px;"></span>
                      <span>Public: {{ stats.public_campaigns }}</span>
                    </div>
                    <div class="d-flex align-items-center">
                      <span class="bg-warning rounded-circle me-2" style="width: 8px; height: 8px;"></span>
                      <span>Private: {{ stats.private_campaigns }}</span>
                    </div>
                  </div>
                </div>
                <router-link to="/admin/campaigns" class="mt-3 d-inline-block text-decoration-none">
                  Manage Campaigns
                  <i class="bi bi-arrow-right ms-1"></i>
                </router-link>
              </div>
            </div>
          </div>
        
          <div class="col-md-4 col-sm-6 mb-3">
            <div class="card border-0 content-card h-100">
              <div class="card-body">
                <div class="d-flex justify-content-between align-items-center mb-3">
                  <h6 class="card-subtitle text-muted">Pending Sponsors</h6>
                  <div class="icon-circle gradient-blue-light">
                    <i class="bi bi-building-add text-white"></i>
                  </div>
                </div>
                <h2 class="display-6 fw-bold mb-0">{{ stats.pending_sponsors || 0 }}</h2>
                <small class="text-muted">Awaiting Approval</small>
                <router-link to="/admin/users?role=sponsor&status=pending" class="mt-3 d-inline-block text-decoration-none">
                  Manage
                  <i class="bi bi-arrow-right ms-1"></i>
                </router-link>
              </div>
            </div>
          </div>
          
          <div class="col-md-4 col-sm-6 mb-3">
            <div class="card border-0 content-card h-100">
              <div class="card-body">
                <div class="d-flex justify-content-between align-items-center mb-3">
                  <h6 class="card-subtitle text-muted">Pending Influencers</h6>
                  <div class="icon-circle gradient-purple-light">
                    <i class="bi bi-person-video2 text-white"></i>
                  </div>
                </div>
                <h2 class="display-6 fw-bold mb-0">{{ stats.pending_influencers || 0 }}</h2>
                <small class="text-muted">Awaiting Approval</small>
                <router-link to="/admin/users?role=influencer&status=pending" class="mt-3 d-inline-block text-decoration-none">
                  Manage
                  <i class="bi bi-arrow-right ms-1"></i>
                </router-link>
              </div>
            </div>
          </div>
        </div>
        <!-- Campaigns & Ad Requests -->
        <div class="row mb-4">
          <div class="col-md-6 mb-3">
            <div class="card border-0 content-card h-100">
              <div class="card-header bg-white border-0 py-3 d-flex justify-content-between align-items-center">
                <h4 class="mb-0 text-primary">Campaigns</h4>
                <router-link to="/admin/campaigns" class="btn btn-sm btn-primary">View All</router-link>
              </div>
              <div class="card-body campaign-card-body">
                <div class="d-flex align-items-center mb-4">
                  <div class="me-4">
                    <div class="position-relative d-inline-block campaign-chart">
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
                      <div class="position-absolute top-50 start-50 translate-middle text-center campaign-count">
                        <h4 class="mb-0">{{ stats.public_campaigns + stats.private_campaigns }}</h4>
                        <small>Total</small>
                      </div>
                    </div>
                  </div>
                  <div class="campaign-stats">
                    <div class="mb-3">
                      <div class="d-flex align-items-center campaign-stat-item">
                        <span class="bg-primary rounded-circle me-2" style="width: 12px; height: 12px;"></span>
                        <span class="me-2">Public:</span>
                        <span class="fw-bold">{{ stats.public_campaigns || 0 }}</span>
                      </div>
                    </div>
                    <div>
                      <div class="d-flex align-items-center campaign-stat-item">
                        <span class="bg-secondary rounded-circle me-2" style="width: 12px; height: 12px;"></span>
                        <span class="me-2">Private:</span>
                        <span class="fw-bold">{{ stats.private_campaigns || 0 }}</span>
                      </div>
                    </div>
                  </div>
                </div>
                <div class="row text-center g-3">
                  <div class="col-6">
                    <div class="card bg-light border-0 campaign-stat-card">
                      <div class="card-body py-3">
                        <h6 class="text-danger mb-1">Flagged</h6>
                        <h4 class="mb-0">{{ stats.flagged_campaigns || 0 }}</h4>
                      </div>
                    </div>
                  </div>
                  <div class="col-6">
                    <div class="card bg-light border-0 campaign-stat-card">
                      <div class="card-body py-3">
                        <h6 class="text-primary mb-1">Avg. Budget</h6>
                        <h4 class="mb-0">{{ formatCurrency(dashboardSummary.avgCampaignBudget || 0) }}</h4>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
          
          <div class="col-md-6 mb-3">
            <div class="card border-0 content-card h-100">
              <div class="card-header bg-white border-0 py-3 d-flex justify-content-between align-items-center">
                <h4 class="mb-0 text-primary">Ad Request Status</h4>
                <router-link to="/admin/engagements" class="btn btn-sm btn-primary">Manage</router-link>
              </div>
              <div class="card-body">
                <div v-if="stats && stats.ad_requests_by_status" class="mb-3">
                  <div class="progress rounded-pill mb-4 status-progress" style="height: 1.5rem;">
                    <div class="progress-bar bg-warning text-dark" 
                         :style="`width: ${getStatusPercentage('Pending')}%`" 
                         role="progressbar">
                      <span class="status-label">Pending</span>
                    </div>
                    <div class="progress-bar bg-info" 
                         :style="`width: ${getStatusPercentage('Negotiating')}%`" 
                         role="progressbar">
                      <span class="status-label">Negotiating</span>
                    </div>
                    <div class="progress-bar bg-success" 
                         :style="`width: ${getStatusPercentage('Accepted')}%`" 
                         role="progressbar">
                      <span class="status-label">Accepted</span>
                    </div>
                    <div class="progress-bar bg-danger" 
                         :style="`width: ${getStatusPercentage('Rejected')}%`" 
                         role="progressbar">
                      <span class="status-label">Rejected</span>
                    </div>
                  </div>
                  
                  <div class="row mt-4">
                    <div class="col-6 col-md-3 mb-3">
                      <div class="status-badge-container">
                        <span class="badge bg-warning p-2 me-2"></span>
                        <div>
                          <div class="small text-muted">Pending</div>
                          <div class="fw-bold">{{ stats.ad_requests_by_status.Pending || 0 }}</div>
                        </div>
                      </div>
                    </div>
                    <div class="col-6 col-md-3 mb-3">
                      <div class="status-badge-container">
                        <span class="badge bg-info p-2 me-2"></span>
                        <div>
                          <div class="small text-muted">Negotiating</div>
                          <div class="fw-bold">{{ stats.ad_requests_by_status.Negotiating || 0 }}</div>
                        </div>
                      </div>
                    </div>
                    <div class="col-6 col-md-3 mb-3">
                      <div class="status-badge-container">
                        <span class="badge bg-success p-2 me-2"></span>
                        <div>
                          <div class="small text-muted">Accepted</div>
                          <div class="fw-bold">{{ stats.ad_requests_by_status.Accepted || 0 }}</div>
                        </div>
                      </div>
                    </div>
                    <div class="col-6 col-md-3 mb-3">
                      <div class="status-badge-container">
                        <span class="badge bg-danger p-2 me-2"></span>
                        <div>
                          <div class="small text-muted">Rejected</div>
                          <div class="fw-bold">{{ stats.ad_requests_by_status.Rejected || 0 }}</div>
                        </div>
                      </div>
                    </div>
                  </div>
                  
                  <div class="adrequest-summary mt-3 pt-3 border-top">
                    <div class="d-flex justify-content-between align-items-center">
                      <div>
                        <span class="text-muted">Total Requests:</span>
                        <span class="ms-2 fw-bold">{{ Object.values(stats.ad_requests_by_status || {}).reduce((sum, val) => sum + val, 0) }}</span>
                      </div>
                      <div>
                        <span class="text-muted">Acceptance Rate:</span>
                        <span class="ms-2 badge rounded-pill" :class="calculatePercentage('Accepted') > 50 ? 'bg-success' : 'bg-warning'">
                          {{ calculatePercentage('Accepted') }}%
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
        <!-- Data Insights Section -->
        <div class="row mb-4">
          <div class="col-md-6 mb-3">
            <div class="card border-0 content-card h-100">
              <div class="card-header bg-white border-0">
                <h5 class="mb-0">Ad Request Status Distribution</h5>
              </div>
              <div class="card-body">
                <div class="d-flex flex-wrap justify-content-center">
                  <div class="position-relative chart-container-custom" style="width: 200px; height: 200px;">
                    <svg width="200" height="200" viewBox="0 0 200 200">
                      <!-- Background circle -->
                      <circle cx="100" cy="100" r="80" fill="none" stroke="#e9ecef" stroke-width="20" />
                      
                      <!-- Acceptance Rate -->
                      <circle 
                        cx="100" 
                        cy="100" 
                        r="80" 
                        fill="none" 
                        stroke="#28a745" 
                        stroke-width="20"
                        stroke-dasharray="503"
                        :stroke-dashoffset="503 - (503 * calculatePercentage('Accepted') / 100)"
                        transform="rotate(-90 100 100)"
                      />
                      
                      <!-- Negotiation Rate -->
                      <circle 
                        cx="100" 
                        cy="100" 
                        r="80" 
                        fill="none" 
                        stroke="#ffc107" 
                        stroke-width="20"
                        stroke-dasharray="503"
                        :stroke-dashoffset="503 - (503 * calculatePercentage('Negotiating') / 100)"
                        transform="rotate(-90 100 100)"
                        style="stroke-dasharray: 503; opacity: 0.8"
                      />
                      
                      <!-- Pending Rate -->
                      <circle 
                        cx="100" 
                        cy="100" 
                        r="80" 
                        fill="none" 
                        stroke="#007bff" 
                        stroke-width="20"
                        stroke-dasharray="503"
                        :stroke-dashoffset="503 - (503 * calculatePercentage('Pending') / 100)"
                        transform="rotate(-90 100 100)"
                        style="stroke-dasharray: 503; opacity: 0.7"
                      />
                      
                      <!-- Rejection Rate -->
                      <circle 
                        cx="100" 
                        cy="100" 
                        r="80" 
                        fill="none" 
                        stroke="#dc3545" 
                        stroke-width="20"
                        stroke-dasharray="503"
                        :stroke-dashoffset="503 - (503 * calculatePercentage('Rejected') / 100)"
                        transform="rotate(-90 100 100)"
                        style="stroke-dasharray: 503; opacity: 0.6"
                      />
                    </svg>
                    <div class="position-absolute top-50 start-50 translate-middle text-center total-count">
                      <h4 class="mb-0">{{ Object.values(stats.ad_requests_by_status || {}).reduce((sum, val) => sum + val, 0) }}</h4>
                      <small class="text-muted">Total</small>
                    </div>
                  </div>
                  
                  <div class="ms-4">
                    <div class="mb-2">
                      <div class="d-flex align-items-center status-item">
                        <span class="badge bg-success p-2 me-2"></span>
                        <span>Accepted: {{ stats.ad_requests_by_status?.Accepted || 0 }} ({{ calculatePercentage('Accepted') }}%)</span>
                      </div>
                    </div>
                    <div class="mb-2">
                      <div class="d-flex align-items-center status-item">
                        <span class="badge bg-warning p-2 me-2"></span>
                        <span>Negotiating: {{ stats.ad_requests_by_status?.Negotiating || 0 }} ({{ calculatePercentage('Negotiating') }}%)</span>
                      </div>
                    </div>
                    <div class="mb-2">
                      <div class="d-flex align-items-center status-item">
                        <span class="badge bg-primary p-2 me-2"></span>
                        <span>Pending: {{ stats.ad_requests_by_status?.Pending || 0 }} ({{ calculatePercentage('Pending') }}%)</span>
                      </div>
                    </div>
                    <div>
                      <div class="d-flex align-items-center status-item">
                        <span class="badge bg-danger p-2 me-2"></span>
                        <span>Rejected: {{ stats.ad_requests_by_status?.Rejected || 0 }} ({{ calculatePercentage('Rejected') }}%)</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
          
          <div class="col-md-6 mb-3">
            <div class="card border-0 content-card h-100">
              <div class="card-header bg-white border-0">
                <h5 class="mb-0">Platform Activity</h5>
              </div>
              <div class="card-body">
                <div class="row g-3">
                  <div class="col-sm-6">
                    <div class="activity-card bg-primary-gradient">
                      <div class="card-body p-3">
                        <div class="d-flex justify-content-between">
                          <div>
                            <h6 class="text-white mb-1">Current Users</h6>
                            <h4 class="mb-0 text-white">{{ stats.total_users }}</h4>
                          </div>
                          <div class="activity-icon">
                            <i class="bi bi-person-lines-fill text-white"></i>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                  
                  <div class="col-sm-6">
                    <div class="activity-card bg-success-gradient">
                      <div class="card-body p-3">
                        <div class="d-flex justify-content-between">
                          <div>
                            <h6 class="text-white mb-1">Campaign Conversion</h6>
                            <h4 class="mb-0 text-white">{{ Math.round(dashboardSummary.conversionRate?.value || 0) }}%</h4>
                          </div>
                          <div class="activity-icon">
                            <i class="bi bi-graph-up text-white"></i>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                  
                  <div class="col-sm-6">
                    <div class="activity-card bg-warning-gradient">
                      <div class="card-body p-3">
                        <div class="d-flex justify-content-between">
                          <div>
                            <h6 class="text-white mb-1">Active Campaigns</h6>
                            <h4 class="mb-0 text-white">{{ stats.public_campaigns + stats.private_campaigns }}</h4>
                          </div>
                          <div class="activity-icon">
                            <i class="bi bi-broadcast-pin text-white"></i>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                  
                  <div class="col-sm-6">
                    <div class="activity-card bg-danger-gradient">
                      <div class="card-body p-3">
                        <div class="d-flex justify-content-between">
                          <div>
                            <h6 class="text-white mb-1">Flagged Content</h6>
                            <h4 class="mb-0 text-white">{{ stats.flagged_campaigns + stats.flagged_users }}</h4>
                          </div>
                          <div class="activity-icon">
                            <i class="bi bi-shield-exclamation text-white"></i>
                          </div>
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
        <div class="card border-0 content-card">
          <div class="card-header bg-white border-0 py-3">
            <h4 class="mb-0 text-primary">Quick Actions</h4>
          </div>
          <div class="card-body">
            <div class="row g-3">
              <div class="col-md-4 col-sm-6">
                <router-link to="/admin/users" class="action-card h-100">
                  <div class="card-body text-center p-4">
                    <div class="action-icon bg-primary">
                      <i class="bi bi-people-fill text-white fs-3"></i>
                    </div>
                    <h5 class="text-primary mt-3">Manage Users</h5>
                    <p class="text-muted mb-0 small">View and manage platform users</p>
                  </div>
                </router-link>
              </div>
              <div class="col-md-4 col-sm-6">
                <router-link to="/admin/campaigns" class="action-card h-100">
                  <div class="card-body text-center p-4">
                    <div class="action-icon bg-success">
                      <i class="bi bi-bullseye text-white fs-3"></i>
                    </div>
                    <h5 class="text-success mt-3">Campaigns</h5>
                    <p class="text-muted mb-0 small">Manage and moderate campaigns</p>
                  </div>
                </router-link>
              </div>
              <div class="col-md-4 col-sm-6">
                <router-link to="/admin/statistics" class="action-card h-100">
                  <div class="card-body text-center p-4">
                    <div class="action-icon bg-info">
                      <i class="bi bi-bar-chart-line-fill text-white fs-3"></i>
                    </div>
                    <h5 class="text-info mt-3">Analytics</h5>
                    <p class="text-muted mb-0 small">View detailed platform statistics</p>
                  </div>
                </router-link>
              </div>
            </div>
          </div>
        </div>
        
        <!-- Pending Approvals Section -->
        <div class="row mb-4">
          <div class="col-12">
            <div class="card border-0 content-card">
          <div class="card-header bg-white border-0 py-3 d-flex justify-content-between align-items-center">
                <h4 class="mb-0">Pending Approvals</h4>
                <router-link to="/admin/users?status=pending" class="btn btn-sm btn-outline-primary">View All</router-link>
          </div>
          <div class="card-body p-0">
                <div class="table-responsive">
                  <table class="table table-hover mb-0">
                <thead class="table-light">
                  <tr>
                        <th scope="col" style="width: 40px;"></th>
                        <th scope="col">Name</th>
                        <th scope="col">Email</th>
                        <th scope="col">Role</th>
                        <th scope="col">Registered</th>
                        <th scope="col" class="text-end">Actions</th>
                  </tr>
                </thead>
                <tbody>
                      <tr v-if="loading && pendingUsers.length === 0">
                        <td colspan="6" class="text-center py-4">
                          <div class="spinner-border text-primary" role="status">
                            <span class="visually-hidden">Loading...</span>
                          </div>
                        </td>
                      </tr>
                      <tr v-else-if="pendingUsers.length === 0">
                        <td colspan="6" class="text-center py-4">
                          <i class="bi bi-check-circle-fill text-success fs-1 d-block mb-2"></i>
                          <p class="mb-0">No pending approvals at the moment!</p>
                        </td>
                      </tr>
                  <tr v-for="user in pendingUsers.slice(0, 5)" :key="user.id">
                    <td>
                          <i v-if="user.role === 'sponsor'" class="bi bi-briefcase text-primary"></i>
                          <i v-else-if="user.role === 'influencer'" class="bi bi-person-badge text-info"></i>
                    </td>
                    <td>
                          <strong>{{ user.username }}</strong><br>
                          <small class="text-muted">{{ user.company_name || user.influencer_name || 'N/A' }}</small>
                    </td>
                        <td>{{ user.email }}</td>
                        <td>
                          <span v-if="user.role === 'sponsor'" class="badge bg-primary">Sponsor</span>
                          <span v-else-if="user.role === 'influencer'" class="badge bg-info">Influencer</span>
                        </td>
                        <td>{{ formatDate(user.created_at) }}</td>
                        <td class="text-end">
                          <button @click="approveUser(user)" class="btn btn-sm btn-success me-1">
                            <i class="bi bi-check-lg"></i> Approve
                        </button>
                          <button @click="rejectUser(user)" class="btn btn-sm btn-outline-danger">
                            <i class="bi bi-x-lg"></i> Reject
                        </button>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
                <div v-if="pendingUsers.length > 5" class="text-center p-3 border-top">
                  <router-link to="/admin/users?status=pending" class="text-decoration-none">
                View all {{ pendingUsers.length }} pending users
              </router-link>
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
.admin-dashboard {
  animation: fadeIn 0.5s ease-in-out;
}

.dashboard-title {
  font-weight: 700;
  margin-bottom: 1.5rem;
  color: #4361ee;
  position: relative;
  padding-bottom: 0.5rem;
  display: inline-block;
}

.dashboard-title::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 0;
  width: 80px;
  height: 3px;
  background: linear-gradient(to right, #4361ee, #3a0ca3);
}

.dashboard-card {
  border-radius: 15px;
  overflow: hidden;
  box-shadow: 0 8px 16px rgba(0,0,0,0.1);
  transition: transform 0.3s, box-shadow 0.3s;
}

.dashboard-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 12px 20px rgba(0,0,0,0.15);
}

.content-card {
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.08);
  transition: box-shadow 0.3s, transform 0.3s;
}

.content-card:hover {
  box-shadow: 0 8px 16px rgba(0,0,0,0.12);
  transform: translateY(-3px);
}

.gradient-blue {
  background: linear-gradient(135deg, #4361ee, #3a0ca3);
}

.gradient-green {
  background: linear-gradient(135deg, #4cc9f0, #4895ef);
}

.gradient-purple {
  background: linear-gradient(135deg, #7209b7, #560bad);
}

.gradient-blue-light {
  background: linear-gradient(135deg, #4361ee, #3f37c9);
}

.gradient-purple-light {
  background: linear-gradient(135deg, #7209b7, #560bad);
}

.icon-container {
  width: 50px;
  height: 50px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.2);
  display: flex;
  align-items: center;
  justify-content: center;
}

.icon-circle {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
}

.pulse-dot {
  display: inline-block;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background-color: #fff;
  position: relative;
  animation: pulse 1.5s infinite;
}

.activity-card {
  border-radius: 12px;
  border: none;
  overflow: hidden;
  box-shadow: 0 4px 8px rgba(0,0,0,0.08);
  transition: transform 0.3s;
}

.activity-card:hover {
  transform: translateY(-3px);
}

.bg-primary-gradient {
  background: linear-gradient(135deg, #4361ee, #3a0ca3);
}

.bg-success-gradient {
  background: linear-gradient(135deg, #4cc9f0, #4895ef);
}

.bg-warning-gradient {
  background: linear-gradient(135deg, #f48c06, #e85d04);
}

.bg-danger-gradient {
  background: linear-gradient(135deg, #ef476f, #d90429);
}

.action-card {
  border-radius: 10px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.08);
  transition: transform 0.3s, box-shadow 0.3s;
  border: none;
  text-decoration: none;
  display: block;
  background-color: white;
}

.action-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 8px 16px rgba(0,0,0,0.12);
}

.activity-icon {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.2);
  display: flex;
  align-items: center;
  justify-content: center;
  transition: transform 0.3s;
}

.activity-card:hover .activity-icon {
  transform: scale(1.1);
}

.status-progress {
  box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
  transition: box-shadow 0.3s;
}

.status-progress:hover {
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
}

.status-badge-container {
  display: flex;
  align-items: center;
  padding: 6px;
  border-radius: 8px;
  transition: background-color 0.3s;
}

.status-badge-container:hover {
  background-color: rgba(0, 0, 0, 0.03);
}

.status-item {
  padding: 4px 8px;
  border-radius: 8px;
  transition: background-color 0.3s, transform 0.2s;
}

.status-item:hover {
  background-color: rgba(0, 0, 0, 0.05);
  transform: translateX(3px);
}

.chart-container-custom {
  transition: transform 0.3s;
}

.chart-container-custom:hover {
  transform: scale(1.05);
}

.action-icon {
  width: 70px;
  height: 70px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto;
  transition: transform 0.3s;
}

.action-card:hover .action-icon {
  transform: scale(1.1);
}

.total-count {
  transition: transform 0.3s;
}

.chart-container-custom:hover .total-count {
  transform: translate(-50%, -50%) scale(1.1);
}

@keyframes pulse {
  0% {
    transform: scale(0.95);
    box-shadow: 0 0 0 0 rgba(255, 255, 255, 0.7);
  }
  70% {
    transform: scale(1);
    box-shadow: 0 0 0 8px rgba(255, 255, 255, 0);
  }
  100% {
    transform: scale(0.95);
    box-shadow: 0 0 0 0 rgba(255, 255, 255, 0);
  }
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

.spin {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
</style> 