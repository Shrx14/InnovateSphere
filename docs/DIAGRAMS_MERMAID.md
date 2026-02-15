# InnovateSphere - Visual Diagrams & System Flows

## 1. HIGH-LEVEL SYSTEM ARCHITECTURE

```mermaid
graph TB
    subgraph Client["🖥️ Client Layer"]
        React["React Frontend<br/>Landing, Dashboard, Admin Panel"]
    end
    
    subgraph Gateway["🚪 API Gateway"]
        Flask["Flask Application<br/>CORS, Rate Limiter, JWT"]
    end
    
    subgraph API["📍 API Routes"]
        Health["Health<br/>Routes"]
        Auth_R["Auth<br/>Routes"]
        Gen["Generation<br/>Routes"]
        Ret["Retrieval<br/>Routes"]
        Nov["Novelty<br/>Routes"]
        Admin_R["Admin<br/>Routes"]
        Ideas["Ideas<br/>Routes"]
        Public["Public<br/>Routes"]
        Analytics_R["Analytics<br/>Routes"]
        Domains_R["Domains<br/>Routes"]
    end
    
    subgraph Services["⚙️ Service Layer"]
        Generator["Generator<br/>Multi-pass<br/>LLM Pipeline"]
        Retrieval["Retrieval<br/>ArXiv+GitHub<br/>Orchestration"]
        Novelty["Novelty<br/>Analyzer<br/>Semantic Scoring"]
        Semantic["Semantic<br/>Embedder<br/>Cache Layer"]
    end
    
    subgraph Storage["💾 Data Layer"]
        DB["PostgreSQL<br/>+ pgvector<br/>Persistent Data"]
        Cache["Cache<br/>Embeddings<br/>LRU 5000"]
    end
    
    subgraph External["🌐 External Services"]
        ArXiv["arXiv API<br/>Academic Papers"]
        GitHub["GitHub API<br/>Repositories"]
        LLM["LLM Backend<br/>Ollama/OpenAI"]
        HF["HuggingFace<br/>Embedding Models"]
    end
    
    React -->|HTTP/REST| Flask
    Flask --> Health
    Flask --> Auth_R
    Flask --> Gen
    Flask --> Ret
    Flask --> Nov
    Flask --> Admin_R
    Flask --> Ideas
    Flask --> Public
    Flask --> Analytics_R
    Flask --> Domains_R
    
    Gen --> Generator
    Ret --> Retrieval
    Nov --> Novelty
    
    Generator --> Retrieval
    Generator --> Semantic
    Generator --> DB
    
    Retrieval --> ArXiv
    Retrieval --> GitHub
    Retrieval --> DB
    
    Novelty --> Semantic
    Novelty --> DB
    
    Semantic --> Cache
    Semantic --> DB
    Semantic --> HF
    
    Generator --> LLM
    Retrieval --> LLM
```

## 2. USER FLOW - IDEA EXPLORATION

```mermaid
graph TD
    Start["👤 User Lands on Site"]
    
    Start -->|Anonymous| Browse["Browse Explore Page"]
    Start -->|Has Account| Login["Login"]
    
    Browse --> Search["Search/Filter Ideas<br/>- Keyword<br/>- Domain"]
    Search --> View["View Idea Card<br/>Limited Details"]
    
    View -->|Wants Full Access| SignUp["Sign Up"]
    View -->|Click Idea| IdeaDetail["View Idea Details<br/>- Full problem statement<br/>- Tech stack<br/>- Sources<br/>- Reviews"]
    
    Login --> Auth["JWT Token Stored"]
    SignUp --> Auth
    
    Auth --> FullAccess["🔓 Access Full Features"]
    FullAccess --> Submit["Submit Review<br/>or Feedback"]
    
    IdeaDetail -->|Authenticated| Review["Leave Review<br/>1-5 Rating + Comment"]
    IdeaDetail -->|Authenticated| Request["Request Idea<br/>Track Demand"]
    
    Review --> DB1["Save Review<br/>Update Quality Score"]
    Request --> DB1
    Submit --> DB1
    
    FullAccess -->|Wants to Create| CreatePage["Go to /user/generate"]
    CreatePage --> CreateIdea["📝 Enter Idea Details<br/>- Problem Description<br/>- Domain Selection<br/>- Parameters"]
```

