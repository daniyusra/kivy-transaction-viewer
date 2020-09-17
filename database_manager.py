# -*- coding: utf-8 -*-
"""
Created on Tue Aug 18 00:00:02 2020

@author: ASUS
"""

import sqlite3

class DatabaseManager:
    def __init__(self):
        self.conn = sqlite3.connect('database.db')
        
        self.c = self.conn.cursor()
        
        self.c.execute(''' SELECT count(name) FROM sqlite_master WHERE type='table' AND name='details' ''')


        if self.c.fetchone()[0]==1 :
        	print('Table details exists.')
        else:
            self.c.execute(""" CREATE TABLE IF NOT EXISTS details(
                            details_id INTEGER PRIMARY KEY ,
                            name text,
                            type integer
                        ); """)
            self.c.execute(""" INSERT INTO details(name,type) VALUES ('Groceries',0)""")
            self.c.execute("""INSERT INTO details(name,type) VALUES ('Income',1)""")
            #IMPORTANT: TYPE 0 is SPENDING, TYPE 1 is EARNINGS!
        
        

        self.c.execute(""" CREATE TABLE IF NOT EXISTS transactions (
                transaction_id INTEGER PRIMARY KEY ,
                date text NOT NULL ,
                amount real NOT NULL CHECK (amount != 0),
                details_id integer ,
                notes text,
                FOREIGN KEY (details_id) REFERENCES details(details_id)        
                    ON UPDATE CASCADE
                    ON DELETE SET NULL
            ); """)
    
    #FOR TRANSACTIONS
    
    #CREATE
    def transaction_create(self,date,amount,details_id = None, notes = None):
        with self.conn:
            self.c.execute("INSERT INTO transactions(date,amount,details_id,notes) VALUES (?, ?, ?,?)",(date,amount,details_id,notes))
            
    #RETRIEVE
    def transaction_get_spendings(self, details = None, date_start = None, date_end = None):
        if date_end is None:
            self.c.execute("SELECT date FROM transactions ORDER BY date DESC LIMIT 1")
            date_end = self.c.fetchone()[0]
        
        if date_start is None:
            self.c.execute("SELECT date FROM transactions ORDER BY date ASC LIMIT 1 ")
            date_start = self.c.fetchone()[0]
            
        if details is None:
            sql="SELECT * FROM transactions WHERE amount < 0 AND date BETWEEN ? AND ? "
            request = []
            request.append(date_start)
            request.append(date_end)
            
            self.c.execute(sql,request)
            return self.c.fetchall()
        
        
        h_details = [ detail[0] for detail in details ]
        request = h_details.copy()
        
        sql="SELECT * FROM transactions WHERE details_id in ({seq}) AND amount < 0 AND date BETWEEN ? AND ? ORDER BY date DESC ".format(seq=','.join(['?']*len(h_details)))
        

        
        request.append(date_start)
        request.append(date_end)
        self.c.execute(sql,request)
        return self.c.fetchall()
            
            
    def transaction_get_earnings(self, details = None, date_start = None, date_end = None):
        if date_end is None:
            self.c.execute("SELECT date FROM transactions ORDER BY date DESC LIMIT 1")
            date_end = self.c.fetchone()[0]
        
        if date_start is None:
            self.c.execute("SELECT date FROM transactions ORDER BY date ASC LIMIT 1")
            date_start = self.c.fetchone()[0]
            
        if details is None:
            sql="SELECT * FROM transactions WHERE amount > 0 AND date BETWEEN ? AND ? ORDER BY date DESC "
            request = []
            request.append(date_start)
            request.append(date_end)
            
            self.c.execute(sql,request)
            return self.c.fetchall()
        
        
        h_details = [ detail[0] for detail in details ]
        request = h_details.copy()
        request.append(date_start)
        request.append(date_end)
        
        sql="SELECT * FROM transactions WHERE details_id in ({seq}) AND amount > 0 AND date BETWEEN ? AND ? ORDER BY date DESC ".format(seq=','.join(['?']*len(h_details)))
        
        self.c.execute(sql,request)
        return self.c.fetchall()
    
    def transaction_get_all(self):
        self.c.execute("SELECT * FROM transactions ORDER BY date DESC ")
        return self.c.fetchall()
    
    def transaction_get_by_id(self, transaction_id):
        self.c.execute("SELECT * FROM transactions where transaction_id = ? ", (transaction_id,))
        return self.c.fetchall()
        
            
    #UPDATE
    def transaction_update(self,transaction_id, date , amount , details_id = None, notes = None ):
        with self.conn:
            # if date is None:
            #      self.c.execute("SELECT date FROM transactions WHERE transaction_id = ? LIMIT 1", (transaction_id,))
            #      date = self.c.fetchone()[0]
            
            # if amount is None:
            #      self.c.execute("SELECT amount FROM transactions WHERE transaction_id = ? LIMIT 1", (transaction_id,))
            #      amount = self.c.fetchone()[0]

            # if details_id is None:
            #      self.c.execute("SELECT details_id FROM transactions WHERE transaction_id = ? LIMIT 1", (transaction_id,))
            #      details_id = self.c.fetchone()[0]                 
            
            # if notes is None:
            #      self.c.execute("SELECT notes FROM transactions WHERE transaction_id = ? LIMIT 1", (transaction_id,))
            #      notes = self.c.fetchone()[0] 

            self.c.execute(""" UPDATE transactions
                                SET date = ? ,
                                    amount = ?,
                                    details_id = ? ,
                                    notes = ?
                                WHERE
                                    transaction_id = ?; 
                                    
                                    """, (date,amount,details_id,notes,transaction_id))                      
    #DELETE
    
    def transaction_delete(self,transaction_id):
        with self.conn:
            self.c.execute("DELETE FROM transactions WHERE transaction_id =  ? ", (transaction_id,))
        
    
    #FOR DETAILS
    #CREATE
    def details_create(self,name,transaction_type):
        with self.conn:
            self.c.execute(""" INSERT INTO details(name,type) VALUES (?,?)""",(name,transaction_type))
        
    #READ
    def details_read_all(self):
        self.c.execute(""" SELECT * FROM details ORDER BY details_id""")
        return self.c.fetchall()

    def details_read_by_type(self,transaction_type):
        self.c.execute(""" SELECT * FROM details WHERE type = ?""", (transaction_type,))
        return self.c.fetchall()
    
    def details_read_by_id(self,details_id = None):
        self.c.execute(""" SELECT * FROM details WHERE details_id = ?""",(details_id,))
        return self.c.fetchall()
    
    #UPDATE
    def details_update(self, details_id, name = None, transaction_type = None):
        with self.conn:
            if transaction_type is None:
                 self.c.execute("SELECT transaction_type FROM details WHERE details_id= ? LIMIT 1", (details_id,))
                 transaction_type = self.c.fetchone()[0]
            
            if name is None:
                 self.c.execute("SELECT name FROM details WHERE details_id = ? LIMIT 1", (details_id,))
                 name = self.c.fetchone()[0]  
                 
            self.c.execute(""" UPDATE details
                                                SET name= ? ,
                                                    type = ?
                                                WHERE
                                                    details_id = ?; 
                                                    
                                                    """, (name, transaction_type ,details_id))  
                
    #DELETE
    def details_delete(self,details_id):
        with self.conn:
            self.c.execute("DELETE FROM details WHERE details_id =  ? ",(details_id,))
        
    
    #delete
    def __del__(self):    
        #commit the changes to db			
        self.conn.commit()
        #close the connection
        self.conn.close()
        
