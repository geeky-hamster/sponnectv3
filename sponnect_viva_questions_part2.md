# Sponnect Application - Viva Questions and Answers (Part 2)

## API & Data Flow

### 41. Explain the authentication flow in Sponnect from login to accessing protected routes.
**Answer:** The authentication flow works as follows:
1. User submits credentials (username/password) to `/api/login`
2. Backend validates credentials against the User model
3. If valid, a JWT token is generated with user ID and role as claims
4. Token is returned to frontend and stored in localStorage
5. Axios interceptor adds token to Authorization header of subsequent requests
6. Protected backend routes use decorators like `@jwt_required()` to verify tokens
7. Role-specific decorators (`@admin_required`, etc.) check user permissions
8. If token is invalid or expired, a 401 error is returned
9. If role doesn't match required role, a 403 error is returned

### 42. How does Sponnect implement role-based access control (RBAC)?
**Answer:** Sponnect implements RBAC through:
1. User model with a 'role' field (admin, sponsor, influencer)
2. Custom decorators in Flask that check JWT claims:
   ```python
   def role_required(required_role):
       def decorator(fn):
           @wraps(fn)
           def wrapper(*args, **kwargs):
               verify_jwt_in_request()
               claims = get_jwt()
               user_role = claims.get('role')
               if user_role != required_role and user_role != 'admin':
                   return jsonify(message=f"{required_role.capitalize()} access required"), 403
               return fn(*args, **kwargs)
           return wrapper
       return decorator
   ```
3. These decorators (`@admin_required`, `@sponsor_required`, `@influencer_required`) applied to API endpoints
4. Frontend router guards that check user role before allowing access to certain views

### 43. Describe the campaign creation data flow from frontend to database.
**Answer:** The campaign creation flow is:
1. Sponsor fills form in CampaignCreateView.vue with campaign details
2. Form data validated in frontend (required fields, numeric budget, valid dates)
3. Axios POST request to `/api/sponsor/campaigns` with validated data
4. Backend route handler validates JWT and confirms sponsor role
5. Request data parsed and validated
6. New Campaign object created with sponsor_id from JWT
7. Campaign object saved to database
8. Response with created campaign details returned to frontend
9. Frontend redirects to campaign detail view

### 44. How does Sponnect handle data serialization between backend and frontend?
**Answer:** Sponnect handles data serialization through:
1. Backend serializer functions (e.g., `serialize_user_profile()`, `serialize_campaign_detail()`)
2. These functions convert ORM objects to dictionaries with selected fields
3. JSON serialization via Flask's `jsonify()` function for API responses
4. Date formatting functions for consistent date representation
5. Currency formatting for monetary values
6. Frontend automatically deserializes JSON responses to JavaScript objects
7. Special handling for nested objects and relationships

### 45. Explain the negotiation data flow when a counter-offer is made.
**Answer:** When a counter-offer is made:
1. User (sponsor/influencer) submits updated terms via frontend form
2. Request sent to `/api/sponsor/ad_requests/:id` (PUT) or `/api/influencer/ad_requests/:id` (PATCH)
3. Backend validates user permissions and request data
4. AdRequest record updated with new terms (payment_amount, requirements, message)
5. AdRequest status set to "Negotiating"
6. last_offer_by field updated to indicate whose turn is next
7. New NegotiationHistory record created to track this counter-offer
8. Other party notified of the counter-offer
9. Response sent back to frontend with updated ad request
10. UI updates to show current negotiation state

### 46. What API endpoints are available for administrators to approve users?
**Answer:** Admin user approval endpoints include:
1. `/api/admin/sponsors/:id/approve` (PATCH) - Approve sponsor accounts
2. `/api/admin/influencers/:id/approve` (PATCH) - Approve influencer accounts
3. `/api/admin/sponsors/:id/reject` (PATCH) - Reject sponsor accounts
4. `/api/admin/influencers/:id/reject` (PATCH) - Reject influencer accounts
These endpoints update the sponsor_approved or influencer_approved field and trigger notification emails.

### 47. How does Sponnect handle pagination in API responses?
**Answer:** Sponnect handles pagination through:
1. Query parameters for page and per_page (e.g., ?page=2&per_page=10)
2. SQLAlchemy's paginate() method to limit database results
3. Helper function serialize_pagination() to format pagination metadata
4. Response format including both data array and pagination metadata:
   ```json
   {
     "items": [...],
     "pagination": {
       "page": 2,
       "per_page": 10,
       "total_pages": 5,
       "total_items": 48,
       "has_prev": true,
       "has_next": true
     }
   }
   ```