## 3. USER FLOW - IDEA GENERATION JOURNEY

```mermaid
graph TD
    User["👤 Authenticated User"]
    User -->|Navigate to| GenPage["/user/generate PAGE"]
    
    GenPage --> Input["📝 Input Generation Details<br/>- Subject/Problem Description<br/>- Domain Selection<br/>- Optional: Parameters"]
    
    Input -->|Click Generate| Submit["POST /api/ideas/generate"]
    
    Submit -->|PROCESSING| Phase0["⚙️ PHASE 0: Input Conditioning<br/>- Sanitize query<br/>- Map domain<br/>- Estimate feasibility"]
    
    Phase0 -->|✓ Evidence sufficient?| Phase1["⚙️ PHASE 1: Retrieval<br/>- Search arXiv (papers)<br/>- Search GitHub (repos)<br/>- Deduplicate, rank by relevance<br/>- Apply reputation scores<br/>Min: 3 sources"]
    
    Phase0 -->|✗ Insufficient| Error1["❌ ERROR<br/>Not enough evidence<br/>Try broader query"]
    
    Phase1 -->|Sources collected| Phase2["⚙️ PHASE 2: Landscape Analysis<br/>LLM PASS 1<br/>- Identify gaps<br/>- Detect trends<br/>- Assess saturation"]
    
    Phase2 --> Phase3["⚙️ PHASE 3: Constraint Synthesis<br/>LLM PASS 2-3<br/>- Apply bias rules<br/>- Generate problem statement<br/>- Generate tech stack<br/>- Check rejected patterns<br/>- Apply penalties"]
    
    Phase3 --> Phase4["⚙️ PHASE 4: Evidence Validation<br/>LLM PASS 4<br/>- Map sources to claims<br/>- Validate factual accuracy<br/>- Cross-check feasibility"]
    
    Phase4 --> Scoring["📊 COMPUTE SCORES<br/>- Novelty: Similarity + Temporal + Specificity<br/>- Quality: Feedback + Evidence + Rating<br/>- Penalties applied"]
    
    Scoring --> SaveDB["💾 Save to Database<br/>- ProjectIdea<br/>- IdeaSources<br/>- GenerationTrace"]
    
    SaveDB --> Success["✅ SUCCESS<br/>Idea Generated"]
    
    Success --> Display["📱 User Sees:<br/>- Title<br/>- Novelty Score<br/>- Quality Score<br/>- Full Details<br/>- Sources"]
    
    Display --> Actions["💬 User Can:<br/>- View Full Details<br/>- Submit Review<br/>- Leave Feedback<br/>- Request Idea<br/>- Share/Bookmark"]
    
    Error1 --> AddMore["↩️ User Can:<br/>- Modify query<br/>- Change domain<br/>- Try again"]
    
    AddMore -->|Retry| Submit
```

## 4. AI GENERATION PIPELINE - DETAILED

