"""
Storage layer for auction history using MySQL.
"""

import mysql.connector
from mysql.connector import Error
import json
from pathlib import Path
from datetime import datetime
from typing import List, Optional, Dict, Any
from .models import AuctionOutcome, OpponentProfile, StrategyPerformance

class AuctionHistoryStorage:
    """ MySQL-based storage for auction history"""
    def __init__(self, mysql_config: dict = None):
        """
        Initialize storage with MySQL connection

        Args:
        mysql_config: Dict with keys: host, port, user, password, database
        """
        if not mysql_config:
            raise ValueError("MySQL config required. Provide host, port, user, password, database")

        self.mysql_config= mysql_config
        self._init_database()



    def _init_database(self):
        """ Create tables if they don't exist."""
        conn = mysql.connector.connect(**self.mysql_config)
        cursor = conn.cursor()

        #Auction outcomes table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS auction_outcomes (
        id INT AUTO_INCREMENT PRIMARY KEY,
        auction_id VARCHAR(255) UNIQUE,
        domain VARCHAR(255),
        platform VARCHAR(50),
        timestamp DATETIME,
        estimated_value DECIMAL(10,2),
        current_bid_at_decision DECIMAL(10,2),
        final_price DECIMAL(10,2),
        num_bidders INT,
        hours_remaining_at_decision DECIMAL(5,2),
        bot_detected BOOLEAN,
        strategy_used VARCHAR(50),
        recommended_bid DECIMAL(10,2),
        decision_source VARCHAR(50),
        confidence DECIMAL(3,2),
        result VARCHAR(20),
        profit_margin DECIMAL(5,4),
        opponent_hash VARCHAR(255),
        raw_data TEXT,
        INDEX idx_platform(platform),
        INDEX idx_estimated_value(estimated_value),
        INDEX idx_timestamp(timestamp)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)

        # Opponent Profiles table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS opponent_profiles (
           opponent_id VARCHAR(255) PRIMARY KEY,
           first_seen DATETIME,
           last_seen DATETIME,
           encounter_count INT,
           is_likely_bot BOOLEAN,
           avg_reaction_time DECIMAL(8,2),
           aggression_scores TEXT,
           platforms TEXT,
           wins INT,
           losses INT
           ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)

        # Strategy Performance Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS strategy_performance(
            id INT AUTO_INCREMENT PRIMARY KEY,
            strategy VARCHAR(50),
            platform VARCHAR(50),
            value_tier VARCHAR(20),
            total_uses INT,
            wins INT,
            total_profit DECIMAL(12,2),
            UNIQUE(strategy, platform, value_tier)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)  
        conn.commit()
        conn.close()

    def record_outcome(self, outcome: AuctionOutcome):
        """ Save an auction outcome."""
        conn = mysql.connector.connect(**self.mysql_config)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO auction_outcomes
            (auction_id, domain, platform, timestamp, estimated_value,
            current_bid_at_decision, final_price, num_bidders, hours_remaining_at_decision,
            bot_detected, strategy_used, recommended_bid, decision_source,
            confidence, result, profit_margin, opponent_hash, raw_data)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                domain = VALUES(domain),
                platform = VALUES(platform),
                timestamp = VALUES(timestamp),
                estimated_value = VALUES(estimated_value),
                current_bid_at_decision = VALUES(current_bid_at_decision),
                final_price = VALUES(final_price),
                num_bidders = VALUES(num_bidders),
                hours_remaining_at_decision = VALUES(hours_remaining_at_decision),
                bot_detected = VALUES(bot_detected),
                strategy_used = VALUES(strategy_used),
                recommended_bid = VALUES(recommended_bid),
                decision_source = VALUES(decision_source),
                confidence = VALUES(confidence),
                result = VALUES(result),
                profit_margin = VALUES(profit_margin),
                opponent_hash = VALUES(opponent_hash),
                raw_data = VALUES(raw_data)
            """, (
                outcome.auction_id, outcome.domain, outcome.platform, outcome.timestamp.isoformat() if outcome.timestamp else None,
                outcome.estimated_value,
                outcome.current_bid_at_decision, outcome.final_price, outcome.num_bidders, outcome.hours_remaining_at_decision,
                bool(outcome.bot_detected), outcome.strategy_used, outcome.recommended_bid, outcome.decision_source,
                outcome.confidence, outcome.result, outcome.profit_margin, outcome.opponent_hash, 
                outcome.json() if hasattr(outcome, 'json') else None
            ))
        conn.commit()
        conn.close()

        # Update strategy performance
        self._update_strategy_performance(outcome)

    def _update_strategy_performance(self, outcome: AuctionOutcome):
        """Update strategy performance stats."""
        # Determine value tier
        if outcome.estimated_value >= 1000:
            value_tier = "high"
        elif outcome.estimated_value >= 100:
            value_tier = "medium"
        else:
            value_tier = "low"

        conn = mysql.connector.connect(**self.mysql_config)
        cursor = conn.cursor()
        
        # Get Existing Stats
        cursor.execute("""
        SELECT total_uses, wins, total_profit FROM strategy_performance
        WHERE strategy = %s AND platform = %s AND value_tier = %s
        """, (outcome.strategy_used, outcome.platform, value_tier))

        row = cursor.fetchone()
        if row:
            total_uses, wins, total_profit = row
        else:
            total_uses, wins, total_profit = 0, 0, 0.0

        # Update stats
        total_uses += 1
        if outcome.result == "won":
            wins += 1
            if outcome.profit_margin:
                total_profit += outcome.profit_margin * outcome.final_price

        cursor.execute("""
        INSERT INTO strategy_performance
        (strategy, platform, value_tier, total_uses, wins, total_profit)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            total_uses = VALUES(total_uses),
            wins = VALUES(wins),
            total_profit = VALUES(total_profit)
        """, (outcome.strategy_used, outcome.platform, value_tier, total_uses, wins, total_profit))

        conn.commit()
        conn.close()

    def get_similar_auctions(self, platform: str, value_min: float, value_max: float, limit: int = 10) -> List[Dict[str,Any]]:
        """ Find similar past auctions for context."""
        conn = mysql.connector.connect(**self.mysql_config)
        cursor = conn.cursor()

        cursor.execute("""
        SELECT raw_data FROM auction_outcomes
        WHERE platform = %s
        AND estimated_value BETWEEN %s AND %s
        ORDER BY timestamp DESC
        LIMIT %s
        """, (platform, value_min, value_max, limit))

        results =[]
        for row in cursor.fetchall():
            results.append(json.loads(row[0]))
        
        conn.close()
        return results
    
    def get_strategy_performance(self, strategy: str, platform: str = None, value_tier: str = None) -> Dict[str, Any]:
        """ Get performance stats for a strategy."""
        conn = mysql.connector.connect(**self.mysql_config)
        cursor = conn.cursor()

        query = " SELECT * FROM strategy_performance WHERE strategy = %s"
        params = [strategy]

        if platform:
            query += " AND platform = %s"
            params.append(platform)

        if value_tier:
            query += " AND value_tier = %s"
            params.append(value_tier)

        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        if not rows:
            return {"strategy": strategy, "total_uses": 0, "win_rate": 0}
        
        # Aggregate across all matching rows
        total_uses = sum(r[4] for r in rows)
        wins = sum(r[5] for r in rows)
        total_profit = sum(r[6] for r in rows)
        return {
            "strategy": strategy,
            "total_uses": total_uses,
            "wins": wins,
            "win_rate": wins / max( 1, total_uses),
            "total_profit": total_profit,
            "avg_profit_per_win": total_profit / max( 1, wins)
        }

    
    def get_best_strategy_for_context(self, platform:str, value_tier:str, min_samples: int=5) -> Optional[str]:
        """ Find the best performing strategy for a given context."""
        conn = mysql.connector.connect(**self.mysql_config)
        cursor = conn.cursor()

        cursor.execute("""
        SELECT strategy, total_uses, wins, CAST(wins AS DECIMAL(10,2))/ total_uses as win_rate
        FROM strategy_performance
        WHERE platform = %s AND value_tier = %s AND total_uses >= %s
        ORDER BY win_rate DESC
        LIMIT 1
        """, (platform, value_tier, min_samples))

        row = cursor.fetchone()
        conn.close()

        if row:
            return row[0]
        return None