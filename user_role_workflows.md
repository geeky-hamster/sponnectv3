# Sponnect Role-Based Workflows

This document details the workflows and data flows for each user role within the Sponnect application (Admin, Sponsor, and Influencer).

## 1. Admin User Workflows

### 1.1 User Management Workflow

**Process Flow:**
1. Admin logs in → Authentication token generated → Admin Dashboard loads
2. Admin navigates to User Management section
3. Admin views list of pending approvals for sponsors and influencers
4. Admin reviews user details and makes approval/rejection decision
5. Upon approval/rejection, user status is updated in database
6. Email notification sent to user regarding approval status

**Data Flow:**
```
Admin → AdminUsersView.vue → API Request (/api/admin/users) → app.py (route handler) → models.py (User query) → Database (users table)
     ↓
     User data returned to frontend
     ↓
Admin → User review → Approval/Rejection action → API Request (/api/admin/sponsors/:id/approve) → app.py → User model update → Database update
     ↓
     Response returned → UI updated → Email notification triggered → mailer.py → SMTP Server → User inbox
```

### 1.2 Campaign Moderation Workflow

**Process Flow:**
1. Admin reviews active campaigns from dashboard
2. Admin can flag inappropriate campaigns
3. Admin can review flagged campaigns and take action (e.g., hide from public view)
4. Admin can monitor campaign metrics and performance

**Data Flow:**
```
Admin → AdminCampaignsView.vue → API Request (/api/admin/campaigns) → app.py → Campaign queries → Database
     ↓
     Campaign list returned to frontend
     ↓
Admin → Campaign selection → API Request (/api/admin/campaigns/:id) → Campaign detail returned
     ↓
Admin → Flag action → API Request (/api/admin/campaigns/:id/flag) → app.py → Campaign model update → Database update
     ↓
     Response returned → UI updated → Campaign flagged
```

### 1.3 Analytics & Reporting Workflow

**Process Flow:**
1. Admin accesses analytics dashboard
2. System generates data visualizations for key metrics:
   - User growth
   - Campaign activity
   - Ad request status distribution
   - Conversion rates
   - Revenue trends
3. Admin can export data for further analysis

**Data Flow:**
```
Admin → AdminStatisticsView.vue → Multiple API Requests:
                                 → /api/charts/user-growth
                                 → /api/charts/campaign-activity
                                 → /api/charts/ad-request-status
                                 → /api/charts/conversion-rates
                                 → app.py → Aggregation queries across models → Database
     ↓
     Aggregated data returned to frontend
     ↓
     Chart components render visualizations
     ↓
Admin → Export action → API Request (/api/admin/export/users) → app.py → task.py → Celery worker → Background processing
     ↓
     Task ID returned → Polling for completion → File download
```

### 1.4 Ad Request Moderation Workflow

**Process Flow:**
1. Admin reviews active ad requests
2. Admin can flag inappropriate requests
3. Admin monitors negotiation process
4. Admin reviews payment transactions

**Data Flow:**
```
Admin → AdminView.vue → API Request (/api/admin/ad_requests) → app.py → AdRequest queries → Database
     ↓
     Ad request list returned to frontend
     ↓
Admin → Ad request selection → API Request (/api/admin/ad_requests/:id) → AdRequest detail returned
     ↓
Admin → Flag action → API Request (/api/admin/ad_requests/:id/flag) → app.py → AdRequest model update → Database update
     ↓
     Response returned → UI updated → Ad request flagged
```

## 2. Sponsor User Workflows

### 2.1 Registration & Profile Setup Workflow

**Process Flow:**
1. Sponsor registers an account → Confirmation email sent
2. Sponsor completes profile information (company, industry, etc.)
3. Sponsor awaits admin approval
4. Upon approval, sponsor gains access to full functionality

**Data Flow:**
```
Sponsor → RegisterView.vue → API Request (/api/register with role=sponsor) → app.py → User model creation → Database (users table)
       ↓
       Authentication token returned → LocalStorage
       ↓
Sponsor → ProfileView.vue → Form completion → API Request (/api/profile) → app.py → User model update → Database update
       ↓
       Response returned → Profile saved → Awaiting approval status
       ↓
Admin approval (see Admin workflow) → Database update → Email notification → Sponsor receives approval
```

