# Wealth Advisor Assistant - Architecture & Flow Diagrams

## 1. SYSTEM ARCHITECTURE OVERVIEW

```
┌─────────────────────────────────────────────────────────────────┐
│                    ORCHESTRATOR LAYER                           │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │           LangGraph Workflow (workflow.py)               │  │
│  │  Routes: Fetcher → Analyzer → Human Approval → Memory   │  │
│  └──────────────────────────────────────────────────────────┘  │
└──────────┬──────────────────────────────────────────────┬───────┘
           │                                              │
      ┌────▼──────┐                          ┌───────────▼────┐
      │  AGENT    │                          │  AGENT         │
      │  NODES    │                          │  NODES         │
      └────┬──────┘                          └────────┬───────┘
           │                                          │
      ┌────▼──────────────┬──────────────────────────▼────────┐
      │  Fetcher Node     │  Analyzer Node                    │
      │ (fetcher_node.py) │ (analyzer_node.py)               │
      │                   │                                   │
      │ • Load data       │ • Net worth calc                 │
      │ • CRM tool        │ • Risk profiling                 │
      │ • Validate        │ • Anomaly detection              │
      └────┬──────────────┴──────────────────┬────────────────┘
           │                                 │
      ┌────▼──────────────┬──────────────────▼──────────────┐
      │    TOOLS LAYER    │                                 │
      │                   │                                 │
      │ • fetch_crm_data  │ • detect_anomalies             │
      │ • llm_validation  │ • llm_enhancement              │
      │ • llm_summaries   │                                 │
      └───────────────────┴─────────────────────────────────┘
           │                                     │
      ┌────▼────────────────────────────────────▼──────┐
      │        EXTERNAL SERVICES                       │
      │                                                 │
      │ ChatOpenAI (gpt-4.1-mini) → Fallback Rule-based│
      └────────────────────────────────────────────────┘
           │
      ┌────▼───────────────────┐
      │   MEMORY LAYER         │
      │                        │
      │ Short-term: Session    │
      │ Long-term: JSON store  │
      └────────────────────────┘
```

---

## 2. DETAILED AGENT INTERACTION FLOW

### Phase 1: Data Fetching

```
╔════════════════════════════════════════════════════════════════╗
║ INPUT: client_id (e.g., "C-12345")                            ║
╚═══════════════════════════╦══════════════════════════════════╝
                            ▼
            ┌─────────────────────────────────┐
            │  FETCHER AGENT NODE             │
            │  (fetcher_node.py)              │
            └─────────────────────────────────┘
                    │         │         │
        ┌───────────┴─────────┴─────────┴──────────┐
        │                                           │
        ▼                      ▼                    ▼
    Load JSON File         invoke()             LLM Validation
    mock_client_data   fetch_crm_data.invoke()  generate_
                                                   validation()
        │                      │                    │
        ▼                      ▼                    ▼
    ✓ financial_data    ✓ crm_data          ✓ validation_result
    (accounts,          (demographics,       (completeness
     transactions)       life_events)        score)
        │                      │                    │
        └──────────────────────┴────────────────────┘
                               ▼
                    STATE UPDATE: {
                      client_data: {...},
                      crm_data: {...},
                      validation: {...}
                    }
                               ▼
                    Route to Analyzer Agent
```

### Phase 2: Analysis & Anomaly Detection

