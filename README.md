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
    %% External Components
    Polymarket[📊 Polymarket]
    Kalshi[🎯 Kalshi]
    
    %% Backend Directory
    subgraph Backend["Backend Directory"]
        Market[Market<br/>- Market ID<br/>- Name<br/>- Description]
        BookOrder[Book Order<br/>- Market ID<br/>- Time Stamp<br/>- Bids / asks]
    end
    
    %% Platform Directory
    subgraph Platform["Platform Directory"]
        PolyInterface[Polymarket<br/>Interface]
        KalshiInterface[Kalshi Interface]
        TestInterface[Test Interface]
        BasePlatform[Base Platform Class]
    end
    
    %% Core Directory
    subgraph Core["Core Directory"]
        %% Manager Class
        subgraph Manager["Manager Class"]
            ContinuousEngine[Function: Continuous Trading Engine]
            CheckArbitrage[Function: Check Arbitrage]
            UpdateMarkets[Function: Update Markets]
            ExecuteOrder[Execute Order]
            PullBooks[Pull all Books from MARKET<br/>PAIRS]
            AddBookDB[Add Book to DB of<br/>all books]
        end
        
        %% Arbitrage Class
        subgraph Arbitrage["Arbitrage Class"]
            ReturnResults[Return results]
            ArbitrageCalc[Arbitrage Calculator]
        end
        
        %% Similarity Class
        subgraph Similarity["Similarity Class"]
            CheckSimilarity[Check similarity]
            AddRelation[Add relation of<br/>MarketA - MarketB to<br/>MARKET PAIRS table]
        end
    end
    
    %% DB Directory
    subgraph DB["DB Directory"]
        subgraph DBManager["DB Manager Class"]
            AddBooks[Add BOOKS]
            GetMarketPairs[Get All MARKET<br/>PAIRS]
            NewMarkets[New MARKETS?<br/>(market_ids: list[int])]
            AddMarkets[Add MARKETS<br/>(markets: list[Market])]
            GetBooks[Get BOOKS<br/>(market_ids: list[int])]
            AddMarketPairs[Add MARKET PAIRS<br/>(markets: list[Market])]
        end
        
        subgraph FastAPI["Fast API Wrapper Class"]
            APIGetMarketPairs[/api/get_market_pairs]
            APIGetOrderBooks[/api/get_order_books/?=[market_ids]]
        end
        
        PostgreSQL[(PostgreSQL)]
    end
    
    %% External connections
    Polymarket --> PolyInterface
    Kalshi --> KalshiInterface
    
    %% Platform connections
    PolyInterface --> BasePlatform
    KalshiInterface --> BasePlatform
    TestInterface --> BasePlatform
    
    %% Platform to Core connections
    BasePlatform --> ContinuousEngine
    
    %% Core internal connections
    ContinuousEngine --> CheckArbitrage
    ContinuousEngine --> UpdateMarkets
    CheckArbitrage --> PullBooks
    CheckArbitrage --> ArbitrageCalc
    UpdateMarkets --> AddBookDB
    
    %% Core to Backend connections
    PullBooks --> Market
    AddBookDB --> BookOrder
    
    %% Similarity connections
    CheckSimilarity --> AddRelation
    
    %% Core to DB connections
    ExecuteOrder --> AddBooks
    Manager --> GetMarketPairs
    Manager --> NewMarkets
    Manager --> AddMarkets
    Manager --> GetBooks
    Manager --> AddMarketPairs
    
    %% DB internal connections
    DBManager --> PostgreSQL
    FastAPI --> DBManager
    
    %% Return paths
    ArbitrageCalc --> ReturnResults
    
    %% Styling
    classDef external fill:#4285f4,stroke:#333,stroke-width:2px,color:#fff
    classDef backend fill:#e3f2fd,stroke:#333,stroke-width:2px
    classDef platform fill:#e8f5e8,stroke:#333,stroke-width:2px
    classDef core fill:#fff3e0,stroke:#333,stroke-width:2px
    classDef database fill:#f3e5f5,stroke:#333,stroke-width:2px
    
    class Polymarket,Kalshi external
    class Market,BookOrder backend
    class PolyInterface,KalshiInterface,TestInterface,BasePlatform platform
    class Manager,Arbitrage,Similarity,ContinuousEngine,CheckArbitrage,UpdateMarkets core
    class DBManager,FastAPI,PostgreSQL database
```
