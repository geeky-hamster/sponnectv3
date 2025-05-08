# Sponnect Application Architecture

## Overview
Sponnect is a web-based platform that connects event organizers/influencers with potential sponsors. The application facilitates the creation, discovery, negotiation, and management of sponsorship opportunities.

## Core Modules

### 1. Authentication Module
- **Components**: Login, Registration, Profile Management
- **Data Flow**: 
  - Frontend (LoginView/RegisterView) → Backend (/api/login, /api/register) → Database (users table)
  - Profile updates: ProfileView → /api/profile → User model
- **Key Files**:
  - Frontend: `src/views/LoginView.vue`, `src/views/RegisterView.vue`, `src/views/ProfileView.vue`
  - Backend: Authentication routes in `app.py`, `User` model in `models.py`
  - State: `src/stores/auth.js`

### 2. User Management Module
- **Components**: Admin User Management, User Approval
- **Data Flow**:
  - Admin dashboard → Admin users view → User approval/rejection API → Database update
  - User list: AdminUsersView → /api/admin/users → User model
  - User approval: AdminUsersView → /api/admin/sponsors/:id/approve or /api/admin/influencers/:id/approve → User model
- **Key Files**:
  - Frontend: `src/views/admin/UsersView.vue`, `src/views/admin/DashboardView.vue`
  - Backend: Admin user routes in `app.py`, `User` model in `models.py`

### 3. Campaign Management Module
- **Components**: Campaign Creation, Editing, Listing, Detail View
- **Data Flow**:
  - Campaign creation: SponsorCampaignCreate → /api/sponsor/campaigns (POST) → Campaign model
  - Campaign listing: SponsorCampaigns → /api/sponsor/campaigns (GET) → Campaign model
  - Campaign detail: SponsorCampaignDetail → /api/sponsor/campaigns/:id (GET) → Campaign model
  - Campaign editing: SponsorCampaignEdit → /api/sponsor/campaigns/:id (PUT) → Campaign model
- **Key Files**:
  - Frontend: `src/views/sponsor/CampaignCreateView.vue`, `src/views/sponsor/CampaignsView.vue`, `src/views/sponsor/CampaignDetailView.vue`, `src/views/sponsor/CampaignEditView.vue`
  - Backend: Campaign routes in `app.py`, `Campaign` model in `models.py`

### 4. Ad Request/Negotiation Module
- **Components**: Ad Request Creation, Negotiation, Status Management
- **Data Flow**:
  - Ad request creation: 
    - Sponsor initiated: SponsorCreateRequest → /api/sponsor/campaigns/:id/ad_requests (POST) → AdRequest model
    - Influencer initiated: InfluencerCampaignBrowse → /api/influencer/campaigns/:id/apply (POST) → AdRequest model
  - Negotiation: 
    - Sponsor: SponsorAdRequestDetail → /api/sponsor/ad_requests/:id (PUT) → AdRequest model + NegotiationHistory model
    - Influencer: InfluencerAdRequestDetail → /api/influencer/ad_requests/:id (PATCH) → AdRequest model + NegotiationHistory model
  - History tracking: Ad request detail views → /api/ad_requests/:id/history → NegotiationHistory model
- **Key Files**:
  - Frontend: `src/views/sponsor/AdRequestsView.vue`, `src/views/sponsor/AdRequestDetailView.vue`, `src/views/influencer/AdRequestsView.vue`, `src/views/influencer/AdRequestDetailView.vue`
  - Backend: Ad request routes in `app.py`, `AdRequest` and `NegotiationHistory` models in `models.py`

### 5. Payment Module
- **Components**: Payment Processing, Receipt Generation
- **Data Flow**:
  - Payment creation: PaymentConfirmationView → /api/sponsor/ad_requests/:id/payments (POST) → Payment model
  - Payment retrieval: PaymentConfirmationView → /api/sponsor/ad_requests/:id/payments (GET) → Payment model
  - Receipt generation: PaymentConfirmationView → /api/sponsor/payments/:id/receipt (GET) → Payment model
- **Key Files**:
  - Frontend: `src/views/sponsor/PaymentConfirmationView.vue`
  - Backend: Payment routes in `app.py`, `Payment` model in `models.py`

### 6. Progress Update Module
- **Components**: Progress Tracking, Update Submission
- **Data Flow**:
  - Progress update submission: InfluencerAdRequestDetail → /api/influencer/ad_requests/:id/progress (POST) → ProgressUpdate model
  - Progress retrieval: 
    - Influencer: InfluencerAdRequestDetail → /api/influencer/ad_requests/:id/progress (GET) → ProgressUpdate model
    - Sponsor: SponsorAdRequestDetail → /api/sponsor/ad_requests/:id/progress (GET) → ProgressUpdate model
  - Update approval: SponsorAdRequestDetail → /api/sponsor/ad_requests/:id/progress/:updateId (PATCH) → ProgressUpdate model
- **Key Files**:
  - Frontend: Progress update components in request detail views
  - Backend: Progress update routes in `app.py`, `ProgressUpdate` model in `models.py`

