import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'

// Public pages
import LandingPage from '../views/LandingPage.vue'
import LoginView from '../views/LoginView.vue'
import RegisterView from '../views/RegisterView.vue'

// Lazy loading for role-specific pages (they'll be loaded only when needed)
const SponsorDashboard = () => import('../views/sponsor/DashboardView.vue')
const SponsorCampaigns = () => import('../views/sponsor/CampaignsView.vue')
const SponsorCampaignDetail = () => import('../views/sponsor/CampaignDetailView.vue')
const SponsorCampaignCreate = () => import('../views/sponsor/CampaignCreateView.vue')
const SponsorCampaignEdit = () => import('../views/sponsor/CampaignEditView.vue')
const SponsorAdRequests = () => import('../views/sponsor/AdRequestsView.vue')
const SponsorAdRequestDetail = () => import('../views/sponsor/AdRequestDetailView.vue')
const SponsorCreateRequest = () => import('../views/sponsor/CreateRequestView.vue')
const PaymentConfirmationView = () => import('../views/sponsor/PaymentConfirmationView.vue')
const InfluencerDashboard = () => import('../views/influencer/DashboardView.vue')
const InfluencerAdRequests = () => import('../views/influencer/AdRequestsView.vue')
const InfluencerAdRequestDetail = () => import('../views/influencer/AdRequestDetailView.vue')
const InfluencerCampaignBrowse = () => import('../views/influencer/CampaignBrowseView.vue')
const AdminDashboard = () => import('../views/admin/DashboardView.vue')
const AdminUsers = () => import('../views/admin/UsersView.vue')
const AdminCampaigns = () => import('../views/admin/CampaignsView.vue')
const AdminStatistics = () => import('../views/admin/StatisticsView.vue')
const AdminReports = () => import('../views/admin/ReportsView.vue')
const ProfileView = () => import('../views/ProfileView.vue')
const InfluencerSearchView = () => import('../views/search/InfluencerSearchView.vue')
const CampaignSearchView = () => import('../views/search/CampaignSearchView.vue')

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: LandingPage
    },
    {
      path: '/login',
      name: 'login',
      component: LoginView,
      meta: { requiresGuest: true }
    },
    {
      path: '/register',
      name: 'register',
      component: RegisterView,
      meta: { requiresGuest: true }
    },
    {
      path: '/profile',
      name: 'profile',
      component: ProfileView,
      meta: { requiresAuth: true }
    },
    
    // Sponsor routes
    {
      path: '/sponsor/dashboard',
      name: 'sponsor-dashboard',
      component: SponsorDashboard,
      meta: { requiresAuth: true, role: 'sponsor' }
    },
    {
      path: '/sponsor/campaigns',
      name: 'sponsor-campaigns',
      component: SponsorCampaigns,
      meta: { requiresAuth: true, role: 'sponsor' }
    },
    {
      path: '/sponsor/campaigns/create',
      name: 'sponsor-campaign-create',
      component: SponsorCampaignCreate,
      meta: { requiresAuth: true, role: 'sponsor' }
    },
    {
      path: '/sponsor/campaigns/:id',
      name: 'sponsor-campaign-detail',
      component: SponsorCampaignDetail,
      meta: { requiresAuth: true, role: 'sponsor' }
    },
    {
      path: '/sponsor/campaigns/:id/edit',
      name: 'sponsor-campaign-edit',
      component: SponsorCampaignEdit,
      meta: { requiresAuth: true, role: 'sponsor' }
    },
    {
      path: '/sponsor/campaigns/:id/create-request',
      name: 'sponsor-create-request',
      component: SponsorCreateRequest,
      meta: { requiresAuth: true, role: 'sponsor' }
    },
    {
      path: '/sponsor/ad-requests',
      name: 'sponsor-ad-requests',
      component: SponsorAdRequests,
      meta: { requiresAuth: true, role: 'sponsor' }
    },
    {
      path: '/sponsor/ad-requests/:id',
      name: 'sponsor-ad-request-detail',
      component: SponsorAdRequestDetail,
      meta: { requiresAuth: true, role: 'sponsor' }
    },
    {
      path: '/sponsor/payments/confirm/:adRequestId',
      name: 'payment-confirmation',
      component: PaymentConfirmationView,
      meta: { requiresAuth: true, role: 'sponsor' },
      props: true
    },
    {
      path: '/sponsor/payments/receipt/:adRequestId/:paymentId',
      name: 'payment-receipt',
      component: PaymentConfirmationView,
      meta: { requiresAuth: true, role: 'sponsor' },
      props: true
    },
    
    // Influencer routes
    {
      path: '/influencer/dashboard',
      name: 'influencer-dashboard',
      component: InfluencerDashboard,
      meta: { requiresAuth: true, role: 'influencer' }
    },
    {
      path: '/influencer/ad-requests',
      name: 'influencer-ad-requests',
      component: InfluencerAdRequests,
      meta: { requiresAuth: true, role: 'influencer' }
    },
    {
      path: '/influencer/ad-requests/:id',
      name: 'influencer-ad-request-detail',
      component: InfluencerAdRequestDetail,
      meta: { requiresAuth: true, role: 'influencer' }
    },
    {
      path: '/influencer/campaigns/browse',
      name: 'influencer-campaign-browse',
      component: InfluencerCampaignBrowse,
      meta: { requiresAuth: true, role: 'influencer' }
    },
    {
      path: '/campaigns/:id',
      name: 'campaign-detail',
      component: InfluencerCampaignBrowse,
      props: route => ({ selectedCampaignId: parseInt(route.params.id) }),
      meta: { requiresAuth: true }
    },
    
    // Search routes
    {
      path: '/search/influencers',
      name: 'search-influencers',
      component: InfluencerSearchView,
      meta: { requiresAuth: true, role: 'sponsor' }
    },
    {
      path: '/search/campaigns',
      name: 'search-campaigns',
      redirect: '/influencer/campaigns/browse',
      meta: { requiresAuth: true, role: 'influencer' }
    },
    
    // Admin routes
    {
      path: '/admin/dashboard',
      name: 'admin-dashboard',
      component: AdminDashboard,
      meta: { requiresAuth: true, role: 'admin' }
    },
    {
      path: '/admin/users',
      name: 'admin-users',
      component: AdminUsers,
      meta: { requiresAuth: true, role: 'admin' }
    },
    {
      path: '/admin/campaigns',
      name: 'admin-campaigns',
      component: AdminCampaigns,
      meta: { requiresAuth: true, role: 'admin' }
    },
    {
      path: '/admin/statistics',
      name: 'admin-statistics',
      component: AdminStatistics,
      meta: { requiresAuth: true, role: 'admin' }
    },
    {
      path: '/admin/reports',
      name: 'admin-reports',
      component: AdminReports,
      meta: { requiresAuth: true, role: 'admin' }
    },
    
    // 404 route
    {
      path: '/:pathMatch(.*)*',
      name: 'not-found',
      redirect: '/'
    }
  ]
})