```
╔════════════════════════════════════════════════════════════════╗
║ INPUT: client_data, crm_data (from Fetcher)                   ║
╚═══════════════════════════╦══════════════════════════════════╝
                            ▼
            ┌─────────────────────────────────┐
            │  ANALYZER AGENT NODE            │
            │  (analyzer_node.py)             │
            └─────────────────────────────────┘
                    │         │         │         │
        ┌───────────┼─────────┼─────────┼─────────┼─────────┐
        │           │         │         │         │         │
        ▼           ▼         ▼         ▼         ▼         ▼
    Calculate  Determine  invoke()   Generate  Try LLM   Merge
    Net Worth  Risk      detect_     Rule-     Enhance   Results
               Profile   anomalies   based     Recom-
                                     Recom.    mendations
        │           │         │         │         │         │
        ▼           ▼         ▼         ▼         ▼         ▼
    nw: 250K   aggressive  anomalies  rule_     llm_      merged
                           [           recom     recom     recom
                            high: 2    ]         ]         ]
                            med: 1
                           ]

                               ▼
                    DECISION POINT:
                    ┌──────────────────────┐
                    │ High Severity Found? │
                    └──────┬──────────┬────┘
                           │ YES      │ NO
                    ┌──────▼──┐    ┌──▼─────────┐
                    │ Set     │    │ Auto-      │
                    │requires │    │ Approve    │
                    │_approval│    │ = true     │
                    │= true   │    └──┬─────────┘
                    └──┬──────┘       │
                       │             ▼
                       │        Store in Memory
                       │             │
                       ▼             ▼
            Human Approval Node    COMPLETE
```

### Phase 3: Human-in-the-Loop Checkpoint

```
╔════════════════════════════════════════════════════════════════╗
║ CONDITION: requires_approval == true                          ║
║ (High-severity anomalies detected)                            ║
╚═══════════════════════════╦══════════════════════════════════╝
                            ▼
            ┌─────────────────────────────────┐
            │  HUMAN APPROVAL NODE            │
            │  (workflow.py)                  │
            └─────────────────────────────────┘
                            │
                ┌───────────┴──────────┐
                │                      │
                ▼                      ▼
            Generate                Display
            LLM Summary              • Anomalies found
                                     • Risk profile
                                     • Metrics
                │                      │
                └──────────┬───────────┘
                           ▼
            ┌────────────────────────────────┐
            │    USER DECISION PROMPT        │
            │                                │
            │ [A] Approve recommendations    │
            │ [R] Reject (flag for review)   │
            │ [V] View detailed analysis     │
            │ [D] Details (recommendations)  │
            └──────────┬─────────────────────┘
                       │
        ┌──────────────┼──────────────┬───────────────┐
        │              │              │               │
        ▼              ▼              ▼               ▼
    [A] Approve   [R] Reject      [V] View         [D] Details
     │             │              │                 │
     ├─ Save ✓    ├─ Save ✗      └─ Reshow    (Return to prompt)
     │             │              Approval     after showing
     ▼             ▼              │
    Continue      Flag for       Loop back
    (→Memory)     Review         to prompt
                  (→Memory)
```

### Phase 4: Memory Persistence

```
┌────────────────────────────────────────────────────────────┐
│        MEMORY LAYER - TWO-TIER PERSISTENCE                 │
└────────────────────────────────────────────────────────────┘

SHORT-TERM MEMORY                  LONG-TERM MEMORY
┌──────────────────────┐           ┌────────────────────────┐
│  Session Context     │           │  Persistent Store      │
│  (In-Memory Dict)    │           │  (JSON File)           │
├──────────────────────┤           ├────────────────────────┤
│                      │           │                        │
│ client_id            │           │ [Entry 1]              │
│ client_data          │           │ {                      │
│ crm_data             │           │  "timestamp": ...,     │
│ analysis_result      │           │  "client_id": ...,     │
│ approval_decision    │           │  "net_worth": ...,     │
│ memory_summary       │           │  "risk_profile": ...,  │
│                      │           │  "llm_summary": ...,   │
│ (Active during       │           │  "decision": ...       │
│  session)            │           │ }                      │
│                      │           │                        │
│                      │           │ [Entry 2]              │
│                      │           │ {...}                  │
│                      │           │                        │
│                      │           │ ... (last 100 entries) │
│                      │           │                        │
└──────────────────────┘           └────────────────────────┘
           │                                    ▲
           │                                    │
           └────────────────────────────────────┘
         After Approval, Persist to JSON
```

---

## 3. TOOL ABSTRACTION LAYER

