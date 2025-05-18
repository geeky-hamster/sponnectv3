# Sponnect Application - Viva Questions and Answers (Part 1)

## System Architecture & Technologies

### 1. What is the overall architecture of the Sponnect application?
**Answer:** Sponnect follows a modern web application architecture with separate frontend and backend components. The frontend is built with Vue.js as a Single Page Application (SPA), while the backend uses Flask to provide RESTful API endpoints. The application uses a relational database for data storage, Redis for caching and as a message broker, and Celery for asynchronous task processing. This architecture provides scalability, maintainability, and separation of concerns.

### 2. What frontend framework is used in Sponnect and why?
**Answer:** Sponnect uses Vue.js 3 as its frontend framework. Vue.js was chosen for its reactive data-binding capabilities, component-based architecture, and lightweight footprint. It provides good performance while maintaining developer productivity with its intuitive API and comprehensive documentation.

### 3. What backend framework is used in Sponnect and why?
**Answer:** Sponnect uses Flask (Python) for its backend. Flask was chosen because it's a lightweight, flexible microframework that allows for rapid development while providing the necessary tools for building RESTful APIs. It integrates well with SQLAlchemy ORM for database operations and has a simple extension system for additional functionality.

### 4. How does Sponnect handle state management in the frontend?
**Answer:** Sponnect uses Pinia for state management in the Vue.js frontend. Pinia provides a centralized store for managing application state, with support for multiple stores, TypeScript integration, and devtools support. It allows for clean separation of concerns by organizing state, actions, and getters.

### 5. Describe the database approach used in Sponnect.
**Answer:** Sponnect uses a relational database with SQLAlchemy ORM (Object-Relational Mapping) for database interactions. This approach provides structured data storage with proper relationships between entities, transaction support, and data integrity. The application defines models such as User, Campaign, AdRequest, etc., which are mapped to database tables.

### 6. How does Sponnect handle authentication?
**Answer:** Sponnect uses JSON Web Tokens (JWT) for authentication. When a user logs in, the backend validates credentials and generates a JWT with role-based claims. This token is stored in the browser's localStorage and included in the Authorization header of subsequent API requests. Protected routes on the backend verify the JWT and check role permissions through decorators like `@jwt_required()` and `@admin_required`.

### 7. What is the purpose of Redis in the Sponnect architecture?
**Answer:** Redis serves two primary purposes in Sponnect: 
1. As a caching mechanism to improve performance by storing frequently accessed data like dashboard statistics with appropriate timeouts
2. As a message broker for Celery, enabling asynchronous task processing for operations like email sending, report generation, and scheduled jobs

### 8. What role does Celery play in the Sponnect application?
**Answer:** Celery is used for asynchronous task processing in Sponnect. It handles background operations such as:
1. Sending email notifications
2. Generating exportable reports and files
3. Running scheduled tasks (e.g., checking for expired campaigns)
4. Processing long-running operations that shouldn't block the main request-response cycle

### 9. How is the frontend of Sponnect organized?
**Answer:** The frontend is organized into:
1. Views: Page components organized by user role (admin, sponsor, influencer)
2. Components: Reusable UI elements
3. Services: API communication layer using Axios
4. Stores: State management with Pinia
5. Router: Navigation management with Vue Router
6. Utils: Helper functions for common tasks
7. Assets: Static resources like images and CSS

### 10. Explain the role separation in the Sponnect application.
**Answer:** Sponnect has three distinct user roles:
1. **Admin**: Manages users, moderates content, views analytics, and has access to all platform functionalities
2. **Sponsor**: Creates campaigns, searches for influencers, manages ad requests, and processes payments
3. **Influencer**: Discovers campaigns, applies to opportunities, negotiates with sponsors, and delivers content

### 11. What build system does Sponnect use for the frontend?
**Answer:** Sponnect uses Vite as its build system for the frontend. Vite provides fast development server startup through native ES modules, Hot Module Replacement (HMR), and efficient production builds with optimization features like code-splitting and tree-shaking.

### 12. How does the application handle API communication?
**Answer:** Sponnect uses Axios for API communication between the frontend and backend. Axios interceptors are configured to automatically attach JWT tokens to outgoing requests. API services are organized in a dedicated `/services` directory, with separate modules for different entities (users, campaigns, ad requests, etc.) for better maintainability.

### 13. What HTTP methods are used in the Sponnect API and for what purposes?
**Answer:**
- GET: Retrieving data (user profiles, campaigns, ad requests)
- POST: Creating new resources (users, campaigns, payments)
- PUT: Complete updates to existing resources (editing campaigns)
- PATCH: Partial updates (approving users, flagging content)
- DELETE: Removing resources (deleting campaigns)

### 14. How does Sponnect handle file uploads and storage?
**Answer:** While not explicitly detailed in the documentation, Sponnect would typically handle file uploads through multipart form data and store references to file paths in the database. Files would likely be stored in a designated directory or in object storage, with URLs or paths stored in the database for retrieval.