// Navigation guards
router.beforeEach((to, from, next) => {
  const authStore = useAuthStore()
  const isAuthenticated = authStore.isAuthenticated
  const userRole = authStore.userRole
  
  // Check if the route requires authentication
  if (to.meta.requiresAuth && !isAuthenticated) {
    next({ name: 'login' })
    return
  }
  
  // Check if the route requires a specific role
  if (to.meta.role && to.meta.role !== userRole) {
    // Redirect to appropriate dashboard based on role
    if (userRole === 'sponsor') {
      next({ name: 'sponsor-dashboard' })
    } else if (userRole === 'influencer') {
      next({ name: 'influencer-dashboard' })
    } else if (userRole === 'admin') {
      next({ name: 'admin-dashboard' })
    } else {
      next({ name: 'home' })
    }
    return
  }
  
  // Check if the route requires guest access only
  if (to.meta.requiresGuest && isAuthenticated) {
    // Redirect to appropriate dashboard based on role
    if (userRole === 'sponsor') {
      next({ name: 'sponsor-dashboard' })
    } else if (userRole === 'influencer') {
      next({ name: 'influencer-dashboard' })
    } else if (userRole === 'admin') {
      next({ name: 'admin-dashboard' })
    } else {
      next({ name: 'home' })
    }
    return
  }
  
  next()
})

export default router 