### 2.2 Campaign Creation & Management Workflow

**Process Flow:**
1. Sponsor creates a new campaign with details:
   - Campaign name
   - Description
   - Start/end dates
   - Budget
   - Category
   - Goals
   - Visibility (public/private)
2. Sponsor can edit campaign details
3. Sponsor can view campaign status and metrics
4. Sponsor can pause or complete campaigns

**Data Flow:**
```
Sponsor → SponsorCampaignCreate.vue → Form completion → API Request (/api/sponsor/campaigns) → app.py → Campaign model creation → Database (campaigns table)
       ↓
       Response returned → Redirect to campaign list
       ↓
Sponsor → SponsorCampaigns.vue → API Request (/api/sponsor/campaigns) → Campaign list returned
       ↓
Sponsor → Campaign selection → SponsorCampaignDetail.vue → API Request (/api/sponsor/campaigns/:id) → Campaign detail returned
       ↓
Sponsor → Edit action → SponsorCampaignEdit.vue → Form update → API Request (/api/sponsor/campaigns/:id PUT) → Campaign model update → Database update
       ↓
Sponsor → Status update (e.g., pause) → API Request (/api/sponsor/campaigns/:id/complete) → Campaign model update → Database update
```

### 2.3 Influencer Discovery & Ad Request Workflow

**Process Flow:**
1. Sponsor searches for influencers using filters (category, reach, niche)
2. Sponsor reviews influencer profiles
3. Sponsor selects an influencer and initiates an ad request:
   - Selects campaign
   - Defines requirements
   - Sets payment offer
   - Adds message
4. Ad request is sent to influencer

**Data Flow:**
```
Sponsor → InfluencerSearchView.vue → API Request (/api/search/influencers with filters) → app.py → User model query (influencers) → Database
       ↓
       Filtered influencer list returned to frontend
       ↓
Sponsor → Influencer selection → CreateRequestView.vue → Form completion → API Request (/api/sponsor/campaigns/:id/ad_requests) → app.py → AdRequest model creation → Database (ad_requests table)
       ↓
       Response returned → Redirect to ad requests list
       ↓
       Notification system → Influencer notified of new request
```

### 2.4 Negotiation & Payment Workflow

**Process Flow:**
1. Sponsor receives notification of influencer response
2. Sponsor reviews influencer counter-offers
3. Sponsor can accept, reject, or counter-offer
4. Upon agreement, sponsor proceeds to payment:
   - Reviews final terms
   - Initiates payment through payment gateway
   - Receives receipt/confirmation
5. Sponsor monitors influencer progress updates

**Data Flow:**
```
Sponsor → SponsorAdRequests.vue → API Request (/api/sponsor/ad_requests) → app.py → AdRequest model query → Database
       ↓
       Ad request list returned to frontend
       ↓
Sponsor → Ad request selection → SponsorAdRequestDetail.vue → API Request (/api/sponsor/ad_requests/:id) → AdRequest detail + NegotiationHistory returned
       ↓
Sponsor → Negotiation action (counter/accept/reject) → API Request (/api/sponsor/ad_requests/:id PUT) → AdRequest model update + NegotiationHistory creation → Database update
       ↓
       Response returned → UI updated with new status
       ↓
Sponsor → Payment initiation → PaymentConfirmationView.vue → API Request (/api/sponsor/ad_requests/:id/payments POST) → app.py → Payment model creation → Payment gateway integration → Database (payments table)
       ↓
       Payment confirmation → Receipt generation → API Request (/api/sponsor/payments/:id/receipt) → Receipt returned
       ↓
Sponsor → Progress monitoring → API Request (/api/sponsor/ad_requests/:id/progress) → ProgressUpdate records returned → Sponsor reviews progress
```

### 2.5 Performance Analytics Workflow

**Process Flow:**
1. Sponsor accesses dashboard for performance metrics
2. Sponsor views campaign-specific analytics
3. Sponsor reviews ROI metrics for completed ad requests

**Data Flow:**
```
Sponsor → SponsorDashboard.vue → API Request (/api/charts/dashboard-summary) → app.py → Aggregation queries → Database
       ↓
       Dashboard data returned to frontend
       ↓
Sponsor → Campaign selection → API Request (/api/sponsor/campaigns/:id/negotiation_summary) → Campaign performance data returned
       ↓
       Chart components render visualizations
```