### 15. What caching strategies are used in Sponnect?
**Answer:** Sponnect uses Redis-based caching through Flask-Caching. Specific strategies include:
1. Time-based caching with varying timeouts (e.g., dashboard data cached for 120 seconds)
2. Query-string-based cache keys for parameter-dependent data
3. Selective caching of computationally expensive operations (like aggregate queries)
4. Cache invalidation when underlying data changes

### 16. How is the application deployed?
**Answer:** The application follows a modern deployment approach with:
1. Frontend: Vue.js SPA compiled to static assets served via Nginx or similar web server
2. Backend: Flask API server running with a production WSGI server
3. Database: PostgreSQL for production use
4. Supporting services: Redis for caching/message broker, SMTP for emails
These components can be deployed using containers (Docker) or traditional hosting.

### 17. What design patterns are evident in the Sponnect codebase?
**Answer:**
1. MVC (Model-View-Controller): Separation of data models, views, and controller logic
2. Repository Pattern: Data access abstraction through models
3. Factory Pattern: Creating objects based on conditions (e.g., serializers)
4. Decorator Pattern: Role-based access control through decorators
5. Observer Pattern: Event-based notifications through the system

### 18. How does Sponnect handle errors and exceptions?
**Answer:** Sponnect handles errors through:
1. Global error handler for unhandled exceptions in Flask
2. Try-catch blocks in critical sections
3. HTTP status codes for API responses (400 for bad requests, 404 for not found, etc.)
4. Structured error responses with descriptive messages
5. Client-side error handling in Axios interceptors
6. Logging of errors for debugging and monitoring

### 19. What is the port on which the frontend development server runs?
**Answer:** Based on the provided information, the frontend development server runs on port 5175 (after ports 5173 and 5174 were found to be in use).

### 20. What technologies are used for the database in Sponnect?
**Answer:** Sponnect uses SQLAlchemy ORM with PostgreSQL (in production). SQLAlchemy provides an abstraction layer for database operations, allowing the application to work with Python objects instead of raw SQL. PostgreSQL offers robust features like JSON support, complex queries, and high reliability for production use.

## Database Design & Models

### 21. What are the main entities in the Sponnect database schema?
**Answer:** The main entities in Sponnect's database schema are:
1. Users (with role differentiation)
2. Campaigns
3. Ad Requests
4. Negotiation History
5. Payments
6. Progress Updates

### 22. How is the User model structured to handle different user roles?
**Answer:** The User model contains:
- Core fields for all users (id, username, email, password_hash, role, is_active)
- Role-specific fields:
  - Sponsor fields: company_name, industry, sponsor_approved
  - Influencer fields: influencer_name, category, niche, reach, influencer_approved
- A 'role' field that specifies the user type ('sponsor', 'influencer', or 'admin')
This allows a single table to handle all users while accommodating role-specific data.

### 23. Describe the relationships between Campaign and User models.
**Answer:** Campaigns have a many-to-one relationship with Users (sponsors). Each campaign is created by a single sponsor (user with role='sponsor'), indicated by the sponsor_id foreign key in the Campaign model. The User model has a one-to-many relationship with Campaigns, represented by the campaigns relationship attribute that returns all campaigns created by a particular sponsor.

### 24. Explain the AdRequest model and its relationships.
**Answer:** The AdRequest model connects sponsors (through campaigns) with influencers. It contains:
- campaign_id: Foreign key to the Campaign model
- influencer_id: Foreign key to the User model (target influencer)
- initiator_id: Foreign key to the User model (who created the request)
- Negotiation details: payment_amount, requirements, message, status
- Tracking fields: created_at, updated_at, last_offer_by
AdRequest has relationships with Campaign (many-to-one) and User (many-to-one for both influencer and initiator).

### 25. How does the Payment model relate to AdRequest?
**Answer:** The Payment model has a many-to-one relationship with AdRequest. Each payment is associated with a specific ad request through the ad_request_id foreign key. Multiple payments could theoretically be made for a single ad request, although typically there would be one payment per accepted ad request. The relationship includes cascade deletion, so if an ad request is deleted, associated payments are also removed.

### 26. What indexes are defined on the database tables and why?
**Answer:** Indexes are defined to optimize query performance:
- Users: Indexes on role, email, username for filtering and lookups
- Campaigns: Indexes on sponsor_id, visibility, status for filtering campaigns
- AdRequests: Indexes on campaign_id+influencer_id, status for filtering requests
- Payments: Index on ad_request_id for quick lookups
- NegotiationHistory: Indexes on ad_request_id, user_id for history retrieval
These indexes speed up common queries like finding campaigns by sponsor or filtering ad requests by status.

### 27. How does Sponnect handle data validation at the model level?
**Answer:** Sponnect uses SQLAlchemy validators with the `@validates` decorator to enforce data integrity at the model level. For example:
- Validating that role is one of 'influencer', 'sponsor', or 'admin'
- Ensuring industry values match predefined constants
- Checking category values against allowed lists
These validations prevent invalid data from being stored in the database.

