# Sponnect Project Documentation

## 1. Introduction

### 1.1 Company Profile/Institute Profile/Client Profile

SponnectV3 is a sponsorship management platform designed to connect event organizers with potential sponsors.

### 1.2 Abstract

Sponnect is a web-based application that serves as a bridge between event organizers and sponsors. It provides a platform for event organizers to showcase their events and for sponsors to find and support events that align with their marketing objectives.

### 1.3 Existing System and Need for System

**Existing System:**
- Traditional sponsorship acquisition relies on personal connections and cold outreach
- Manual tracking of sponsorship proposals and agreements using spreadsheets and emails
- Limited visibility into available sponsorship opportunities for potential sponsors
- Inefficient negotiation processes conducted through multiple communication channels

**Need for System:**
- Centralize sponsorship management in a single platform
- Increase visibility of events seeking sponsorship
- Streamline the negotiation and agreement process
- Provide analytics and reporting for better decision making

### 1.4 Scope of System

Sponnect aims to provide:
- User management for both event organizers and sponsors
- Event and sponsorship package creation and management
- Discovery platform for sponsors to find relevant events
- Communication tools for negotiation
- Document management for contracts and agreements

### 1.5 Operating Environment- Hardware and Software

**Hardware Requirements:**
- Server: Cloud-based hosting
- Client: Any device with a modern web browser
- Minimum RAM: 4GB for optimal performance

**Software Requirements:**
- Server OS: Linux (Ubuntu)
- Web Server: Nginx/Apache
- Database: SQL (PostgreSQL/MySQL)
- Client OS: Platform independent (accessible via web browsers)
- Supported Browsers: Chrome, Firefox, Safari, Edge (latest versions)

### 1.6 Brief Description of Technology Used

**Frontend:**
- Framework: Vue.js 3
- Build Tool: Vite
- State Management: Pinia
- UI Components: Bootstrap 5
- HTTP Client: Axios
- Routing: Vue Router

**Backend:**
- Framework: Flask (Python)
- Database: SQLAlchemy ORM
- Authentication: Flask-JWT-Extended, Flask-Login
- Email Service: Flask-Mail

## 2. Proposed System

### 2.1 Study of Similar Systems

Several platforms offer aspects of sponsorship management, including:

1. **SponsorPitch**
   - Focus on proposal creation

2. **Sponseasy**
   - Primarily targeted at event organizers

3. **SponsorMyEvent**
   - Marketplace approach

Sponnect aims to provide a comprehensive end-to-end solution with advanced analytics, flexible negotiation tools, and a user-friendly interface.

### 2.2 Feasibility Study

**Technical Feasibility:**
- Modern web technologies can support the required features
- Cloud infrastructure allows for scalability and reliability

**Economic Feasibility:**
- Subscription-based revenue model
- Tiered pricing structure to accommodate different user segments

**Operational Feasibility:**
- User-friendly interface reduces training and adoption barriers
- Automated workflows reduce manual intervention requirements

### 2.3 Objectives of Proposed System

1. Create a centralized platform connecting event organizers with potential sponsors
2. Reduce the time and effort required to secure sponsorships
3. Increase visibility of sponsorship opportunities for both parties
4. Streamline the negotiation process with integrated communication tools
5. Provide analytics to measure ROI for both sponsors and organizers

### 2.4 Users of System

1. **Event Organizers**
   - Create and manage event profiles
   - Define sponsorship packages and opportunities
   - Review sponsor applications
   - Negotiate terms and finalize agreements

2. **Sponsors**
   - Discover relevant sponsorship opportunities
   - Filter events based on criteria
   - Submit sponsorship applications
   - Negotiate terms with event organizers

3. **System Administrators**
   - Manage user accounts and permissions
   - Monitor platform usage and performance
   - Generate system-wide reports

## 3. Analysis and Design

### 3.1 System Requirements

**Functional Requirements:**

1. **User Management**
   - User registration and authentication
   - Profile creation and management
   - Role-based access control
   - Password reset and account recovery

2. **Event Management**
   - Create, edit, and delete event profiles
   - Upload media and documentation
   - Define audience demographics
   - Set event dates and location details

3. **Sponsorship Package Management**
   - Create tiered sponsorship packages
   - Define benefits and deliverables
   - Set pricing and availability
   - Customize package offerings

