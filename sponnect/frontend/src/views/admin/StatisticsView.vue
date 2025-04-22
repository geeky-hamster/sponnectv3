<script setup>
import { ref, onMounted, computed, watch } from 'vue'
import { adminService } from '../../services/api'
import { Bar, Pie, Line } from 'vue-chartjs'
import { Chart as ChartJS, Title, Tooltip, Legend, BarElement, CategoryScale, LinearScale, PieController, ArcElement, PointElement, LineElement } from 'chart.js'

// Register Chart.js components
ChartJS.register(Title, Tooltip, Legend, BarElement, CategoryScale, LinearScale, PieController, ArcElement, PointElement, LineElement)

// State
const loading = ref(true)
const chartLoading = ref(true)
const error = ref('')
const timeRange = ref('last_30_days')
const timeRanges = [
  { label: 'Today', value: 'today' },
  { label: 'Last 7 Days', value: 'last_7_days' },
  { label: 'Last 30 Days', value: 'last_30_days' },
  { label: 'This Month', value: 'this_month' },
  { label: 'Last Month', value: 'last_month' },
  { label: 'This Year', value: 'this_year' }
]

const stats = ref({
  users: {
    total: 0,
    active: 0,
    pending: 0,
    flagged: 0,
    by_role: {
      influencer: 0,
      sponsor: 0,
      admin: 0
    },
    growth: []
  },
  campaigns: {
    total: 0,
    active: 0,
    pending: 0,
    completed: 0,
    rejected: 0,
    by_category: [],
    spend: {
      total: 0,
      avg_per_campaign: 0
    }
  },
  engagements: {
    total: 0,
    pending: 0,
    approved: 0,
    rejected: 0,
    completed: 0,
    avg_rating: 0
  },
  revenue: {
    total: 0,
    current_month: 0,
    previous_month: 0,
    growth_percentage: 0
  }
})

// Chart data refs
const userGrowthChartData = ref({
  labels: [],
  datasets: [{
    label: 'New Users',
    data: [],
    backgroundColor: 'rgba(67, 97, 238, 0.2)',
    borderColor: 'rgba(67, 97, 238, 1)',
    borderWidth: 1,
    tension: 0.4
  }]
})

const campaignDistributionChartData = ref({
  labels: [],
  datasets: [{
    data: [],
    backgroundColor: [
      'rgba(67, 97, 238, 0.7)',
      'rgba(114, 9, 183, 0.7)',
      'rgba(76, 175, 80, 0.7)',
      'rgba(255, 152, 0, 0.7)',
      'rgba(244, 67, 54, 0.7)',
      'rgba(33, 150, 243, 0.7)'
    ]
  }]
})

const adRequestStatusChartData = ref({
  labels: [],
  datasets: [{
    data: [],
    backgroundColor: [
      'rgba(255, 152, 0, 0.7)', // Pending
      'rgba(33, 150, 243, 0.7)', // Negotiating
      'rgba(76, 175, 80, 0.7)',  // Accepted
      'rgba(244, 67, 54, 0.7)'   // Rejected
    ]
  }]
})

const campaignActivityChartData = ref({
  labels: [],
  datasets: [
    {
      label: 'New Campaigns',
      data: [],
      backgroundColor: 'rgba(67, 97, 238, 0.5)',
      borderColor: 'rgba(67, 97, 238, 1)',
      borderWidth: 1
    },
    {
      label: 'Ad Requests',
      data: [],
      backgroundColor: 'rgba(76, 175, 80, 0.5)',
      borderColor: 'rgba(76, 175, 80, 1)',
      borderWidth: 1
    }
  ]
})

// Computed properties
const userGrowth = computed(() => {
  if (!stats.value?.users?.growth || stats.value.users.growth.length < 2) return 0
  
  const current = stats.value.users.growth[stats.value.users.growth.length - 1]?.count || 0
  const previous = stats.value.users.growth[stats.value.users.growth.length - 2]?.count || 0
  
  if (previous === 0) return 100
  return ((current - previous) / previous) * 100
})

const revenueGrowth = computed(() => {
  return stats.value?.revenue?.growth_percentage || 0
})

// API calls
const loadStats = async () => {
  loading.value = true
  error.value = ''
  
  try {
    // Load main statistics
    const statsResponse = await adminService.getStats()
    stats.value = statsResponse.data || {}
    
    // Load chart data
    await loadChartData()
  } catch (err) {
    console.error('Failed to load statistics:', err)
    error.value = 'Failed to load statistics. Please try again later.'
  } finally {
    loading.value = false
  }
}

