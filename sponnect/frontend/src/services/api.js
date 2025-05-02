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
  completeCampaign: (id) => apiService.patch(`/api/sponsor/campaigns/${id}/complete`),
  
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
  getAdRequests: (params) => {
    console.log("Getting ad requests with params:", params);
    return apiService.get('/api/influencer/ad_requests', { params })
      .then(response => {
        console.log("Ad requests response:", response.data);
        
        // Validate response data
        if (!response.data || !Array.isArray(response.data)) {
          console.warn("Unexpected ad requests data format:", response.data);
          return { data: [] };
        }
        
        // Sanitize each ad request
        const sanitizedRequests = response.data.map(request => {
          // Ensure dates are valid
          if (request.created_at && !isValidDate(request.created_at)) {
            request.created_at = null;
          }
          if (request.updated_at && !isValidDate(request.updated_at)) {
            request.updated_at = null;
          }
          return request;
        });
        
        return { data: sanitizedRequests };
      })
      .catch(error => {
        console.error("Error fetching ad requests:", error);
        throw error;
      });
  },
  
  respondToAdRequest: (requestId, data) => {
    console.log(`Sending request to /api/influencer/ad_requests/${requestId} with data:`, data);
    
    // Validate data before sending
    const validData = { 
      action: data.action 
    };
    
    // Only include message if it's not empty
    if (data.message) {
      validData.message = data.message;
    }
    
    // Only include payment amount for negotiation
    if (data.action === 'negotiate' && data.payment_amount) {
      validData.payment_amount = parseFloat(data.payment_amount);
    }
    
    return apiService.patch(`/api/influencer/ad_requests/${requestId}`, validData)
      .then(response => {
        console.log("Response from respond to ad request:", response.data);
        return response;
      })
      .catch(error => {
        console.error("Error responding to ad request:", error);
        throw error;
      });
  },
  
  // Campaign applications
  getAvailableCampaigns: (params) => {
    console.log("Getting available campaigns with params:", params);
    return apiService.get('/api/search/campaigns', { params })
      .then(response => {
        console.log("Available campaigns response:", response.data);
        
        // Handle different response formats
        let campaigns = [];
        
        if (Array.isArray(response.data)) {
          campaigns = response.data;
        } else if (response.data && Array.isArray(response.data.campaigns)) {
          campaigns = response.data.campaigns;
        } else if (response.data && typeof response.data === 'object') {
          // Handle case where data might be a single campaign object
          campaigns = [response.data];
        } else {
          console.error("Unexpected campaigns data format:", response.data);
          campaigns = [];
        }
        
        // Validate and sanitize each campaign
        const sanitizedCampaigns = campaigns.map(campaign => {
          // Create a new object with default values
          return {
            id: campaign.id || 0,
            name: campaign.name || "Unnamed Campaign",
            description: campaign.description || "",
            budget: campaign.budget || 0,
            start_date: isValidDate(campaign.start_date) ? campaign.start_date : null,
            end_date: isValidDate(campaign.end_date) ? campaign.end_date : null,
            ...campaign
          };
        });
        
        return { data: sanitizedCampaigns };
      })
      .catch(error => {
        console.error("Error fetching available campaigns:", error);
        throw error;
      });
  },
  
  applyCampaign: (data) => {
    const campaignId = data.campaign_id;
    console.log(`Applying for campaign ${campaignId} with data:`, data);
    return apiService.post(`/api/influencer/campaigns/${campaignId}/apply`, data)
      .then(response => {
        console.log("Campaign application response:", response.data);
        return response;
      })
      .catch(error => {
        console.error("Error applying for campaign:", error);
        throw error;
      });
  },
  
  // Progress Updates
  getProgressUpdates: (adRequestId) => apiService.get(`/api/influencer/ad_requests/${adRequestId}/progress`),
  addProgressUpdate: (adRequestId, data) => apiService.post(`/api/influencer/ad_requests/${adRequestId}/progress`, data),
  
  // Payments
  getPayments: (adRequestId) => apiService.get(`/api/influencer/ad_requests/${adRequestId}/payments`),
  
  // Negotiations
  getNegotiations: () => apiService.get('/api/influencer/negotiations'),
  getNegotiationHistory: (adRequestId) => apiService.get(`/api/ad_requests/${adRequestId}/history`)
}