4. **Discovery and Matching**
   - Search functionality with multiple filters
   - Recommendation engine based on profiles
   - Saved searches and alerts
   - Browse featured and trending events

5. **Communication**
   - In-platform messaging system
   - Notification preferences
   - Email integration
   - Document sharing capabilities

6. **Negotiation**
   - Offer and counter-offer system
   - Status tracking of negotiations
   - Terms and conditions management
   - Digital signature integration

7. **Analytics and Reporting**
   - Performance dashboards
   - Custom report generation
   - Data export capabilities
   - ROI measurement tools

8. **Payment Processing**
   - Secure payment gateway integration
   - Multiple payment methods support
   - Invoice generation

**Non-Functional Requirements:**

1. **Performance**
   - Page load time under 3 seconds
   - Support for concurrent users (up to 1000 initially)
   - Responsive design for all device types
   - Efficient database queries and caching

2. **Security**
   - HTTPS/SSL encryption
   - Data encryption at rest and in transit
   - Regular security audits
   - Compliance with data protection regulations

3. **Reliability**
   - Data backup and disaster recovery
   - Graceful error handling
   - System monitoring and alerting

4. **Scalability**
   - Horizontal and vertical scaling capabilities
   - Database optimization for growing data
   - Load balancing implementation

5. **Usability**
   - Intuitive user interface
   - Consistent design language
   - Accessibility compliance (WCAG 2.1)
   - Multi-language support capability

### 3.2 Entity Relationship Diagram (ERD)

```
[User] 1---* [Event]
[User] 1---* [Sponsor Profile]
[Event] *---* [Sponsorship Package]
[Sponsor Profile] *---* [Sponsorship Application]
[Sponsorship Package] 1---* [Sponsorship Application]
[Sponsorship Application] 1---* [Negotiation]
[Negotiation] 1---1 [Agreement]
[Agreement] 1---* [Payment]
[User] 1---* [Message]
[Message] *---1 [Conversation]
[User] *---* [Notification]
```

The ERD represents the database structure and relationships between entities in the Sponnect system. The key entities include:

- **User**: Core entity that represents both organizers and sponsors
- **Event**: Created by organizers, contains information about events seeking sponsorship
- **Sponsorship Package**: Defined by organizers for specific events, detailing offerings and pricing
- **Sponsorship Application**: Created when a sponsor applies for a specific package
- **Negotiation**: Tracks the negotiation process between sponsors and organizers
- **Agreement**: Represents the final agreed terms between parties
- **Payment**: Tracks payment information related to agreements

Relationships are defined with appropriate cardinality (one-to-many, many-to-many) to ensure proper data modeling and referential integrity.

### 3.3 Table Structure

**Users Table**
| Field | Type | Constraints | Description |
|-------|------|------------|-------------|
| id | INTEGER | PRIMARY KEY | Unique identifier for each user |
| email | VARCHAR(255) | UNIQUE, NOT NULL | User's email address, used for login |
| password_hash | VARCHAR(255) | NOT NULL | Hashed password for security |
| first_name | VARCHAR(100) | NOT NULL | User's first name |
| last_name | VARCHAR(100) | NOT NULL | User's last name |
| user_type | ENUM | NOT NULL (organizer, sponsor, admin) | Type of user account |
| created_at | TIMESTAMP | NOT NULL | When the account was created |
| updated_at | TIMESTAMP | NOT NULL | When the account was last updated |
| last_login | TIMESTAMP | NULL | When the user last logged in |
| is_active | BOOLEAN | DEFAULT TRUE | Whether the account is active |
| profile_image | VARCHAR(255) | NULL | Path to user's profile image |

**Events Table**
| Field | Type | Constraints | Description |
|-------|------|------------|-------------|
| id | INTEGER | PRIMARY KEY | Unique identifier for each event |
| organizer_id | INTEGER | FOREIGN KEY (users.id) | Reference to the event creator |
| title | VARCHAR(255) | NOT NULL | Event title |
| description | TEXT | NOT NULL | Detailed description of the event |
| start_date | DATE | NOT NULL | When the event starts |
| end_date | DATE | NOT NULL | When the event ends |
| location | VARCHAR(255) | NOT NULL | Where the event will take place |
| attendee_count | INTEGER | NULL | Expected number of attendees |
| category | VARCHAR(100) | NOT NULL | Event category (e.g., conference, concert) |
| status | ENUM | NOT NULL (draft, published, completed) | Current status of the event |
| created_at | TIMESTAMP | NOT NULL | When the event was created |
| updated_at | TIMESTAMP | NOT NULL | When the event was last updated |
| cover_image | VARCHAR(255) | NULL | Path to event cover image |
| website | VARCHAR(255) | NULL | Event website URL |

