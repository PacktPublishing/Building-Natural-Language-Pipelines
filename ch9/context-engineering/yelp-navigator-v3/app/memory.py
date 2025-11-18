"""Business Memory Manager using SQLite for caching business information."""
import sqlite3
import json
from datetime import datetime
from typing import Dict, Any, Optional, List
from pathlib import Path


class BusinessMemory:
    """
    Manages persistent storage of business information using SQLite.
    
    This allows the agent to:
    1. Remember businesses from previous searches
    2. Answer follow-up questions without re-querying APIs
    3. Build up knowledge about businesses over multiple conversations
    """
    
    def __init__(self, db_path: str = None):
        """
        Initialize the business memory database.
        
        Args:
            db_path: Path to SQLite database file. Defaults to './business_memory.db'
        """
        if db_path is None:
            db_path = Path(__file__).parent.parent / "business_memory.db"
        
        self.db_path = str(db_path)
        self._init_db()
    
    def _init_db(self):
        """Create tables if they don't exist."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Main business info table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS businesses (
                business_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                rating REAL,
                review_count INTEGER,
                categories TEXT,
                price_range TEXT,
                phone TEXT,
                location TEXT,
                website TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Business details (website content, etc.)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS business_details (
                business_id TEXT PRIMARY KEY,
                website_content TEXT,
                has_website_info INTEGER,
                content_length INTEGER,
                fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (business_id) REFERENCES businesses(business_id)
            )
        """)
        
        # Sentiment analysis data
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS business_sentiment (
                business_id TEXT PRIMARY KEY,
                total_reviews INTEGER,
                positive_count INTEGER,
                neutral_count INTEGER,
                negative_count INTEGER,
                overall_sentiment TEXT,
                sentiment_data TEXT,
                analyzed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (business_id) REFERENCES businesses(business_id)
            )
        """)
        
        conn.commit()
        conn.close()
    
    def store_business(self, business: Dict[str, Any]) -> bool:
        """
        Store or update basic business information.
        
        Args:
            business: Dictionary containing business data with 'id' key required
            
        Returns:
            True if successful, False otherwise
        """
        if not business.get('id'):
            return False
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO businesses 
                (business_id, name, rating, review_count, categories, price_range, 
                 phone, location, website, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                business['id'],
                business.get('name'),
                business.get('rating'),
                business.get('review_count'),
                json.dumps(business.get('categories', [])),
                business.get('price_range'),
                business.get('phone'),
                json.dumps(business.get('location', {})),
                business.get('website'),
                datetime.now()
            ))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error storing business: {e}")
            return False
    
    def store_business_details(self, business_id: str, details: Dict[str, Any]) -> bool:
        """
        Store detailed information about a business (website content, etc.).
        
        Args:
            business_id: The business ID
            details: Dictionary containing detail data
            
        Returns:
            True if successful, False otherwise
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO business_details 
                (business_id, website_content, has_website_info, content_length, fetched_at)
                VALUES (?, ?, ?, ?, ?)
            """, (
                business_id,
                details.get('website_content', ''),
                1 if details.get('has_website_info') else 0,
                details.get('website_content_length', 0),
                datetime.now()
            ))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error storing business details: {e}")
            return False
    
    def store_sentiment_data(self, business_id: str, sentiment: Dict[str, Any]) -> bool:
        """
        Store sentiment analysis data for a business.
        
        Args:
            business_id: The business ID
            sentiment: Dictionary containing sentiment analysis results
            
        Returns:
            True if successful, False otherwise
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            dist = sentiment.get('sentiment_distribution', {})
            cursor.execute("""
                INSERT OR REPLACE INTO business_sentiment 
                (business_id, total_reviews, positive_count, neutral_count, 
                 negative_count, overall_sentiment, sentiment_data, analyzed_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                business_id,
                sentiment.get('total_reviews', 0),
                dist.get('positive', 0),
                dist.get('neutral', 0),
                dist.get('negative', 0),
                sentiment.get('overall_sentiment'),
                json.dumps(sentiment),
                datetime.now()
            ))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error storing sentiment data: {e}")
            return False
    
    def get_business(self, business_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve basic business information from memory.
        
        Args:
            business_id: The business ID to look up
            
        Returns:
            Dictionary with business data or None if not found
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM businesses WHERE business_id = ?
            """, (business_id,))
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return {
                    'id': row['business_id'],
                    'name': row['name'],
                    'rating': row['rating'],
                    'review_count': row['review_count'],
                    'categories': json.loads(row['categories']) if row['categories'] else [],
                    'price_range': row['price_range'],
                    'phone': row['phone'],
                    'location': json.loads(row['location']) if row['location'] else {},
                    'website': row['website'],
                    'cached_at': row['updated_at']
                }
            return None
        except Exception as e:
            print(f"Error retrieving business: {e}")
            return None
    
    def get_business_details(self, business_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve detailed information about a business.
        
        Args:
            business_id: The business ID to look up
            
        Returns:
            Dictionary with business details or None if not found
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM business_details WHERE business_id = ?
            """, (business_id,))
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return {
                    'business_id': row['business_id'],
                    'website_content': row['website_content'],
                    'has_website_info': bool(row['has_website_info']),
                    'website_content_length': row['content_length'],
                    'fetched_at': row['fetched_at']
                }
            return None
        except Exception as e:
            print(f"Error retrieving business details: {e}")
            return None
    
    def get_sentiment_data(self, business_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve sentiment analysis data for a business.
        
        Args:
            business_id: The business ID to look up
            
        Returns:
            Dictionary with sentiment data or None if not found
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM business_sentiment WHERE business_id = ?
            """, (business_id,))
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                sentiment_data = json.loads(row['sentiment_data']) if row['sentiment_data'] else {}
                return {
                    'business_id': row['business_id'],
                    'total_reviews': row['total_reviews'],
                    'sentiment_distribution': {
                        'positive': row['positive_count'],
                        'neutral': row['neutral_count'],
                        'negative': row['negative_count']
                    },
                    'overall_sentiment': row['overall_sentiment'],
                    'full_data': sentiment_data,
                    'analyzed_at': row['analyzed_at']
                }
            return None
        except Exception as e:
            print(f"Error retrieving sentiment data: {e}")
            return None
    
    def get_all_cached_businesses(self) -> List[Dict[str, Any]]:
        """
        Get a list of all businesses currently in memory.
        
        Returns:
            List of business dictionaries with basic info
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT business_id, name, rating, review_count 
                FROM businesses 
                ORDER BY updated_at DESC
            """)
            
            rows = cursor.fetchall()
            conn.close()
            
            return [{
                'id': row['business_id'],
                'name': row['name'],
                'rating': row['rating'],
                'review_count': row['review_count']
            } for row in rows]
        except Exception as e:
            print(f"Error retrieving cached businesses: {e}")
            return []
    
    def has_business_details(self, business_id: str) -> bool:
        """Check if we have detailed information cached for a business."""
        return self.get_business_details(business_id) is not None
    
    def has_sentiment_data(self, business_id: str) -> bool:
        """Check if we have sentiment data cached for a business."""
        return self.get_sentiment_data(business_id) is not None
    
    def clear_all(self):
        """Clear all cached data. Useful for testing."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM business_sentiment")
        cursor.execute("DELETE FROM business_details")
        cursor.execute("DELETE FROM businesses")
        conn.commit()
        conn.close()