// Helper function to validate dates
function isValidDate(dateString) {
  if (!dateString) return false;
  
  // First check with standard Date parsing
  const date = new Date(dateString);
  if (!isNaN(date.getTime())) {
    return true;
  }
  
  // Try additional date formats if standard parsing fails
  if (typeof dateString === 'string') {
    // Check if we have a timestamp with time component (DD-MM-YYYY HH:MM:SS)
    if (dateString.includes(' ')) {
      const [datePart, timePart] = dateString.split(' ');
      
      // Try DD-MM-YYYY HH:MM:SS format
      if (datePart.includes('-') && timePart.includes(':')) {
        const [day, month, year] = datePart.split('-').map(part => parseInt(part, 10));
        
        if (!isNaN(day) && !isNaN(month) && !isNaN(year)) {
          const [hours, minutes, seconds] = timePart.split(':').map(part => parseInt(part, 10));
          
          // Create date with time components
          const fullDate = new Date(year, month - 1, day, 
                         !isNaN(hours) ? hours : 0, 
                         !isNaN(minutes) ? minutes : 0, 
                         !isNaN(seconds) ? seconds : 0);
                         
          if (!isNaN(fullDate.getTime())) {
            return true;
          }
        }
      }
    }
    
    // Try DD-MM-YYYY format
    const dashParts = dateString.split('-');
    if (dashParts.length === 3) {
      const day = parseInt(dashParts[0], 10);
      const month = parseInt(dashParts[1], 10) - 1;
      const year = parseInt(dashParts[2], 10);
      const parsedDate = new Date(year, month, day);
      
      if (!isNaN(parsedDate.getTime())) {
        return true;
      }
    }
    
    // Try YYYY-MM-DD format
    if (dashParts.length === 3) {
      const year = parseInt(dashParts[0], 10);
      const month = parseInt(dashParts[1], 10) - 1;
      const day = parseInt(dashParts[2], 10);
      
      if (year > 1000) {
        const parsedDate = new Date(year, month, day);
        if (!isNaN(parsedDate.getTime())) {
          return true;
        }
      }
    }
  }
  
  return false;
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
  searchCampaigns: (params) => {
    console.log('Executing search campaigns with params:', params);
    
    // Validate parameters before sending to API
    const cleanParams = {};
    
    // Only add parameters with actual values
    if (params) {
      if (params.query && typeof params.query === 'string' && params.query.trim()) {
        cleanParams.query = params.query.trim();
      }
      
      if (params.category && typeof params.category === 'string') {
        cleanParams.category = params.category;
      }
      
      // Handle numeric parameters
      if (params.min_budget && !isNaN(parseFloat(params.min_budget))) {
        cleanParams.min_budget = parseFloat(params.min_budget);
      }
      
      if (params.max_budget && !isNaN(parseFloat(params.max_budget))) {
        cleanParams.max_budget = parseFloat(params.max_budget);
      }
      
      // Sorting parameters
      if (params.sort_by) {
        cleanParams.sort_by = params.sort_by;
      }
      
      if (params.sort_order) {
        cleanParams.sort_order = params.sort_order;
      }
      
      // Pagination parameters
      if (params.page && !isNaN(parseInt(params.page))) {
        cleanParams.page = parseInt(params.page);
      }
      
      if (params.limit && !isNaN(parseInt(params.limit))) {
        cleanParams.limit = parseInt(params.limit);
      }
    }
    
    return apiService.get('/api/search/campaigns', { params: cleanParams })
      .then(response => {
        console.log('Search campaigns API response:', response);
        
        // Validate and normalize the response
        if (!response.data) {
          console.warn('Empty data received from search campaigns API');
          return { data: [] };
        }
        
        // Process the response to handle different formats
        let campaigns = [];
        
        if (Array.isArray(response.data)) {
          campaigns = response.data;
        } else if (response.data.campaigns && Array.isArray(response.data.campaigns)) {
          campaigns = response.data.campaigns;
          
          // If pagination info exists, preserve it
          if (response.data.pagination) {
            return {
              data: {
                campaigns: campaigns,
                pagination: response.data.pagination
              }
            };
          }
        } else if (typeof response.data === 'object' && !Array.isArray(response.data) && response.data.id) {
          // Single campaign object
          campaigns = [response.data];
        }
        
        return { data: campaigns };
      })
      .catch(error => {
        console.error('Error in searchCampaigns:', error);
        throw error;
      });
  }
}

