# 🤖 GITHUB COPILOT AGENT - MEESHO IMAGE OPTIMIZER CONTEXT PROMPT

**Version:** 1.0  
**Date:** January 9, 2026  
**Purpose:** Initial context setup (DO NOT START CODING YET)  
**Next Step:** Incremental build prompts will follow

---

## ⚠️ IMPORTANT: THIS IS CONTEXT ONLY

**This prompt is for context and understanding only.**  
**Do NOT start generating code yet.**  
**We will provide specific build prompts incrementally.**

---

## 📋 PROJECT OVERVIEW

### **What We're Building**
A web application that helps Meesho sellers optimize their product images to reduce shipping costs.

**Problem:** Meesho sellers overpay ₹500-5,000/month on shipping because the platform's AI analyzes product images to estimate weight.

**Solution:** An app that:
1. Accepts product images from sellers
2. Automatically optimizes them (6 techniques)
3. Predicts the shipping cost savings
4. Provides the optimized image for upload to Meesho

### **Business Model**
```
FREE TRIAL:     2 free image optimizations (to prove value)
PRO PLAN:       ₹499/month (unlimited optimizations)
PREMIUM PLAN:   ₹1,499/month (pro features + support)
```

### **Key Success Metric**
**Smooth onboarding → Free trial → Clear ROI → Purchase**

---

## 🎯 USER JOURNEY (CRITICAL)

```
1. LANDING PAGE
   ↓ [Sign Up]
2. EMAIL VERIFICATION
   ↓ [Verify Email]
3. ONBOARDING (NEW - IMPORTANT)
   ├─ Welcome screen ("Start your free trial")
   ├─ Features overview (5 sec read)
   ├─ "Upload your first image"
   ↓
4. FIRST IMAGE UPLOAD (Trial #1)
   ├─ Drag-drop interface
   ├─ Enter weight + category
   ├─ Process image
   ├─ Show BEFORE → AFTER → SAVINGS
   ├─ "Nice! That's trial 1 of 2"
   ↓
5. DASHBOARD
   ├─ Show: "1 free trial remaining"
   ├─ Pricing plans visible
   ├─ CTA: "Upgrade to Pro"
   ↓
6. SECOND IMAGE UPLOAD (Trial #2)
   ├─ Same flow as trial #1
   ├─ After results: "Trial ended! Upgrade to continue"
   ├─ Show pricing
   ↓
7. PAYMENT (Razorpay)
   ├─ Upgrade flow
   ├─ Process payment
   ├─ Subscription active
   ↓
8. UNLIMITED USAGE
   ├─ No limits
   ├─ Full feature access
```

---

## 🏗️ TECHNICAL ARCHITECTURE

### **Frontend (React)**
```
Pages:
├── Landing Page (public)
├── Auth Pages (Signup, Login, Email Verify)
├── Onboarding Page (NEW - post-signup)
├── Dashboard (authenticated)
├── Upload Page (authenticated)
├── Processing Page (authenticated)
├── Results Page (authenticated)
├── Pricing Page (public + authenticated)
└── Settings Page (authenticated)

Components:
├── TrialCounter (shows remaining trials)
├── DragDropZone (upload interface)
├── BeforeAfterComparison (image display)
├── SavingsHighlight (cost display)
├── PricingPlans (subscription options)
└── PaymentModal (Razorpay integration)
```

### **Backend (FastAPI + Python)**
```
Core Functions:
├── User Authentication (JWT)
├── Email Verification (OTP/Link)
├── Trial Management (track 2 free uploads)
├── Image Upload & Storage (AWS S3)
├── Image Optimization (6 techniques)
├── Cost Prediction (Meesho formula)
├── Subscription Management (Razorpay)
└── Usage Tracking (database)

API Endpoints:
├── /api/auth/signup
├── /api/auth/login
├── /api/auth/verify-email
├── /api/images/upload
├── /api/images/history
├── /api/user/trial-status
├── /api/subscriptions/create
├── /api/subscriptions/verify
└── /api/subscriptions/current
```

