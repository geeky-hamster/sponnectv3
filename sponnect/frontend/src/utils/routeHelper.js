/**
 * Route helper utility for centralizing route definitions
 * This helps prevent broken links between components
 */

// Define application routes by role
const routes = {
  // Public routes
  public: {
    home: '/',
    login: '/login',
    register: '/register',
  },
  
  // Sponsor routes
  sponsor: {
    dashboard: '/sponsor/dashboard',
    campaigns: '/sponsor/campaigns',
    campaignCreate: '/sponsor/campaigns/create',
    campaignDetail: (id) => `/sponsor/campaigns/${id}`,
    campaignEdit: (id) => `/sponsor/campaigns/${id}/edit`,
    createRequest: (id) => `/sponsor/campaigns/${id}/create-request`,
    adRequests: '/sponsor/ad-requests',
    adRequestDetail: (id) => `/sponsor/ad-requests/${id}`,
  },
  
  // Influencer routes
  influencer: {
    dashboard: '/influencer/dashboard',
    adRequests: '/influencer/ad-requests',
    adRequestDetail: (id) => `/influencer/ad-requests/${id}`,
    campaignBrowse: '/influencer/campaigns/browse',
    campaignDetail: (id) => `/campaigns/${id}`,
  },
  
  // Admin routes
  admin: {
    dashboard: '/admin/dashboard',
    users: '/admin/users',
    campaigns: '/admin/campaigns',
    statistics: '/admin/statistics',
    reports: '/admin/reports',
  },
  
  // Shared routes
  shared: {
    profile: '/profile',
    campaignDetail: (id) => `/campaigns/${id}`,
  }
};

/**
 * Get route path by role and route name
 * @param {string} role - User role (sponsor, influencer, admin)
 * @param {string} routeName - Name of the route
 * @param {any} params - Parameters for dynamic routes
 * @returns {string} Route path
 */
export const getRoute = (role, routeName, params = null) => {
  // Get route definition from role section
  let route = routes[role]?.[routeName];
  
  // If not found, check shared routes
  if (!route) {
    route = routes.shared[routeName];
  }
  
  // If still not found, check public routes
  if (!route) {
    route = routes.public[routeName];
  }
  
  // If function, call with params
  if (typeof route === 'function' && params !== null) {
    return route(params);
  }
  
  return route || '/';
};

/**
 * Get dashboard route based on user role
 * @param {string} role - User role
 * @returns {string} Dashboard route
 */
export const getDashboardRoute = (role) => {
  switch (role) {
    case 'sponsor':
      return routes.sponsor.dashboard;
    case 'influencer':
      return routes.influencer.dashboard;
    case 'admin':
      return routes.admin.dashboard;
    default:
      return routes.public.home;
  }
};

export default routes; 