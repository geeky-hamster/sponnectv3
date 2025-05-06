<script setup>
import { ref, onMounted, computed, watch, onUnmounted } from 'vue'
import { adminService } from '../../services/api'
import { Bar, Pie, Line } from 'vue-chartjs'
import { Chart as ChartJS, Title, Tooltip, Legend, BarElement, CategoryScale, LinearScale, PieController, ArcElement, PointElement, LineElement } from 'chart.js'
import { formatCurrency, formatDate, formatDateTime } from '../../utils/formatters'

// Register Chart.js components
ChartJS.register(Title, Tooltip, Legend, BarElement, CategoryScale, LinearScale, PieController, ArcElement, PointElement, LineElement)

// State
const loading = ref(true)
const chartLoading = ref(true)
const error = ref('')
const timeRange = ref('last_30_days')

// Add screen size tracking
const isSmallScreen = ref(window.innerWidth < 576)
const isMediumScreen = ref(window.innerWidth < 768)
const isLargeScreen = ref(window.innerWidth < 992)

// Initialize stats with the same structure as the backend response
const stats = ref({
  total_users: 0,
  active_sponsors: 0,
  active_influencers: 0,
  pending_sponsors: 0,
  public_campaigns: 0,
  private_campaigns: 0,
  flagged_users: 0,
  flagged_campaigns: 0,
  ad_requests_by_status: {
    Pending: 0,
    Negotiating: 0,
    Accepted: 0,
    Rejected: 0
  },
  payment_stats: {
    total_payments: 0,
    total_platform_fees: 0,
    total_payment_count: 0,
    recent_fees: 0
  },
  // For computed values and chart data
  users: {
    growth: []
  },
  campaigns: {
    total: 0,
    active: 0
  },
  engagements: {
    total: 0,
    completed: 0
  },
  revenue: {
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

// Responsive chart options
const getChartOptions = (chartType) => {
  const baseOptions = {
    responsive: true,
    maintainAspectRatio: false,
  }
  
  switch(chartType) {
    case 'line':
      return {
        ...baseOptions,
        plugins: {
          legend: {
            position: 'top',
            display: !isMediumScreen.value
          },
          tooltip: {
            mode: 'index',
            intersect: false
          }
        },
        scales: {
          y: {
            beginAtZero: true,
            ticks: {
              maxTicksLimit: isSmallScreen.value ? 5 : 10
            }
          },
          x: {
            ticks: {
              maxRotation: 45,
              minRotation: 45,
              maxTicksLimit: isSmallScreen.value ? 5 : 10
            }
          }
        }
      }
    case 'pie':
      return {
        ...baseOptions,
        plugins: {
          legend: {
            position: isSmallScreen.value ? 'bottom' : 'right',
            align: isSmallScreen.value ? 'center' : 'start',
            labels: {
              boxWidth: isSmallScreen.value ? 15 : 20,
              padding: isSmallScreen.value ? 10 : 20
            }
          }
        }
      }
    case 'bar':
      return {
        ...baseOptions,
        plugins: {
          legend: {
            position: 'top',
            display: !isSmallScreen.value,
            labels: {
              boxWidth: isMediumScreen.value ? 10 : 20
            }
          },
          tooltip: {
            mode: 'index',
            intersect: false
          }
        },
        scales: {
          x: {
            stacked: false,
            ticks: {
              maxRotation: 45,
              minRotation: 45,
              maxTicksLimit: isSmallScreen.value ? 5 : 10
            }
          },
          y: {
            stacked: false,
            beginAtZero: true,
            ticks: {
              maxTicksLimit: isSmallScreen.value ? 5 : 10
            }
          }
        }
      }
    default:
      return baseOptions
  }
}

// Computed properties
const userGrowth = computed(() => {
  if (!stats.value?.users?.growth || !Array.isArray(stats.value.users.growth) || stats.value.users.growth.length < 2) return 0
  
  const current = stats.value.users.growth[stats.value.users.growth.length - 1]?.count || 0
  const previous = stats.value.users.growth[stats.value.users.growth.length - 2]?.count || 0
  
  if (previous === 0) return 0
  return ((current - previous) / previous) * 100
})

const revenueGrowth = computed(() => {
  return stats.value?.revenue?.growth_percentage || 0
})

// Handle window resize
const handleResize = () => {
  isSmallScreen.value = window.innerWidth < 576
  isMediumScreen.value = window.innerWidth < 768
  isLargeScreen.value = window.innerWidth < 992
}

// API calls
const loadStats = async () => {
  loading.value = true
  error.value = ''
  
  try {
    // Load main statistics
    const statsResponse = await adminService.getStats()
    console.log('Stats API response:', statsResponse)
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
    console.log('User Growth API response:', userGrowthResponse)
    
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
    console.log('Campaign Distribution API response:', campaignDistResponse)
    
    if (campaignDistResponse.data) {
      // The backend returns data in the format {labels: [...], datasets: [{data: [...]}]}
      campaignDistributionChartData.value.labels = campaignDistResponse.data.labels || []
      campaignDistributionChartData.value.datasets[0].data = campaignDistResponse.data.datasets?.[0]?.data || []
    }
    
    // Load ad request status chart data
    const adRequestStatusResponse = await adminService.getAdRequestStatusChart()
    console.log('Ad Request Status API response:', adRequestStatusResponse)
    
    if (adRequestStatusResponse.data) {
      // The backend returns data in the format {labels: [...], datasets: [{data: [...]}]}
      adRequestStatusChartData.value.labels = adRequestStatusResponse.data.labels || []
      adRequestStatusChartData.value.datasets[0].data = adRequestStatusResponse.data.datasets?.[0]?.data || []
    }
    
    // Load campaign activity chart data
    const campaignActivityResponse = await adminService.getCampaignActivityChart({
      time_range: timeRange.value
    })
    console.log('Campaign Activity API response:', campaignActivityResponse)
    
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

// Format percentage
const formatPercentage = (value) => {
  const numValue = Number(value) || 0
  return `${numValue > 0 ? '+' : ''}${numValue.toFixed(1)}%`
}

// Setup and load data
onMounted(() => {
  loadStats()
  
  // Add window resize event listener
  window.addEventListener('resize', handleResize)
})

// Clean up event listeners
onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
})

// Watch for time range changes
watch(timeRange, () => {
  loadStats()
})
</script>

<template>
  <div class="admin-statistics py-3 py-md-5">
    <div class="container-fluid container-md">
      <div class="d-flex flex-column flex-md-row justify-content-between align-items-start align-items-md-center mb-4">
        <h1 class="h2 mb-3 mb-md-0 dashboard-title">Dashboard Statistics</h1>
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
      
      <!-- Loading Spinner -->
      <div v-if="loading" class="text-center py-5">
        <div class="spinner-border text-primary" role="status">
          <span class="visually-hidden">Loading...</span>
        </div>
        <p class="mt-3">Loading statistics...</p>
      </div>
      
      <div v-else>
        <!-- Summary Cards Row -->
        <div class="row g-3 g-md-4 mb-4">
          <!-- Users Card -->
          <div class="col-6 col-md-6 col-lg-3">
            <div class="card border-0 dashboard-card gradient-blue h-100">
              <div class="card-body p-4">
                <div class="d-flex justify-content-between align-items-start">
                  <div>
                    <h6 class="card-subtitle mb-2 text-white opacity-75">Total Users</h6>
                    <h2 class="mb-2 card-value text-white">{{ formatNumber(stats.total_users) }}</h2>
                    <div class="text-white">
                      <i class="bi bi-arrow-up-right"></i>
                      <span>{{ userGrowth >= 0 ? '+' : '' }}{{ formatPercentage(userGrowth) }}</span>
                    </div>
                  </div>
                  <div class="icon-container">
                    <i class="bi bi-people-fill text-white fs-4"></i>
                  </div>
                </div>
                <router-link to="/admin/users" class="stretched-link"></router-link>
              </div>
            </div>
          </div>
          
          <!-- Campaign Card -->
          <div class="col-6 col-md-6 col-lg-3">
            <div class="card border-0 dashboard-card gradient-green h-100">
              <div class="card-body p-4">
                <div class="d-flex justify-content-between align-items-start">
                  <div>
                    <h6 class="card-subtitle mb-2 text-white opacity-75">Campaigns</h6>
                    <h2 class="mb-2 card-value text-white">{{ stats.public_campaigns + stats.private_campaigns }}</h2>
                    <div class="d-flex align-items-center small">
                      <span class="badge bg-light text-success me-2">{{ stats.public_campaigns }} Public</span>
                      <span class="badge bg-light text-secondary">{{ stats.private_campaigns }} Private</span>
                    </div>
                  </div>
                  <div class="icon-container">
                    <i class="bi bi-bullseye text-white fs-4"></i>
                  </div>
                </div>
                <router-link to="/admin/campaigns" class="stretched-link"></router-link>
              </div>
            </div>
          </div>
          
          <!-- Engagement Card -->
          <div class="col-6 col-md-6 col-lg-3">
            <div class="card border-0 dashboard-card gradient-orange h-100">
              <div class="card-body p-4">
                <div class="d-flex justify-content-between align-items-start">
                  <div>
                    <h6 class="card-subtitle mb-2 text-white opacity-75">Ad Requests</h6>
                    <h2 class="mb-2 card-value text-white">{{ Object.values(stats.ad_requests_by_status || {}).reduce((sum, val) => sum + val, 0) }}</h2>
                    <div class="d-flex align-items-center small text-white">
                      <i class="bi bi-check-circle-fill me-1"></i>
                      <span>{{ stats.ad_requests_by_status?.Accepted || 0 }} accepted</span>
                    </div>
                  </div>
                  <div class="icon-container">
                    <i class="bi bi-clipboard2-data text-white fs-4"></i>
                  </div>
                </div>
                <router-link to="/admin/engagements" class="stretched-link"></router-link>
              </div>
            </div>
          </div>
          
          <!-- Flagged Items Card -->
          <div class="col-6 col-md-6 col-lg-3">
            <div class="card border-0 dashboard-card gradient-red h-100">
              <div class="card-body p-4">
                <div class="d-flex justify-content-between align-items-start">
                  <div>
                    <h6 class="card-subtitle mb-2 text-white opacity-75">Flagged Items</h6>
                    <h2 class="mb-2 card-value text-white">{{ stats.flagged_users + stats.flagged_campaigns }}</h2>
                    <div class="d-flex flex-wrap gap-2">
                      <span class="badge bg-light text-danger">{{ stats.flagged_users }} Users</span>
                      <span class="badge bg-light text-danger">{{ stats.flagged_campaigns }} Campaigns</span>
                    </div>
                  </div>
                  <div class="icon-container">
                    <i class="bi bi-shield-exclamation text-white fs-4"></i>
                  </div>
                </div>
                <router-link to="/admin/users?flagged=true" class="stretched-link"></router-link>
              </div>
            </div>
          </div>
        </div>
        
        <!-- Charts Row -->
        <div class="row g-4 mb-4">
          <!-- User Growth Chart -->
          <div class="col-12 col-lg-6">
            <div class="card border-0 chart-card h-100">
              <div class="card-header bg-white border-0 pt-3 pt-md-4 pb-3">
                <h5 class="mb-0">User Growth</h5>
                <p class="text-muted small mb-0">New user registrations over time</p>
              </div>
              <div class="card-body">
                <div class="chart-container" style="min-height: 250px; height: 30vh;">
                  <div v-if="userGrowthChartData.labels.length === 0" class="text-center text-muted py-5">
                    <i class="bi bi-exclamation-circle fs-1"></i>
                    <p>No user growth data available for the selected period</p>
                  </div>
                  <Line
                    v-else
                    :data="userGrowthChartData"
                    :options="getChartOptions('line')"
                  />
                </div>
              </div>
            </div>
          </div>
          
          <!-- Campaign Distribution Chart -->
          <div class="col-12 col-lg-6">
            <div class="card border-0 chart-card h-100">
              <div class="card-header bg-white border-0 pt-3 pt-md-4 pb-3">
                <h5 class="mb-0">Campaign Budget Distribution</h5>
                <p class="text-muted small mb-0">Campaigns by budget range</p>
              </div>
              <div class="card-body">
                <div class="chart-container" style="min-height: 250px; height: 30vh;">
                  <div v-if="campaignDistributionChartData.labels.length === 0" class="text-center text-muted py-5">
                    <i class="bi bi-exclamation-circle fs-1"></i>
                    <p>No campaign distribution data available</p>
                  </div>
                  <Pie
                    v-else
                    :data="campaignDistributionChartData"
                    :options="getChartOptions('pie')"
                  />
                </div>
              </div>
            </div>
          </div>
        </div>
        
        <!-- Ad Request Status and Campaign Activity Row -->
        <div class="row g-4 mt-3 mt-md-4">
          <!-- Ad Request Status Chart -->
          <div class="col-12 col-lg-6">
            <div class="card border-0 chart-card h-100">
              <div class="card-header bg-white border-0 pt-3 pt-md-4 pb-3">
                <h5 class="mb-0">Ad Request Status</h5>
                <p class="text-muted small mb-0">Distribution of ad requests by status</p>
              </div>
              <div class="card-body">
                <div class="chart-container" style="min-height: 250px; height: 30vh;">
                  <div v-if="adRequestStatusChartData.labels.length === 0" class="text-center text-muted py-5">
                    <i class="bi bi-exclamation-circle fs-1"></i>
                    <p>No ad request data available for the selected period</p>
                  </div>
                  <Pie
                    v-else
                    :data="adRequestStatusChartData"
                    :options="getChartOptions('pie')"
                  />
                </div>
              </div>
            </div>
          </div>
          
          <!-- Campaign Activity Chart -->
          <div class="col-12 col-lg-6">
            <div class="card border-0 chart-card h-100">
              <div class="card-header bg-white border-0 pt-3 pt-md-4 pb-3">
                <h5 class="mb-0">Campaign Activity</h5>
                <p class="text-muted small mb-0">New campaigns and ad requests over time</p>
              </div>
              <div class="card-body">
                <div class="chart-container" style="min-height: 250px; height: 30vh;">
                  <div v-if="campaignActivityChartData.labels.length === 0" class="text-center text-muted py-5">
                    <i class="bi bi-exclamation-circle fs-1"></i>
                    <p>No campaign activity data available</p>
                  </div>
                  <Bar
                    v-else
                    :data="campaignActivityChartData"
                    :options="getChartOptions('bar')"
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
.dashboard-title {
  font-weight: 700;
  margin-bottom: 1.5rem;
  position: relative;
  padding-bottom: 0.5rem;
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
  position: relative;
}

.dashboard-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 12px 20px rgba(0,0,0,0.15);
}

.gradient-blue {
  background: linear-gradient(135deg, #4361ee, #3a0ca3);
}

.gradient-green {
  background: linear-gradient(135deg, #4cc9f0, #4895ef);
}

.gradient-orange {
  background: linear-gradient(135deg, #f48c06, #e85d04);
}

.gradient-red {
  background: linear-gradient(135deg, #ef476f, #d90429);
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

.chart-card {
  border-radius: 15px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.08);
  transition: box-shadow 0.3s;
  overflow: hidden;
}

.chart-card:hover {
  box-shadow: 0 8px 16px rgba(0,0,0,0.12);
}

.chart-container {
  position: relative;
  width: 100%;
}

/* Responsive adjustments for card values */
.card-value {
  font-size: 1.5rem;
  font-weight: 700;
}

@media (min-width: 576px) {
  .card-value {
    font-size: 1.75rem;
  }
}

@media (min-width: 992px) {
  .card-value {
    font-size: 2rem;
  }
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