**Sponsorship Packages Table**
| Field | Type | Constraints | Description |
|-------|------|------------|-------------|
| id | INTEGER | PRIMARY KEY | Unique identifier for each package |
| event_id | INTEGER | FOREIGN KEY (events.id) | Reference to associated event |
| name | VARCHAR(100) | NOT NULL | Package name (e.g., Gold, Silver) |
| description | TEXT | NOT NULL | Package description |
| price | DECIMAL | NOT NULL | Base price of the package |
| benefits | TEXT | NOT NULL | List of benefits included |
| availability | INTEGER | NOT NULL | Number of packages available |
| is_negotiable | BOOLEAN | DEFAULT TRUE | Whether price is negotiable |
| created_at | TIMESTAMP | NOT NULL | When the package was created |
| updated_at | TIMESTAMP | NOT NULL | When the package was last updated |

**Sponsorship Applications Table**
| Field | Type | Constraints | Description |
|-------|------|------------|-------------|
| id | INTEGER | PRIMARY KEY | Unique identifier for each application |
| sponsor_id | INTEGER | FOREIGN KEY (users.id) | Reference to applying sponsor |
| package_id | INTEGER | FOREIGN KEY (sponsorship_packages.id) | Reference to package applied for |
| status | ENUM | NOT NULL (pending, approved, rejected, negotiating) | Current status of application |
| message | TEXT | NULL | Optional message from sponsor |
| created_at | TIMESTAMP | NOT NULL | When the application was submitted |
| updated_at | TIMESTAMP | NOT NULL | When the application was last updated |

**Negotiations Table**
| Field | Type | Constraints | Description |
|-------|------|------------|-------------|
| id | INTEGER | PRIMARY KEY | Unique identifier for each negotiation |
| application_id | INTEGER | FOREIGN KEY (sponsorship_applications.id) | Reference to the application |
| current_offer | DECIMAL | NOT NULL | Current offer amount |
| status | ENUM | NOT NULL (pending, accepted, rejected, countered) | Current status of negotiation |
| initiated_by | INTEGER | FOREIGN KEY (users.id) | User who initiated negotiation |
| terms | TEXT | NULL | Additional terms being negotiated |
| created_at | TIMESTAMP | NOT NULL | When negotiation started |
| updated_at | TIMESTAMP | NOT NULL | When negotiation was last updated |
| expires_at | TIMESTAMP | NULL | When offer expires |

**Messages Table**
| Field | Type | Constraints | Description |
|-------|------|------------|-------------|
| id | INTEGER | PRIMARY KEY | Unique identifier for each message |
| sender_id | INTEGER | FOREIGN KEY (users.id) | User who sent the message |
| conversation_id | INTEGER | FOREIGN KEY (conversations.id) | Conversation the message belongs to |
| content | TEXT | NOT NULL | Message content |
| created_at | TIMESTAMP | NOT NULL | When message was sent |
| is_read | BOOLEAN | DEFAULT FALSE | Whether message has been read |

**Conversations Table**
| Field | Type | Constraints | Description |
|-------|------|------------|-------------|
| id | INTEGER | PRIMARY KEY | Unique identifier for each conversation |
| title | VARCHAR(255) | NULL | Optional conversation title |
| created_at | TIMESTAMP | NOT NULL | When conversation started |

**Conversation Participants Table**
| Field | Type | Constraints | Description |
|-------|------|------------|-------------|
| id | INTEGER | PRIMARY KEY | Unique identifier for each entry |
| conversation_id | INTEGER | FOREIGN KEY (conversations.id) | Reference to conversation |
| user_id | INTEGER | FOREIGN KEY (users.id) | Reference to participant |

**Notifications Table**
| Field | Type | Constraints | Description |
|-------|------|------------|-------------|
| id | INTEGER | PRIMARY KEY | Unique identifier for each notification |
| user_id | INTEGER | FOREIGN KEY (users.id) | User receiving notification |
| title | VARCHAR(255) | NOT NULL | Notification title |
| message | TEXT | NOT NULL | Notification content |
| type | VARCHAR(50) | NOT NULL | Type of notification |
| reference_id | INTEGER | NULL | ID of referenced entity |
| is_read | BOOLEAN | DEFAULT FALSE | Whether notification has been read |
| created_at | TIMESTAMP | NOT NULL | When notification was created |

