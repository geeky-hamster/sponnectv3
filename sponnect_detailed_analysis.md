# Sponnect Application - Detailed Functionality & Data Flow Analysis

## Application Overview

Sponnect is a comprehensive web platform designed to connect influencers with sponsors for promotional campaigns and collaborations. The application serves three distinct user roles - Administrators, Sponsors, and Influencers - each with unique workflows and capabilities.

## Tech Stack

**Frontend:**
- Vue.js 3 with Vue Router for routing
- Pinia for state management
- Axios for API communication
- Bootstrap 5 for UI components
- Vite as the build tool

**Backend:**
- Flask (Python) for API endpoints
- SQLAlchemy ORM for database interactions
- JWT for authentication
- Celery for background tasks
- Redis for caching and task queue

**Database:**
- SQL database (PostgreSQL-compatible schema)
- Relational data model with clear entity relationships

**Development Environment:**
- Local development server runs on port 5175
- API server runs on default Flask port (5000)

## Core Database Entities

### Users
- Stores all user accounts with role differentiation
- Contains specific fields for each role (sponsor/influencer)
- Tracks approval status and account status

**Schema Details:**
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(80) UNIQUE NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    password_hash VARCHAR(128) NOT NULL,
    role VARCHAR(20) NOT NULL DEFAULT 'influencer',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    sponsor_approved BOOLEAN DEFAULT NULL,
    influencer_approved BOOLEAN DEFAULT NULL,
    is_flagged BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    -- Sponsor specific fields
    company_name VARCHAR(100),
    industry VARCHAR(100),
    
    -- Influencer specific fields
    influencer_name VARCHAR(100),
    category VARCHAR(50),
    niche VARCHAR(100),
    reach INTEGER DEFAULT 0
);

CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_approval ON users(sponsor_approved, influencer_approved);
```

### Campaigns
- Created by sponsors
- Contains details like budget, dates, requirements
- Visibility controls (public/private)
- Status tracking (draft, active, completed, etc.)

**Schema Details:**
```sql
CREATE TABLE campaigns (
    id SERIAL PRIMARY KEY,
    name VARCHAR(120) NOT NULL,
    description TEXT,
    start_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    end_date TIMESTAMP,
    budget FLOAT NOT NULL,
    visibility VARCHAR(10) NOT NULL DEFAULT 'private',
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    category VARCHAR(50),
    goals TEXT,
    is_flagged BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    sponsor_id INTEGER NOT NULL REFERENCES users(id)
);