```mermaid
graph LR
    Query["🔤 User Query<br/>+ Domain"] -->|Condition| P0["📦 PHASE 0<br/>Input Prep"]
    
    P0 -->|Retrieve| P1["🔍 PHASE 1<br/>RETRIEVAL"]
    
    P1 -->|arXiv Search| ArXiv["academic<br/>papers"]
    P1 -->|GitHub Search| GHub["code<br/>repos"]
    
    ArXiv -->|deduplicate<br/>rank| Sources["✓ Top Sources<br/>3-20 results"]
    GHub -->|deduplicate<br/>rank| Sources
    
    Sources -->|Analyze| P2["🧠 LLM PASS 1<br/>LANDSCAPE"]
    
    P2 -->|Problem<br/>Formulation| P3a["🧠 LLM PASS 2<br/>PROBLEM"]
    
    P3a -->|Tech Stack<br/>Generation| P3b["🧠 LLM PASS 3<br/>SYNTHESIS"]
    
    P3b -->|with<br/>Constraints| Constraints["Bias Rules<br/>Admin Verdicts<br/>Domain Rules"]
    
    Constraints -->|constrained| P4["🧠 LLM PASS 4<br/>EVIDENCE"]
    
    P4 -->|validate| Result["✅ Final Idea<br/>Problem + Tech + Sources"]
    
    Result -->|analyze| Novelty["📈 Novelty Score<br/>Similarity + Temporal<br/>+ Specificity"]
    
    Result -->|compute| Quality["📈 Quality Score<br/>Feedback + Evidence<br/>+ Reviews"]
    
    Novelty -->|HITL| Penalties["⚠️ Penalties<br/>Admin feedback<br/>Source reputation"]
    
    Quality -->|HITL| Penalties
    
    Penalties -->|save| DB["💾 Store Idea<br/>+ Trace"]
    
    DB -->|deliver| User["👤 User Receives<br/>Scored Idea"]
```

## 5. NOVELTY SCORING ENGINE

```mermaid
graph TD
    Input["🔤 Idea Description<br/>📂 Domain<br/>📚 Retrieved Sources"]
    
    Input -->|Step 1| Embed["🔗 Semantic Embeddings<br/>- Embed query (384-dim)<br/>- Embed sources (384-dim)<br/>- Use SentenceTransformers"]
    
    Embed -->|Step 2| Sim["📊 Similarity Analysis<br/>- Cosine similarity to all sources<br/>- Compute: mean, variance, min, max<br/>- Signal: mean_similarity"]
    
    Input -->|Step 2| Spec["📊 Specificity Signal<br/>- Parse query keywords<br/>- Count unique terms<br/>- Compare to source diversity<br/>- Signal: 0-100"]
    
    Input -->|Step 2| Temp["📊 Temporal Signal<br/>- Extract publication dates<br/>- Compute recency score<br/>- Penalize if all old<br/>- Signal: 0-100"]
    
    Input -->|Step 2| Sat["📊 Saturation Penalty<br/>- Count similar ideas in domain<br/>- Compare novelty distribution<br/>- Penalty: -5 to -30"]
    
    Sim --> Signals["🎯 SIGNALS BLEND<br/>Similarity + Specificity<br/>+ Temporal - Saturation"]
    
    Spec --> Signals
    Temp --> Signals
    Sat --> Signals
    
    Signals -->|Formula| BaseScore["📈 Base Score = 50<br/>+ (specificity × 0.3)<br/>+ (temporal × 0.2)<br/>- (saturation × 0.5)<br/>Range: 0-100"]
    
    BaseScore -->|Domain| Bonus["🎁 Domain Bonuses<br/>- Trending domain: +5<br/>- Emerging tech: +10<br/>- Hot category: +8"]
    
    Bonus -->|HITL| AdminPenalty["⚠️ Admin HITL Penalties<br/>- Rejection cascade: -20<br/>- Downgrade cascade: -10<br/>- Verdict multiplier"]
    
    AdminPenalty -->|Stability Check| Smooth["🔄 Moving Average<br/>- Compare to recent similar<br/>- Smooth extreme scores<br/>- Determine confidence level"]
    
    Smooth -->|Normalize| Output["✅ Final Score<br/>Novelty: 0-100 (float)<br/>Level: Very Low to Very High<br/>Confidence: High/Medium/Low"]
```

## 6. DATABASE ENTITY RELATIONSHIP

