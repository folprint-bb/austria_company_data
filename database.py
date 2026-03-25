import sqlite3
import json
from datetime import datetime

class Database:
    def __init__(self, db_name='companies.db'):
        self.db_name = db_name
    
    def get_connection(self):
        conn = sqlite3.connect(self.db_name)
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_database(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS companies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                category TEXT NOT NULL,
                address TEXT,
                phone TEXT,
                email TEXT,
                website TEXT,
                description TEXT,
                scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_category ON companies(category)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_name ON companies(name)
        ''')
        
        conn.commit()
        conn.close()
    
    def save_companies(self, companies, category):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        for company in companies:
            cursor.execute('''
                INSERT INTO companies (name, category, address, phone, email, website, description)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                company.get('name'),
                category,
                company.get('address'),
                company.get('phone'),
                company.get('email'),
                company.get('website'),
                company.get('description')
            ))
        
        conn.commit()
        conn.close()
    
    def get_companies(self, category=None, search=''):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        query = 'SELECT * FROM companies WHERE 1=1'
        params = []
        
        if category:
            query += ' AND category = ?'
            params.append(category)
        
        if search:
            query += ' AND (name LIKE ? OR address LIKE ? OR description LIKE ?)'
            search_param = f'%{search}%'
            params.extend([search_param, search_param, search_param])
        
        query += ' ORDER BY scraped_at DESC'
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        companies = []
        for row in rows:
            companies.append({
                'id': row['id'],
                'name': row['name'],
                'category': row['category'],
                'address': row['address'],
                'phone': row['phone'],
                'email': row['email'],
                'website': row['website'],
                'description': row['description'],
                'scraped_at': row['scraped_at']
            })
        
        conn.close()
        return companies
    
    def delete_companies(self, category=None):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if category:
            cursor.execute('DELETE FROM companies WHERE category = ?', (category,))
        else:
            cursor.execute('DELETE FROM companies')
        
        conn.commit()
        conn.close()