### 7. Search Module
- **Components**: Influencer Search, Campaign Search
- **Data Flow**:
  - Influencer search: InfluencerSearchView → /api/search/influencers (GET) → User model (filtered)
  - Campaign search: InfluencerCampaignBrowse → /api/search/campaigns (GET) → Campaign model (filtered)
- **Key Files**:
  - Frontend: `src/views/search/InfluencerSearchView.vue`, `src/views/influencer/CampaignBrowseView.vue`
  - Backend: Search routes in `app.py`

### 8. Analytics Module
- **Components**: Dashboard Statistics, Charts
- **Data Flow**:
  - Dashboard summary: Admin/Sponsor/Influencer Dashboard → /api/charts/dashboard-summary → Aggregated data from models
  - User growth: AdminStatistics → /api/charts/user-growth → User model (aggregated)
  - Ad request status: AdminStatistics → /api/charts/ad-request-status → AdRequest model (aggregated)
  - Campaign activity: AdminStatistics → /api/charts/campaign-activity → Campaign model (aggregated)
  - Conversion rates: AdminStatistics → /api/charts/conversion-rates → Various models (aggregated)
- **Key Files**:
  - Frontend: Dashboard views, `src/views/admin/StatisticsView.vue`
  - Backend: Chart routes in `app.py`

## Data Flow Diagrams

### User Authentication Flow
```
User → LoginView.vue → [API: /api/login] → models.py (User) → Database
     ↓
     TokenGeneration
     ↓
FrontendStores (auth.js) → LocalStorage (token) → Protected Routes
```

### Campaign Creation Flow
```
Sponsor → SponsorCampaignCreate.vue → [API: /api/sponsor/campaigns] → models.py (Campaign) → Database
       ↓
       CampaignCreated
       ↓
SponsorCampaigns.vue (Campaign List) ← [API: /api/sponsor/campaigns] ← Database (Campaign table)
```

### Ad Request & Negotiation Flow
```
Sponsor → CreateRequestView.vue → [API: /api/sponsor/campaigns/:id/ad_requests] → models.py (AdRequest) → Database
       ↓
       RequestCreated
       ↓
Influencer → InfluencerAdRequests.vue ← [API: /api/influencer/ad_requests] ← Database (AdRequest table)
          ↓
          InfluencerAdRequestDetail.vue → [API: /api/influencer/ad_requests/:id] (PATCH - Negotiate) → Database
          ↓
          NegotiationUpdated
          ↓
Sponsor → SponsorAdRequestDetail.vue ← [API: /api/sponsor/ad_requests/:id] ← Database (AdRequest + NegotiationHistory)
       ↓
       SponsorAdRequestDetail.vue → [API: /api/sponsor/ad_requests/:id] (PUT - Respond) → Database
       ↓
       ... (negotiation continues) ...
       ↓
       Agreement Reached (Status: Accepted)
       ↓
Sponsor → PaymentConfirmationView.vue → [API: /api/sponsor/ad_requests/:id/payments] → models.py (Payment) → Database
       ↓
       PaymentComplete
       ↓
Influencer → Delivery Process → ProgressUpdate.vue → [API: /api/influencer/ad_requests/:id/progress] → Database (ProgressUpdate)
```

### Search Flow
```
Sponsor → InfluencerSearchView.vue → [API: /api/search/influencers] → Database (User filtered)
       ↓                                (with filters)
       InfluencerResults
       ↓
       CreateRequestView.vue (if sponsor wants to create request)

Influencer → CampaignBrowseView.vue → [API: /api/search/campaigns] → Database (Campaign filtered)
          ↓                               (with filters)
          CampaignResults
          ↓
          AdRequestCreation (if influencer wants to apply)
```

## Database Structure

The application uses SQLAlchemy ORM with the following main tables:
- `users`: Stores user account data for influencers, sponsors, and admins
- `campaigns`: Stores campaign information created by sponsors
- `ad_requests`: Tracks requests for collaboration and negotiation state
- `negotiation_history`: Records all negotiation activities for ad requests
- `payments`: Tracks payment information for completed deals
- `progress_updates`: Stores progress updates submitted by influencers

## Tech Stack

**Frontend:**
- Vue.js 3 with Vue Router for routing
- Pinia for state management
- Axios for API communication

**Backend:**
- Flask (Python) for API endpoints
- SQLAlchemy ORM for database interactions
- Celery for background tasks (reminders, exports)

**Database:**
- SQL database (likely PostgreSQL based on the models)

## Deployment Architecture

The application appears to use a standard web architecture:
- Vue.js frontend served as static assets
- Flask backend providing REST API endpoints
- Database server for data persistence
- Background workers (Celery) for async operations

## Security Considerations

- Authentication uses JWT tokens
- Password hashing for secure storage
- Role-based access control for different user types
- API routes secured based on user roles

## Future Enhancements Possibilities

- Enhanced analytics dashboard
- Integration with payment gateways
- Mobile application
- Real-time notifications
- AI-powered matching between sponsors and influencers 