## 3. Influencer User Workflows

### 3.1 Registration & Profile Setup Workflow

**Process Flow:**
1. Influencer registers an account → Confirmation email sent
2. Influencer completes profile information:
   - Public name/handle
   - Category (e.g., Technology, Fashion)
   - Niche specialization
   - Audience reach statistics
3. Influencer awaits admin approval
4. Upon approval, influencer gains access to full functionality

**Data Flow:**
```
Influencer → RegisterView.vue → API Request (/api/register with role=influencer) → app.py → User model creation → Database (users table)
          ↓
          Authentication token returned → LocalStorage
          ↓
Influencer → ProfileView.vue → Form completion → API Request (/api/profile) → app.py → User model update → Database update
          ↓
          Response returned → Profile saved → Awaiting approval status
          ↓
Admin approval (see Admin workflow) → Database update → Email notification → Influencer receives approval
```

### 3.2 Campaign Discovery Workflow

**Process Flow:**
1. Influencer browses available public campaigns
2. Influencer applies filters (category, budget range, duration)
3. Influencer views campaign details
4. Influencer can choose to apply for campaigns

**Data Flow:**
```
Influencer → InfluencerCampaignBrowse.vue → API Request (/api/search/campaigns with filters) → app.py → Campaign model query (public campaigns) → Database
          ↓
          Filtered campaign list returned to frontend
          ↓
Influencer → Campaign selection → Campaign detail modal → API Request (/api/campaigns/:id) → Campaign detail returned
          ↓
          Influencer reviews campaign details → Decision to apply
```

### 3.3 Campaign Application Workflow

**Process Flow:**
1. Influencer selects a campaign to apply for
2. Influencer defines their offering:
   - Proposed deliverables
   - Timeline
   - Payment request
   - Message to sponsor
3. Application submitted as an ad request
4. Influencer awaits sponsor response

**Data Flow:**
```
Influencer → Campaign selection → Application form → API Request (/api/influencer/campaigns/:id/apply) → app.py → AdRequest model creation → Database (ad_requests table)
          ↓
          Response returned → Redirect to ad requests list
          ↓
          Notification system → Sponsor notified of new application
```

### 3.4 Ad Request Management & Negotiation Workflow

**Process Flow:**
1. Influencer receives ad requests from sponsors
2. Influencer reviews request details:
   - Campaign information
   - Requirements
   - Payment offer
   - Sponsor message
3. Influencer can accept, reject, or counter-offer
4. Negotiation continues until agreement or rejection
5. Upon acceptance, influencer begins work

**Data Flow:**
```
Influencer → InfluencerAdRequests.vue → API Request (/api/influencer/ad_requests) → app.py → AdRequest model query → Database
          ↓
          Ad request list returned to frontend
          ↓
Influencer → Ad request selection → InfluencerAdRequestDetail.vue → API Request (/api/influencer/ad_requests/:id) → AdRequest detail + NegotiationHistory returned
          ↓
Influencer → Negotiation action (counter/accept/reject) → API Request (/api/influencer/ad_requests/:id PATCH) → AdRequest model update + NegotiationHistory creation → Database update
          ↓
          Response returned → UI updated with new status
          ↓
          Notification system → Sponsor notified of influencer response
```

### 3.5 Content Delivery & Progress Update Workflow

**Process Flow:**
1. Influencer works on campaign deliverables
2. Influencer submits progress updates:
   - Content descriptions
   - Media uploads (links/images)
   - Metrics data (views, engagement)
3. Sponsor reviews and provides feedback
4. Influencer completes campaign

**Data Flow:**
```
Influencer → InfluencerAdRequestDetail.vue → Progress update form → API Request (/api/influencer/ad_requests/:id/progress POST) → app.py → ProgressUpdate model creation → Database (progress_updates table)
          ↓
          Response returned → UI updated with progress history
          ↓
          Notification system → Sponsor notified of new progress update
          ↓
Sponsor review (see Sponsor workflow) → Feedback provided → Influencer receives feedback
          ↓
Influencer → Final delivery → Campaign completion
```

### 3.6 Payment Receipt & Analytics Workflow