5. Frontend components for rendering pagination controls

### 48. What happens in the data flow when a sponsor makes a payment?
**Answer:** When a sponsor makes a payment:
1. Sponsor confirms payment in PaymentConfirmationView.vue
2. POST request to `/api/sponsor/ad_requests/:id/payments`
3. Backend validates ad request status (must be "Accepted")
4. Payment amount retrieved from ad request
5. Platform fee calculated (1% of payment amount)
6. Influencer amount calculated (payment minus fee)
7. New Payment record created and saved to database
8. Ad request status may be updated
9. Receipt generation triggered
10. Influencer notified of payment
11. Response with payment details returned to frontend

### 49. Explain the data flow for generating and downloading export files.
**Answer:** The export generation flow works as:
1. Admin requests export with filters via frontend
2. POST request to `/api/admin/export/users`
3. Backend dispatches task to Celery worker with task ID returned
4. Frontend polls `/api/admin/tasks/:id` for task status
5. Celery worker executes query with filters in background
6. Results formatted as CSV or JSON file
7. File saved to export directory with timestamp in name
8. Admin notified when export is complete
9. Download URL provided for file retrieval
10. GET request to `/api/admin/exports/:filename` downloads the file

### 50. How does the influencer discover available campaigns?
**Answer:** The campaign discovery flow:
1. Influencer accesses CampaignBrowseView.vue
2. Applies filters (category, budget range, etc.)
3. GET request to `/api/search/campaigns` with filter parameters
4. Backend builds query for public, active campaigns
5. Applies filters to database query
6. Joins campaigns with sponsor data
7. Returns paginated results with campaign details
8. Frontend renders filterable campaign list
9. Influencer can view details and apply to campaigns

### 51. What API endpoints handle the ad request approval process?
**Answer:** The key endpoints are:
1. `/api/sponsor/applications/:id/accept` (PATCH) - Sponsor accepts influencer application
2. `/api/sponsor/applications/:id/reject` (PATCH) - Sponsor rejects influencer application
3. `/api/influencer/ad_requests/:id` (PATCH) - Influencer accepts/rejects/counters sponsor request
These endpoints update the AdRequest status and create appropriate NegotiationHistory records.

### 52. How does Sponnect implement search functionality for influencers?
**Answer:** Influencer search works through:
1. Frontend form in InfluencerSearchView.vue with filter options
2. GET request to `/api/search/influencers` with parameters (category, niche, reach)
3. Backend builds dynamic query on User model with role='influencer'
4. Filters applied based on search parameters:
   ```python
   if category:
       query = query.filter(User.category == category)
   if min_reach:
       query = query.filter(User.reach >= min_reach)
   ```
5. Only approved and active influencers included
6. Results returned with pagination
7. Frontend displays filterable influencer list

### 53. What happens in the data flow when an influencer submits a progress update?
**Answer:** When an influencer submits progress:
1. Influencer creates update in AdRequestDetailView.vue
2. Fills form with content, media links, and metrics
3. POST request to `/api/influencer/ad_requests/:id/progress`
4. Backend validates the ad request exists and belongs to influencer
5. New ProgressUpdate record created with status='Pending'
6. Record saved to database
7. Sponsor notified of new progress update
8. Response sent to frontend
9. UI updated to show pending approval

### 54. How does Sponnect handle error responses in API endpoints?
**Answer:** Sponnect handles API errors through:
1. HTTP status codes (400, 404, 403, 500, etc.)
2. Structured error response format:
   ```json
   {
     "error": "Error message",
     "details": "Additional error details"
   }
   ```
3. Global error handler for unhandled exceptions
4. Try-catch blocks for specific error handling
5. Custom error messages for common conditions
6. Frontend Axios interceptors catch and display errors

### 55. What caching mechanisms are used for API responses?
**Answer:** API caching mechanisms include:
1. Redis-based caching via Flask-Caching
2. Decorator-based cache configuration:
   ```python
   @cache.cached(timeout=180)  # Cache for 3 minutes
   @cache.cached(timeout=300, query_string=True)  # Vary by query parameters
   ```
3. Different cache timeouts based on data volatility
4. Cache invalidation when underlying data changes
5. Query string parameters included in cache keys when needed

