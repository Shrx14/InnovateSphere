# AI Architecture Documentation

## Segment 0.1: AI Pipeline Versioning and Domain Taxonomy

[Previous content for Segment 0.1]

## Segment 1.1: Analytics-First Database Schema

[Previous content for Segment 1.1]

## Segment 1.2: Public vs Authenticated Content Access

### Overview
This segment implements authorization rules and response shaping to provide limited, read-only access to certain content for anonymous users while unlocking richer features for authenticated users. This enforces clear boundaries without duplicating logic and supports performance and cost control.

### Public vs Authenticated Access Rules

#### Anonymous Users (No Authentication Required)
- **Allowed Actions:**
  - View a list of public project ideas via GET /api/public/ideas
  - Search project ideas by keyword and domain
  - View limited idea details via GET /api/ideas/<idea_id> (with requires_login flag)
- **Visible Fields:** id, title, problem_statement, tech_stack, domain name
- **Restrictions:** Cannot see full descriptions, sources, reviews, popularity metrics, or access novelty scoring. Cannot submit reviews or requests.

#### Authenticated Users (JWT Required for Certain Actions)
- **Allowed Actions:**
  - View full project idea details, including sources and reviews
  - Submit idea requests (tracked in idea_requests)
  - Submit reviews (rating + optional comment, one per user per idea)
  - See personalized content filtered by preferred domain
- **Visible Fields:** All idea fields, sources, reviews, average rating, request count

### Rationale for Feature Gating
- **User Experience:** Encourages signups by showing value of full access
- **Performance:** Limits database queries and response sizes for anonymous users
- **Cost Control:** Reduces load on AI-related features for non-paying users
- **Analytics:** Tracks demand through requests and reviews for data-driven improvements

### API Implementation Details

#### GET /api/public/ideas
- No authentication required
- Query parameters: q (keyword search), domain_id (filter by domain)
- Returns limited idea data for public browsing

#### GET /api/ideas/<idea_id>
- Authentication optional
- Returns limited fields + requires_login flag if not authenticated
- Returns full details if authenticated

#### POST /api/ideas/<idea_id>/request
- Authentication required
- Creates entry in idea_requests for demand tracking

#### POST /api/ideas/<idea_id>/review
- Authentication required
- Allows rating (1-5) + optional comment
- Enforces one review per user per idea

### Access Control Enforcement
- Uses @jwt_required() only for routes requiring authentication
- For mixed-access routes, detects authentication gracefully without returning 401 for public access
- All rules are explicit and documented in route code

### Response Shaping
- Helper functions serialize_public_idea() and serialize_full_idea() avoid duplication
- Public responses include requires_login: true and signup encouragement message
- Authenticated responses include computed fields like average_rating and requested_count