### 28. What is the purpose of the NegotiationHistory model?
**Answer:** The NegotiationHistory model provides an audit trail of all interactions in the negotiation process. It records:
- Each offer, counter-offer, acceptance, or rejection
- Who made the action (user_id and user_role)
- The details of each offer (payment_amount, requirements, message)
- Timestamps for chronological tracking
This history is crucial for dispute resolution, understanding the negotiation process, and providing transparency.

### 29. How does Sponnect track the status of ad requests?
**Answer:** Ad requests are tracked through the status field in the AdRequest model, which can have values like:
- 'Pending': Initial state when created
- 'Negotiating': When counter-offers are being made
- 'Accepted': When both parties agree to terms
- 'Rejected': When either party declines
The last_offer_by field tracks whose turn it is in the negotiation process.

### 30. What is the purpose of the ProgressUpdate model?
**Answer:** The ProgressUpdate model tracks the delivery of content and campaign milestones. It includes:
- Content description of what was delivered
- Media URLs linking to the delivered content
- Metrics data for performance tracking (views, engagement)
- Status field for sponsor approval process
- Feedback field for sponsor comments
- Timestamps for tracking delivery timeline
This model enables influencers to document their work and sponsors to verify completion.

### 31. How are campaign metrics and performance tracked in the database?
**Answer:** Campaign performance is tracked through:
1. Ad request status distribution (counts of pending, accepted, rejected requests)
2. Payment records associated with the campaign
3. Progress updates submitted by influencers
4. Calculated conversion rates (accepted requests / total requests)
These metrics are queried and aggregated through database joins and aggregate functions.

### 32. What foreign key constraints exist in the database schema?
**Answer:** Key foreign key constraints include:
- Campaign.sponsor_id → User.id (campaigns belong to sponsors)
- AdRequest.campaign_id → Campaign.id (requests belong to campaigns)
- AdRequest.influencer_id → User.id (requests target influencers)
- AdRequest.initiator_id → User.id (requests initiated by users)
- Payment.ad_request_id → AdRequest.id (payments for requests)
- NegotiationHistory.ad_request_id → AdRequest.id (history for requests)
- NegotiationHistory.user_id → User.id (history created by users)
- ProgressUpdate.ad_request_id → AdRequest.id (updates for requests)
Some relationships include 'ondelete=CASCADE' to ensure referential integrity.

### 33. How does Sponnect handle timestamps in the database?
**Answer:** Sponnect uses several timestamp fields:
- created_at: When records are created, default=datetime.utcnow()
- updated_at: When records are modified, with onupdate triggers to auto-update
- Specialized timestamps like Payment.created_at for transaction tracking
All timestamps are stored in UTC for consistency, and conversion to local time (IST) happens at the application level before display.

### 34. What unique constraints exist in the database schema?
**Answer:** Key unique constraints include:
- User.username: Ensures unique usernames across the platform
- User.email: Ensures unique email addresses for account security
These constraints prevent duplicate accounts and ensure user identity integrity.

### 35. How does the database schema support the negotiation workflow?
**Answer:** The negotiation workflow is supported by:
1. AdRequest model tracking the current state and latest terms
2. NegotiationHistory model recording each step in the process
3. last_offer_by field indicating whose turn it is to respond
4. status field tracking the progression from Pending → Negotiating → Accepted/Rejected
This structure allows for a complete record of the negotiation process.

### 36. What is the relationship between User and ProgressUpdate models?
**Answer:** There's no direct relationship in the schema, but they're connected through the AdRequest model. Influencers (Users) submit ProgressUpdates for their AdRequests, while sponsors review these updates. The relationship chain is: User → AdRequest → ProgressUpdate.

### 37. How does Sponnect handle soft deletion vs. hard deletion?
**Answer:** Based on the provided schema, Sponnect primarily uses:
- Soft deletion for Users through the is_active Boolean field (deactivation rather than deletion)
- Hard deletion for some resources like campaigns with cascade effects on related records
This approach preserves user data for records and compliance while allowing cleanup of transactional data.

### 38. How are campaign categories managed in the database?
**Answer:** Campaign categories are stored as string values in the Category field of the Campaign model. They're validated against a predefined list of categories (CATEGORIES constant) using the @validates decorator to ensure only valid categories are stored. This approach provides flexibility while maintaining data integrity.

### 39. What is the purpose of the 'is_flagged' field in multiple models?
**Answer:** The is_flagged Boolean field (in Users, Campaigns, AdRequests) allows administrators to mark content that requires review, might violate policies, or needs attention. This enables content moderation by highlighting potentially problematic items without immediately removing them, creating a review workflow for administrators.

### 40. How does the database schema support the payment process?
**Answer:** The payment process is supported through:
1. The Payment model storing transaction details
2. Relationship to AdRequest connecting payment to specific collaborations
3. Fields for amount, platform_fee, and influencer_amount for financial tracking
4. Status field tracking payment progression (Pending → Completed)
5. transaction_id and payment_response fields for external payment gateway integration 