### 56. How does Sponnect handle file uploads and storage?
**Answer:** While not explicitly detailed, Sponnect likely handles file uploads through:
1. Multipart form data for file uploads
2. Backend validation for file types and sizes
3. Storage in a designated directory or object storage
4. Database storage of file paths/URLs
5. Integration with media serving for retrieval

### 57. What data flows are involved in the admin dashboard statistics?
**Answer:** Admin dashboard statistics involve:
1. Frontend request to `/api/charts/dashboard-summary`
2. Backend performs multiple aggregation queries:
   - User statistics (counts by role, approval status)
   - Campaign statistics (counts by status, average budget)
   - Ad request statistics (counts by status, conversion rates)
   - Payment statistics (total amounts, fees)
   - Recent activity (last 24 hours metrics)
3. Results cached in Redis for performance
4. Combined statistics returned as JSON
5. Frontend renders various charts and metrics displays

### 58. How does Sponnect handle data validation in API requests?
**Answer:** Data validation happens at multiple levels:
1. Frontend form validation with error messages
2. Backend request parsing and validation
3. Model-level validation with `@validates` decorators
4. Database constraints (NOT NULL, UNIQUE, etc.)
5. Type checking and conversion
6. Custom validation logic for business rules

### 59. What API endpoints are involved in the notification system?
**Answer:** While not fully detailed, notifications likely involve:
1. Endpoints that trigger notifications (user approval, payment processing)
2. Background tasks for sending email notifications
3. Database queries to identify recipients
4. Email templates for formatting notification content
5. SMTP integration for delivery

### 60. How are API endpoints organized in the Sponnect backend?
**Answer:** Endpoints are organized by:
1. Role-based groups (`/api/admin/`, `/api/sponsor/`, `/api/influencer/`)
2. Resource-based paths (`/api/campaigns`, `/api/ad_requests`)
3. Action-specific endpoints (`/api/sponsor/campaigns/:id/complete`)
4. Chart/analytics endpoints (`/api/charts/dashboard-summary`)
5. Authentication endpoints (`/api/login`, `/api/register`)
This organization provides clear separation of concerns and role-based access control.

## Frontend Implementation

### 61. How is the Vue.js component structure organized in Sponnect?
**Answer:** The Vue.js components are organized as:
1. Views: Page-level components in `/views` directory, further organized by role:
   - `/views/admin/`
   - `/views/sponsor/`
   - `/views/influencer/`
   - `/views/search/`
2. Common components: Reusable UI elements in `/components`
3. Layout components: Header, footer, navigation
4. Form components: Input fields, buttons, validation
5. Data display components: Tables, charts, cards

### 62. What frontend routing approach does Sponnect use?
**Answer:** Sponnect uses Vue Router for frontend routing with:
1. Route definitions in `/router/index.js`
2. Nested routes for hierarchical navigation
3. Route guards for authentication and role-based access
4. Lazy loading for performance optimization
5. Parameter-based routes for detail views (e.g., `/sponsor/campaigns/:id`)

### 63. How does Sponnect handle form validation in the frontend?
**Answer:** Form validation is implemented through:
1. Reactive form state with Vue's reactivity system
2. Validation rules in component setup functions
3. Error messages stored in reactive objects
4. Form submission prevented if validation fails
5. Visual indicators for validation status
6. Real-time validation as users type

### 64. Explain the state management approach in Sponnect's frontend.
**Answer:** Sponnect uses Pinia for state management with:
1. Separate stores for different domains (auth, campaigns, etc.)
2. State, actions, and getters organized by functionality
3. Composition API for defining stores
4. Centralized data management
5. Reactive updates across components
6. DevTools integration for debugging

### 65. How does Sponnect handle API communication in the frontend?
**Answer:** API communication is managed through:
1. Axios for HTTP requests
2. Service modules in `/services` directory
3. Interceptors for token handling and error processing
4. Base API configuration with common settings
5. Service functions for specific API endpoints
6. Response transformation and error handling

### 66. What authentication mechanisms are implemented in the frontend?
**Answer:** Frontend authentication includes:
1. Login form for credential submission
2. JWT token storage in localStorage
3. Axios interceptor for adding Authorization header
4. Router guards to protect private routes
5. Auth store for centralized authentication state
6. Automatic redirect to login for unauthenticated requests

### 67. How does the sponsor view and manage their campaigns in the frontend?
**Answer:** Sponsors manage campaigns through:
1. CampaignsView.vue listing all sponsor campaigns
2. CampaignCreateView.vue for creating new campaigns
3. CampaignEditView.vue for updating campaigns
4. CampaignDetailView.vue for viewing details and metrics
5. Filter controls for sorting and filtering campaigns
6. Action buttons for campaign management (complete, pause)