```mermaid
erDiagram
    USERS ||--o{ PROJECT_IDEAS : creates
    USERS ||--o{ IDEA_REQUEST : makes
    USERS ||--o{ IDEA_REVIEW : writes
    USERS ||--o{ IDEA_FEEDBACK : leaves
    USERS ||--o{ ADMIN_VERDICT : issues
    USERS ||--o{ GENERATION_TRACE : generates
    USERS ||--o{ SEARCH_QUERY : searches
    USERS ||--o{ ABUSE_EVENT : triggers
    
    DOMAINS ||--o{ DOMAIN_CATEGORY : has
    DOMAINS ||--o{ PROJECT_IDEAS : categorizes
    
    PROJECT_IDEAS ||--o{ IDEA_SOURCE : retrieved_from
    PROJECT_IDEAS ||--o{ IDEA_REVIEW : receives
    PROJECT_IDEAS ||--o{ IDEA_FEEDBACK : receives
    PROJECT_IDEAS ||--o{ IDEA_VIEW : viewed_in
    PROJECT_IDEAS ||--o{ VIEW_EVENT : tracked_by
    PROJECT_IDEAS ||--o{ ADMIN_VERDICT : receives
    PROJECT_IDEAS ||--o{ GENERATION_TRACE : traced_by
    PROJECT_IDEAS ||--o{ IDEA_REQUEST : requested_for
    
    AI_PIPELINE_VERSION ||--o{ PROJECT_IDEAS : versions
    BIAS_PROFILE ||--o{ GENERATION_TRACE : constrains
    PROMPT_VERSION ||--o{ GENERATION_TRACE : uses

    USERS {
        int id PK
        string email UK
        string password_hash
        string role
        datetime created_at
    }
    
    PROJECT_IDEAS {
        int id PK
        string title
        text problem_statement
        text tech_stack
        int domain_id FK
        string ai_pipeline_version
        boolean is_ai_generated
        boolean is_public
        boolean is_validated
        int quality_score_cached
        int novelty_score_cached
        json novelty_context
        json idea_embedding
        datetime created_at
    }
    
    IDEA_SOURCE {
        int id PK
        int idea_id FK
        string source_type
        string title
        string url UK
        text summary
        date published_date
    }
    
    IDEA_REVIEW {
        int id PK
        int user_id FK
        int idea_id FK
        int rating
        text comment
        datetime created_at
    }
    
    IDEA_FEEDBACK {
        int id PK
        int user_id FK
        int idea_id FK
        string feedback_type
        text comment
        datetime created_at
    }
    
    IDEA_REQUEST {
        int id PK
        int user_id FK
        int idea_id FK
        text request_context
        datetime created_at
    }
    
    ADMIN_VERDICT {
        int id PK
        int idea_id FK
        int admin_id FK
        string verdict
        text reason
        datetime created_at
    }
    
    GENERATION_TRACE {
        int id PK
        int idea_id FK
        int user_id FK
        text query
        string domain_name
        json phase_0_output
        json phase_1_output
        json phase_2_output
        json phase_3_output
        json phase_4_output
        json constraints_active
        int retrieval_time_ms
        int analysis_time_ms
        int generation_time_ms
        datetime created_at
    }
    
    DOMAIN {
        int id PK
        string name UK
    }
    
    DOMAIN_CATEGORY {
        int id PK
        string name
        int domain_id FK
    }
    
    IDEA_VIEW {
        int id PK
        int idea_id FK
        int user_id FK
        datetime viewed_at
    }
    
    VIEW_EVENT {
        int id PK
        int idea_id FK
        int user_id FK
        string event_type
        int duration_ms
        string session_id
        datetime created_at
    }
    
    SEARCH_QUERY {
        int id PK
        int user_id FK
        string query
        string domain
        int results_count
        float duration_ms
        string source
        datetime created_at
    }
    
    ABUSE_EVENT {
        int id PK
        int user_id FK
        string event_type
        string severity
        text description
        json metadata
        datetime created_at
    }
    
    TOKEN_BLOCKLIST {
        int id PK
        string jti UK
        datetime created_at
    }
```

## 7. ADMIN REVIEW & HITL WORKFLOW

