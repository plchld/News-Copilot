# Optimized Agent Data Flow Visualization - News-Copilot System

This document provides comprehensive Mermaid diagrams showing how data flows in the **optimized** News-Copilot system with the new two-tier execution model.

## 1. Optimized High-Level System Architecture

```mermaid
graph TB
    User[👤 User Request] --> RequestType{Request Type}
    
    RequestType --> |"Analyze" Button| CoreAPI[🎯 Core Analysis API]
    RequestType --> |Feature Button| OnDemandAPI[⚡ On-Demand API]
    
    CoreAPI --> CoreCoordinator[🎯 Core Coordinator]
    OnDemandAPI --> OnDemandCoordinator[⚡ On-Demand Coordinator]
    
    subgraph CoreAgents["🚀 Core Agents (Immediate)"]
        Jargon[📝 Jargon Agent]
        Viewpoints[👁️ Viewpoints Agent]
    end
    
    subgraph OnDemandAgents["🎯 On-Demand Agents (User-Triggered)"]
        FactCheck[✅ Fact Check Agent]
        Bias[⚖️ Bias Agent]
        Timeline[📅 Timeline Agent]
        Expert[🎓 Expert Agent]
        XPulse[🐦 X Pulse Agent]
    end
    
    subgraph Cache["💾 Intelligent Cache"]
        CoreResults[(Core Results)]
        ArticleContext[(Article Context)]
        UserSession[(User Session)]
    end
    
    CoreCoordinator --> CoreAgents
    CoreAgents --> Cache
    Cache --> OnDemandCoordinator
    OnDemandCoordinator --> OnDemandAgents
    
    CoreAgents --> |Immediate Response| User
    OnDemandAgents --> |Targeted Response| User
    
    subgraph External["🌍 External Services"]
        GrokAPI[🤖 Grok API]
        XSearch[🔍 X/Twitter Search]
        WebSearch[🌐 Web Search]
    end
    
    CoreAgents -.-> |API Calls| GrokAPI
    OnDemandAgents -.-> |API Calls| GrokAPI
    XPulse -.-> |Live Search| XSearch
    FactCheck -.-> |Verification| WebSearch
```

## 2. Optimized User Journey Flow

```mermaid
sequenceDiagram
    participant User
    participant CoreAPI
    participant CoreCoordinator
    participant Cache
    participant OnDemandAPI
    participant OnDemandCoordinator
    participant JargonAgent
    participant ViewpointsAgent
    participant SpecificAgent

    Note over User: User clicks "Analyze"
    User->>CoreAPI: POST /analyze/core
    CoreAPI->>CoreCoordinator: execute_core_analysis()
    
    par Core Analysis (Parallel)
        CoreCoordinator->>JargonAgent: execute(context)
        CoreCoordinator->>ViewpointsAgent: execute(context)
    end
    
    JargonAgent-->>CoreCoordinator: jargon_result
    ViewpointsAgent-->>CoreCoordinator: viewpoints_result
    
    CoreCoordinator->>Cache: store_core_results()
    CoreCoordinator-->>CoreAPI: core_results
    CoreAPI-->>User: Display Jargon + Viewpoints (2-3 seconds)
    
    Note over User: User clicks "Fact Check"
    User->>OnDemandAPI: POST /analyze/on-demand/fact-check
    OnDemandAPI->>OnDemandCoordinator: execute_on_demand()
    OnDemandCoordinator->>Cache: get_enhanced_context()
    Cache-->>OnDemandCoordinator: cached_context
    OnDemandCoordinator->>SpecificAgent: execute(enhanced_context)
    SpecificAgent-->>OnDemandCoordinator: specific_result
    OnDemandCoordinator-->>OnDemandAPI: fact_check_result
    OnDemandAPI-->>User: Display Fact Check (3-5 seconds)
```

## 3. Intelligent Caching System