### 68. How are ad requests visualized in the influencer interface?
**Answer:** Influencers view ad requests through:
1. AdRequestsView.vue showing all received requests
2. AdRequestDetailView.vue for detailed view
3. Status indicators using color-coding and badges
4. Negotiation history timeline
5. Action buttons for responding (accept, reject, counter)
6. Progress submission forms for accepted requests

### 69. What charting libraries are used in the admin dashboard?
**Answer:** While not explicitly specified, the application likely uses Chart.js or similar libraries with:
1. Line charts for time-series data (user growth)
2. Pie/donut charts for distribution (status breakdown)
3. Bar charts for comparisons (campaign performance)
4. Area charts for cumulative data
5. Vue component wrappers for chart integration

### 70. How does Sponnect handle responsive design in the frontend?
**Answer:** Responsive design is implemented through:
1. Bootstrap 5 grid system for layout
2. Media queries for breakpoint-specific styling
3. Responsive component design
4. Mobile-first approach
5. Conditional rendering for different screen sizes
6. Flexible UI components that adapt to container size

### 71. What UI framework does Sponnect use and why?
**Answer:** Sponnect uses Bootstrap 5 as its UI framework because:
1. It provides a comprehensive set of pre-styled components
2. It has a robust grid system for responsive layouts
3. It's widely adopted with good community support
4. It integrates well with Vue.js
5. It offers utility classes for rapid development

### 72. How does the payment confirmation interface work?
**Answer:** The payment confirmation interface:
1. Shows ad request details and terms
2. Displays the agreed payment amount
3. Calculates and shows platform fee
4. Provides payment method selection
5. Includes terms acceptance checkbox
6. Features a prominent "Confirm Payment" button
7. Shows loading state during processing
8. Redirects to receipt view upon completion

### 73. How does Sponnect implement the negotiation interface?
**Answer:** The negotiation interface includes:
1. Display of current terms (payment, requirements)
2. Negotiation history timeline showing all offers
3. Form for counter-offer with editable fields
4. Action buttons (Accept, Reject, Counter)
5. Status indicators to show negotiation stage
6. Messages between parties
7. Clear labeling of whose turn it is

### 74. What data visualization components are used in the sponsor dashboard?
**Answer:** Sponsor dashboard visualizations likely include:
1. Campaign performance metrics cards
2. Ad request status distribution chart
3. Conversion rate indicators
4. Payment history table
5. Timeline of active campaigns
6. Application response rate metrics

### 75. How does the frontend handle loading states and transitions?
**Answer:** Loading states are handled through:
1. Reactive loading flags in component setup
2. Loading spinners or skeleton screens
3. Disabled buttons during processing
4. Error states for failed operations
5. Success notifications for completed actions
6. Transition animations between states

### 76. What error handling strategies are used in the frontend?
**Answer:** Frontend error handling includes:
1. Global error handling for Axios requests
2. Try-catch blocks in critical operations
3. User-friendly error messages
4. Form validation error displays
5. Error boundaries for component failures
6. Fallback UI for error states

### 77. How does Sponnect implement the campaign discovery interface for influencers?
**Answer:** The campaign discovery interface features:
1. Filterable list of available campaigns
2. Search functionality by keywords
3. Category and budget range filters
4. Campaign cards with key information
5. Detail modal for additional information
6. Apply button for interested influencers
7. Sorting options (newest, highest budget, etc.)

### 78. What frontend caching mechanisms might be used in Sponnect?
**Answer:** Frontend caching likely includes:
1. Vue's reactive caching for component data
2. Browser localStorage for user settings
3. Session storage for temporary data
4. In-memory caching for repeated calculations
5. Service worker caching for offline capability

### 79. How does the frontend handle date and currency formatting?
**Answer:** Formatting is handled through:
1. Utility functions in `/utils` directory
2. Consistent date format helpers
3. Currency formatting with proper locale and symbols (₹)
4. ISO date strings for data exchange
5. Human-readable formats for display
6. Timezone conversion (UTC to IST)

### 80. What features would the admin user management interface include?
**Answer:** The admin user management interface includes:
1. Filterable list of all users
2. Role and status filters
3. Search functionality
4. User detail view
5. Approval buttons for pending users
6. Flag/unflag toggles for problematic accounts
7. Activate/deactivate controls
8. User statistics and metrics

## Backend Implementation 