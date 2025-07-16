## **Events Contract Trading**

**Kalshi / Polymarket Statistical Arbitrage Monitoring and Trade Execution**

Check it out:  
[Live Project Site](https://harris-song.github.io/events-contract-trading)
[![LinkedIn - Harris](https://img.shields.io/badge/LinkedIn-blue?logo=linkedin&logoColor=white)](https://www.linkedin.com/in/harris-song/)
[![LinkedIn - Henry](https://img.shields.io/badge/LinkedIn-blue?logo=linkedin&logoColor=white)](https://www.linkedin.com/in/hmac213/)

---

### Introduction


A robust, full-stack interface for real-time ingestion and processing of Polymarket and Kalshi data, designed to support continuous statistical arbitrage analysis across event-based markets. The system leverages [OpenAI Structured Outputs](https://platform.openai.com/docs/guides/structured-outputs?api-mode=chat) through the API to automatically detect and surface new cross-platform arbitrage opportunities through structured market comparisons. 

Backed by a PostgreSQL database and integrated with a high-performance Python-based FAST API, the backend adheres to RESTful API design principles, enabling reliable access to historical and live market data. A live project site provides real-time visualization and interaction with the arbitrage engine, while the API framework supports extensible endpoint creation for research, trading, and analytics applications.

### Setup

To get started with the project, clone the repository and install all necessary dependencies. Then, run the backend service using the command-line interface provided by the Manager module. This will initialize the API and connect to the configured PostgreSQL database, enabling real-time access to market data and arbitrage calculations.

```bash
git clone https://github.com/harris-song/events-contract-trading
cd events-contract-trading
pip install -r requirements.txt
python -m backend.core.Manager
```


### System Diagram
Each component is modular, with clearly defined responsibilities across the `Backend`, `Core`, `Platform`, and `DB` directories. The `Manager` class coordinates the continuous trading engine and database updates.


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