CREATE INDEX idx_campaigns_sponsor ON campaigns(sponsor_id);
CREATE INDEX idx_campaigns_visibility ON campaigns(visibility);
CREATE INDEX idx_campaigns_status ON campaigns(status);
CREATE INDEX idx_campaigns_category ON campaigns(category);
```

### Ad Requests
- Connects sponsors with influencers
- Tracks negotiation status and payment offers
- Links to campaigns
- Can be initiated by either sponsors or influencers

**Schema Details:**
```sql
CREATE TABLE ad_requests (
    id SERIAL PRIMARY KEY,
    campaign_id INTEGER NOT NULL REFERENCES campaigns(id),
    influencer_id INTEGER NOT NULL REFERENCES users(id),
    initiator_id INTEGER NOT NULL REFERENCES users(id),
    message TEXT,
    requirements TEXT NOT NULL,
    payment_amount FLOAT NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'Pending',
    last_offer_by VARCHAR(20),
    is_flagged BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_adrequest_campaign_influencer ON ad_requests(campaign_id, influencer_id);
CREATE INDEX idx_adrequest_status ON ad_requests(status);
CREATE INDEX idx_adrequest_influencer ON ad_requests(influencer_id);
CREATE INDEX idx_adrequest_initiator ON ad_requests(initiator_id);
```

### Payments
- Records payment transactions
- Tracks platform fees and influencer amounts
- Maintains payment status and receipts

**Schema Details:**
```sql
CREATE TABLE payments (
    id SERIAL PRIMARY KEY,
    ad_request_id INTEGER NOT NULL REFERENCES ad_requests(id) ON DELETE CASCADE,
    amount FLOAT NOT NULL,
    platform_fee FLOAT NOT NULL DEFAULT 0.0,
    influencer_amount FLOAT NOT NULL DEFAULT 0.0,
    status VARCHAR(20) NOT NULL DEFAULT 'Pending',
    payment_method VARCHAR(50) NOT NULL DEFAULT 'Razorpay',
    transaction_id VARCHAR(100),
    payment_response TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_payments_adrequest ON payments(ad_request_id);
CREATE INDEX idx_payments_status ON payments(status);
```

### Negotiation History
- Complete audit trail of all negotiation activities
- Records offers, counter-offers, and messages
- Provides historical context for dispute resolution

**Schema Details:**
```sql
CREATE TABLE negotiation_history (
    id SERIAL PRIMARY KEY,
    ad_request_id INTEGER NOT NULL REFERENCES ad_requests(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES users(id),
    user_role VARCHAR(20) NOT NULL,
    action VARCHAR(20) NOT NULL,
    message TEXT,
    payment_amount FLOAT,
    requirements TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_negotiation_adrequest ON negotiation_history(ad_request_id);
CREATE INDEX idx_negotiation_user ON negotiation_history(user_id);
CREATE INDEX idx_negotiation_action ON negotiation_history(action);
```

### Progress Updates
- Documents campaign progress by influencers
- Allows media links and performance metrics
- Tracks sponsor feedback and approval status

**Schema Details:**
```sql
CREATE TABLE progress_updates (
    id SERIAL PRIMARY KEY,
    ad_request_id INTEGER NOT NULL REFERENCES ad_requests(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    media_urls TEXT,
    metrics_data TEXT,
    status VARCHAR(20) DEFAULT 'Pending',
    feedback TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_progress_adrequest ON progress_updates(ad_request_id);
CREATE INDEX idx_progress_status ON progress_updates(status);
```

## Role-Based Functionality Analysis

## 1. Administrator Role

### 1.1 User Management

**Functionality:**
- View a comprehensive list of all users in the system
- Filter and sort users by various criteria (role, status, creation date)
- Approve or reject new sponsor and influencer registrations
- Flag/unflag users for review or inappropriate behavior
- Activate/deactivate user accounts as needed
- Monitor user growth and platform adoption

**Data Flow:**
1. **Frontend to Backend:**
   - Administrator accesses `AdminUsersView.vue` in the admin dashboard
   - Vue component initializes with data fetching hook:
     ```javascript
     // AdminUsersView.vue
     setup() {
       const users = ref([])
       const loading = ref(true)
       const error = ref(null)
       const filters = reactive({
         role: '',
         status: '',
         search: '',
         page: 1,
         perPage: 10
       })
       
       const fetchUsers = async () => {
         loading.value = true
         try {
           const queryParams = new URLSearchParams()
           if (filters.role) queryParams.append('role', filters.role)
           if (filters.status) queryParams.append('status', filters.status)
           if (filters.search) queryParams.append('search', filters.search)
           queryParams.append('page', filters.page)
           queryParams.append('per_page', filters.perPage)
           
           const response = await axios.get(`/api/admin/users?${queryParams.toString()}`)
           users.value = response.data.users
           pagination.value = response.data.pagination
         } catch (err) {
           error.value = 'Failed to load users'
           console.error(err)
         } finally {
           loading.value = false
         }
       }
       
       onMounted(fetchUsers)
       watch(filters, fetchUsers)
       
       // Rest of the component...
     }
     ```
   - Component makes API request to `/api/admin/users` with filter parameters
   - Request includes JWT token in Authorization header:
     ```
     GET /api/admin/users?role=sponsor&status=pending&page=1&per_page=10
     Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
     ```

2. **Backend Processing:**
   - `admin_list_users()` function in `app.py` validates admin role through decorator:
     ```python
     @app.route('/api/admin/users', methods=['GET'])
     @jwt_required()
     @admin_required
     def admin_list_users():
         # Extract query parameters
         role_filter = request.args.get('role')
         status_filter = request.args.get('status')
         search_query = request.args.get('search')
         page = int(request.args.get('page', 1))
         per_page = min(int(request.args.get('per_page', 10)), 50)  # Limit max per page
         
         # Build the query
         query = User.query
         
         # Apply filters
         if role_filter:
             query = query.filter(User.role == role_filter)
         
         if status_filter == 'pending':
             if role_filter == 'sponsor':
                 query = query.filter(User.sponsor_approved.is_(None))
             elif role_filter == 'influencer':
                 query = query.filter(User.influencer_approved.is_(None))
             else:
                 query = query.filter(or_(
                     and_(User.role == 'sponsor', User.sponsor_approved.is_(None)),
                     and_(User.role == 'influencer', User.influencer_approved.is_(None))
                 ))
         elif status_filter == 'approved':
             if role_filter == 'sponsor':
                 query = query.filter(User.sponsor_approved == True)
             elif role_filter == 'influencer':
                 query = query.filter(User.influencer_approved == True)
             else:
                 query = query.filter(or_(
                     and_(User.role == 'sponsor', User.sponsor_approved == True),
                     and_(User.role == 'influencer', User.influencer_approved == True)
                 ))
         elif status_filter == 'rejected':
             if role_filter == 'sponsor':
                 query = query.filter(User.sponsor_approved == False)
             elif role_filter == 'influencer':
                 query = query.filter(User.influencer_approved == False)
             else:
                 query = query.filter(or_(
                     and_(User.role == 'sponsor', User.sponsor_approved == False),
                     and_(User.role == 'influencer', User.influencer_approved == False)
                 ))
         elif status_filter == 'flagged':
             query = query.filter(User.is_flagged == True)
             
         # Apply search query
         if search_query:
             search_term = f"%{search_query}%"
             query = query.filter(or_(
                 User.username.ilike(search_term),
                 User.email.ilike(search_term),
                 User.company_name.ilike(search_term),
                 User.influencer_name.ilike(search_term)
             ))
         
         # Order by most recent first
         query = query.order_by(User.created_at.desc())
         
         # Paginate results
         paginated_users = query.paginate(page=page, per_page=per_page, error_out=False)
         
         # Serialize the users
         result = {
             'users': [serialize_user_profile(user) for user in paginated_users.items],
             'pagination': serialize_pagination(paginated_users)
         }
         
         return jsonify(result), 200
     ```

3. **Database Interaction:**
   - SQLAlchemy ORM converts the filters to SQL queries. The equivalent raw SQL query would be:
     ```sql
     SELECT 
         users.id, 
         users.username, 
         users.email, 
         users.role, 
         users.is_active, 
         users.sponsor_approved, 
         users.influencer_approved, 
         users.is_flagged, 
         users.created_at, 
         users.company_name, 
         users.industry, 
         users.influencer_name, 
         users.category, 
         users.niche, 
         users.reach 
     FROM 
         users 
     WHERE 
         users.role = 'sponsor' 
         AND users.sponsor_approved IS NULL
     ORDER BY 
         users.created_at DESC 
     LIMIT 10 OFFSET 0;
     ```
   - Database executes the query and returns the results
   - For pagination, a second query is made to get the total count:
     ```sql
     SELECT COUNT(*) FROM users WHERE users.role = 'sponsor' AND users.sponsor_approved IS NULL;
     ```

4. **Response Processing:**
   - User records retrieved from database (typically 10 per page)
   - Each user serialized using `serialize_user_profile()` function:
     ```python
     def serialize_user_profile(user):
         data = {
             'id': user.id,
             'username': user.username,
             'email': user.email,
             'role': user.role,
             'is_active': user.is_active,
             'is_flagged': user.is_flagged,
             'created_at': user.created_at.isoformat() if user.created_at else None
         }
         
         if user.role == 'sponsor':
             data.update({
                 'company_name': user.company_name, 
                 'industry': user.industry, 
                 'sponsor_approved': user.sponsor_approved
             })
         elif user.role == 'influencer':
             data.update({
                 'influencer_name': user.influencer_name, 
                 'category': user.category, 
                 'niche': user.niche, 
                 'reach': user.reach,
                 'influencer_approved': user.influencer_approved
             })
             
         return data
     ```
   - Pagination metadata added to response:
     ```python
     def serialize_pagination(pagination_obj):
         return {
             'page': pagination_obj.page,
             'per_page': pagination_obj.per_page,
             'total_pages': pagination_obj.pages,
             'total_items': pagination_obj.total,
             'has_prev': pagination_obj.has_prev,
             'has_next': pagination_obj.has_next,
             'prev_num': pagination_obj.prev_num,
             'next_num': pagination_obj.next_num
         }
     ```
   - JSON response formatted and returned to frontend:
     ```json
     {
       "users": [
         {
           "id": 42,
           "username": "acmecorp",
           "email": "contact@acmecorp.com",
           "role": "sponsor",
           "is_active": true,
           "is_flagged": false,
           "created_at": "2023-05-15T10:30:22.123456",
           "company_name": "Acme Corporation",
           "industry": "Technology",
           "sponsor_approved": null
         },
         // More users...
       ],
       "pagination": {
         "page": 1,
         "per_page": 10,
         "total_pages": 5,
         "total_items": 47,
         "has_prev": false,
         "has_next": true,
         "prev_num": null,
         "next_num": 2
       }
     }
     ```
   - Frontend receives the response and updates the UI accordingly

5. **User Approval Process:**
   - Admin reviews pending user in the interface
   - Clicks "Approve" button triggering a user approval action:
     ```javascript
     // AdminUsersView.vue
     const approveUser = async (userId, userRole) => {
       try {
         loading.value = true
         const endpoint = userRole === 'sponsor' 
           ? `/api/admin/sponsors/${userId}/approve` 
           : `/api/admin/influencers/${userId}/approve`
         
         await axios.patch(endpoint)
         notifications.success(`User ${userId} has been approved successfully`)
         fetchUsers() // Refresh the user list
       } catch (err) {
         notifications.error('Failed to approve user')
         console.error(err)
       } finally {
         loading.value = false
       }
     }
     ```
   - API request sent to:
     - `/api/admin/sponsors/:id/approve` (for sponsors)
     - `/api/admin/influencers/:id/approve` (for influencers)
   - Backend endpoint processes the approval:
     ```python
     @app.route('/api/admin/sponsors/<int:sponsor_id>/approve', methods=['PATCH'])
     @jwt_required()
     @admin_required
     def admin_approve_sponsor(sponsor_id):
         user = User.query.filter_by(id=sponsor_id, role='sponsor').first_or_404()
         
         # Update approval status
         user.sponsor_approved = True
         db.session.commit()
         
         # Send approval email notification
         try:
             send_approval_notification(user.email, 'sponsor')
         except Exception as e:
             # Log error but don't fail the request
             app.logger.error(f"Failed to send approval email: {str(e)}")
         
         return jsonify({'message': f'Sponsor {sponsor_id} has been approved', 'user_id': sponsor_id}), 200
     ```
   - Database update executed:
     ```sql
     UPDATE users 
     SET sponsor_approved = TRUE 
     WHERE id = 42 AND role = 'sponsor';
     ```
   - Email notification sent via `mailer.py` using templated HTML:
     ```python
     def send_approval_notification(email, role):
         subject = f"Your {role.capitalize()} account has been approved"
         
         # Load email template
         template = render_template(
             'emails/account_approval.html',
             role=role,
             login_url=config.LOGIN_URL
         )
         
         # Send email asynchronously
         send_email_task.delay(
             recipient=email,
             subject=subject,
             html_body=template
         )
     ```
   - Success response returned to frontend:
     ```json
     {
       "message": "Sponsor 42 has been approved",
       "user_id": 42
     }
     ```
   - UI updates to reflect approval status with appropriate visual indicators

6. **User Flagging Process:**
   - Admin flags suspicious user via dedicated button:
     ```javascript
     const flagUser = async (userId) => {
       try {
         loading.value = true
         await axios.patch(`/api/admin/users/${userId}/flag`)
         notifications.success(`User ${userId} has been flagged for review`)
         fetchUsers() // Refresh the user list
       } catch (err) {
         notifications.error('Failed to flag user')
         console.error(err)
       } finally {
         loading.value = false
       }
     }
     ```
   - API request to `/api/admin/users/:id/flag`
   - Backend processes the flag request:
     ```python
     @app.route('/api/admin/users/<int:user_id>/flag', methods=['PATCH'])
     @jwt_required()
     @admin_required
     def admin_flag_user(user_id):
         user = User.query.get_or_404(user_id)
         
         # Toggle flag status
         user.is_flagged = not user.is_flagged
         db.session.commit()
         
         action = "flagged" if user.is_flagged else "unflagged"
         return jsonify({'message': f'User {user_id} has been {action}', 'is_flagged': user.is_flagged}), 200
     ```
   - Database update executed:
     ```sql
     UPDATE users 
     SET is_flagged = TRUE 
     WHERE id = 42;
     ```
   - Flagged users highlighted in admin dashboard with visual indicators (typically red badges or warning icons)
   - Further moderation actions may be triggered based on flagging

### 1.2 Campaign Moderation

**Functionality:**
- View all campaigns across the platform
- Filter campaigns by status, category, date range
- Flag/unflag inappropriate campaign content
- Monitor campaign metrics and performance
- Track campaign status changes

**Data Flow:**
1. **Campaign Listing:**
   - Frontend initialization in `AdminCampaignsView.vue`:
     ```javascript
     // AdminCampaignsView.vue
     setup() {
       const campaigns = ref([])
       const loading = ref(true)
       const error = ref(null)
       const filters = reactive({
         status: '',
         category: '',
         startDate: '',
         endDate: '',
         search: '',
         page: 1,
         perPage: 10
       })
       
       const fetchCampaigns = async () => {
         loading.value = true
         try {
           const queryParams = new URLSearchParams()
           Object.entries(filters).forEach(([key, value]) => {
             if (value) queryParams.append(key, value)
           })
           
           const response = await axios.get(`/api/admin/campaigns?${queryParams.toString()}`)
           campaigns.value = response.data.campaigns
           pagination.value = response.data.pagination
         } catch (err) {
           error.value = 'Failed to load campaigns'
           console.error(err)
         } finally {
           loading.value = false
         }
       }
       
       onMounted(fetchCampaigns)
       watch(filters, fetchCampaigns)
       
       // Rest of the component...
     }
     ```
   - API request to `/api/admin/campaigns` with query parameters:
     ```
     GET /api/admin/campaigns?status=active&category=Technology&page=1&perPage=10
     Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
     ```
   - Backend handler processes the request:
     ```python
     @app.route('/api/admin/campaigns', methods=['GET'])
     @jwt_required()
     @admin_required
     def admin_list_campaigns():
         # Extract query parameters
         status = request.args.get('status')
         category = request.args.get('category')
         search = request.args.get('search')
         start_date = request.args.get('startDate')
         end_date = request.args.get('endDate')
         page = int(request.args.get('page', 1))
         per_page = min(int(request.args.get('perPage', 10)), 50)
         
         # Start building the query
         query = Campaign.query.join(User, Campaign.sponsor_id == User.id)
         
         # Apply filters
         if status:
             query = query.filter(Campaign.status == status)
         
         if category:
             query = query.filter(Campaign.category == category)
         
         if search:
             search_term = f"%{search}%"
             query = query.filter(or_(
                 Campaign.name.ilike(search_term),
                 Campaign.description.ilike(search_term),
                 User.username.ilike(search_term),
                 User.company_name.ilike(search_term)
             ))
         
         # Apply date range filters if provided
         if start_date:
             try:
                 start_date_obj = datetime.strptime(start_date, '%Y-%m-%d')
                 query = query.filter(Campaign.start_date >= start_date_obj)
             except ValueError:
                 # Invalid date format, ignore this filter
                 pass
         
         if end_date:
             try:
                 end_date_obj = datetime.strptime(end_date, '%Y-%m-%d')
                 query = query.filter(Campaign.end_date <= end_date_obj)
             except ValueError:
                 # Invalid date format, ignore this filter
                 pass
         
         # Order by most recent first
         query = query.order_by(Campaign.created_at.desc())
         
         # Paginate the results
         paginated_campaigns = query.paginate(page=page, per_page=per_page, error_out=False)
         
         # Serialize the campaigns
         result = {
             'campaigns': [serialize_campaign_with_sponsor(campaign) for campaign in paginated_campaigns.items],
             'pagination': serialize_pagination(paginated_campaigns)
         }
         
         return jsonify(result), 200
     ```
   - Database executes complex query with joins:
     ```sql
     SELECT 
         campaigns.id,
         campaigns.name,
         campaigns.description,
         campaigns.start_date,
         campaigns.end_date,
         campaigns.budget,
         campaigns.visibility,
         campaigns.status,
         campaigns.category,
         campaigns.goals,
         campaigns.is_flagged,
         campaigns.created_at,
         campaigns.sponsor_id,
         users.username AS sponsor_username,
         users.company_name AS sponsor_company
     FROM 
         campaigns
     JOIN 
         users ON campaigns.sponsor_id = users.id
     WHERE 
         campaigns.status = 'active' 
         AND campaigns.category = 'Technology'
     ORDER BY 
         campaigns.created_at DESC
     LIMIT 10 OFFSET 0;
     ```
   - Count query for pagination:
     ```sql
     SELECT 
         COUNT(*) 
     FROM 
         campaigns
     JOIN 
         users ON campaigns.sponsor_id = users.id
     WHERE 
         campaigns.status = 'active' 
         AND campaigns.category = 'Technology';
     ```
   - Backend serializes campaign data with sponsors:
     ```python
     def serialize_campaign_with_sponsor(campaign):
         data = serialize_campaign_detail(campaign)
         # Add sponsor details
         data['sponsor'] = {
             'id': campaign.sponsor.id,
             'username': campaign.sponsor.username,
             'company_name': campaign.sponsor.company_name
         }
         
         # Add campaign metrics
         active_ad_requests_count = AdRequest.query.filter(
             AdRequest.campaign_id == campaign.id
         ).count()
         
         accepted_ad_requests_count = AdRequest.query.filter(
             AdRequest.campaign_id == campaign.id,
             AdRequest.status == 'Accepted'
         ).count()
         
         data['metrics'] = {
             'total_ad_requests': active_ad_requests_count,
             'accepted_ad_requests': accepted_ad_requests_count,
             'conversion_rate': round((accepted_ad_requests_count / active_ad_requests_count * 100) if active_ad_requests_count > 0 else 0, 2)
         }
         
         return data
     ```
   - Response JSON returned to frontend:
     ```json
     {
       "campaigns": [
         {
           "id": 123,
           "name": "Summer Product Launch",
           "budget": 50000,
           "budget_formatted": "₹50,000.00",
           "visibility": "public",
           "status": "active",
           "is_flagged": false,
           "description": "Promote our new product line for summer",
           "goals": "Increase brand awareness and drive product sales",
           "sponsor_id": 42,
           "category": "Technology",
           "start_date": "01-06-2023",
           "end_date": "31-08-2023",
           "created_at": "15-05-2023 10:30:22",
           "start_date_iso": "2023-06-01T00:00:00",
           "end_date_iso": "2023-08-31T00:00:00",
           "created_at_iso": "2023-05-15T10:30:22.123456",
           "sponsor_name": "acmecorp",
           "sponsor_company": "Acme Corporation",
           "sponsor": {
             "id": 42,
             "username": "acmecorp",
             "company_name": "Acme Corporation"
           },
           "metrics": {
             "total_ad_requests": 15,
             "accepted_ad_requests": 8,
             "conversion_rate": 53.33
           }
         },
         // More campaigns...
       ],
       "pagination": {
         "page": 1,
         "per_page": 10,
         "total_pages": 8,
         "total_items": 78,
         "has_prev": false,
         "has_next": true,
         "prev_num": null,
         "next_num": 2
       }
     }
     ```

2. **Campaign Flagging Process:**
   - Admin identifies inappropriate campaign content
   - Flags campaign via UI action:
     ```javascript
     const flagCampaign = async (campaignId) => {
       try {
         loading.value = true
         await axios.patch(`/api/admin/campaigns/${campaignId}/flag`)
         notifications.success(`Campaign ${campaignId} has been flagged for review`)
         fetchCampaigns() // Refresh campaign list
       } catch (err) {
         notifications.error('Failed to flag campaign')
         console.error(err)
       } finally {
         loading.value = false
       }
     }
     ```
   - API request to `/api/admin/campaigns/:id/flag`
   - Backend handler processes the flag request:
     ```python
     @app.route('/api/admin/campaigns/<int:campaign_id>/flag', methods=['PATCH'])
     @jwt_required()
     @admin_required
     def admin_flag_campaign(campaign_id):
         campaign = Campaign.query.get_or_404(campaign_id)
         
         # Toggle flag status
         campaign.is_flagged = not campaign.is_flagged
         db.session.commit()
         
         # Get sponsor details to send notification
         sponsor = User.query.get(campaign.sponsor_id)
         
         # If flagging (not unflagging), notify sponsor
         if campaign.is_flagged:
             try:
                 # Notify sponsor of campaign being flagged
                 send_campaign_flag_notification(
                     sponsor.email,
                     campaign.name,
                     "Your campaign has been flagged for review by our content moderation team. Please check your dashboard for more information."
                 )
             except Exception as e:
                 # Log error but don't fail the request
                 app.logger.error(f"Failed to send flag notification: {str(e)}")
         
         action = "flagged" if campaign.is_flagged else "unflagged"
         return jsonify({
             'message': f'Campaign {campaign_id} has been {action}',
             'is_flagged': campaign.is_flagged
         }), 200
     ```
   - Database update executed:
     ```sql
     UPDATE campaigns 
     SET is_flagged = TRUE 
     WHERE id = 123;
     ```
   - Sponsor notification generation:
     ```python
     def send_campaign_flag_notification(email, campaign_name, message):
         subject = f"Campaign Flagged: {campaign_name}"
         
         # Load email template
         template = render_template(
             'emails/campaign_status_notification.html',
             campaign_name=campaign_name,
             message=message,
             action_url=config.SPONSOR_DASHBOARD_URL,
             action_text="View Campaign"
         )
         
         # Send email asynchronously
         send_email_task.delay(
             recipient=email,
             subject=subject,
             html_body=template
         )
     ```
   - Success response returned to frontend:
     ```json
     {
       "message": "Campaign 123 has been flagged",
       "is_flagged": true
     }
     ```
   - UI updates to highlight flagged campaigns with visual indicators

3. **Campaign Status Monitoring:**
   - Scheduled background task runs periodically (daily at midnight):
     ```python
     @celery.task(name="update_expired_campaigns")
     def update_expired_campaigns():
         """Check and update campaigns that have passed their end date"""
         app.logger.info("Running expired campaigns check")
         
         today = datetime.utcnow().date()
         
         # Find expired active campaigns
         expired_campaigns = Campaign.query.filter(
             Campaign.status == 'active',
             Campaign.end_date < today
         ).all()
         
         updated_count = 0
         for campaign in expired_campaigns:
             campaign.status = 'completed'
             updated_count += 1
             
             # Get sponsor details to send notification
             sponsor = User.query.get(campaign.sponsor_id)
             if sponsor:
                 try:
                     send_campaign_expiry_notification(
                         sponsor.email,
                         campaign.name,
                         f"Your campaign '{campaign.name}' has ended and has been automatically marked as completed."
                     )
                 except Exception as e:
                     app.logger.error(f"Failed to send expiry notification for campaign {campaign.id}: {str(e)}")
         
         # Commit all changes at once for efficiency
         if updated_count > 0:
             db.session.commit()
             app.logger.info(f"Updated {updated_count} expired campaigns to 'completed' status")
         else:
             app.logger.info("No expired campaigns found")
         
         return updated_count
     ```
   - Database query to find expired campaigns:
     ```sql
     SELECT * FROM campaigns 
     WHERE status = 'active' 
     AND end_date < CURRENT_DATE;
     ```
   - Batch update to complete expired campaigns:
     ```sql
     UPDATE campaigns 
     SET status = 'completed' 
     WHERE id IN (123, 456, 789);
     ```
   - Email notifications sent to affected sponsors
   - Task results logged for monitoring
   - Campaign status changes reflected in admin dashboard
   - Status history may be tracked for audit purposes

4. **Campaign Detail Analysis:**
   - Admin can access detailed campaign information:
     ```javascript
     const viewCampaignDetails = async (campaignId) => {
       try {
         loading.value = true
         const response = await axios.get(`/api/admin/campaigns/${campaignId}`)
         selectedCampaign.value = response.data
         showDetailModal.value = true
       } catch (err) {
         notifications.error('Failed to load campaign details')
         console.error(err)
       } finally {
         loading.value = false
       }
     }
     ```
   - Backend retrieves comprehensive campaign data:
     ```python
     @app.route('/api/admin/campaigns/<int:campaign_id>', methods=['GET'])
     @jwt_required()
     @admin_required
     def admin_get_campaign(campaign_id):
         campaign = Campaign.query.get_or_404(campaign_id)
         
         # Get basic campaign details
         result = serialize_campaign_detail(campaign)
         
         # Get ad request statistics
         ad_requests = AdRequest.query.filter_by(campaign_id=campaign_id).all()
         
         # Calculate statistics
         stats = {
             'total_requests': len(ad_requests),
             'pending': sum(1 for req in ad_requests if req.status == 'Pending'),
             'accepted': sum(1 for req in ad_requests if req.status == 'Accepted'),
             'rejected': sum(1 for req in ad_requests if req.status == 'Rejected'),
             'negotiating': sum(1 for req in ad_requests if req.status == 'Negotiating'),
         }
         
         # Add payment data if any
         payment_data = db.session.query(
             func.sum(Payment.amount).label('total_paid'),
             func.sum(Payment.platform_fee).label('total_fees')
         ).join(AdRequest, Payment.ad_request_id == AdRequest.id)\
          .filter(AdRequest.campaign_id == campaign_id)\
          .first()
         
         stats['total_paid'] = float(payment_data.total_paid or 0)
         stats['total_fees'] = float(payment_data.total_fees or 0)
         stats['total_paid_formatted'] = format_currency(stats['total_paid'])
         stats['total_fees_formatted'] = format_currency(stats['total_fees'])
         
         # Add progress update statistics
         progress_stats = db.session.query(
             func.count(ProgressUpdate.id).label('total_updates')
         ).join(AdRequest, ProgressUpdate.ad_request_id == AdRequest.id)\
          .filter(AdRequest.campaign_id == campaign_id)\
          .first()
         
         stats['total_progress_updates'] = progress_stats.total_updates
         
         # Add stats to result
         result['statistics'] = stats
         
         return jsonify(result), 200
     ```
   - Complex database queries to gather statistics:
     ```sql
     -- Ad request statistics
     SELECT COUNT(*) FROM ad_requests WHERE campaign_id = 123;
     
     -- Payment statistics
     SELECT 
         SUM(payments.amount) AS total_paid,
         SUM(payments.platform_fee) AS total_fees
     FROM 
         payments
     JOIN 
         ad_requests ON payments.ad_request_id = ad_requests.id
     WHERE 
         ad_requests.campaign_id = 123;
     
     -- Progress update statistics
     SELECT 
         COUNT(progress_updates.id) AS total_updates
     FROM 
         progress_updates
     JOIN 
         ad_requests ON progress_updates.ad_request_id = ad_requests.id
     WHERE 
         ad_requests.campaign_id = 123;
     ```
   - Detailed response with analytics returned:
     ```json
     {
       "id": 123,
       "name": "Summer Product Launch",
       "description": "Promote our new product line for summer",
       "start_date": "01-06-2023",
       "end_date": "31-08-2023",
       "budget": 50000,
       "budget_formatted": "₹50,000.00",
       "visibility": "public",
       "status": "active",
       "is_flagged": false,
       "category": "Technology",
       "goals": "Increase brand awareness and drive product sales",
       "created_at": "15-05-2023 10:30:22",
       "sponsor_name": "acmecorp",
       "sponsor_company": "Acme Corporation",
       "statistics": {
         "total_requests": 15,
         "pending": 2,
         "accepted": 8,
         "rejected": 3,
         "negotiating": 2,
         "total_paid": 240000.0,
         "total_fees": 2400.0,
         "total_paid_formatted": "₹240,000.00",
         "total_fees_formatted": "₹2,400.00",
         "total_progress_updates": 24
       }
     }
     ```
   - Admin can view comprehensive performance metrics 
   - Insights help identify problematic campaigns or successful patterns

### 1.3 Ad Request Moderation

**Functionality:**
- View all ad requests platform-wide
- Monitor negotiation processes between sponsors and influencers
- Flag inappropriate ad requests
- Track conversion rates and completion rates
- Resolve disputes between parties if necessary

**Data Flow:**
1. **Ad Request Listing:**
   - Frontend component initializes data fetching:
     ```javascript
     // AdminAdRequestsView.vue
     setup() {
       const adRequests = ref([])
       const loading = ref(true)
       const error = ref(null)
       const filters = reactive({
         status: '',
         campaign: '',
         influencer: '',
         date_range: '',
         is_flagged: false,
         page: 1,
         perPage: 10
       })
       
       const fetchAdRequests = async () => {
         loading.value = true
         try {
           const queryParams = new URLSearchParams()
           Object.entries(filters).forEach(([key, value]) => {
             if (value) queryParams.append(key, value)
           })
           
           const response = await axios.get(`/api/admin/ad_requests?${queryParams.toString()}`)
           adRequests.value = response.data.ad_requests
           pagination.value = response.data.pagination
         } catch (err) {
           error.value = 'Failed to load ad requests'
           console.error(err)
         } finally {
           loading.value = false
         }
       }
       
       onMounted(fetchAdRequests)
       watch(filters, fetchAdRequests)
       
       // Rest of component...
     }
     ```
   - API request with filters:
     ```
     GET /api/admin/ad_requests?status=Negotiating&is_flagged=true&page=1&perPage=10
     Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
     ```
   - Backend handler processes the request with complex database joins:
     ```python
     @app.route('/api/admin/ad_requests', methods=['GET'])
     @jwt_required()
     @admin_required
     def admin_list_ad_requests():
         # Extract query parameters
         status = request.args.get('status')
         campaign_id = request.args.get('campaign')
         influencer_id = request.args.get('influencer')
         date_range = request.args.get('date_range')
         is_flagged = request.args.get('is_flagged', type=bool)
         page = int(request.args.get('page', 1))
         per_page = min(int(request.args.get('perPage', 10)), 50)
         
         # Start building the query with necessary joins
         query = AdRequest.query.join(
             Campaign, AdRequest.campaign_id == Campaign.id
         ).join(
             User, User.id == AdRequest.influencer_id, aliased=True
         ).join(
             User, User.id == Campaign.sponsor_id, aliased=True
         )
         
         # Apply filters
         if status:
             query = query.filter(AdRequest.status == status)
         
         if campaign_id:
             query = query.filter(AdRequest.campaign_id == campaign_id)
         
         if influencer_id:
             query = query.filter(AdRequest.influencer_id == influencer_id)
         
         if is_flagged is not None:
             query = query.filter(AdRequest.is_flagged == is_flagged)
         
         # Apply date range filter if provided
         if date_range:
             if date_range == '7days':
                 date_threshold = datetime.utcnow() - timedelta(days=7)
                 query = query.filter(AdRequest.created_at >= date_threshold)
             elif date_range == '30days':
                 date_threshold = datetime.utcnow() - timedelta(days=30)
                 query = query.filter(AdRequest.created_at >= date_threshold)
             elif date_range == '90days':
                 date_threshold = datetime.utcnow() - timedelta(days=90)
                 query = query.filter(AdRequest.created_at >= date_threshold)
         
         # Add ordering - most recent first
         query = query.order_by(AdRequest.updated_at.desc())
         
         # Execute paginated query
         paginated_requests = query.paginate(page=page, per_page=per_page, error_out=False)
         
         # Serialize ad requests with related entities
         result = {
             'ad_requests': [serialize_ad_request_with_relations(req) for req in paginated_requests.items],
             'pagination': serialize_pagination(paginated_requests)
         }
         
         return jsonify(result), 200
     ```
   - Database executes complex query with multiple joins:
     ```sql
     SELECT 
         ad_requests.id,
         ad_requests.campaign_id,
         ad_requests.influencer_id,
         ad_requests.initiator_id,
         ad_requests.message,
         ad_requests.requirements,
         ad_requests.payment_amount,
         ad_requests.status,
         ad_requests.last_offer_by,
         ad_requests.is_flagged,
         ad_requests.created_at,
         ad_requests.updated_at,
         campaigns.name AS campaign_name,
         campaigns.sponsor_id,
         influencer.id AS influencer_id,
         influencer.username AS influencer_username,
         influencer.influencer_name,
         sponsor.id AS sponsor_id,
         sponsor.username AS sponsor_username,
         sponsor.company_name
     FROM 
         ad_requests
     JOIN 
         campaigns ON ad_requests.campaign_id = campaigns.id
     JOIN 
         users AS influencer ON ad_requests.influencer_id = influencer.id
     JOIN 
         users AS sponsor ON campaigns.sponsor_id = sponsor.id
     WHERE 
         ad_requests.status = 'Negotiating'
         AND ad_requests.is_flagged = TRUE
     ORDER BY 
         ad_requests.updated_at DESC
     LIMIT 10 OFFSET 0;
     ```
   - Count query for pagination:
     ```sql
     SELECT COUNT(*) FROM ad_requests
     JOIN campaigns ON ad_requests.campaign_id = campaigns.id
     JOIN users AS influencer ON ad_requests.influencer_id = influencer.id
     JOIN users AS sponsor ON campaigns.sponsor_id = sponsor.id
     WHERE ad_requests.status = 'Negotiating'
     AND ad_requests.is_flagged = TRUE;
     ```
   - Ad request serialization with associated entities:
     ```python
     def serialize_ad_request_with_relations(ad_request):
         # Base ad request data
         data = {
             'id': ad_request.id,
             'status': ad_request.status,
             'payment_amount': ad_request.payment_amount,
             'payment_amount_formatted': format_currency(ad_request.payment_amount),
             'requirements': ad_request.requirements,
             'message': ad_request.message,
             'last_offer_by': ad_request.last_offer_by,
             'is_flagged': ad_request.is_flagged,
             'created_at': format_datetime(ad_request.created_at),
             'updated_at': format_datetime(ad_request.updated_at),
             'created_at_iso': ad_request.created_at.isoformat() if ad_request.created_at else None,
             'updated_at_iso': ad_request.updated_at.isoformat() if ad_request.updated_at else None
         }
         
         # Add campaign details
         data['campaign'] = {
             'id': ad_request.campaign.id,
             'name': ad_request.campaign.name,
             'budget': ad_request.campaign.budget,
             'budget_formatted': format_currency(ad_request.campaign.budget),
             'category': ad_request.campaign.category
         }
         
         # Add influencer details
         data['influencer'] = {
             'id': ad_request.target_influencer.id,
             'username': ad_request.target_influencer.username,
             'influencer_name': ad_request.target_influencer.influencer_name,
             'category': ad_request.target_influencer.category,
             'reach': ad_request.target_influencer.reach
         }
         
         # Add sponsor details
         data['sponsor'] = {
             'id': ad_request.campaign.sponsor.id,
             'username': ad_request.campaign.sponsor.username,
             'company_name': ad_request.campaign.sponsor.company_name
         }
         
         # Determine who initiated
         if ad_request.initiator_id == ad_request.campaign.sponsor_id:
             data['initiated_by'] = 'sponsor'
         else:
             data['initiated_by'] = 'influencer'
         
         # Get negotiation rounds count
         negotiation_count = NegotiationHistory.query.filter_by(
             ad_request_id=ad_request.id
         ).count()
         
         data['negotiation_rounds'] = negotiation_count
         
         # Get payment status if any
         payment = Payment.query.filter_by(
             ad_request_id=ad_request.id
         ).order_by(Payment.created_at.desc()).first()
         
         if payment:
             data['payment_status'] = payment.status
         else:
             data['payment_status'] = None
         
         return data
     ```
   - Response JSON with detailed information:
     ```json
     {
       "ad_requests": [
         {
           "id": 456,
           "status": "Negotiating",
           "payment_amount": 30000,
           "payment_amount_formatted": "₹30,000.00",
           "requirements": "3 Instagram posts, 4 Stories, 1 Reel",
           "message": "I can offer additional content for the proposed budget",
           "last_offer_by": "influencer",
           "is_flagged": true,
           "created_at": "20-05-2023 14:25:18",
           "updated_at": "22-05-2023 09:10:42",
           "created_at_iso": "2023-05-20T14:25:18.123456",
           "updated_at_iso": "2023-05-22T09:10:42.789123",
           "campaign": {
             "id": 123,
             "name": "Summer Product Launch",
             "budget": 50000,
             "budget_formatted": "₹50,000.00",
             "category": "Technology"
           },
           "influencer": {
             "id": 789,
             "username": "travelwithjohn",
             "influencer_name": "TravelWithJohn",
             "category": "Lifestyle",
             "reach": 50000
           },
           "sponsor": {
             "id": 42,
             "username": "acmecorp",
             "company_name": "Acme Corporation"
           },
           "initiated_by": "sponsor",
           "negotiation_rounds": 4,
           "payment_status": null
         },
         // More ad requests...
       ],
       "pagination": {
         "page": 1,
         "per_page": 10,
         "total_pages": 3,
         "total_items": 28,
         "has_prev": false,
         "has_next": true,
         "prev_num": null,
         "next_num": 2
       }
     }
     ```

2. **Negotiation History Viewing:**
   - Admin views detailed negotiation history:
     ```javascript
     const viewNegotiationHistory = async (adRequestId) => {
       try {
         historyLoading.value = true
         const response = await axios.get(`/api/ad_requests/${adRequestId}/history`)
         negotiationHistory.value = response.data.history
         showHistoryModal.value = true
       } catch (err) {
         notifications.error('Failed to load negotiation history')
         console.error(err)
       } finally {
         historyLoading.value = false
       }
     }
     ```
   - Backend retrieves complete history:
     ```python
     @app.route('/api/ad_requests/<int:ad_request_id>/history', methods=['GET'])
     @jwt_required()
     def get_negotiation_history(ad_request_id):
         # First check if the ad request exists
         ad_request = AdRequest.query.get_or_404(ad_request_id)
         
         # Get all history items for this ad request
         history_items = NegotiationHistory.query.filter_by(
             ad_request_id=ad_request_id
         ).order_by(NegotiationHistory.created_at.asc()).all()
         
         # Serialize history items
         history_data = [serialize_negotiation_history(item) for item in history_items]
         
         # Add first offer from ad request creation if not already in history
         if not history_items or history_items[0].created_at > ad_request.created_at:
             # This happens when the ad request was created before history tracking was implemented
             initial_offer = {
                 'id': None,
                 'ad_request_id': ad_request_id,
                 'user_role': 'influencer' if ad_request.initiator_id == ad_request.influencer_id else 'sponsor',
                 'action': 'propose',
                 'message': ad_request.message,
                 'payment_amount': ad_request.payment_amount,
                 'payment_amount_formatted': format_currency(ad_request.payment_amount),
                 'requirements': ad_request.requirements,
                 'created_at': format_datetime(ad_request.created_at),
                 'created_at_iso': ad_request.created_at.isoformat() if ad_request.created_at else None,
                 'user': {
                     'id': ad_request.initiator_id,
                     'username': User.query.get(ad_request.initiator_id).username
                 }
             }
             history_data.insert(0, initial_offer)
         
         return jsonify({'history': history_data}), 200
     ```
   - Database query to retrieve negotiation history:
     ```sql
     SELECT 
         negotiation_history.id,
         negotiation_history.ad_request_id,
         negotiation_history.user_id,
         negotiation_history.user_role,
         negotiation_history.action,
         negotiation_history.message,
         negotiation_history.payment_amount,
         negotiation_history.requirements,
         negotiation_history.created_at,
         users.username
     FROM 
         negotiation_history
     JOIN 
         users ON negotiation_history.user_id = users.id
     WHERE 
         negotiation_history.ad_request_id = 456
     ORDER BY 
         negotiation_history.created_at ASC;
     ```
   - History serialization with user details:
     ```python
     def serialize_negotiation_history(history_item):
         data = {
             'id': history_item.id,
             'ad_request_id': history_item.ad_request_id,
             'user_role': history_item.user_role,
             'action': history_item.action,
             'message': history_item.message,
             'payment_amount': history_item.payment_amount,
             'payment_amount_formatted': format_currency(history_item.payment_amount),
             'requirements': history_item.requirements,
             'created_at': format_datetime(history_item.created_at),
             'created_at_iso': history_item.created_at.isoformat() if history_item.created_at else None,
             'user': {
                 'id': history_item.user_id,
                 'username': history_item.user.username
             }
         }
         return data
     ```
   - Response with chronological negotiation history:
     ```json
     {
       "history": [
         {
           "id": null,
           "ad_request_id": 456,
           "user_role": "sponsor",
           "action": "propose",
           "message": "We'd love to collaborate on our summer campaign",
           "payment_amount": 15000,
           "payment_amount_formatted": "₹15,000.00",
           "requirements": "3 Instagram posts, 2 Stories",
           "created_at": "20-05-2023 14:25:18",
           "created_at_iso": "2023-05-20T14:25:18.123456",
           "user": {
             "id": 42,
             "username": "acmecorp"
           }
         },
         {
           "id": 1001,
           "ad_request_id": 456,
           "user_role": "influencer",
           "action": "counter",
           "message": "I would need a higher budget for this scope of work",
           "payment_amount": 25000,
           "payment_amount_formatted": "₹25,000.00",
           "requirements": "3 Instagram posts, 2 Stories",
           "created_at": "20-05-2023 16:40:33",
           "created_at_iso": "2023-05-20T16:40:33.456789",
           "user": {
             "id": 789,
             "username": "travelwithjohn"
           }
         },
         {
           "id": 1002,
           "ad_request_id": 456,
           "user_role": "sponsor",
           "action": "counter",
           "message": "We can adjust the scope for this budget",
           "payment_amount": 20000,
           "payment_amount_formatted": "₹20,000.00",
           "requirements": "2 Instagram posts, 2 Stories",
           "created_at": "21-05-2023 09:15:27",
           "created_at_iso": "2023-05-21T09:15:27.123456",
           "user": {
             "id": 42,
             "username": "acmecorp"
           }
         },
         {
           "id": 1003,
           "ad_request_id": 456,
           "user_role": "influencer",
           "action": "counter",
           "message": "I can offer additional content for the proposed budget",
           "payment_amount": 30000,
           "payment_amount_formatted": "₹30,000.00",
           "requirements": "3 Instagram posts, 4 Stories, 1 Reel",
           "created_at": "22-05-2023 09:10:42",
           "created_at_iso": "2023-05-22T09:10:42.789123",
           "user": {
             "id": 789,
             "username": "travelwithjohn"
           }
         }
       ]
     }
     ```

3. **Dispute Resolution:**
   - Admin reviews flagged ad requests for potential disputes
   - May flag problematic requests for further review:
     ```javascript
     const flagAdRequest = async (adRequestId) => {
       try {
         loading.value = true
         await axios.patch(`/api/admin/ad_requests/${adRequestId}/flag`)
         notifications.success(`Ad Request ${adRequestId} has been flagged for review`)
         fetchAdRequests() // Refresh the list
       } catch (err) {
         notifications.error('Failed to flag ad request')
         console.error(err)
       } finally {
         loading.value = false
       }
     }
     ```
   - Backend handles flagging:
     ```python
     @app.route('/api/admin/ad_requests/<int:ad_request_id>/flag', methods=['PATCH'])
     @jwt_required()
     @admin_required
     def admin_flag_ad_request(ad_request_id):
         ad_request = AdRequest.query.get_or_404(ad_request_id)
         
         # Toggle flag status
         ad_request.is_flagged = not ad_request.is_flagged
         db.session.commit()
         
         # Get related users
         sponsor = User.query.get(ad_request.campaign.sponsor_id)
         influencer = User.query.get(ad_request.influencer_id)
         
         # If flagging (not unflagging), notify both parties
         if ad_request.is_flagged:
             try:
                 # Create notification message
                 message = "An administrator has flagged your ad request for review. Please check your dashboard for more information."
                 
                 # Notify sponsor
                 send_ad_request_flag_notification(
                     sponsor.email,
                     f"Ad Request for '{ad_request.campaign.name}' flagged",
                     message
                 )
                 
                 # Notify influencer
                 send_ad_request_flag_notification(
                     influencer.email,
                     f"Ad Request for '{ad_request.campaign.name}' flagged",
                     message
                 )
             except Exception as e:
                 # Log error but don't fail the request
                 app.logger.error(f"Failed to send flag notification: {str(e)}")
         
         action = "flagged" if ad_request.is_flagged else "unflagged"
         return jsonify({
             'message': f'Ad Request {ad_request_id} has been {action}',
             'is_flagged': ad_request.is_flagged
         }), 200
     ```
   - Database update executed:
     ```sql
     UPDATE ad_requests 
     SET is_flagged = TRUE 
     WHERE id = 456;
     ```
   - Both parties receive email notifications
   - Admin can communicate through platform messaging or email
   - System maintains complete audit trail through negotiation history
   - Admin may request edits or suggest compromise:
     ```javascript
     const sendAdminMessage = async () => {
       try {
         loading.value = true
         await axios.post(`/api/admin/ad_requests/${selectedRequest.value.id}/message`, {
           message: adminMessage.value,
           send_to: recipientType.value  // 'both', 'sponsor', or 'influencer'
         })
         notifications.success('Message sent successfully')
         adminMessage.value = ''
         showMessageModal.value = false
       } catch (err) {
         notifications.error('Failed to send message')
         console.error(err)
       } finally {
         loading.value = false
       }
     }
     ```

4. **Status and Metrics Tracking:**
   - Admin dashboard shows ad request conversion metrics:
     ```python
     @app.route('/api/charts/ad-request-status', methods=['GET'])
     @jwt_required()
     @admin_required
     @cache.cached(timeout=180)  # Cache for 3 minutes
     def chart_ad_request_status():
         # Group ad requests by status
         status_counts = db.session.query(
             AdRequest.status,
             func.count(AdRequest.id).label('count')
         ).group_by(AdRequest.status).all()
         
         # Convert to dictionary
         status_data = {status: count for status, count in status_counts}
         
         # Ensure all statuses have a value
         all_statuses = ['Pending', 'Accepted', 'Rejected', 'Negotiating']
         result = {status: status_data.get(status, 0) for status in all_statuses}
         
         # Calculate conversion rate
         total_requests = sum(result.values())
         conversion_rate = (result.get('Accepted', 0) / total_requests * 100) if total_requests > 0 else 0
         
         # Add to result
         result['total'] = total_requests
         result['conversion_rate'] = round(conversion_rate, 2)
         
         return jsonify(result), 200
     ```
   - Database query for ad request status distribution:
     ```sql
     SELECT 
         status, 
         COUNT(id) as count
     FROM 
         ad_requests
     GROUP BY 
         status;
     ```
   - Response with status distribution and metrics:
     ```json
     {
       "Pending": 52,
       "Accepted": 187,
       "Rejected": 94,
       "Negotiating": 38,
       "total": 371,
       "conversion_rate": 50.40
     }
     ```
   - Visual representation in admin dashboard
   - Time-based filtering for trend analysis

### 1.4 Analytics Dashboard

**Functionality:**
- View comprehensive platform statistics
- Analyze user growth trends with time-based filters
- Monitor campaign activity and success rates
- Review conversion rates for ad requests
- Export user and transaction data
- Generate reports for business insights

**Data Flow:**
1. **Dashboard Summary:**
   - Frontend component initialization:
     ```javascript
     // AdminDashboardView.vue
     setup() {
       const dashboardData = ref(null)
       const loading = ref(true)
       const error = ref(null)
       
       const fetchDashboardData = async () => {
         loading.value = true
         try {
           const response = await axios.get('/api/charts/dashboard-summary')
           dashboardData.value = response.data
         } catch (err) {
           error.value = 'Failed to load dashboard data'
           console.error(err)
         } finally {
           loading.value = false
         }
       }
       
       onMounted(fetchDashboardData)
       
       // Refresh every 5 minutes
       const refreshInterval = setInterval(fetchDashboardData, 5 * 60 * 1000)
       onUnmounted(() => {
         clearInterval(refreshInterval)
       })
       
       // Rest of component...
     }
     ```
   - API request to `/api/charts/dashboard-summary`
   - Backend performs multiple aggregation queries:
     ```python
     @app.route('/api/charts/dashboard-summary', methods=['GET'])
     @jwt_required()
     @admin_required
     @cache.cached(timeout=120)  # Cache for 2 minutes
     def chart_dashboard_summary():
         result = {}
         
         # User statistics
         user_stats = db.session.query(
             func.count(User.id).label('total_users'),
             func.sum(case([(User.role == 'sponsor', 1)], else_=0)).label('sponsors'),
             func.sum(case([(User.role == 'influencer', 1)], else_=0)).label('influencers'),
             func.sum(case([(User.is_active == True, 1)], else_=0)).label('active_users'),
             func.sum(case([
                 (and_(User.role == 'sponsor', User.sponsor_approved.is_(None)), 1)
             ], else_=0)).label('pending_sponsors'),
             func.sum(case([
                 (and_(User.role == 'influencer', User.influencer_approved.is_(None)), 1)
             ], else_=0)).label('pending_influencers')
         ).first()
         
         result['users'] = {
             'total': user_stats.total_users,
             'sponsors': user_stats.sponsors,
             'influencers': user_stats.influencers,
             'active': user_stats.active_users,
             'pending_sponsors': user_stats.pending_sponsors,
             'pending_influencers': user_stats.pending_influencers
         }
         
         # Calculate new users in last 7 days
         seven_days_ago = datetime.utcnow() - timedelta(days=7)
         new_users = db.session.query(func.count(User.id)).filter(
             User.created_at >= seven_days_ago
         ).scalar()
         result['users']['new_last_7_days'] = new_users
         
         # Campaign statistics
         campaign_stats = db.session.query(
             func.count(Campaign.id).label('total_campaigns'),
             func.sum(case([(Campaign.status == 'active', 1)], else_=0)).label('active_campaigns'),
             func.sum(case([(Campaign.status == 'completed', 1)], else_=0)).label('completed_campaigns'),
             func.sum(case([(Campaign.visibility == 'public', 1)], else_=0)).label('public_campaigns'),
             func.sum(case([(and_(
                 Campaign.visibility == 'public',
                 Campaign.status == 'active'
             ), 1)], else_=0)).label('public_active_campaigns')
         ).first()
         
         result['campaigns'] = {
             'total': campaign_stats.total_campaigns,
             'active': campaign_stats.active_campaigns,
             'completed': campaign_stats.completed_campaigns,
             'public': campaign_stats.public_campaigns,
             'public_active': campaign_stats.public_active_campaigns
         }
         
         # Calculate average budget
         avg_budget = db.session.query(
             func.avg(Campaign.budget).label('avg_budget')
         ).scalar()
         result['campaigns']['avg_budget'] = round(float(avg_budget or 0), 2)
         result['campaigns']['avg_budget_formatted'] = format_currency(result['campaigns']['avg_budget'])
         
         # Ad request statistics
         ad_request_stats = db.session.query(
             func.count(AdRequest.id).label('total_requests'),
             func.sum(case([(AdRequest.status == 'Pending', 1)], else_=0)).label('pending'),
             func.sum(case([(AdRequest.status == 'Accepted', 1)], else_=0)).label('accepted'),
             func.sum(case([(AdRequest.status == 'Rejected', 1)], else_=0)).label('rejected'),
             func.sum(case([(AdRequest.status == 'Negotiating', 1)], else_=0)).label('negotiating')
         ).first()
         
         result['ad_requests'] = {
             'total': ad_request_stats.total_requests,
             'pending': ad_request_stats.pending,
             'accepted': ad_request_stats.accepted,
             'rejected': ad_request_stats.rejected,
             'negotiating': ad_request_stats.negotiating
         }
         
         # Calculate conversion rate
         if ad_request_stats.total_requests > 0:
             conversion_rate = (ad_request_stats.accepted / ad_request_stats.total_requests) * 100
             result['ad_requests']['conversion_rate'] = round(conversion_rate, 2)
         else:
             result['ad_requests']['conversion_rate'] = 0
         
         # Payment statistics
         payment_stats = db.session.query(
             func.sum(Payment.amount).label('total_payments'),
             func.sum(Payment.platform_fee).label('total_fees'),
             func.count(Payment.id).label('payment_count')
         ).first()
         
         result['payments'] = {
             'total_amount': float(payment_stats.total_payments or 0),
             'total_fees': float(payment_stats.total_fees or 0),
             'count': payment_stats.payment_count,
             'total_amount_formatted': format_currency(float(payment_stats.total_payments or 0)),
             'total_fees_formatted': format_currency(float(payment_stats.total_fees or 0))
         }
         
         # Calculate average payment amount
         if payment_stats.payment_count > 0:
             avg_payment = payment_stats.total_payments / payment_stats.payment_count
             result['payments']['avg_payment'] = round(float(avg_payment), 2)
             result['payments']['avg_payment_formatted'] = format_currency(result['payments']['avg_payment'])
         else:
             result['payments']['avg_payment'] = 0
             result['payments']['avg_payment_formatted'] = format_currency(0)
         
         # Recent activity (last 24 hours)
         yesterday = datetime.utcnow() - timedelta(days=1)
         
         recent_users = db.session.query(func.count(User.id)).filter(
             User.created_at >= yesterday
         ).scalar()
         
         recent_campaigns = db.session.query(func.count(Campaign.id)).filter(
             Campaign.created_at >= yesterday
         ).scalar()
         
         recent_ad_requests = db.session.query(func.count(AdRequest.id)).filter(
             AdRequest.created_at >= yesterday
         ).scalar()
         
         recent_payments = db.session.query(func.count(Payment.id)).filter(
             Payment.created_at >= yesterday
         ).scalar()
         
         result['recent_activity'] = {
             'new_users': recent_users,
             'new_campaigns': recent_campaigns,
             'new_ad_requests': recent_ad_requests,
             'new_payments': recent_payments
         }
         
         return jsonify(result), 200
     ```
   - Multiple database queries executed for different sections:
     ```sql
     -- User statistics
     SELECT 
         COUNT(id) AS total_users,
         SUM(CASE WHEN role = 'sponsor' THEN 1 ELSE 0 END) AS sponsors,
         SUM(CASE WHEN role = 'influencer' THEN 1 ELSE 0 END) AS influencers,
         SUM(CASE WHEN is_active = TRUE THEN 1 ELSE 0 END) AS active_users,
         SUM(CASE WHEN role = 'sponsor' AND sponsor_approved IS NULL THEN 1 ELSE 0 END) AS pending_sponsors,
         SUM(CASE WHEN role = 'influencer' AND influencer_approved IS NULL THEN 1 ELSE 0 END) AS pending_influencers
     FROM 
         users;
     
     -- New users in last 7 days
     SELECT COUNT(id) FROM users WHERE created_at >= NOW() - INTERVAL '7 days';
     
     -- Campaign statistics
     SELECT 
         COUNT(id) AS total_campaigns,
         SUM(CASE WHEN status = 'active' THEN 1 ELSE 0 END) AS active_campaigns,
         SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) AS completed_campaigns,
         SUM(CASE WHEN visibility = 'public' THEN 1 ELSE 0 END) AS public_campaigns,
         SUM(CASE WHEN visibility = 'public' AND status = 'active' THEN 1 ELSE 0 END) AS public_active_campaigns
     FROM 
         campaigns;
     
     -- Average campaign budget
     SELECT AVG(budget) AS avg_budget FROM campaigns;
     
     -- Ad request statistics
     SELECT 
         COUNT(id) AS total_requests,
         SUM(CASE WHEN status = 'Pending' THEN 1 ELSE 0 END) AS pending,
         SUM(CASE WHEN status = 'Accepted' THEN 1 ELSE 0 END) AS accepted,
         SUM(CASE WHEN status = 'Rejected' THEN 1 ELSE 0 END) AS rejected,
         SUM(CASE WHEN status = 'Negotiating' THEN 1 ELSE 0 END) AS negotiating
     FROM 
         ad_requests;
     
     -- Payment statistics
     SELECT 
         SUM(amount) AS total_payments,
         SUM(platform_fee) AS total_fees,
         COUNT(id) AS payment_count
     FROM 
         payments;
     
     -- Recent activity (last 24 hours)
     SELECT COUNT(id) FROM users WHERE created_at >= NOW() - INTERVAL '1 day';
     SELECT COUNT(id) FROM campaigns WHERE created_at >= NOW() - INTERVAL '1 day';
     SELECT COUNT(id) FROM ad_requests WHERE created_at >= NOW() - INTERVAL '1 day';
     SELECT COUNT(id) FROM payments WHERE created_at >= NOW() - INTERVAL '1 day';
     ```
   - Results cached in Redis for 120 seconds:
     ```python
     @cache.cached(timeout=120)  # Cache for 2 minutes
     ```
   - Comprehensive response returned to frontend:
     ```json
     {
       "users": {
         "total": 538,
         "sponsors": 187,
         "influencers": 348,
         "active": 512,
         "pending_sponsors": 12,
         "pending_influencers": 24,
         "new_last_7_days": 42
       },
       "campaigns": {
         "total": 256,
         "active": 142,
         "completed": 98,
         "public": 178,
         "public_active": 120,
         "avg_budget": 35250.75,
         "avg_budget_formatted": "₹35,250.75"
       },
       "ad_requests": {
         "total": 371,
         "pending": 52,
         "accepted": 187,
         "rejected": 94,
         "negotiating": 38,
         "conversion_rate": 50.40
       },
       "payments": {
         "total_amount": 5640000.0,
         "total_fees": 56400.0,
         "count": 187,
         "total_amount_formatted": "₹5,640,000.00",
         "total_fees_formatted": "₹56,400.00",
         "avg_payment": 30160.43,
         "avg_payment_formatted": "₹30,160.43"
       },
       "recent_activity": {
         "new_users": 8,
         "new_campaigns": 5,
         "new_ad_requests": 13,
         "new_payments": 4
       }
     }
     ```
   - Frontend renders various charts, cards, and metrics displays
   - Dashboard provides a single view of platform health

2. **User Growth Analysis:**
   - Frontend requests time-series data:
     ```javascript
     const fetchUserGrowthData = async () => {
       try {
         loading.value = true
         const response = await axios.get('/api/charts/user-growth', {
           params: {
             period: selectedPeriod.value, // 'month', 'quarter', 'year'
             role: selectedRole.value      // 'all', 'sponsor', 'influencer'
           }
         })
         chartData.value = response.data
       } catch (err) {
         error.value = 'Failed to load growth data'
         console.error(err)
       } finally {
         loading.value = false
       }
     }
     ```
   - API request with parameters:
     ```
     GET /api/charts/user-growth?period=month&role=all
     Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
     ```
   - Backend performs time-based aggregation:
     ```python
     @app.route('/api/charts/user-growth', methods=['GET'])
     @jwt_required()
     @admin_required
     @cache.cached(timeout=300, query_string=True)  # Cache for 5 minutes, vary by query parameters
     def chart_user_growth():
         # Get query parameters
         period = request.args.get('period', 'month')
         role = request.args.get('role', 'all')
         
         # Determine time format and grouping based on period
         if period == 'month':
             # Last 30 days, grouped by day
             start_date = datetime.utcnow() - timedelta(days=30)
             date_format = '%Y-%m-%d'
             date_extract = func.date(User.created_at)
             date_trunc = func.date_trunc('day', User.created_at)
         elif period == 'quarter':
             # Last 90 days, grouped by week
             start_date = datetime.utcnow() - timedelta(days=90)
             date_format = '%Y-%U'  # Year and week number
             date_extract = func.strftime('%Y-%U', User.created_at)
             date_trunc = func.date_trunc('week', User.created_at)
         elif period == 'year':
             # Last 365 days, grouped by month
             start_date = datetime.utcnow() - timedelta(days=365)
             date_format = '%Y-%m'
             date_extract = func.strftime('%Y-%m', User.created_at)
             date_trunc = func.date_trunc('month', User.created_at)
         else:
             # Default to monthly view
             start_date = datetime.utcnow() - timedelta(days=30)
             date_format = '%Y-%m-%d'
             date_extract = func.date(User.created_at)
             date_trunc = func.date_trunc('day', User.created_at)
         
         # Build base query
         query = db.session.query(
             date_trunc.label('date'),
             func.count(User.id).label('count')
         ).filter(User.created_at >= start_date)
         
         # Apply role filter if specified
         if role != 'all':
             query = query.filter(User.role == role)
         
         # Group by date and order by date
         query = query.group_by(date_trunc).order_by(date_trunc)
         
         # Execute query
         records = query.all()
         
         # Format the results
         data = []
         for date, count in records:
             data.append({
                 'date': date.strftime(date_format) if hasattr(date, 'strftime') else date,
                 'count': count
             })
         
         # Get cumulative data by calculating running total
         cumulative_data = []
         running_total = 0
         for item in data:
             running_total += item['count']
             cumulative_data.append({
                 'date': item['date'],
                 'count': running_total
             })
         
         return jsonify({
             'data': data,
             'cumulative': cumulative_data,
             'period': period,
             'role': role
         }), 200
     ```
   - Database query for time-series aggregation:
     ```sql
     -- For monthly view (last 30 days, grouped by day)
     SELECT 
         DATE_TRUNC('day', created_at) AS date,
         COUNT(id) AS count
     FROM 
         users
     WHERE 
         created_at >= NOW() - INTERVAL '30 days'
     GROUP BY 
         DATE_TRUNC('day', created_at)
     ORDER BY 
         date;
     ```
   - Response formatted for visualization libraries:
     ```json
     {
       "data": [
         { "date": "2023-04-22", "count": 3 },
         { "date": "2023-04-23", "count": 5 },
         { "date": "2023-04-24", "count": 8 },
         // ... more daily data points
         { "date": "2023-05-21", "count": 6 }
       ],
       "cumulative": [
         { "date": "2023-04-22", "count": 3 },
         { "date": "2023-04-23", "count": 8 },
         { "date": "2023-04-24", "count": 16 },
         // ... more cumulative data points
         { "date": "2023-05-21", "count": 42 }
       ],
       "period": "month",
       "role": "all"
     }
     ```
   - Frontend renders interactive charts:
     ```javascript
     // Chart rendering with Chart.js
     const renderChart = () => {
       if (!chartData.value) return
       
       const ctx = document.getElementById('userGrowthChart').getContext('2d')
       
       new Chart(ctx, {
         type: 'line',
         data: {
           labels: chartData.value.data.map(item => item.date),
           datasets: [
             {
               label: 'New Users',
               data: chartData.value.data.map(item => item.count),
               backgroundColor: 'rgba(75, 192, 192, 0.2)',
               borderColor: 'rgba(75, 192, 192, 1)',
               borderWidth: 1
             },
             {
               label: 'Total Users',
               data: chartData.value.cumulative.map(item => item.count),
               backgroundColor: 'rgba(153, 102, 255, 0.2)',
               borderColor: 'rgba(153, 102, 255, 1)',
               borderWidth: 1
             }
           ]
         },
         options: {
           responsive: true,
           scales: {
             y: {
               beginAtZero: true
             }
           }
         }
       })
     }
     ```

3. **Data Export:**
   - Admin initiates export from dashboard:
     ```javascript
     const exportUsers = async () => {
       try {
         loading.value = true
         const response = await axios.post('/api/admin/export/users', {
           filters: userFilters.value,
           format: exportFormat.value  // 'csv' or 'json'
         })
         
         exportTaskId.value = response.data.task_id
         exportStatus.value = 'processing'
         
         // Start polling for task completion
         exportPollInterval = setInterval(checkExportStatus, 2000)
       } catch (err) {
         notifications.error('Failed to start export')
         console.error(err)
       } finally {
         loading.value = false
       }
     }
     
     const checkExportStatus = async () => {
       try {
         const response = await axios.get(`/api/admin/tasks/${exportTaskId.value}`)
         
         if (response.data.status === 'completed') {
           clearInterval(exportPollInterval)
           exportStatus.value = 'completed'
           exportFileUrl.value = response.data.file_url
           notifications.success('Export completed successfully')
         } else if (response.data.status === 'failed') {
           clearInterval(exportPollInterval)
           exportStatus.value = 'failed'
           notifications.error(`Export failed: ${response.data.error}`)
         }
         // Otherwise continue polling
       } catch (err) {
         clearInterval(exportPollInterval)
         exportStatus.value = 'failed'
         notifications.error('Failed to check export status')
         console.error(err)
       }
     }
     ```
   - Backend dispatches export task to Celery worker:
     ```python
     @app.route('/api/admin/export/users', methods=['POST'])
     @jwt_required()
     @admin_required
     def export_users():
         # Get request data
         data = request.get_json() or {}
         filters = data.get('filters', {})
         export_format = data.get('format', 'csv')
         
         # Validate format
         if export_format not in ['csv', 'json']:
             return jsonify({'error': 'Invalid export format'}), 400
         
         # Get current user for notification
         current_user_id = get_jwt_identity()
         
         # Start export task in background
         task = export_users_task.delay(
             filters=filters,
             format=export_format,
             user_id=current_user_id
         )
         
         return jsonify({'task_id': task.id, 'status': 'processing'}), 202
     ```
   - Celery worker performs export asynchronously:
     ```python
     @celery.task(name="export_users_task")
     def export_users_task(filters, format='csv', user_id=None):
         """
         Export users based on filters to CSV or JSON
         """
         try:
             # Build query with filters
             query = User.query
             
             if 'role' in filters and filters['role']:
                 query = query.filter(User.role == filters['role'])
             
             if 'status' in filters:
                 if filters['status'] == 'active':
                     query = query.filter(User.is_active == True)
                 elif filters['status'] == 'inactive':
                     query = query.filter(User.is_active == False)
             
             if 'approval' in filters:
                 if filters['approval'] == 'pending':
                     query = query.filter(or_(
                         and_(User.role == 'sponsor', User.sponsor_approved.is_(None)),
                         and_(User.role == 'influencer', User.influencer_approved.is_(None))
                     ))
                 elif filters['approval'] == 'approved':
                     query = query.filter(or_(
                         and_(User.role == 'sponsor', User.sponsor_approved == True),
                         and_(User.role == 'influencer', User.influencer_approved == True)
                     ))
                 elif filters['approval'] == 'rejected':
                     query = query.filter(or_(
                         and_(User.role == 'sponsor', User.sponsor_approved == False),
                         and_(User.role == 'influencer', User.influencer_approved == False)
                     ))
             
             # Execute query
             users = query.all()
             
             # Generate timestamp for filename
             timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
             filename = f"user_export_{timestamp}.{format}"
             filepath = os.path.join(app.config['EXPORT_DIRECTORY'], filename)
             
             # Ensure export directory exists
             os.makedirs(app.config['EXPORT_DIRECTORY'], exist_ok=True)
             
             # Export data in requested format
             if format == 'csv':
                 with open(filepath, 'w', newline='') as csvfile:
                     fieldnames = [
                         'id', 'username', 'email', 'role', 'is_active', 
                         'created_at', 'sponsor_approved', 'influencer_approved',
                         'company_name', 'industry', 'influencer_name', 
                         'category', 'niche', 'reach'
                     ]
                     writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                     writer.writeheader()
                     
     @sponsor_required
     def sponsor_create_campaign():
     ```
   - Invalid or expired tokens rejected with 401/403
   - Role mismatch returns 403 Forbidden

### 2. Campaign Creation to Discovery Flow

1. **Creation to Publication:**
   - Sponsor creates campaign in database
   - When visibility set to "public", campaign becomes searchable
   - Background tasks may index campaign for efficient searching

2. **Discovery Process:**
   - Influencer searches with filters
   - Database query returns matching campaigns
   - Sponsor details joined with campaign data
   - Results displayed in influencer interface

### 3. Negotiation and Agreement Flow

1. **Full Negotiation Cycle:**
   - Initiator creates ad request
   - Recipient responds (accept/reject/counter)
   - Each action logged in negotiation history
   - Status updated with each response
   - Notifications sent to both parties at each step
   - Loop continues until final status (Accepted/Rejected)

2. **Agreement Finalization:**
   - Upon acceptance, status changes to "Accepted"
   - Payment becomes available for sponsor
   - Progress tracking enabled for influencer
   - Contractual terms finalized and stored

### 4. Payment to Delivery Flow

1. **Complete Workflow:**
   - Sponsor initiates payment
   - System calculates platform fee (1%)
   - Payment record created with breakdown
   - Receipt generated for both parties
   - Influencer begins work on deliverables
   - Progress updates submitted with proof
   - Sponsor reviews and provides feedback
   - Cycle continues until all deliverables completed
   - Campaign marked as completed

### 5. Data Analytics Collection

1. **Event Tracking:**
   - User actions stored in respective tables
   - Timestamps captured for time-series analysis
   - Status changes tracked for conversion analysis
   - Financial data recorded for revenue reporting

2. **Report Generation:**
   - Admin dashboard requests aggregated data
   - Complex queries run with appropriate joins
   - Results cached for performance
   - Charts and visualizations rendered in UI

## Security Considerations

1. **Authentication Security:**
   - Password hashing with Werkzeug security
   - JWT tokens with expiration
   - Role-based access control
   - Protection against CSRF attacks

2. **Data Protection:**
   - Input validation on all endpoints
   - SQL injection prevention via ORM
   - XSS protection in frontend
   - Rate limiting for sensitive operations

3. **Financial Security:**
   - Transaction logging for all payments
   - Audit trails for negotiation history
   - Immutable records for completed transactions
   - Secure receipt generation and storage

## Background Processing

1. **Celery Tasks:**
   - Email notifications sent asynchronously
   - Report generation handled in background
   - Campaign status updates automated
   - Long-running operations offloaded from request handlers

2. **Caching Strategy:**
   - Dashboard data cached with Redis
   - Frequently accessed data cached with appropriate timeouts
   - Cache invalidation on relevant data changes
   - Tiered caching for optimized performance

## Deployment Architecture

The application follows a modern web application architecture:

1. **Frontend:**
   - Vue.js SPA served from static assets
   - Compiled with Vite build system
   - Served via Nginx or similar web server
   - Connects to backend API via Axios

2. **Backend:**
   - Flask API server with RESTful endpoints
   - JWT authentication middleware
   - SQLAlchemy ORM for database interactions
   - Celery for asynchronous task processing

3. **Database:**
   - PostgreSQL for production use
   - Well-defined schema with relationships
   - Indexes for query optimization
   - Foreign key constraints for data integrity

4. **Auxiliary Services:**
   - Redis for caching and Celery broker
   - SMTP server for email delivery
   - Object storage for media files (implied)
   - Logging service for error tracking

This architecture provides scalability, maintainability, and separation of concerns, allowing each component to be scaled independently as needed. 