### **Infrastructure (Azure)**
```
Compute:
├── Azure App Service (FastAPI backend)
├── Azure Container Registry (Docker images)
└── Azure Functions (async processing)

Storage:
├── Azure Blob Storage (images - replaces S3)
├── Azure SQL Database (PostgreSQL)
└── Azure Cache for Redis (sessions)

Services:
├── Azure Key Vault (secrets management)
├── Azure Monitor (logging & monitoring)
├── Azure Application Insights (analytics)
└── Azure DevOps (CI/CD pipeline)

Network:
├── Azure Application Gateway (load balancing)
├── Azure Front Door (CDN + DDoS protection)
└── SSL/TLS certificates (Azure managed)
```

---

## 🔐 SECURITY REQUIREMENTS

### **Authentication & Authorization**
```
✅ JWT tokens (secure, expiring)
✅ Refresh tokens (rotating)
✅ Email verification (prevent spam)
✅ Rate limiting (prevent abuse)
✅ CORS configuration (secure origin)
✅ CSRF protection (form tokens)
✅ SQL injection prevention (parameterized queries)
✅ XSS prevention (input sanitization)
```

### **Data Protection**
```
✅ HTTPS only (all endpoints)
✅ Password hashing (bcrypt, not plain text)
✅ Secrets in environment variables (not code)
✅ Database encryption (Azure managed)
✅ Image encryption (at rest in blob storage)
✅ PII protection (GDPR compliance)
✅ Data access logs (audit trail)
```

### **Payment Security**
```
✅ Razorpay integration (PCI compliant)
✅ No storing card details (Razorpay handles)
✅ Webhook verification (validate signatures)
✅ Transaction logging (for disputes)
✅ Encryption of payment data in transit
```

---

## 📊 ARCHITECTURE PRINCIPLES

### **SOLID Principles**
```
S - Single Responsibility:
  Each class/function does ONE thing
  Example: ImageProcessor only processes images

O - Open/Closed:
  Open for extension, closed for modification
  Use inheritance/composition for new features

L - Liskov Substitution:
  Subtypes must be substitutable for base types
  Example: All payment providers implement IPay interface

I - Interface Segregation:
  Clients depend on specific interfaces, not monolithic ones
  Example: ImageOptimizer interface, separate from validation

D - Dependency Injection:
  Inject dependencies, don't create them in classes
  Example: Pass S3Client to ImageProcessor, not hardcoded
```

### **Design Patterns**
```
Factory Pattern:
  ImageOptimizerFactory creates specific optimizers
  PaymentProviderFactory creates Razorpay client

Strategy Pattern:
  Different optimization strategies (crop, resize, compress)
  Different payment strategies (Razorpay, future PayPal)

Observer Pattern:
  When image processing complete → notify frontend
  When subscription created → update database

Repository Pattern:
  ImageRepository abstracts database queries
  UserRepository handles user data access

Middleware Pattern:
  Authentication middleware
  Error handling middleware
  Logging middleware
  Rate limiting middleware
```

### **System Design Patterns**
```
Microservices Ready:
  Image processing can be extracted to separate service
  Payment handling can be extracted to separate service

Async Processing:
  Use Celery for long-running image optimization
  Don't block HTTP requests

Caching Strategy:
  Cache Meesho cost brackets (rarely change)
  Cache user trial status (check frequently)
  Cache optimization results (5 min TTL)

Error Handling:
  Graceful degradation (if S3 fails, queue for retry)
  Circuit breaker pattern (Razorpay timeout)
  Exponential backoff (retries)
```

---

## 📝 LOGGING & MONITORING

### **Logging Levels**
```
DEBUG:    Development info, variable values
INFO:    Important milestones (user signup, payment success)
WARNING: Recoverable issues (image processing fallback)
ERROR:   Errors that affect functionality
CRITICAL:System failures (database down)
```

### **What to Log**
```
Authentication:
  ✅ User signup attempt (email)
  ✅ Email verification (success/fail)
  ✅ Login attempt (success/fail)
  ✅ JWT token generation/refresh

Images:
  ✅ Image upload (size, format)
  ✅ Optimization started/completed
  ✅ Cost prediction (inputs, output)
  ✅ Download event

Payments:
  ✅ Razorpay order creation
  ✅ Payment webhook received
  ✅ Subscription activation
  ✅ Payment failures (reason)

Errors:
  ✅ Stack traces (full context)
  ✅ User ID (for debugging)
  ✅ Request ID (trace across services)
  ✅ Timestamp (when error occurred)

Performance:
  ✅ Image processing time
  ✅ API response times
  ✅ Database query times
  ✅ S3 upload/download times
```