const loadChartData = async () => {
  chartLoading.value = true
  
  try {
    // Ensure stats.users.growth is initialized
    if (!stats.value.users) {
      stats.value.users = { growth: [] };
    } else if (!stats.value.users.growth) {
      stats.value.users.growth = [];
    }
    
    // Load user growth chart data
    const userGrowthResponse = await adminService.getUserGrowthChart({ 
      time_range: timeRange.value 
    })
    
    if (userGrowthResponse.data) {
      userGrowthChartData.value.labels = userGrowthResponse.data.labels || []
      userGrowthChartData.value.datasets[0].data = userGrowthResponse.data.datasets?.[0]?.data || []
      
      // Update growth data for stats if available
      if (userGrowthResponse.data.datasets?.[0]?.data && userGrowthResponse.data.labels) {
        stats.value.users.growth = userGrowthResponse.data.labels.map((date, index) => ({
          date: date,
          count: userGrowthResponse.data.datasets[0].data[index] || 0
        }))
      }
    }
    
    // Load campaign distribution chart data
    const campaignDistResponse = await adminService.getCampaignDistributionChart()
    
    if (campaignDistResponse.data) {
      // The backend returns data in the format {labels: [...], datasets: [{data: [...]}]}
      campaignDistributionChartData.value.labels = campaignDistResponse.data.labels || []
      campaignDistributionChartData.value.datasets[0].data = campaignDistResponse.data.datasets?.[0]?.data || []
    }
    
    // Load ad request status chart data
    const adRequestStatusResponse = await adminService.getAdRequestStatusChart()
    
    if (adRequestStatusResponse.data) {
      // The backend returns data in the format {labels: [...], datasets: [{data: [...]}]}
      adRequestStatusChartData.value.labels = adRequestStatusResponse.data.labels || []
      adRequestStatusChartData.value.datasets[0].data = adRequestStatusResponse.data.datasets?.[0]?.data || []
    }
    
    // Load campaign activity chart data
    const campaignActivityResponse = await adminService.getCampaignActivityChart({
      time_range: timeRange.value
    })
    
    if (campaignActivityResponse.data) {
      campaignActivityChartData.value.labels = campaignActivityResponse.data.labels || []
      campaignActivityChartData.value.datasets[0].data = campaignActivityResponse.data.datasets?.[0]?.data || []
      campaignActivityChartData.value.datasets[1].data = campaignActivityResponse.data.datasets?.[1]?.data || []
    }
    
  } catch (err) {
    console.error('Failed to load chart data:', err)
    error.value = 'Failed to load chart data. Please try again later.'
  } finally {
    chartLoading.value = false
  }
}

// Format number with commas
const formatNumber = (num) => {
  return new Intl.NumberFormat().format(num || 0)
}

// Format currency
const formatCurrency = (amount) => {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 0
  }).format(amount || 0)
}

// Format percentage
const formatPercentage = (value) => {
  const numValue = Number(value) || 0
  return `${numValue > 0 ? '+' : ''}${numValue.toFixed(1)}%`
}

// Setup and load data
onMounted(() => {
  loadStats()
})

// Watch for time range changes
watch(timeRange, () => {
  loadStats()
})
</script>