```mermaid
graph TD
    Admin["👨‍💼 Admin User"]
    Admin -->|Navigate to| Dashboard["/admin/review"]
    
    Dashboard -->|See| Queue["📋 Review Queue<br/>- Pending ideas<br/>- Flagged ideas<br/>- User feedback count"]
    
    Queue -->|Click Idea| Detail["📄 Idea Detail View<br/>- Full trace (4 phases)<br/>- User feedback breakdown<br/>- Quality metrics<br/>- Novelty analysis"]
    
    Detail -->|Examine| Trace["📊 Generation Trace<br/>- Phase 0: Input prep results<br/>- Phase 1: Retrieved sources<br/>- Phase 2: Landscape analysis<br/>- Phase 3: Constraints applied<br/>- Phase 4: Evidence validation"]
    
    Detail -->|Review| Feedback["💬 User Feedback<br/>- Quality ratings<br/>- Factual errors reported<br/>- Hallucinations flagged<br/>- Novelty assessments"]
    
    Trace -->|Analyze| Decision["🔍 Make Verdict"]
    Feedback -->|Analyze| Decision
    
    Decision -->|Option 1| Validate["✅ VALIDATE<br/>- Mark as validated<br/>- Quality score × 1.2<br/>- Boost reputation"]
    
    Decision -->|Option 2| Downgrade["▼ DOWNGRADE<br/>- Mark as downgraded<br/>- Quality score × 0.8<br/>- Add to warnings"]
    
    Decision -->|Option 3| Reject["❌ REJECT<br/>- Mark as rejected<br/>- Quality score × 0.5<br/>- Hide from public"]
    
    Validate -->|Document| Record["📝 Record Verdict<br/>- Admin ID<br/>- Verdict type<br/>- Reason<br/>- Timestamp"]
    
    Downgrade -->|Document| Record
    Reject -->|Document| Record
    
    Record -->|Cascade| Cascade["🔄 Apply Cascade<br/>- Find similar ideas<br/>- Share source URLs<br/>- Apply proportional penalties<br/>- Update novelty scores"]
    
    Cascade -->|Update| AllAffected["♻️ Update All Related Ideas<br/>- Recompute quality scores<br/>- Adjust novelty context<br/>- Log changes"]
    
    AllAffected -->|View| Analytics["/admin/analytics<br/>- Quality trends<br/>- Novelty distribution<br/>- Domain performance<br/>- User engagement"]
```

## 8. SOURCE RETRIEVAL ORCHESTRATION

```mermaid
graph TD
    Query["🔤 Query + Domain"]
    
    Query -->|Request| Retrieve["🔍 Retrieve Sources"]
    
    Retrieve -->|Parallel| ArXiv1["Search arXiv<br/>- Build query with domain<br/>- Query: all:{text}<br/>- Sort: relevance"]
    
    Retrieve -->|Parallel| GitHub1["Search GitHub<br/>- Build query with domain<br/>- Sort: stars desc<br/>- Per page: max"]
    
    ArXiv1 -->|Parse| ArXiv2["Parse Results<br/>- Extract title, URL<br/>- Get publish date<br/>- Extract summary"]
    
    GitHub1 -->|Parse| GitHub2["Parse Results<br/>- Extract name, URL<br/>- Get star count<br/>- Extract description"]
    
    ArXiv2 -->|Normalize| ArXiv3["Normalize<br/>format: arxiv<br/>type: paper<br/>metadata: published_date"]
    
    GitHub2 -->|Normalize| GitHub3["Normalize<br/>format: github<br/>type: repo<br/>metadata: stars"]
    
    ArXiv3 -->|Merge| All["🔗 Merge & Deduplicate<br/>- Unique by URL<br/>- Combine results<br/>- Tier: tier_1"]
    
    GitHub3 -->|Merge| All
    
    All -->|Reputation| Rep["⭐ Add Reputation<br/>- Query admin feedback<br/>- Add: validated_count<br/>- Add: rejected_count"]
    
    Rep -->|Rank| Rank["📊 Rank Sources<br/>- ArXiv: recent first<br/>- GitHub: stars desc<br/>- Diversify types<br/>- Round-robin selection"]
    
    Rank -->|Filter| Semantic["🔗 Optional: Semantic Filter<br/>- Embed query & sources<br/>- Cosine similarity<br/>- Keep: sim > threshold"]
    
    Semantic -->|Output| Final["✅ Final Sources<br/>Max: 10 results<br/>Sorted by rank<br/>Diverse types"]
```