```
┌──────────────────────────────────────────────────────────────┐
│  TOOL ABSTRACTION PATTERN (LangChain @tool decorator)       │
└──────────────────────────────────────────────────────────────┘

Agent Code (DOESN'T KNOW IMPLEMENTATION):
┌────────────────────────────────────────────────┐
│ result = fetch_crm_data.invoke({               │
│   "client_id": "C-12345"                       │
│ })                                             │
└────────────────────┬───────────────────────────┘
                     │
                     ▼ (Tool Interface)
                  ┌──────────┐
                  │   Tool   │
                  │ Schema   │
                  │ (JSON)   │
                  └──────────┘
                     │
        ┌────────────┼────────────┐
        ▼            ▼            ▼
    Input        Output       Validation
    Type         Type         Rules
    Check        Check        Check
        │            │            │
        └────────────┼────────────┘
                     │
                     ▼
    ┌───────────────────────────────────┐
    │  IMPLEMENTATION (tools/crm_tool.py)
    │                                   │
    │  @tool                            │
    │  def fetch_crm_data(...):        │
    │    """Get CRM demographics"""     │
    │    # Real implementation here     │
    │    return crm_data               │
    └───────────────────────────────────┘

BENEFITS:
✓ Agents decoupled from implementations
✓ Tools swappable without code changes
✓ Automatic schema generation
✓ Built-in validation
✓ Easy to test independently
```

---

## 4. ERROR HANDLING - 3-TIER FALLBACK STRATEGY

```
┌──────────────────────────────────────────────────────────────┐
│        PRIMARY: LLM-ENHANCED ANALYSIS                        │
│        Try to use ChatOpenAI for intelligent decisions       │
└──────────────────────────────────────────────────────────────┘
                          │
                ┌─────────┴─────────┐
                │ LLM Available?    │
                └─────┬────────┬────┘
                      │ YES    │ NO
                      ▼        │
            ┌─────────────────┐│
            │ Use ChatOpenAI  ││
            │ confidence=0.92 ││
            │ (enriched       ││
            │  recommendations)
            └─────────┬───────┘│
                      │        │
                      ▼        │
            ┌───────────────┐  │
            │ SUCCESS ✓     │  │
            │ Return        │  │
            └───────────────┘  │
                      │        │
                      │        ▼
                      │  ┌──────────────────────────────────┐
                      │  │  SECONDARY: RULE-BASED ANALYSIS  │
                      │  │  Use predefined anomaly rules    │
                      │  └──────────────────────────────────┘
                      │                     │
                      │          ┌──────────┴──────────┐
                      │          │ Rules Available?   │
                      │          └──────┬────────┬────┘
                      │                │ YES    │ NO
                      │                ▼        │
                      │     ┌──────────────────┐│
                      │     │ Apply Rules      ││
                      │     │ confidence=0.85  ││
                      │     │ (known patterns) ││
                      │     └────┬─────────────┘│
                      │          │              │
                      │          ▼              │
                      │    ┌──────────────────┐│
                      │    │ SUCCESS ✓        ││
                      │    │ Return           ││
                      │    └──────────────────┘│
                      │          │             │
                      │          │             ▼
                      │          │  ┌──────────────────────┐
                      │          │  │ TERTIARY: ERROR      │
                      │          │  │ STATE HANDLING       │
                      │          │  │                      │
                      │          │  │ Return partial       │
                      │          │  │ results + error log  │
                      │          │  │ confidence=0.0       │
                      │          │  └──────────────────────┘
                      │          │             │
                      └──────────┼─────────────┘
                                 │
                                 ▼
                    ┌────────────────────────┐
                    │ RESULT STATE           │
                    │                        │
                    │ client_data            │
                    │ analysis_result        │
                    │ confidence_score       │
                    │ error_log (if any)     │
                    └────────────────────────┘
```

---

## 5. STATE MACHINE - WORKFLOW EXECUTION