### **Monitoring Metrics**
```
User Metrics:
  - Total signups
  - Email verified users
  - Trial users
  - Paid users
  - Churn rate

Product Metrics:
  - Images uploaded
  - Avg processing time
  - Avg savings shown
  - Conversion rate (trial → paid)

Technical Metrics:
  - API response times (p50, p95, p99)
  - Error rate (errors/total requests)
  - Database query times
  - S3 operation times
  - Celery task processing times

Business Metrics:
  - MRR (Monthly Recurring Revenue)
  - CAC (Customer Acquisition Cost)
  - LTV (Lifetime Value)
  - Churn rate
```

---

## 🗄️ DATABASE SCHEMA (OVERVIEW)

### **Users Table**
```sql
users:
  id (PK)
  email (UNIQUE)
  password_hash
  name
  email_verified (boolean)
  created_at
  updated_at
```

### **Trial & Subscription Table**
```sql
user_subscriptions:
  id (PK)
  user_id (FK)
  trial_uploads_remaining (int, max 2)
  subscription_tier ('free_trial', 'pro', 'premium')
  razorpay_subscription_id
  renewal_date
  status ('active', 'cancelled', 'expired')
  created_at
  updated_at
```

### **Images Table**
```sql
processed_images:
  id (PK)
  user_id (FK)
  s3_original_url
  s3_optimized_url
  weight_category
  product_category
  current_cost_prediction
  optimized_cost_prediction
  savings
  is_trial (boolean, counts toward trial limit)
  created_at
```

### **Audit Log Table**
```sql
audit_logs:
  id (PK)
  user_id (FK)
  action (upload, payment, login)
  details (JSON)
  ip_address
  user_agent
  created_at
```

---

## 🎯 FEATURE CHECKLIST (PHASED)

### **Phase 1: Core MVP (Week 1-2)**
```
Backend:
  ✅ User authentication (signup/login)
  ✅ Email verification
  ✅ Trial tracking (2 free uploads)
  ✅ Image upload to Azure Blob Storage
  ✅ Image optimization (6 techniques)
  ✅ Cost prediction

Frontend:
  ✅ Landing page
  ✅ Signup/Login pages
  ✅ Email verification page
  ✅ Onboarding page (NEW)
  ✅ Upload page
  ✅ Results page
  ✅ Dashboard (show trial status)
```

### **Phase 2: Payment Integration (Week 2-3)**
```
Backend:
  ✅ Razorpay integration
  ✅ Subscription creation
  ✅ Webhook handling (payment success)
  ✅ Subscription status tracking
  ✅ Usage limits enforcement (trial vs paid)

Frontend:
  ✅ Pricing page
  ✅ Payment modal
  ✅ Subscription confirmation
  ✅ Upgrade CTA (after 2 trials)
  ✅ Plan management page
```

### **Phase 3: Polish & Monitoring (Week 3-4)**
```
Backend:
  ✅ Comprehensive logging
  ✅ Error handling (all edge cases)
  ✅ Rate limiting
  ✅ Request validation
  ✅ Security headers

Frontend:
  ✅ Error messages (user-friendly)
  ✅ Loading states
  ✅ Success confirmations
  ✅ Responsive design (mobile-ready)
  ✅ Accessibility (WCAG 2.1)
```

---

## 💻 TECH STACK DETAILS

### **Frontend**
```
Framework:      React 18
Language:       TypeScript (for type safety)
State:          React Context + Hooks (no Redux - keep simple)
HTTP Client:    Axios (with interceptors for auth)
Routing:        React Router v6
UI Library:     None (custom CSS, keep lightweight)
Form Handling:  React Hook Form (minimal)
Styling:        CSS Modules (scoped, no conflicts)
Icons:          SVG (minimal size)
Build Tool:     Vite (faster than Create React App)
```