## 9. API REQUEST FLOW - GENERATION

```mermaid
sequenceDiagram
    actor User as 👤 User
    participant FE as 🖥️ Frontend
    participant API as 🚪 Flask API
    participant Gen as ⚙️ Generator
    participant Ret as 📚 Retrieval
    participant LLM as 🤖 LLM
    participant DB as 💾 Database
    
    User->>FE: Click Generate
    FE->>User: Show Form
    User->>FE: Submit (subject, domain)
    FE->>API: POST /api/ideas/generate
    activate API
    
    API->>API: Validate JWT
    API->>API: Parse & Validate Input
    API->>Gen: generate_idea(subject, domain)
    activate Gen
    
    Gen->>Gen: Phase 0: Input Conditioning
    Gen->>Ret: retrieve_sources(query, domain)
    activate Ret
    
    Ret->>Ret: Search ArXiv
    Ret->>Ret: Search GitHub
    Ret->>Ret: Merge, Deduplicate, Rank
    
    Ret-->>Gen: sources (list)
    deactivate Ret
    
    Gen->>Gen: Check Evidence Gate
    Gen->>LLM: Phase 2 Landscape Analysis
    activate LLM
    LLM-->>Gen: landscape_output (JSON)
    deactivate LLM
    
    Gen->>LLM: Phase 3 Synthesis with Constraints
    activate LLM
    LLM-->>Gen: synthesis_output (JSON)
    deactivate LLM
    
    Gen->>LLM: Phase 4 Evidence Validation
    activate LLM
    LLM-->>Gen: validation_output (JSON)
    deactivate LLM
    
    Gen->>Gen: Novelty Analysis
    Gen->>Gen: Quality Score Calc
    Gen->>Gen: Build Trace Object
    
    Gen->>DB: Save ProjectIdea
    Gen->>DB: Save IdeaSources
    Gen->>DB: Save GenerationTrace
    
    Gen-->>API: idea_id, novelty_score, quality_score
    deactivate Gen
    
    API->>API: Format Response
    API-->>FE: {idea_id, scores...}
    deactivate API
    
    FE->>FE: Show Success
    FE->>User: Display Generated Idea
```

## 10. TECH STACK OVERVIEW

```mermaid
graph TB
    subgraph Frontend["🖥️ FRONTEND"]
        Vite["Vite 7.3"]
        React["React 18.2"]
        Router["React Router v6.22"]
        RadixUI["Radix UI"]
        Charts["Recharts 3.7"]
        Tailwind["Tailwind CSS 3.3"]
        Framer["Framer Motion"]
    end
    
    subgraph Backend["🐍 BACKEND"]
        Flask["Flask 2.3"]
        SQLAlchemy["SQLAlchemy ORM"]
        Pydantic["Pydantic v2"]
        JWT["JWT Auth"]
        Cache["Flask-Caching"]
        Limiter["Flask-Limiter"]
    end
    
    subgraph DB["💾 DATABASE"]
        Postgres["PostgreSQL 13+"]
        PGVector["pgvector"]
    end
    
    subgraph ML["🤖 ML/AI"]
        SentenceT["SentenceTransformers"]
        OpenAISDK["OpenAI SDK 1.0+"]
    end
    
    subgraph LLM["🧠 LLM PROVIDERS"]
        Ollama["Ollama<br/>qwen2.5:7b"]
        OpenAI["OpenAI API<br/>GPT-4o-mini"]
    end
    
    subgraph External["🌐 EXTERNAL APIs"]
        ArXiv["arXiv API"]
        GitHub["GitHub API"]
        HF["HuggingFace Hub"]
    end
    
    subgraph Infra["🐳 INFRASTRUCTURE"]
        Docker["Docker"]
        Compose["Docker Compose"]
        Neon["Neon Cloud"]
    end
    
    React -->|REST| Backend
    Vite -->|Build| React
    
    Flask -->|Query| SQLAlchemy
    SQLAlchemy -->|CRUD| DB
    
    Backend -->|Uses| JWT
    Backend -->|Uses| Cache
    Backend -->|Uses| Limiter
    Backend -->|Validates| Pydantic
    
    Backend -->|Calls| ML
    ML -->|Uses| SentenceT
    ML -->|Uses| OpenAISDK
    
    Backend -->|Calls| LLM
    LLM -->|Routes to| Ollama
    LLM -->|Routes to| OpenAI
    
    Backend -->|Retrieves| External
    
    Docker -->|Containerize| Backend
    Compose -->|Orchestrate| Backend
    Neon -->|Host| Postgres
```