**Process Flow:**
1. Influencer receives payment notification
2. Influencer views payment details and status
3. Influencer accesses dashboard for performance metrics
4. Influencer reviews completed campaign history

**Data Flow:**
```
Influencer → InfluencerAdRequestDetail.vue → API Request (/api/influencer/ad_requests/:id/payments) → app.py → Payment model query → Database
          ↓
          Payment information returned to frontend
          ↓
Influencer → InfluencerDashboard.vue → API Request (/api/charts/dashboard-summary) → app.py → Aggregation queries → Database
          ↓
          Dashboard data returned to frontend
          ↓
Influencer → API Request (/api/influencer/negotiations) → Negotiation history data returned
          ↓
          Chart components render visualizations
```

## 4. Cross-Role Interactions

### 4.1 Sponsor-Influencer Interaction Flow

```
Sponsor → Creates Campaign → Campaign stored in DB
       ↓
Influencer → Discovers Campaign → Views Details
          ↓
Two possible paths:
       ↓                       ↓
Sponsor initiates request    Influencer applies to campaign
       ↓                       ↓
AdRequest created           AdRequest created
       ↓                       ↓
Influencer receives request   Sponsor receives application
       ↓                       ↓
Negotiation cycle begins      Negotiation cycle begins
       ↓                       ↓
       ↓------- Negotiation cycle (multiple rounds) ------↓
       ↓                       ↓
Agreement reached            Agreement reached
       ↓                       ↓
Sponsor makes payment → Payment stored in DB → Influencer views payment
       ↓                       ↓
Influencer performs work → Progress updates → Sponsor reviews progress
       ↓                       ↓
Campaign completion → Performance metrics recorded → Both parties view analytics
```

### 4.2 Admin-User Interaction Flow

```
Sponsor/Influencer → Registration → Pending approval status
                  ↓
Admin → Reviews application → Approval decision
     ↓                       ↓
Approved                    Rejected
     ↓                       ↓
User notified              User notified
     ↓
User gains full access → Creates content (campaigns/applications)
     ↓
Admin → Content moderation → Flagging if necessary
     ↓
Flagged content → User notification → Resolution process
```

## 5. Database Interactions by Role

### 5.1 Admin Database Access

| Table | Access Type | Purpose |
|-------|-------------|---------|
| users | Read/Write | User approval, flagging, deactivation |
| campaigns | Read/Write (limited) | Campaign moderation, flagging |
| ad_requests | Read/Write (limited) | Ad request moderation, flagging |
| payments | Read | Payment monitoring, reporting |
| negotiation_history | Read | Dispute resolution, monitoring |
| progress_updates | Read | Content monitoring |

### 5.2 Sponsor Database Access

| Table | Access Type | Purpose |
|-------|-------------|---------|
| users (own) | Read/Write | Profile management |
| users (influencers) | Read | Influencer discovery |
| campaigns | Read/Write (own) | Campaign management |
| ad_requests | Read/Write (as sponsor) | Ad request management |
| payments | Read/Write (as sponsor) | Payment creation, receipt viewing |
| negotiation_history | Read (as participant) | Negotiation tracking |
| progress_updates | Read/Write (feedback) | Progress monitoring |

### 5.3 Influencer Database Access

| Table | Access Type | Purpose |
|-------|-------------|---------|
| users (own) | Read/Write | Profile management |
| campaigns | Read | Campaign discovery |
| ad_requests | Read/Write (as influencer) | Ad request management |
| payments | Read (as recipient) | Payment verification |
| negotiation_history | Read (as participant) | Negotiation tracking |
| progress_updates | Read/Write (own) | Progress submission |

## 6. Notification Flows

### 6.1 Email Notifications

| Event | Sender | Recipient | Content |
|-------|--------|-----------|---------|
| User Registration | System | User | Confirmation, next steps |
| Account Approval | System | User | Approval status, access information |
| New Ad Request | System | Influencer | Request details, action link |
| Ad Request Response | System | Sponsor | Response details, action link |
| Payment Confirmation | System | Both | Payment details, receipt |
| Progress Update | System | Sponsor | Update notification, review link |
| Progress Feedback | System | Influencer | Feedback notification, action link |

### 6.2 In-App Notifications

Similar flow to email notifications but delivered through the application's interface, stored in the database, and marked as read/unread by users. 