### 3.4 Use Case Diagrams

**User Authentication Use Case**
```
+-------------------+
|                   |
|  [User]           |
|                   |
+--------+----------+
         |
         |
         v
+-------------------+
|                   |
|  Register         |
|                   |
+-------------------+
         |
         |
         v
+-------------------+
|                   |
|  Login            |
|                   |
+-------------------+
         |
         |
         v
+-------------------+
|                   |
|  Reset Password   |
|                   |
+-------------------+
```

**Event Management Use Case**
```
+-------------------+
|                   |
|  [Organizer]      |
|                   |
+--------+----------+
         |
         |
         v
+-------------------+
|                   |
|  Create Event     |
|                   |
+-------------------+
         |
         |
         v
+-------------------+
|                   |
|  Manage Packages  |
|                   |
+-------------------+
         |
         |
         v
+-------------------+
|                   |
|  Review Apps      |
|                   |
+-------------------+
         |
         |
         v
+-------------------+
|                   |
|  Negotiate Terms  |
|                   |
+-------------------+
```

**Sponsorship Application Use Case**
```
+-------------------+
|                   |
|  [Sponsor]        |
|                   |
+--------+----------+
         |
         |
         v
+-------------------+
|                   |
|  Browse Events    |
|                   |
+-------------------+
         |
         |
         v
+-------------------+
|                   |
|  View Packages    |
|                   |
+-------------------+
         |
         |
         v
+-------------------+
|                   |
|  Apply for        |
|  Sponsorship      |
|                   |
+-------------------+
         |
         |
         v
+-------------------+
|                   |
|  Negotiate Terms  |
|                   |
+-------------------+
```

### 3.5 Class Diagram

```
+----------------+       +----------------+       +---------------+
| User           |       | Event          |       | Package       |
+----------------+       +----------------+       +---------------+
| -id            |       | -id            |       | -id           |
| -email         |       | -title         |       | -name         |
| -password      |1     *| -description   |1     *| -price        |
| -firstName     +-------+ -startDate     +-------+ -benefits     |
| -lastName      |       | -endDate       |       | -availability |
| -userType      |       | -location      |       +---------------+
+-------+--------+       +----------------+               |
        |                                                 |
        |                                                 |
+-------v--------+       +----------------+       +-------v-------+
| Organizer      |       | Sponsor        |       | Application   |
+----------------+       +----------------+       +---------------+
| -events        |       | -applications  |       | -sponsor      |
| -createEvent() |       | -apply()       |       | -package      |
| -manageEvent() |       | -negotiate()   |       | -status       |
+----------------+       +----------------+       | -messages     |
                                                 +---------------+
                                                        |
                                                        |
                                               +--------v--------+
                                               | Negotiation     |
                                               +----------------+
                                               | -application   |
                                               | -currentOffer  |
                                               | -status        |
                                               | -terms         |
                                               | -counterOffer()|
                                               | -accept()      |
                                               | -reject()      |
                                               +----------------+
```

**Description:**

The class diagram illustrates the object-oriented structure of the Sponnect system. Key classes include:

1. **User**: Base class containing common attributes for all user types
   - Attributes: id, email, password, firstName, lastName, userType
   - Subclasses: Organizer, Sponsor
   
2. **Organizer**: Specialized user that creates and manages events
   - Attributes: events (collection of events created)
   - Methods: createEvent(), manageEvent()
   
3. **Sponsor**: Specialized user that applies for sponsorships
   - Attributes: applications (collection of submitted applications)
   - Methods: apply(), negotiate()

4. **Event**: Represents an event created by an organizer
   - Attributes: id, title, description, startDate, endDate, location
   - Relationships: belongs to one Organizer, has many Packages

5. **Package**: Represents a sponsorship package for an event
   - Attributes: id, name, price, benefits, availability
   - Relationships: belongs to one Event, has many Applications

6. **Application**: Represents a sponsor's application for a package
   - Attributes: sponsor, package, status, messages
   - Relationships: belongs to one Sponsor, belongs to one Package, has many Negotiations

7. **Negotiation**: Represents the negotiation process for an application
   - Attributes: application, currentOffer, status, terms
   - Methods: counterOffer(), accept(), reject()