## 11. DEPLOYMENT ARCHITECTURE

```mermaid
graph TB
    subgraph Development["💻 DEVELOPMENT"]
        DevDocker["Docker Compose<br/>Local Stack"]
        LocalDB["PostgreSQL<br/>Local"]
        LocalLLM["Ollama<br/>Local Models"]
    end
    
    subgraph Production["🚀 PRODUCTION"]
        subgraph Frontend["Frontend Hosting"]
        Vercel["Vercel/Netlify<br/>Vite Build"]
        CDN["CDN<br/>Static Assets"]
        end
        
        subgraph Backend["Backend Hosting"]
            Gunicorn["Gunicorn<br/>WSGI Server"]
            Nginx["Nginx<br/>Reverse Proxy"]
            Region["Multi-region<br/>Load Balancer"]
        end
        
        subgraph Database["Database"]
            Neon["Neon Cloud DB<br/>PostgreSQL + pgvector<br/>Auto-backup"]
            Replica["Read Replica<br/>Analytics"]
        end
        
        subgraph LLMProd["LLM Services"]
            OllamaCloud["Ollama Cloud<br/>Deploy"]
            OpenAIProd["OpenAI API<br/>Enterprise Tier"]
        end
    end
    
    subgraph Monitoring["📊 MONITORING"]
        Logs["Logging<br/>CloudWatch/DataDog"]
        Metrics["Metrics<br/>Prometheus"]
        Trace["Tracing<br/>Jaeger"]
    end
    
    DevDocker -->|Develop & Test| Backend
    LocalDB -->|Local Data| Backend
    LocalLLM -->|Local Inference| Backend
    
    Backend -->|Deploy to| Production
    Frontend -->|CDN| Vercel
    Frontend -->|Traffic| CDN
    Gunicorn -->|Behind| Nginx
    Nginx -->|Route| Region
    Region -->|Query| Neon
    Neon -->|Sync| Replica
    Backend -->|Call| LLMProd
    OllamaCloud -->|Inference| Backend
    OpenAIProd -->|API Key| Backend
    
    Backend -->|Logs| Monitoring
    Neon -->|Metrics| Monitoring
```

## 12. QUALITY & NOVELTY SCORE BREAKDOWN

```mermaid
graph TD
    subgraph QualityCalc["📈 QUALITY SCORE CALCULATION"]
        Base["Base: 50"]
        Feedback["Feedback Impact:<br/>- high_quality: +15<br/>- factual_error: -20<br/>- hallucinated_source: -25<br/>- weak_novelty: -15<br/>Cap: ±40"]
        Evidence["Evidence Bonus:<br/>min(sources × 2, 20)"]
        Reviews["Review Rating Bonus:<br/>(avg_rating - 3) × 2<br/>Default: 3 if none"]
        Verdict["Verdict Multiplier:<br/>- validated: ×1.2<br/>- downgraded: ×0.8<br/>- rejected: ×0.5"]
        
        Final["Quality = (Base<br/>+ Feedback<br/>+ Evidence<br/>+ Reviews)<br/>× Verdict"]
        
        Base --> Final
        Feedback --> Final
        Evidence --> Final
        Reviews --> Final
        Verdict --> Final
        
        Final --> Output["Range: 0-100"]
    end
    
    subgraph NoveltyCalc["📊 NOVELTY SCORE CALCULATION"]
        Sim["Similarity Signal:<br/>cosine(query, sources)<br/>Range: 0-1"]
        Spec["Specificity Signal:<br/>unique_keywords / total<br/>Range: 0-100"]
        Temp["Temporal Signal:<br/>recency_score<br/>Range: 0-100"]
        Sat["Saturation Penalty:<br/>-5 to -30 based on<br/>similar ideas count"]
        
        BaseScore["Base Score = 50<br/>+ (sim × 0.3)<br/>+ (temp × 0.2)<br/>- (sat × 0.5)"]
        
        Domain["Domain Bonus:<br/>+5 to +10<br/>based on profile"]
        
        HITL["HITL Penalties:<br/>- Rejection cascade: -20<br/>- Downgrade: -10"]
        
        Smooth["Stability Check:<br/>Moving average<br/>Confidence: H/M/L"]
        
        Sim --> BaseScore
        Spec --> BaseScore
        Temp --> BaseScore
        Sat --> BaseScore
        
        BaseScore --> Domain
        Domain --> HITL
        HITL --> Smooth
        
        Smooth --> OutputN["Range: 0-100<br/>Level: Very Low→High<br/>Confidence: High/Med/Low"]
    end
```

