import { apiService } from '../stores/auth'

// Auth Services
export const authService = {
  login: (credentials) => apiService.post('/api/login', credentials),
  register: (userData) => apiService.post('/api/register', userData),
  getProfile: () => apiService.get('/api/profile'),
  updateProfile: (profileData) => apiService.put('/api/profile', profileData)
}

// Sponsor Services
export const sponsorService = {
  // Campaign management
  getCampaigns: () => apiService.get('/api/sponsor/campaigns'),
  getCampaign: (id) => apiService.get(`/api/sponsor/campaigns/${id}`),
  createCampaign: (campaignData) => apiService.post('/api/sponsor/campaigns', campaignData),
  updateCampaign: (id, campaignData) => apiService.put(`/api/sponsor/campaigns/${id}`, campaignData),
  deleteCampaign: (id) => apiService.delete(`/api/sponsor/campaigns/${id}`),
  
  // Ad request management
  getAdRequests: (params) => apiService.get('/api/sponsor/ad_requests', { params }),
  getAdRequest: (id) => apiService.get(`/api/sponsor/ad_requests/${id}`),
  createAdRequest: (campaignId, requestData) => apiService.post(`/api/sponsor/campaigns/${campaignId}/ad_requests`, requestData),
  negotiateAdRequest: (requestId, data) => apiService.put(`/api/sponsor/ad_requests/${requestId}`, data),
  deleteAdRequest: (requestId) => apiService.delete(`/api/sponsor/ad_requests/${requestId}`),
  
  // Applications
  getCampaignApplications: (campaignId, params) => apiService.get(`/api/sponsor/campaigns/${campaignId}/applications`, { params }),
  acceptApplication: (requestId) => apiService.patch(`/api/sponsor/applications/${requestId}/accept`),
  rejectApplication: (requestId) => apiService.patch(`/api/sponsor/applications/${requestId}/reject`),
  
  // Progress Updates
  getProgressUpdates: (adRequestId) => apiService.get(`/api/sponsor/ad_requests/${adRequestId}/progress`),
  reviewProgressUpdate: (adRequestId, updateId, data) => apiService.patch(`/api/sponsor/ad_requests/${adRequestId}/progress/${updateId}`, data),
  
  // Payments
  getPayments: (adRequestId) => apiService.get(`/api/sponsor/ad_requests/${adRequestId}/payments`),
  createPayment: (adRequestId, data) => apiService.post(`/api/sponsor/ad_requests/${adRequestId}/payments`, data)
}

// Influencer Services
export const influencerService = {
  // Ad request management
  getAdRequests: (params) => apiService.get('/api/influencer/ad_requests', { params }),
  
  respondToAdRequest: (requestId, data) => {
    console.log(`Sending request to /api/influencer/ad_requests/${requestId} with data:`, data)
    
    // Validate data before sending
    const validData = { 
      action: data.action 
    }
    
    // Only include message if it's not empty
    if (data.message) {
      validData.message = data.message
    }
    
    // Only include payment amount for negotiation
    if (data.action === 'negotiate' && data.payment_amount) {
      validData.payment_amount = parseFloat(data.payment_amount)
    }
    
    return apiService.patch(`/api/influencer/ad_requests/${requestId}`, validData)
  },
  
  // Campaign applications
  getAvailableCampaigns: (params) => apiService.get('/api/search/campaigns', { params }),
  applyCampaign: (data) => {
    const campaignId = data.campaign_id;
    return apiService.post(`/api/influencer/campaigns/${campaignId}/apply`, data);
  },
  
  // Progress Updates
  getProgressUpdates: (adRequestId) => apiService.get(`/api/influencer/ad_requests/${adRequestId}/progress`),
  addProgressUpdate: (adRequestId, data) => apiService.post(`/api/influencer/ad_requests/${adRequestId}/progress`, data),
  
  // Payments
  getPayments: (adRequestId) => apiService.get(`/api/influencer/ad_requests/${adRequestId}/payments`),
  
  // Negotiations
  getNegotiations: () => apiService.get('/api/influencer/negotiations')
}

// Search Services
export const searchService = {
  searchInfluencers: (params) => apiService.get('/api/search/influencers', { 
    params: {
      query: params.query,
      category: params.category,
      niche: params.niche,
      min_reach: params.minReach,
      max_reach: params.maxReach,
      limit: params.limit,
      page: params.page || 1
    }
  }),
  searchCampaigns: (params) => apiService.get('/api/search/campaigns', { params })
}

// Admin Services
export const adminService = {
  // User management
  getUsers: (params) => apiService.get('/api/admin/users', { params }),
  flagUser: (userId) => apiService.patch(`/api/admin/users/${userId}/flag`),
  unflagUser: (userId) => apiService.patch(`/api/admin/users/${userId}/unflag`),
  activateUser: (userId) => apiService.patch(`/api/admin/users/${userId}/activate`),
  deactivateUser: (userId) => apiService.patch(`/api/admin/users/${userId}/deactivate`),
  
  // Sponsor management
  getPendingSponsors: () => apiService.get('/api/admin/pending_sponsors'),
  approveSponsor: (sponsorId) => apiService.patch(`/api/admin/sponsors/${sponsorId}/approve`),
  rejectSponsor: (sponsorId) => apiService.patch(`/api/admin/sponsors/${sponsorId}/reject`),
  
  // Campaign management
  getCampaigns: (params) => apiService.get('/api/admin/campaigns', { params }),
  approveCampaign: (campaignId) => apiService.patch(`/api/admin/campaigns/${campaignId}/approve`),
  rejectCampaign: (campaignId) => apiService.patch(`/api/admin/campaigns/${campaignId}/reject`),
  pauseCampaign: (campaignId) => apiService.patch(`/api/admin/campaigns/${campaignId}/pause`),
  activateCampaign: (campaignId) => apiService.patch(`/api/admin/campaigns/${campaignId}/activate`),
  featureCampaign: (campaignId) => apiService.patch(`/api/admin/campaigns/${campaignId}/feature`),
  unfeatureCampaign: (campaignId) => apiService.patch(`/api/admin/campaigns/${campaignId}/unfeature`),
  flagCampaign: (campaignId) => apiService.patch(`/api/admin/campaigns/${campaignId}/flag`),
  unflagCampaign: (campaignId) => apiService.patch(`/api/admin/campaigns/${campaignId}/unflag`),
  
  // Statistics and Analytics
  getStats: () => apiService.get('/api/admin/stats'),
  getUserGrowthChart: (params) => apiService.get('/api/charts/user-growth', { params }),
  getCampaignDistributionChart: () => apiService.get('/api/charts/campaign-distribution'),
  getAdRequestStatusChart: () => apiService.get('/api/charts/ad-request-status'),
  getCampaignActivityChart: (params) => apiService.get('/api/charts/campaign-activity', { params }),
  getDashboardSummary: () => apiService.get('/api/charts/dashboard-summary'),
  getConversionRatesChart: () => apiService.get('/api/charts/conversion-rates')
}

// Negotiation History
export const negotiationService = {
  getHistory: (adRequestId) => apiService.get(`/api/ad_requests/${adRequestId}/history`),
  getCampaignNegotiationSummary: (campaignId) => apiService.get(`/api/sponsor/campaigns/${campaignId}/negotiation_summary`)
} 