```
┌─────────────────────────────────────────────────────────────┐
│  LangGraph STATE MACHINE (workflow.py)                      │
│  Type-Safe with Pydantic AgentState Schema                 │
└─────────────────────────────────────────────────────────────┘

        INPUT
          │
          ▼
    ┌──────────────┐
    │ START STATE  │
    │              │
    │ client_id    │
    │ (only field) │
    └──────┬───────┘
           │
           ▼ (invoke fetcher_node)
    ┌──────────────────────┐
    │ FETCHER NODE STATE   │
    │                      │
    │ client_data    ✓ NEW │
    │ crm_data       ✓ NEW │
    │ validation     ✓ NEW │
    └──────┬───────────────┘
           │
           ▼ (invoke analyzer_node)
    ┌──────────────────────┐
    │ ANALYZER NODE STATE  │
    │                      │
    │ net_worth      ✓ NEW │
    │ risk_profile   ✓ NEW │
    │ anomalies      ✓ NEW │
    │ recommendations✓ NEW │
    │ confidence     ✓ NEW │
    │ requires_approval✓  │
    └──────┬───────────────┘
           │
        ┌──┴──────────────────┐
        │ requires_approval?  │
        └──┬──────────────┬───┘
           │ TRUE         │ FALSE
           ▼              ▼
    ┌────────────┐   ┌──────────────────┐
    │ HUMAN      │   │ AUTO-APPROVE     │
    │ APPROVAL   │   │ NODE             │
    │ NODE       │   │                  │
    │            │   │ approval_decision│
    │ (wait for  │   │ = "auto_approved"│
    │  user      │   └────────┬─────────┘
    │  input)    │            │
    │            │            │
    │ approval   │            │
    │ _decision  │            │
    │ ✓ NEW      │            │
    └────┬───────┘            │
         │                    │
         └─────────┬──────────┘
                   │
                   ▼ (invoke memory_node)
            ┌────────────────┐
            │ MEMORY NODE    │
            │                │
            │ Persist to     │
            │ JSON file      │
            │                │
            │ memory_summary │
            │ ✓ NEW          │
            └────────┬───────┘
                     │
                     ▼
            ┌────────────────┐
            │ END STATE      │
            │ (All fields    │
            │  populated)    │
            └────────────────┘
                     │
                     ▼
                  OUTPUT
```

---

## 6. ANOMALY DETECTION RULES

```
┌──────────────────────────────────────────────────────────┐
│  RULE-BASED ANOMALY DETECTION (tools/anomaly_tool.py)   │
└──────────────────────────────────────────────────────────┘

INPUT: Transaction List
       └─ [txn1, txn2, txn3, ...]

                      ▼

RULE 1: LARGE TRANSACTIONS
┌──────────────────────────────────┐
│ amount > $10,000?                │
├──────────────────────────────────┤
│ YES → Severity: HIGH ⚠️           │
│       Reason: Unusual amount      │
│       Action: Flag for approval   │
│                                  │
│ NO  → Pass (continue to next rule)
└──────────────────────────────────┘

                      │ Continue
                      ▼

RULE 2: TRANSACTION FREQUENCY
┌──────────────────────────────────┐
│ count(txn per day) > 5?          │
├──────────────────────────────────┤
│ YES → Severity: MEDIUM ⚠          │
│       Reason: High frequency      │
│       Action: Include in analysis │
│                                  │
│ NO  → Pass (continue to next rule)
└──────────────────────────────────┘

                      │ Continue
                      ▼

RULE 3: UNUSUAL LOCATIONS
┌──────────────────────────────────┐
│ location outside normal range?   │
├──────────────────────────────────┤
│ YES → Severity: LOW ℹ️             │
│       Reason: Unexpected location │
│       Action: Add to context      │
│                                  │
│ NO  → Clean (no anomaly)          │
└──────────────────────────────────┘

                      │
                      ▼

AGGREGATION:
┌────────────────────────────────┐
│ Anomaly List:                  │
│                                │
│ [                              │
│   {                            │
│     type: "large_transaction", │
│     amount: 25000,             │
│     severity: "high"           │
│   },                           │
│   {                            │
│     type: "high_frequency",    │
│     count: 8,                  │
│     severity: "medium"         │
│   }                            │
│ ]                              │
│                                │
│ triggers_approval = (HIGH > 0) │
│                    = true      │
└────────────────────────────────┘

                      ▼

OUTPUT: {
  anomalies: [...],
  requires_approval: true,
  high_count: 1,
  medium_count: 1,
  low_count: 0
}
```

---

## 7. COMPLETE REQUEST-RESPONSE CYCLE