### **Backend**
```
Framework:      FastAPI (modern, async, automatic OpenAPI docs)
Language:       Python 3.11+
ORM:            SQLAlchemy (with async support)
Database:       PostgreSQL (via psycopg3 async driver)
Queue:          Celery (async tasks)
Message Broker: Redis
Auth:           FastAPI JWT bearer tokens
Validation:     Pydantic (automatic validation)
Image Proc:     OpenCV + Pillow
Payment:        Razorpay SDK
Email:          SendGrid
Environment:    python-dotenv (not hardcoded)
```

### **Infrastructure (Azure)**
```
Web Server:     Azure App Service (Linux containers)
Database:       Azure Database for PostgreSQL
Blob Storage:   Azure Blob Storage (images)
Cache:          Azure Cache for Redis
Secrets:        Azure Key Vault
Logging:        Azure Monitor + Application Insights
CI/CD:          Azure DevOps Pipelines
Container:      Azure Container Registry
Email Service:  SendGrid (external)
Payments:       Razorpay (external)
```

---

## 🚀 DEPLOYMENT STRATEGY (AZURE)

### **Infrastructure as Code**
```
- Use Azure Resource Manager (ARM) templates OR Terraform
- Version control all infrastructure
- Reproducible deployments across environments
```

### **CI/CD Pipeline (Azure DevOps)**
```
Trigger:        Git push to main branch

Build Stage:
  ✅ Run tests (unit + integration)
  ✅ Code quality checks (SonarQube)
  ✅ Security scanning (SAST)
  ✅ Build Docker image
  ✅ Push to Azure Container Registry

Deploy Stage:
  ✅ Deploy to staging environment
  ✅ Run smoke tests
  ✅ Deploy to production (blue-green)
  ✅ Health checks
  ✅ Rollback on failure
```

### **Environment Management**
```
Development:    Local machine (docker-compose)
Staging:        Azure (same as prod, for testing)
Production:     Azure (high availability setup)

Each environment:
  - Separate database
  - Separate blob storage
  - Separate secrets in Key Vault
  - Separate App Service
```

---

## 🔄 DEVELOPMENT WORKFLOW

### **Git Workflow**
```
Branch naming:
  feature/onboarding-page
  feature/razorpay-integration
  bug/image-processing-crash
  hotfix/payment-webhook

Commit messages:
  feat: Add email verification
  fix: Handle image upload timeout
  refactor: Extract cost prediction to service
  docs: Update API documentation
  test: Add unit tests for optimization

Pull Request Process:
  1. Create PR with clear description
  2. Self-review code first
  3. Request review from team
  4. Address feedback
  5. Run tests (automated)
  6. Merge when approved
```

### **Code Review Checklist**
```
✅ Follows SOLID principles
✅ Error handling for all cases
✅ Logging for debugging
✅ Input validation
✅ No hardcoded values (use env vars)
✅ No security vulnerabilities
✅ Tests included
✅ Documentation updated
✅ No breaking changes without migration
```

---

## 🧪 TESTING STRATEGY

### **Test Types**
```
Unit Tests:       Test individual functions (80% coverage)
Integration Tests: Test API endpoints with database
E2E Tests:        Test complete user journeys
Load Tests:       Test performance under load

Test Framework:
  Backend:  pytest (Python)
  Frontend: Vitest/Jest (JavaScript)
```

### **Test Priority**
```
CRITICAL (100% coverage):
  ✅ Authentication logic
  ✅ Payment processing
  ✅ Trial limit enforcement
  ✅ Image optimization results

HIGH (80% coverage):
  ✅ API endpoints
  ✅ Database operations
  ✅ Error handling

MEDIUM (50% coverage):
  ✅ UI components
  ✅ Form validation
  ✅ Navigation
```

---

## 📱 RESPONSIVE DESIGN

### **Breakpoints**
```
Mobile:    < 640px   (primary: phone users)
Tablet:    640-1024px (secondary: tablet users)
Desktop:   > 1024px  (tertiary: desktop users)

Focus: Mobile first (90% of sellers use phones)
```

---

## 🔄 INCREMENTAL BUILD APPROACH