The diagram shows the relationships between classes with appropriate cardinality, highlighting one-to-many relationships between User and Event, Event and Package, and Package and Application.

### 3.6 Activity Diagram

**Sponsorship Negotiation Activity Diagram**
```
[Start] --> (Sponsor views package)
       --> (Sponsor applies for sponsorship)
       --> (Organizer reviews application)
       --> <Decision: Accept?>
       --> [Yes] --> (Send standard agreement)
                 --> (Process payment)
                 --> (Finalize sponsorship)
                 --> [End]
       --> [No] --> <Decision: Negotiate?>
                --> [Yes] --> (Make counter offer)
                          --> (Sponsor reviews)
                          --> <Decision: Accept?>
                          --> [Loop back to negotiation]
                --> [No] --> (Reject application)
                         --> [End]
```

**Description:**

This activity diagram illustrates the sponsorship negotiation process within the Sponnect platform. The process begins when a sponsor views a sponsorship package for an event and decides to apply. After the application is submitted, the event organizer reviews it and makes one of three decisions:

1. **Accept the application as-is**: This leads to sending a standard agreement, processing payment, and finalizing the sponsorship.

2. **Negotiate terms**: If the organizer wishes to modify terms, they make a counter-offer which the sponsor can either accept (moving to agreement stage) or counter (continuing negotiation). This negotiation loop can continue until both parties reach agreement or one party abandons negotiations.

3. **Reject the application**: If the organizer decides the sponsor is not a good fit, they can reject the application outright, ending the process.

The diagram shows decision points with alternative flows and includes a loop for the negotiation process, reflecting real-world back-and-forth negotiation that may occur multiple times before resolution.

### 3.7 Deployment Diagram

```
+------------------+        +------------------+
| Client Device    |        | Load Balancer    |
|                  |        |                  |
| - Web Browser    +------->+ - NGINX         |
+------------------+        +--------+---------+
                                     |
                                     v
+------------------+        +------------------+
| CDN              |        | Web Server       |
|                  |<-------+                  |
| - Static Assets  |        | - Flask App      |
+------------------+        +--------+---------+
                                     |
                   +--------+--------+--------+
                   |                 |        |
                   v                 v        v
        +----------+---+    +--------+--+    +------------+
        | Database     |    | Cache     |    | Message    |
        |              |    |           |    | Queue      |
        | - PostgreSQL |    | - Redis   |    | - Celery   |
        +--------------+    +-----------+    +------------+
```

**Description:**

This deployment diagram illustrates the physical architecture of the Sponnect platform. The system uses a modern, scalable architecture with the following components:

1. **Client Device**: End user devices (desktops, laptops, tablets, mobile phones) accessing the application through web browsers.

2. **Load Balancer (NGINX)**: Distributes incoming traffic across multiple web server instances to ensure high availability and reliability.

3. **CDN (Content Delivery Network)**: Hosts and serves static assets (images, JavaScript, CSS) from edge locations to reduce load times for users worldwide.

4. **Web Server**: Hosts the Flask application that handles HTTP requests and business logic.

5. **Database (PostgreSQL)**: Stores all application data in a relational database management system.

6. **Cache (Redis)**: Provides high-performance caching to reduce database load and improve response times for frequently accessed data.

7. **Message Queue (Celery)**: Handles asynchronous task processing for operations like email sending, notifications, and report generation.

The components are connected through secure network channels, with the load balancer serving as the entry point to the system. This architecture supports horizontal scaling by adding more instances of web servers as user load increases.

### 3.8 Module Hierarchy Diagram

```
[Core Application]
    |
    |--- [User Management]
    |      |--- Registration
    |      |--- Authentication
    |      |--- Profile Management
    |      |--- Permissions
    |
    |--- [Event Management]
    |      |--- Creation
    |      |--- Editing
    |      |--- Media Management
    |      |--- Analytics
    |
    |--- [Sponsorship Management]
    |      |--- Package Creation
    |      |--- Application Processing
    |      |--- Negotiation
    |      |--- Agreements
    |
    |--- [Communication]
    |      |--- Messaging
    |      |--- Notifications
    |      |--- Alerts
    |
    |--- [Payment Processing]
    |      |--- Gateways
    |      |--- Invoicing
    |
    |--- [Analytics & Reporting]
           |--- Dashboards
           |--- Data Export
```