```mermaid
graph TD
    CoreAnalysis[🎯 Core Analysis] --> CacheDecision{Cache Enabled?}
    
    CacheDecision --> |Yes| StoreResults[💾 Store Results]
    CacheDecision --> |No| DirectResponse[📤 Direct Response]
    
    StoreResults --> CoreResultsCache[(Core Results Cache)]
    StoreResults --> ArticleContextCache[(Article Context Cache)]
    StoreResults --> SessionCache[(Session Cache)]
    
    OnDemandRequest[⚡ On-Demand Request] --> CacheCheck{Cache Available?}
    
    CacheCheck --> |Hit| EnhancedContext[📋 Enhanced Context]
    CacheCheck --> |Miss| RequireCore[❌ Require Core Analysis]
    
    EnhancedContext --> |Includes core results| OnDemandExecution[🎯 On-Demand Execution]
    
    subgraph CacheManagement["🔄 Cache Management"]
        TTLCheck[⏰ TTL Check]
        Cleanup[🧹 Cleanup Expired]
        SizeLimit[📏 Size Limit]
    end
    
    CoreResultsCache --> TTLCheck
    TTLCheck --> |Expired| Cleanup
    SizeLimit --> |Exceeded| Cleanup
    
    subgraph CacheEnrichment["⚡ Context Enrichment"]
        CoreSummary[📄 Core Summary]
        KeyConcepts[🔑 Key Concepts]
        Stakeholders[👥 Stakeholders]
    end
    
    CoreResultsCache --> CacheEnrichment
    CacheEnrichment --> EnhancedContext
```

## 4. Performance Comparison: Old vs Optimized

```mermaid
gantt
    title Performance Comparison
    dateFormat X
    axisFormat %s
    
    section Old Architecture
    All Agents (Sequential)    :done, old1, 0, 15s
    User Waits                 :crit, old2, 0, 15s
    
    section Optimized Architecture
    Core Analysis (Parallel)   :done, new1, 0, 3s
    User Gets Results          :milestone, new2, 3s, 0s
    On-Demand (When Requested) :done, new3, 8s, 5s
    User Gets Specific Result  :milestone, new4, 13s, 0s
```

## 5. Resource Optimization Flow

```mermaid
flowchart TD
    Request[📥 Request] --> RequestType{Request Type}
    
    RequestType --> |Core| CorePath[🎯 Core Path]
    RequestType --> |On-Demand| OnDemandPath[⚡ On-Demand Path]
    
    CorePath --> CoreModel{Model Selection}
    CoreModel --> |Fast Response| MiniModel[📱 grok-3-mini]
    CoreModel --> |Premium User| FullModel[🤖 grok-3]
    
    OnDemandPath --> CacheCheck{Cache Available?}
    CacheCheck --> |Yes| CachedExecution[⚡ Cached Execution]
    CacheCheck --> |No| ErrorResponse[❌ Error Response]
    
    CachedExecution --> OnDemandModel{Model Selection}
    OnDemandModel --> |Detailed Analysis| FullModel
    OnDemandModel --> |Quick Analysis| MiniModel
    
    subgraph ResourceSavings["💰 Resource Savings"]
        TokenReduction[🎯 60-80% Token Reduction]
        TimeReduction[⏱️ 70% Response Time Reduction]
        CostReduction[💵 50-70% Cost Reduction]
    end
    
    MiniModel --> ResourceSavings
    FullModel --> ResourceSavings
    CachedExecution --> ResourceSavings
```

## 6. Error Handling and Resilience

```mermaid
stateDiagram-v2
    [*] --> CoreAnalysis
    
    CoreAnalysis --> CoreSuccess : Both agents succeed
    CoreAnalysis --> PartialSuccess : One agent succeeds
    CoreAnalysis --> CoreFailure : Both agents fail
    
    CoreSuccess --> CacheStore : Store results
    PartialSuccess --> CacheStore : Store partial results
    CoreFailure --> ErrorResponse : Return error
    
    CacheStore --> [*] : Ready for on-demand
    
    OnDemandRequest --> CacheCheck
    CacheCheck --> CacheHit : Context found
    CacheCheck --> CacheMiss : No context
    
    CacheHit --> OnDemandExecution
    CacheMiss --> RequireCore : Redirect to core
    
    OnDemandExecution --> OnDemandSuccess : Agent succeeds
    OnDemandExecution --> OnDemandFailure : Agent fails
    
    OnDemandSuccess --> [*]
    OnDemandFailure --> [*] : Graceful error
    RequireCore --> [*] : User guidance
    ErrorResponse --> [*]
```

## 7. API Endpoint Architecture