```
┌─────────────────────────────────────────────────────────┐
│              COMPLETE REQUEST-RESPONSE                  │
│              (All Phases Combined)                      │
└─────────────────────────────────────────────────────────┘

USER INPUT
│
├─ CLI: "Enter client ID: C-12345"
│
└─ Streamlit: Select from dropdown
                      │
                      ▼
        ┌─────────────────────────┐
        │ ORCHESTRATOR STARTS     │
        │ (LangGraph workflow)    │
        └────┬────────────────────┘
             │
             ▼ Node 1: Fetcher
     ┌──────────────────────┐
     │ Load file            │ ① Load mock_client_data.json
     │ Call fetch_crm_data()│ ② Invoke CRM tool
     │ LLM Validation       │ ③ Optional LLM check
     └──────┬───────────────┘
            │
            ▼ Node 2: Analyzer
     ┌──────────────────────┐
     │ Net worth = Assets  │ ④ 500K - 250K = 250K
     │          - Liabilities
     │ Risk = moderate     │ ⑤ Based on age + income
     │ Anomalies = invoke()│ ⑥ Detect large txns
     │ Recommendations     │ ⑦ Rule-based + LLM
     │ Check if approval   │ ⑧ >= 1 HIGH severity?
     └──────┬───────────────┘
            │
      ┌─────┴──────────────┐
      │ HIGH SEVERITY?     │
      └──┬──────────────┬──┘
         │ YES          │ NO
         ▼              ▼
    ┌─────────────┐  ┌──────────────┐
    │ Wait for    │  │ Auto-approve │
    │ approval ⑨  │  │           ⑨  │
    │             │  │              │
    │ User picks: │  │ Set decision │
    │ [A/R/V/D] ⑩│  │ = "approved" │
    └──────┬──────┘  └────────┬─────┘
           │                  │
           ▼                  │
    ┌─────────────┐           │
    │ User Choice │           │
    │ Processed  ⑪│           │
    └──────┬──────┘           │
           │                  │
           └────────┬─────────┘
                    │
                    ▼ Node 3: Memory
            ┌───────────────────┐
            │ Save to JSON file │ ⑫ Persist
            │ Store in session  │ ⑬ Keep in memory
            │ Log decision      │ ⑭ Audit trail
            └────────┬──────────┘
                     │
                     ▼
            ┌──────────────────┐
            │ RETURN RESULT    │
            │                  │
            │ • Net worth      │ ⑮ 250,000
            │ • Risk profile   │    moderate
            │ • Anomalies      │    2 found
            │ • Decision       │    approved
            │ • Memory ref     │    #entry_42
            └──────────────────┘
                     │
                     ▼
            ┌──────────────────┐
            │ DISPLAY TO USER  │
            │                  │
            │ CLI: Print output│
            │ Web: Render UI   │
            └──────────────────┘
```

---

## 8. KEY METRICS AND CONFIDENCE SCORES

```
┌────────────────────────────────────────────────────────┐
│         CONFIDENCE SCORING SYSTEM                      │
└────────────────────────────────────────────────────────┘

LLM-ENHANCED PATH (PRIMARY)
┌────────────────────────────────────────────────────────┐
│ OpenAI gpt-4.1-mini available & responding            │
│                                                        │
│ Base score: 0.85 (rule-based)                         │
│ + 0.07 (LLM validation)                               │
│ = 0.92 confidence in recommendations                  │
│                                                        │
│ Benefits:                                             │
│ • Intelligent context awareness                       │
│ • Personalized advice                                 │
│ • Human-readable summaries                            │
│ • Anomaly interpretation                              │
└────────────────────────────────────────────────────────┘

RULE-BASED PATH (FALLBACK)
┌────────────────────────────────────────────────────────┐
│ LLM unavailable OR cost constraints                   │
│                                                        │
│ Base score: 0.85 (predefined rules)                   │
│                                                        │
│ Benefits:                                             │
│ • No external dependencies                            │
│ • Deterministic results                               │
│ • Fast execution                                      │
│ • Cost-effective                                      │
│                                                        │
│ Limitations:                                          │
│ • Less contextual                                     │
│ • Not adaptive                                        │
│ • Generic recommendations                             │
└────────────────────────────────────────────────────────┘

ERROR STATE (DEGRADED)
┌────────────────────────────────────────────────────────┐
│ Critical error (missing data, service failure)        │
│                                                        │
│ Confidence: 0.0 (unreliable)                          │
│ Status: PARTIAL RESULT                                │
│                                                        │
│ Contains:                                             │
│ • Available data (may be incomplete)                  │
│ • Error log (debugging info)                          │
│ • Recommendations: NONE (too risky)                   │
│                                                        │
│ Action:                                               │
│ • Alert user to issues                                │
│ • Request manual review                               │
│ • Don't make recommendations                          │
└────────────────────────────────────────────────────────┘

VISUALIZATION:
┌──────────────────────────────────────────────────────┐
│  Confidence ▶│ LLM: 0.92 ───────────────────────     │
│              │ Rules: 0.85 ──────────────────       │
│              │ Error: 0.0 ──                        │
│              │        0.0  0.5  1.0                 │
└──────────────────────────────────────────────────────┘
```

