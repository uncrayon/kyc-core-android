# Construction Plan

This document outlines the phased plan for building the Android KYC Video PoC.

## Phases

- [x] Phase 1: Set up Android project structure
- [x] Phase 2: Implement Android capture flow and UI
- [x] Phase 3: Add on-device prechecks
- [x] Phase 4: Set up server infrastructure
- [x] Phase 5: Implement server processing pipeline
- [x] Phase 6: Add fraud hardening features
- [x] Phase 7: Integrate Android and server
- [x] Phase 8: Testing and parameter tuning
- [x] Phase 9: Produce deliverables

## Capture Flow State Machine

```mermaid
stateDiagram-v2
    [*] --> IDLE
    IDLE --> SELFIE_GUIDE
    SELFIE_GUIDE --> SELFIE_RECORD_ACTIVE
    SELFIE_RECORD_ACTIVE --> SELFIE_RECORD_PASSIVE
    SELFIE_RECORD_PASSIVE --> ID_GUIDE
    ID_GUIDE --> ID_RECORD_TILT
    ID_RECORD_TILT --> ID_RECORD_BACK
    ID_RECORD_BACK --> REVIEW_PRECHECKS
    REVIEW_PRECHECKS --> UPLOAD
    UPLOAD --> DONE
    UPLOAD --> RETRY
    RETRY --> IDLE
    DONE --> [*]
## Next Steps

- Run end-to-end testing
- Tune parameters for KPIs
- Deploy to staging
- Gather user feedback