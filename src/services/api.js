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
  
  // Influencer management
  getPendingInfluencers: () => apiService.get('/api/admin/pending_influencers'),
  approveInfluencer: (influencerId) => apiService.patch(`/api/admin/influencers/${influencerId}/approve`),
  rejectInfluencer: (influencerId) => apiService.patch(`/api/admin/influencers/${influencerId}/reject`),
  
  // Get all pending users (both sponsors and influencers)
  getPendingUsers: () => apiService.get('/api/admin/pending_users'),
  
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
  
  // Ad request management
  getAdRequests: (params) => apiService.get('/api/admin/ad_requests', { params }),
  getAdRequest: (adRequestId) => apiService.get(`/api/admin/ad_requests/${adRequestId}`),
  flagAdRequest: (adRequestId) => apiService.patch(`/api/admin/ad_requests/${adRequestId}/flag`),
  unflagAdRequest: (adRequestId) => apiService.patch(`/api/admin/ad_requests/${adRequestId}/unflag`),
  
  // Statistics and Analytics
  getStats: () => apiService.get('/api/admin/stats'),
  getUserGrowthChart: (params) => apiService.get('/api/charts/user-growth', { params }),
  getCampaignDistributionChart: () => apiService.get('/api/charts/campaign-distribution'),
  getAdRequestStatusChart: () => apiService.get('/api/charts/ad-request-status'),
  getCampaignActivityChart: (params) => apiService.get('/api/charts/campaign-activity', { params }),
  getDashboardSummary: () => apiService.get('/api/charts/dashboard-summary'),
  getConversionRatesChart: () => apiService.get('/api/charts/conversion-rates')
} 