## 13. AUTHENTICATION & AUTHORIZATION FLOW

```mermaid
graph TD
    User["👤 User"]
    
    User -->|Email/Password| Login["POST /api/login"]
    
    Login -->|Hash with bcrypt| Hash["🔐 Hash Password"]
    Hash -->|Compare| DBCheck["Query DB for user"]
    
    DBCheck -->|Match| Gen["Generate JWT Token"]
    Gen -->|Payload| Payload["{<br/>user_id: 123,<br/>role: 'user',<br/>exp: now + 1h<br/>}"]
    
    Payload -->|Sign| Sign["Sign with Secret<br/>HS256"]
    Sign -->|Return| Token["Return JWT to Client"]
    
    Token -->|Store| Storage["localStorage"]
    
    User -->|Subsequent Request| Header["Header: Authorization<br/>Bearer {jwt_token}"]
    
    Header -->|Middleware| Verify["@jwt_required()"]
    
    Verify -->|Decode| Decode["Decode & Verify Signature"]
    Decode -->|Check| CheckExp["Check Expiration"]
    CheckExp -->|Extract| Extract["get_jwt_identity()"]
    
    Extract -->|Success| Allow["✅ Inject user_id<br/>to request context"]
    CheckExp -->|Expired| Deny["❌ Return 401<br/>Unauthorized"]
    Decode -->|Invalid| Deny
    
    Allow -->|Route Protection| Check_Role["Check Role:<br/>require_admin()?"]
    
    Check_Role -->|Not Admin| Forbidden["❌ Return 403<br/>Forbidden"]
    Check_Role -->|Is Admin| Continue["✅ Continue"]
    
    Continue -->|Rate Limit| Limiter["@limiter.limit()<br/>Check quota"]
    Limiter -->|Over quota| TooMany["❌ Return 429<br/>Rate Limited"]
    Limiter -->|OK| Proceed["✅ Proceed to Handler"]
```

---

## Summary: Ready-to-Use Diagrams

✅ **1. System Architecture** - Component relationships
✅ **2. User Flow - Exploration** - Anonymous browsing journey  
✅ **3. User Flow - Generation** - Full idea creation process
✅ **4. Generation Pipeline** - 4-phase LLM workflow
✅ **5. Novelty Scoring** - Signal computation & blending
✅ **6. Database ERD** - Entity relationships & schema
✅ **7. Admin HITL** - Review & verdict workflow
✅ **8. Source Retrieval** - Multi-source orchestration
✅ **9. API Sequence** - Request/response flow
✅ **10. Tech Stack** - Dependency overview
✅ **11. Deployment** - Infrastructure layout
✅ **12. Score Calculation** - Quality & novelty formulas
✅ **13. Authentication** - Security & authorization

These diagrams are in Mermaid format and can be rendered in:
- GitHub (native markdown)
- Notion
- Confluence  
- Mermaid Live Editor (mermaid.live)
- Markdown editors with Mermaid support
- Export as PNG/SVG for presentations