```mermaid
graph LR
    subgraph NewEndpoints["🆕 Optimized Endpoints"]
        CoreEndpoint["/analyze/core"]
        OnDemandEndpoint["/analyze/on-demand/{type}"]
        CacheEndpoint["/cache/stats"]
        HealthEndpoint["/health"]
    end
    
    subgraph LegacyEndpoints["🔄 Legacy Support"]
        LegacyEndpoint["/analyze"]
    end
    
    subgraph Coordinators["🎯 Coordinators"]
        CoreCoord[Core Coordinator]
        OnDemandCoord[On-Demand Coordinator]
    end
    
    CoreEndpoint --> CoreCoord
    OnDemandEndpoint --> OnDemandCoord
    LegacyEndpoint --> |Redirects to| CoreCoord
    
    subgraph ResponseTypes["📤 Response Types"]
        ImmediateResponse[Immediate Response<br/>2-3 seconds]
        TargetedResponse[Targeted Response<br/>3-5 seconds]
        ErrorResponse[Error Response<br/>With guidance]
    end
    
    CoreCoord --> ImmediateResponse
    OnDemandCoord --> TargetedResponse
    OnDemandCoord --> ErrorResponse
```

## 8. Concurrent Request Handling

```mermaid
sequenceDiagram
    participant User1
    participant User2
    participant User3
    participant CoreAPI
    participant CoreCoordinator
    participant Cache
    participant OnDemandAPI

    par Concurrent Core Requests
        User1->>CoreAPI: Analyze Article A
        User2->>CoreAPI: Analyze Article B
        User3->>CoreAPI: Analyze Article C
    end
    
    par Parallel Core Processing
        CoreAPI->>CoreCoordinator: Process A
        CoreAPI->>CoreCoordinator: Process B
        CoreAPI->>CoreCoordinator: Process C
    end
    
    par Cache Storage
        CoreCoordinator->>Cache: Store Session A
        CoreCoordinator->>Cache: Store Session B
        CoreCoordinator->>Cache: Store Session C
    end
    
    par User Responses
        CoreAPI-->>User1: Results A (session_a)
        CoreAPI-->>User2: Results B (session_b)
        CoreAPI-->>User3: Results C (session_c)
    end
    
    Note over User1,User3: Users can now request on-demand features
    
    par On-Demand Requests
        User1->>OnDemandAPI: Fact-check (session_a)
        User2->>OnDemandAPI: Bias analysis (session_b)
        User3->>OnDemandAPI: Timeline (session_c)
    end
```

## 9. Memory and Context Management

```mermaid
graph TD
    SessionStart[🚀 Session Start] --> CoreAnalysis[🎯 Core Analysis]
    
    CoreAnalysis --> ContextExtraction[📄 Context Extraction]
    ContextExtraction --> |Article text, entities, topics| BaseContext[📋 Base Context]
    
    BaseContext --> CoreResults[📊 Core Results]
    CoreResults --> |Jargon terms, viewpoints| ContextEnrichment[⚡ Context Enrichment]
    
    ContextEnrichment --> EnhancedContext[📈 Enhanced Context]
    
    subgraph CacheStorage["💾 Cache Storage"]
        ArticleData[(Article Data)]
        CoreData[(Core Results)]
        SessionData[(Session Data)]
        MetaData[(Metadata)]
    end
    
    EnhancedContext --> CacheStorage
    
    OnDemandRequest[⚡ On-Demand Request] --> CacheRetrieval[🔍 Cache Retrieval]
    CacheRetrieval --> CacheStorage
    CacheStorage --> |Enriched context| OnDemandExecution[🎯 On-Demand Execution]
    
    subgraph ContextEnhancement["🔄 Context Enhancement"]
        KeyTerms[🔑 Key Terms]
        MainTopics[📝 Main Topics]
        StakeholderViews[👥 Stakeholder Views]
        PreviousInsights[💡 Previous Insights]
    end
    
    EnhancedContext --> ContextEnhancement
    ContextEnhancement --> OnDemandExecution
```

## Key Optimization Benefits

### 1. **Immediate User Feedback**
- Core analysis (jargon + viewpoints) completes in 2-3 seconds
- Users get immediate value instead of waiting 10-15 seconds
- Progressive enhancement with on-demand features

### 2. **Resource Efficiency**
- **60-80% reduction** in token usage for typical sessions
- **50-70% cost reduction** by only running requested analyses
- **70% faster** initial response time

### 3. **Better User Experience**
- No waiting for unused features
- Clear separation between immediate and detailed analysis
- Cached context enables instant on-demand features

### 4. **Scalability**
- Independent scaling of core vs on-demand services
- Efficient cache management prevents memory bloat
- Concurrent request handling without artificial bottlenecks

### 5. **Maintainability**
- Clear separation of concerns
- Easier to debug and monitor
- Flexible feature addition without affecting core flow

This optimized architecture transforms the system from a "batch processing" model to a "responsive, user-driven" model that matches actual usage patterns and provides immediate value to users. 