---

## 9. DEPLOYMENT ARCHITECTURE

```
┌─────────────────────────────────────────────────────────┐
│        DEPLOYMENT OPTIONS                               │
└─────────────────────────────────────────────────────────┘

OPTION 1: LOCAL DEVELOPMENT
┌────────────────────────────────────────────────────────┐
│ Developer Machine                                      │
│ ┌──────────────────────────────────────────────────┐  │
│ │ Python 3.10+                                     │  │
│ │ ├─ LangChain/LangGraph                           │  │
│ │ ├─ ChatOpenAI API key (env)                      │  │
│ │ ├─ Mock data (JSON)                              │  │
│ │ └─ Streamlit (optional)                          │  │
│ │                                                  │  │
│ │ CLI: python main.py                              │  │
│ │ Web: streamlit run app.py                        │  │
│ └──────────────────────────────────────────────────┘  │
│ File Storage: ./memory_store.json                      │
└────────────────────────────────────────────────────────┘

OPTION 2: CONTAINERIZED (DOCKER)
┌────────────────────────────────────────────────────────┐
│ Docker Image                                           │
│ ┌──────────────────────────────────────────────────┐  │
│ │ Base: python:3.10-slim                           │  │
│ │ ├─ Install dependencies (requirements.txt)       │  │
│ │ ├─ Copy app code                                 │  │
│ │ ├─ Expose ports (8501 for Streamlit)             │  │
│ │ └─ CMD: streamlit run app.py                     │  │
│ │                                                  │  │
│ │ Volume Mounts:                                   │  │
│ │ - /app/data/ (persistent)                        │  │
│ │ - /app/logs/ (persistent)                        │  │
│ └──────────────────────────────────────────────────┘  │
│ Container Storage: /app/data/memory_store.json        │
└────────────────────────────────────────────────────────┘

OPTION 3: CLOUD DEPLOYMENT (FUTURE)
┌────────────────────────────────────────────────────────┐
│ Cloud Platform (AWS/GCP/Azure)                         │
│ ┌──────────────────────────────────────────────────┐  │
│ │ Load Balancer                                    │  │
│ │      │                                            │  │
│ │      ▼                                            │  │
│ │ ┌─────────────────┐                              │  │
│ │ │  API Gateway    │                              │  │
│ │ └────────┬────────┘                              │  │
│ │          │                                        │  │
│ │ ┌────────┴────────┐                              │  │
│ │ ▼                ▼                               │  │
│ │ Microservice 1  Microservice 2  ... (Auto-scale) │  │
│ │ │               │                                │  │
│ │ ├─ Fetcher      ├─ Analyzer                      │  │
│ │ └─ Memory       └─ LLM Client                    │  │
│ │                                                  │  │
│ │ Shared Storage:                                  │  │
│ │ - PostgreSQL (memory_store)                      │  │
│ │ - Redis (session cache)                          │  │
│ │ - S3 (logs & backups)                            │  │
│ └──────────────────────────────────────────────────┘  │
│ Future Integration:                                    │
│ - Multi-tenant support                                │
│ - Scalable CRM APIs                                   │
│ - Real financial data sources                         │
└────────────────────────────────────────────────────────┘
```