**Do NOT build everything at once.**

**Instead, build in this order:**

### **Stage 1: Foundation (Days 1-2)**
- Project setup (Azure, Git, Docker)
- Database schema
- Basic API structure

### **Stage 2: Core Features (Days 3-5)**
- User authentication
- Email verification
- Image upload & optimization

### **Stage 3: Trial System (Days 6-7)**
- Trial tracking
- Onboarding flow
- Dashboard

### **Stage 4: Payment (Days 8-10)**
- Razorpay integration
- Subscription creation
- Usage limits

### **Stage 5: Polish (Days 11-14)**
- Error handling
- Logging & monitoring
- Security hardening
- Performance optimization

---

## ⚡ PERFORMANCE TARGETS

```
Image Processing:     < 5 seconds (p95)
API Response Time:    < 200ms (p95)
Page Load Time:       < 2 seconds (p95)
Database Query Time:  < 100ms (p95)

Infrastructure:
- Auto-scale: 2-10 instances
- Availability: 99.9% uptime
- Recovery time: < 5 minutes
```

---

## 📚 DOCUMENTATION TO CREATE

```
README.md:           Setup instructions
ARCHITECTURE.md:     System design overview
API.md:              API endpoint documentation
DEPLOYMENT.md:       Azure deployment guide
TROUBLESHOOTING.md:  Common issues & solutions
SECURITY.md:         Security considerations
```

---

## 🎯 SUCCESS CRITERIA

```
Week 1 (Jan 10-15):
  ✅ Infrastructure ready
  ✅ Auth working
  ✅ Can upload image
  ✅ Can optimize image

Week 2 (Jan 16-22):
  ✅ Trial system working
  ✅ Dashboard shows trial status
  ✅ Razorpay integrated
  ✅ Onboarding flow smooth

Week 3 (Jan 23-29):
  ✅ All pages complete
  ✅ 5 beta testers onboarded
  ✅ Payment processing working
  ✅ Metrics tracking

Week 4 (Jan 30-Feb 8):
  ✅ 10 beta users
  ✅ 2-3 converted to paid
  ✅ Case studies documented
  ✅ Ready for public launch
```

---

## ⚠️ CRITICAL: NEXT STEPS

**THIS IS CONTEXT ONLY. DO NOT CODE YET.**

Once you've reviewed this context, I will provide:

1. **Initial Setup Prompt** - Project structure, dependencies
2. **Phase-by-Phase Build Prompts** - Specific code generation
3. **Incremental Feature Prompts** - One feature at a time

Each prompt will be:
- ✅ Specific (not vague)
- ✅ Stepwise (not all at once)
- ✅ Reference this context
- ✅ Include security/logging
- ✅ Include error handling
- ✅ Include tests

---

## 📋 PROMPT ENGINEERING PRINCIPLES

When I give you building prompts, they will:

1. **Be Specific**: Exactly what to build, not vague requests
2. **Have Context**: Reference this document for principles
3. **Include Constraints**: Code style, patterns, logging
4. **Show Examples**: Expected inputs/outputs
5. **List Acceptance Criteria**: How to know it's done
6. **Request Tests**: Unit tests included
7. **Ask for Logging**: Debug/info/error logging
8. **Include Security**: Input validation, auth checks
9. **Be Incremental**: One feature per prompt, not ten

---

## 🚀 READY FOR NEXT PHASE

**Your GitHub Copilot agent now has:**

✅ Complete context of what you're building  
✅ Architecture understanding  
✅ Design patterns to follow  
✅ Security requirements  
✅ Logging expectations  
✅ Azure deployment details  
✅ Tech stack specifics  
✅ Testing strategy  

**Next action from you:**

When you're ready, ask for:
**"Give me Prompt 1: Initial Project Setup"**

This will include:
- Project structure
- Dependencies setup
- Database configuration
- Environment variables
- Basic folder structure
- Git configuration

---

**Document Version:** 1.0  
**Created:** January 9, 2026  
**Status:** CONTEXT COMPLETE - AWAITING BUILD PROMPTS  

**Ready to start building incrementally? Say: "Let's begin with Prompt 1: Initial Project Setup"** 🚀