// Admin Services
export const adminService = {
  // User management
  getUsers: (params) => apiService.get('/api/admin/users', { params }),
  flagUser: (userId) => apiService.patch(`/api/admin/users/${userId}/flag`),
  unflagUser: (userId, cascade = true) => apiService.patch(`/api/admin/users/${userId}/unflag?cascade=${cascade}`),
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
  getCampaigns: (params) => {
    console.log('Executing admin getCampaigns with params:', params);
    
    // Validate parameters before sending to API
    const cleanParams = {};
    
    // Only add parameters with actual values
    if (params) {
      // IMPORTANT: Admin API uses 'name' for search term instead of 'search'
      if (params.search && typeof params.search === 'string' && params.search.trim()) {
        cleanParams.name = params.search.trim();
      }
      
      if (params.status && typeof params.status === 'string') {
        cleanParams.status = params.status;
      }
      
      if (params.sponsor_id && !isNaN(parseInt(params.sponsor_id))) {
        cleanParams.sponsor_id = parseInt(params.sponsor_id);
      } else if (params.sponsor_id && typeof params.sponsor_id === 'string' && params.sponsor_id.trim()) {
        cleanParams.sponsor_id = params.sponsor_id.trim();
      }
      
      // Admin API supports flagged filter
      if (params.flagged !== undefined) {
        cleanParams.flagged = params.flagged === true || params.flagged === 'true';
      }
      
      if (params.date_range && typeof params.date_range === 'string') {
        cleanParams.date_range = params.date_range;
      }
      
      // Handle numeric parameters
      if (params.budget_min && !isNaN(parseFloat(params.budget_min))) {
        cleanParams.budget_min = parseFloat(params.budget_min);
      }
      
      if (params.budget_max && !isNaN(parseFloat(params.budget_max))) {
        cleanParams.budget_max = parseFloat(params.budget_max);
      }
      
      // Pagination parameters
      if (params.page && !isNaN(parseInt(params.page))) {
        cleanParams.page = parseInt(params.page);
      }
      
      if (params.per_page && !isNaN(parseInt(params.per_page))) {
        cleanParams.per_page = parseInt(params.per_page);
      }
    }
    
    console.log('Final admin campaigns params:', cleanParams);
    
    return apiService.get('/api/admin/campaigns', { params: cleanParams })
      .then(response => {
        console.log('Admin campaigns API response:', response);
        
        // Validate and normalize the response
        if (!response.data) {
          console.warn('Empty data received from admin campaigns API');
          return { data: { campaigns: [], pagination: { total_items: 0, total_pages: 0, page: 1, per_page: 10 } } };
        }
        
        // Process the response to handle different formats
        let campaigns = [];
        let pagination = null;
        
        if (Array.isArray(response.data)) {
          campaigns = response.data;
        } else if (response.data.campaigns && Array.isArray(response.data.campaigns)) {
          campaigns = response.data.campaigns;
          
          // If pagination info exists, preserve it
          if (response.data.pagination) {
            pagination = response.data.pagination;
          }
        } else if (typeof response.data === 'object' && !Array.isArray(response.data) && response.data.id) {
          // Single campaign object
          campaigns = [response.data];
        }
        
        // Return data with appropriate structure
        if (pagination) {
          return { data: { campaigns, pagination } };
        } else {
          return { data: { campaigns } };
        }
      })
      .catch(error => {
        console.error('Error in admin getCampaigns:', error);
        throw error;
      });
  },
  approveCampaign: (campaignId) => apiService.patch(`/api/admin/campaigns/${campaignId}/approve`),
  rejectCampaign: (campaignId) => apiService.patch(`/api/admin/campaigns/${campaignId}/reject`),
  pauseCampaign: (campaignId) => apiService.patch(`/api/admin/campaigns/${campaignId}/pause`),
  activateCampaign: (campaignId) => apiService.patch(`/api/admin/campaigns/${campaignId}/activate`),
  featureCampaign: (campaignId) => apiService.patch(`/api/admin/campaigns/${campaignId}/feature`),
  unfeatureCampaign: (campaignId) => apiService.patch(`/api/admin/campaigns/${campaignId}/unfeature`),
  flagCampaign: (campaignId) => apiService.patch(`/api/admin/campaigns/${campaignId}/flag`),
  unflagCampaign: (campaignId) => apiService.patch(`/api/admin/campaigns/${campaignId}/unflag`),
  
  // Ad request management
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

// Negotiation History
export const negotiationService = {
  getHistory: (adRequestId) => apiService.get(`/api/ad_requests/${adRequestId}/history`),
  getCampaignNegotiationSummary: (campaignId) => apiService.get(`/api/sponsor/campaigns/${campaignId}/negotiation_summary`)
} 