---

## 10. TESTING SCENARIOS

```
┌─────────────────────────────────────────────────────────┐
│     AVAILABLE TEST CLIENTS & EXPECTED FLOWS             │
└─────────────────────────────────────────────────────────┘

TEST CLIENT 1: C-12345 (John Smith)
├─ Profile: High-risk with anomalies
├─ Expected Flow:
│  ├─ Fetcher: Load data ✓
│  ├─ Analyzer: Detect 2 HIGH + 1 MEDIUM anomaly
│  ├─ requires_approval: TRUE
│  └─ Human Approval: Mandatory
├─ Test Outcome:
│  ├─ Test [A] Approve:
│  │  └─ Save with decision="approved"
│  ├─ Test [R] Reject:
│  │  └─ Save with decision="rejected"
│  └─ Test [V/D] View:
│     └─ Display details & return to prompt
└─ Status: ✓ All paths tested

TEST CLIENT 2: C-67890 (Jane Doe)
├─ Profile: Moderate risk, few anomalies
├─ Expected Flow:
│  ├─ Fetcher: Load data ✓
│  ├─ Analyzer: Detect 0-1 anomalies (all LOW)
│  ├─ requires_approval: FALSE
│  └─ Auto-Approve: Skips human checkpoint
├─ Test Outcome:
│  └─ Completes without requiring user input
└─ Status: ✓ Auto-approval tested

TEST SCENARIO: LLM Unavailable
├─ Setup: Unset OPENAI_API_KEY or invalid key
├─ Expected: Falls back to rule-based
├─ Verify: confidence_score = 0.85 (not 0.92)
└─ Status: ✓ Fallback verified

TEST SCENARIO: Missing Client Data
├─ Setup: Client ID with no file found
├─ Expected: Returns error message
├─ Verify: client_data is None, error logged
└─ Status: ✓ Error handling verified

TEST SCENARIO: CRM Tool Failure
├─ Setup: CRM tool raises exception
├─ Expected: Continues with default CRM data
├─ Verify: crm_data uses defaults, warning logged
└─ Status: ✓ Graceful degradation verified
```

---

## Summary Diagram

```
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃                                                        ┃
┃  WEALTH ADVISOR ASSISTANT - COMPLETE ARCHITECTURE    ┃
┃                                                        ┃
┃  User Input (CLI/Web)                                 ┃
┃       │                                                ┃
┃       ▼                                                ┃
┃  ┌─────────────────────────────────────────────┐     ┃
┃  │    LANGGRAPH ORCHESTRATOR WORKFLOW          │     ┃
┃  │                                             │     ┃
┃  │  1. Fetcher Node                            │     ┃
┃  │  2. Analyzer Node                           │     ┃
┃  │  3. Human Approval (if needed)              │     ┃
┃  │  4. Memory Persistence                      │     ┃
┃  └────────────┬────────────────────────────────┘     ┃
┃               │                                       ┃
┃       ┌───────┴───────────┐                          ┃
┃       ▼                   ▼                          ┃
┃    Tools           External Services               ┃
┃    ├─ fetch_crm    ChatOpenAI ──────┐              ┃
┃    ├─ detect_      (primary)        │              ┃
┃    │  anomalies                     ▼              ┃
┃    ├─ llm_          │               Fallback       ┃
┃    │  enhancement   │               (Rule-based)   ┃
┃    └─ llm_summary   │               ✓              ┃
┃                     └───────────────┘              ┃
┃       │                                            ┃
┃       ▼                                            ┃
┃    ┌───────────────────────────────────────┐      ┃
┃    │  TWO-TIER MEMORY LAYER                │      ┃
┃    │  ├─ Short-term: Session context       │      ┃
┃    │  └─ Long-term: JSON persistence       │      ┃
┃    └──────────────┬────────────────────────┘      ┃
┃                   │                               ┃
┃                   ▼                               ┃
┃            Output to User                         ┃
┃       (Analysis + Recommendations)                ┃
┃                                                  ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
```

---

**End of Architecture & Flow Diagrams Document**

*For additional information, see the comprehensive README.md in the GitHub repository.*