**Description:**

The module hierarchy diagram illustrates the logical organization of the Sponnect platform's functionality. The system is structured into six primary modules, each containing related sub-modules:

1. **User Management**: Handles user accounts, authentication, and authorization, including registration, login, profile management, and role-based permissions.

2. **Event Management**: Manages the creation and management of events, including creation, editing, media attachment, and analytics for event performance.

3. **Sponsorship Management**: Facilitates the core sponsorship process, including package creation, application processing, negotiation workflows, and final agreements.

4. **Communication**: Enables interaction between users through messaging, notifications, and alerts systems.

5. **Payment Processing**: Handles financial transactions through payment gateway integration and invoicing functionality.

6. **Analytics & Reporting**: Provides insights through customizable dashboards and data export capabilities.

This modular architecture promotes separation of concerns, making the system easier to develop, test, and maintain. Each module can be developed independently while maintaining clear interfaces with other modules.

### 3.9 Database Schema Diagram

```
┌───────────────┐     ┌───────────────┐     ┌───────────────┐
│ Users         │     │ Events        │     │ Packages      │
├───────────────┤     ├───────────────┤     ├───────────────┤
│ PK id         │     │ PK id         │     │ PK id         │
│ email         │     │ FK organizer_id│────┼─│ FK event_id   │
│ password_hash │     │ title         │     │ name          │
│ first_name    │     │ description   │     │ description   │
│ last_name     │     │ start_date    │     │ price         │
│ user_type     │     │ end_date      │     │ benefits      │
│ created_at    │     │ location      │     │ availability  │
│ updated_at    │     │ attendee_count│     │ is_negotiable │
│ last_login    │     │ category      │     │ created_at    │
│ is_active     │     │ status        │     │ created_at    │
│ profile_image │     │ created_at    │     └───────┬───────┘
└───────┬───────┘     │ updated_at    │             │
        │             │ cover_image   │             │
        │             │ website       │             │
        │             └───────┬───────┘             │
        │                     │                     │
┌───────┴───────┐     ┌───────┴───────┐     ┌───────┴───────┐
│ Applications  │     │ Negotiations  │     │ Agreements    │
├───────────────┤     ├───────────────┤     ├───────────────┤
│ PK id         │     │ PK id         │     │ PK id         │
│ FK sponsor_id │─────│ FK app_id     │─────│ FK neg_id     │
│ FK package_id │     │ current_offer │     │ document_url  │
│ status        │     │ status        │     │ signed_date   │
│ message       │     │ initiated_by  │     │ start_date    │
│ created_at    │     │ terms         │     │ end_date      │
│ updated_at    │     │ created_at    │     │ status        │
└───────────────┘     │ updated_at    │     └───────────────┘
                      │ expires_at    │
                      └───────────────┘
```

**Description:**

This database schema diagram shows the primary tables in the Sponnect system and their relationships. The schema follows a normalized relational database design with proper foreign key relationships:

1. **Users table**: Central storage for all user accounts (organizers, sponsors, administrators)
2. **Events table**: Stores event information created by organizers
3. **Packages table**: Contains sponsorship packages associated with events
4. **Applications table**: Records sponsorship applications from sponsors for specific packages
5. **Negotiations table**: Tracks the negotiation process for sponsorship applications
6. **Agreements table**: Stores finalized agreements resulting from successful negotiations

The relationships between tables maintain referential integrity through foreign keys:
- Events reference their creator through organizer_id
- Packages reference their associated event through event_id
- Applications reference both the sponsor (user) and the package
- Negotiations reference the application they're associated with
- Agreements reference the negotiation that led to them

This schema supports the complete sponsorship lifecycle from event creation through package definition, application, negotiation, and final agreement.

## 4. Coding

[This section would contain detailed implementation code once development begins]

## 5. Testing

[This section would be completed once the system is developed and ready for testing]

## 6. Limitations of Proposed System

[This section would be completed after system implementation]

## 7. Proposed Enhancements

[This section would be completed after initial system implementation]

## 8. Conclusion

[This section would be completed after system implementation]

## 9. Bibliography

[References would be added here]

## 10. Publication/Competition certificates

[Any certificates would be added here if applicable]

## 11. Appendix–Cost sheet, Datasheet

[Cost information would be added here after implementation]

## 12. User Manual

[User manual would be completed after system implementation] 