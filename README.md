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

```mermaid
graph TB
    %% External
    Polymarket[📊 Polymarket]
    Kalshi[🎯 Kalshi]
    
    %% Backend Directory - Left side, compact
    subgraph Backend["Backend Directory"]
        direction TB
        Market["`Market
        - Market ID
        - Name
        - Description`"]
        BookOrder["`Book Order
        - Market ID
        - Time Stamp
        - Bids / asks`"]
    end
    
    %% Core Directory - Left center, compact
    subgraph Core["Core Directory"]
        direction TB
        subgraph Arbitrage["Arbitrage Class"]
            direction TB
            ReturnResults[Return results]
            ArbitrageCalc[Arbitrage Calculator]
        end
    end
    
    %% Platform Directory - Top center, horizontal layout
    subgraph Platform["Platform Directory"]
        direction TB
        subgraph Interfaces[" "]
            direction LR
            PolyInterface[Polymarket Interface]
            KalshiInterface[Kalshi Interface]
            TestInterface[Test Interface]
        end
        BasePlatform[Base Platform Class]
    end
    
    %% Manager Class - Center, compact
    subgraph Manager["Manager Class"]
        direction TB
        subgraph ManagerFunctions[" "]
            direction TB
            ContinuousEngine["`Function: Continuous Trading Engine`"]
            CheckArbitrageFn["`Function: Check Arbitrage`"]
            UpdateMarketsFn["`Function: Update Markets`"]
        end
        subgraph ManagerActions[" "]
            direction TB
            ExecuteOrder[Execute Order]
            PullBooks["`Pull all Books from MARKET PAIRS`"]
            AddBookDB["`Add Book to DB of all books`"]
        end
    end
    
    %% Similarity Class - Right center
    subgraph Similarity["Similarity Class"]
        direction TB
        CheckSimilarity[Check similarity]
        AddRelation["`Add relation of MarketA - MarketB to MARKET PAIRS table`"]
    end
    
    %% DB Directory - Bottom, compact
    subgraph DB["DB Directory"]
        direction TB
        subgraph DBManager["DB Manager Class"]
            direction LR
            AddBooks[Add BOOKS]
            GetMarketPairs["`Get All MARKET PAIRS`"]
            NewMarkets["`New MARKETS?`"]
            AddMarkets["`Add MARKETS`"]
            GetBooks["`Get BOOKS`"]
            AddMarketPairs["`Add MARKET PAIRS`"]
        end
        subgraph FastAPI["Fast API Wrapper Class"]
            direction TB
            APIGetMarketPairs["`/api/get_market_pairs`"]
            APIGetOrderBooks["`/api/get_order_books`"]
        end
        PostgreSQL[(PostgreSQL)]
    end
    
    %% Connections
    Polymarket --> PolyInterface
    Kalshi --> KalshiInterface
    PolyInterface --> BasePlatform
    KalshiInterface --> BasePlatform
    TestInterface --> BasePlatform
    BasePlatform --> ContinuousEngine
    ContinuousEngine --> CheckArbitrageFn
    ContinuousEngine --> UpdateMarketsFn
    CheckArbitrageFn --> PullBooks
    CheckArbitrageFn --> ArbitrageCalc
    UpdateMarketsFn --> AddBookDB
    PullBooks --> Market
    AddBookDB --> BookOrder
    ArbitrageCalc --> ReturnResults
    CheckSimilarity --> AddRelation
    ExecuteOrder --> AddBooks
    Manager --> GetMarketPairs
    Manager --> NewMarkets
    Manager --> AddMarkets
    Manager --> GetBooks
    Manager --> AddMarketPairs
    DBManager --> PostgreSQL
    FastAPI --> DBManager
```