<template>
  <div class="admin-statistics py-5">
    <div class="container">
      <div class="d-flex justify-content-between align-items-center mb-4">
        <h1>Dashboard Statistics</h1>
        <nav aria-label="breadcrumb">
          <ol class="breadcrumb mb-0">
            <li class="breadcrumb-item">
              <router-link to="/admin/dashboard">Dashboard</router-link>
            </li>
            <li class="breadcrumb-item active">Statistics</li>
          </ol>
        </nav>
      </div>
      
      <!-- Alert Messages -->
      <div v-if="error" class="alert alert-danger alert-dismissible fade show" role="alert">
        {{ error }}
        <button type="button" class="btn-close" @click="error = ''"></button>
      </div>
      
      <!-- Time Range Selector -->
      <div class="card border-0 shadow-sm mb-4">
        <div class="card-body d-flex justify-content-between align-items-center">
          <h5 class="card-title mb-0">
            <i class="bi bi-calendar-range me-2"></i>Time Range
          </h5>
          <div class="time-range-selector" style="width: 200px;">
            <select class="form-select" v-model="timeRange">
              <option v-for="range in timeRanges" :key="range.value" :value="range.value">
                {{ range.label }}
              </option>
            </select>
          </div>
        </div>
      </div>
      
      <!-- Loading Spinner -->
      <div v-if="loading" class="text-center py-5">
        <div class="spinner-border text-primary" role="status">
          <span class="visually-hidden">Loading...</span>
        </div>
        <p class="mt-3">Loading statistics...</p>
      </div>
      
      <div v-else>
        <!-- Summary Cards Row -->
        <div class="row g-4 mb-4">
          <!-- Users Card -->
          <div class="col-md-6 col-lg-3">
            <div class="card border-0 shadow-sm h-100">
              <div class="card-body">
                <div class="d-flex justify-content-between align-items-start">
                  <div>
                    <h6 class="text-muted mb-1">Total Users</h6>
                    <h2 class="mb-2">{{ formatNumber(stats.users?.total || 0) }}</h2>
                    <div :class="userGrowth >= 0 ? 'text-success' : 'text-danger'">
                      <i :class="userGrowth >= 0 ? 'bi bi-graph-up-arrow' : 'bi bi-graph-down-arrow'"></i>
                      <span>{{ formatPercentage(userGrowth) }}</span>
                    </div>
                  </div>
                  <div class="icon-bg bg-primary bg-opacity-10 rounded-circle p-3">
                    <i class="bi bi-people text-primary fs-3"></i>
                  </div>
                </div>
              </div>
              <div class="card-footer bg-white border-0 py-2">
                <router-link to="/admin/users" class="text-decoration-none text-muted small">
                  <i class="bi bi-arrow-right me-1"></i>View all users
                </router-link>
              </div>
            </div>
          </div>
          
          <!-- Campaigns Card -->
          <div class="col-md-6 col-lg-3">
            <div class="card border-0 shadow-sm h-100">
              <div class="card-body">
                <div class="d-flex justify-content-between align-items-start">
                  <div>
                    <h6 class="text-muted mb-1">Active Campaigns</h6>
                    <h2 class="mb-2">{{ formatNumber(stats.campaigns?.active || 0) }}</h2>
                    <div class="text-muted">
                      <i class="bi bi-layers"></i>
                      <span>{{ formatNumber(stats.campaigns?.total || 0) }} total</span>
                    </div>
                  </div>
                  <div class="icon-bg bg-success bg-opacity-10 rounded-circle p-3">
                    <i class="bi bi-megaphone text-success fs-3"></i>
                  </div>
                </div>
              </div>
              <div class="card-footer bg-white border-0 py-2">
                <router-link to="/admin/campaigns" class="text-decoration-none text-muted small">
                  <i class="bi bi-arrow-right me-1"></i>View all campaigns
                </router-link>
              </div>
            </div>
          </div>
          
          <!-- Engagements Card -->
          <div class="col-md-6 col-lg-3">
            <div class="card border-0 shadow-sm h-100">
              <div class="card-body">
                <div class="d-flex justify-content-between align-items-start">
                  <div>
                    <h6 class="text-muted mb-1">Total Engagements</h6>
                    <h2 class="mb-2">{{ formatNumber(stats.engagements?.total || 0) }}</h2>
                    <div class="text-muted">
                      <i class="bi bi-check-circle"></i>
                      <span>{{ formatNumber(stats.engagements?.completed || 0) }} completed</span>
                    </div>
                  </div>
                  <div class="icon-bg bg-warning bg-opacity-10 rounded-circle p-3">
                    <i class="bi bi-briefcase text-warning fs-3"></i>
                  </div>
                </div>
              </div>
              <div class="card-footer bg-white border-0 py-2">
                <router-link to="/admin/engagements" class="text-decoration-none text-muted small">
                  <i class="bi bi-arrow-right me-1"></i>View all engagements
                </router-link>
              </div>
            </div>
          </div>
          
          <!-- Revenue Card -->
          <div class="col-md-6 col-lg-3">
            <div class="card border-0 shadow-sm h-100">
              <div class="card-body">
                <div class="d-flex justify-content-between align-items-start">
                  <div>
                    <h6 class="text-muted mb-1">Total Revenue</h6>
                    <h2 class="mb-2">{{ formatCurrency(stats.revenue?.total || 0) }}</h2>
                    <div :class="revenueGrowth >= 0 ? 'text-success' : 'text-danger'">
                      <i :class="revenueGrowth >= 0 ? 'bi bi-graph-up-arrow' : 'bi bi-graph-down-arrow'"></i>
                      <span>{{ formatPercentage(revenueGrowth) }}</span>
                    </div>
                  </div>
                  <div class="icon-bg bg-info bg-opacity-10 rounded-circle p-3">
                    <i class="bi bi-cash-stack text-info fs-3"></i>
                  </div>
                </div>
              </div>
              <div class="card-footer bg-white border-0 py-2">
                <router-link to="/admin/finances" class="text-decoration-none text-muted small">
                  <i class="bi bi-arrow-right me-1"></i>View financial details
                </router-link>
              </div>
            </div>
          </div>
        </div>
        
        <!-- Charts Row -->
        <div class="row g-4 mb-4">
          <!-- User Growth Chart -->
          <div class="col-lg-6">
            <div class="card border-0 shadow-sm h-100">
              <div class="card-header bg-white border-0 pt-4 pb-3">
                <h5 class="mb-0">User Growth</h5>
                <p class="text-muted small mb-0">New user registrations over time</p>
              </div>
              <div class="card-body">
                <div class="chart-container" style="height: 300px;">
                  <div v-if="userGrowthChartData.labels.length === 0" class="text-center text-muted py-5">
                    <i class="bi bi-exclamation-circle fs-1"></i>
                    <p>No user growth data available for the selected period</p>
                  </div>
                  <Line
                    v-else
                    :data="userGrowthChartData"
                    :options="{
                      responsive: true,
                      maintainAspectRatio: false,
                      plugins: {
                        legend: {
                          position: 'top'
                        }
                      },
                      scales: {
                        y: {
                          beginAtZero: true
                        }
                      }
                    }"
                  />
                </div>
              </div>
            </div>
          </div>
          
          <!-- Campaign Distribution Chart -->
          <div class="col-lg-6">
            <div class="card border-0 shadow-sm h-100">
              <div class="card-header bg-white border-0 pt-4 pb-3">
                <h5 class="mb-0">Campaign Budget Distribution</h5>
                <p class="text-muted small mb-0">Campaigns by budget range</p>
              </div>
              <div class="card-body">
                <div class="chart-container" style="height: 300px;">
                  <div v-if="campaignDistributionChartData.labels.length === 0" class="text-center text-muted py-5">
                    <i class="bi bi-exclamation-circle fs-1"></i>
                    <p>No campaign distribution data available</p>
                  </div>
                  <Pie
                    v-else
                    :data="campaignDistributionChartData"
                    :options="{
                      responsive: true,
                      maintainAspectRatio: false,
                      plugins: {
                        legend: {
                          position: 'right',
                          align: 'start'
                        }
                      }
                    }"
                  />
                </div>
              </div>
            </div>
          </div>
        </div>
        
        <!-- Ad Request Status and Campaign Activity Row -->
        <div class="row g-4 mt-4">
          <!-- Ad Request Status Chart -->
          <div class="col-md-6">
            <div class="card border-0 shadow-sm h-100">
              <div class="card-header bg-white border-0 pt-4 pb-3">
                <h5 class="mb-0">Ad Request Status</h5>
                <p class="text-muted small mb-0">Distribution of ad requests by status</p>
              </div>
              <div class="card-body">
                <div class="chart-container" style="height: 300px;">
                  <div v-if="adRequestStatusChartData.labels.length === 0" class="text-center text-muted py-5">
                    <i class="bi bi-exclamation-circle fs-1"></i>
                    <p>No ad request data available for the selected period</p>
                  </div>
                  <Pie
                    v-else
                    :data="adRequestStatusChartData"
                    :options="{
                      responsive: true,
                      maintainAspectRatio: false,
                      plugins: {
                        legend: {
                          position: 'right',
                          align: 'start'
                        }
                      }
                    }"
                  />
                </div>
              </div>
            </div>
          </div>
          
          <!-- Campaign Activity Chart -->
          <div class="col-md-6">
            <div class="card border-0 shadow-sm h-100">
              <div class="card-header bg-white border-0 pt-4 pb-3">
                <h5 class="mb-0">Campaign Activity</h5>
                <p class="text-muted small mb-0">New campaigns and ad requests over time</p>
              </div>
              <div class="card-body">
                <div class="chart-container" style="height: 300px;">
                  <div v-if="campaignActivityChartData.labels.length === 0" class="text-center text-muted py-5">
                    <i class="bi bi-exclamation-circle fs-1"></i>
                    <p>No campaign activity data available</p>
                  </div>
                  <Bar
                    v-else
                    :data="campaignActivityChartData"
                    :options="{
                      responsive: true,
                      maintainAspectRatio: false,
                      plugins: {
                        legend: {
                          position: 'top'
                        }
                      },
                      scales: {
                        x: {
                          stacked: false
                        },
                        y: {
                          stacked: false,
                          beginAtZero: true
                        }
                      }
                    }"
                  />
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
.icon-bg {
  width: 60px;
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.chart-container {
  position: relative;
  width: 100%;
}

/* Add animation for loading */
@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

.admin-statistics {
  animation: fadeIn 0.5s ease-in-out;
}
</style> 