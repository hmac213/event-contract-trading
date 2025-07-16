## **Events Contract Trading**

**Kalshi / Polymarket Statistical Arbitrage Monitoring and Trade Execution**

Check it out:  
[Live Project Site](https://harris-song.github.io/events-contract-trading)

---

### Introduction

Interface for pulling Polymarket and Kalshi data, continuous updates fro

### Setup

```bash
git clone https://github.com/harris-song/events-contract-trading
cd events-contract-trading
pip install -r requirements.txt
python -m backend.core.Manager
```
%%──────────────────────────────
%%  Continuous‑Trading Platform
%%──────────────────────────────
flowchart TD
    %%── Data models ──
    A[Market<br/>• Market ID<br/>• Name<br/>• Description]
    B[Book Order<br/>• Market ID<br/>• Time Stamp<br/>• Bids / Asks]

    %%── Platform layer ──
    subgraph PLATFORM_DIRECTORY[Platform Directory]
        direction TB
        P1(Polymarket Interface)
        P2(Kalshi Interface)
        P3(Test Interface)
        P0(Base Platform Class)
    end

    %%── Core layer ──
    subgraph CORE_DIRECTORY[Core Directory]
        direction TB
        AR(Arbitrage Class)
        MN(Manager Class<br/>Continuous Trading Engine)
        SM(Similarity Class)
    end

    %%── Database layer ──
    subgraph DATABASE_LAYER[DB Directory]
        direction TB
        DBM(DB Manager Class)
        DB[(PostgreSQL)]
    end

    %%── API layer ──
    API(FastAPI Wrapper<br/><code>/api/get_market_pairs</code><br/><code>/api/get_order_books?market_ids</code>)

    %%── Relationships ──
    P1 --> MN
    P2 --> MN
    P3 --> MN
    A  --> MN
    B  --> MN

    MN --> AR
    AR --> MN
    MN --> SM
    SM --> MN

    MN --> DBM
    DBM --> DB
    API --> DBM
