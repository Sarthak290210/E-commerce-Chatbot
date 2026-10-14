import os
import re
import sqlite3
from pathlib import Path
 
import pandas as pd
from dotenv import load_dotenv
from langchain_groq import ChatGroq
 
load_dotenv()
 
GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")
 
db_path = Path(__file__).parent / "db.sqlite"
 
# LangChain Groq LLM (reads GROQ_API_KEY from the environment / .env)
llm_sql = ChatGroq(
    model=GROQ_MODEL,
    temperature=0.2,
    max_tokens=1024,
)
 
llm_comprehension = ChatGroq(
    model=GROQ_MODEL,
    temperature=0.2,
)
 
sql_prompt = """You are an expert in understanding the database schema and generating SQL queries for a natural language question asked
pertaining to the data you have. The schema is provided in the schema tags. 
<schema> 
table: product 
 
fields: 
product_link - string (hyperlink to product)	
title - string (name of the product)	
brand - string (brand of the product)	
price - integer (price of the product in Indian Rupees)	
discount - float (discount on the product. 10 percent discount is represented as 0.1, 20 percent as 0.2, and such.)	
avg_rating - float (average rating of the product. Range 0-5, 5 is the highest.)	
total_ratings - integer (total number of ratings for the product)
 
</schema>
Make sure whenever you try to search for the brand name, the name can be in any case. 
So, make sure to use %LIKE% to find the brand in condition. Never use "ILIKE". 
Create a single SQL query for the question provided. 
The query should have all the fields in SELECT clause (i.e. SELECT *)

Unless the question asks for a specific number of products, add LIMIT 5.
When the question asks for the best, cheapest, most expensive or top products, use ORDER BY on the relevant column (avg_rating, price, discount) before the LIMIT.
 
Just the SQL query is needed, nothing more. Always provide the SQL in between the <SQL></SQL> tags."""
 
 
comprehension_prompt = """You are an expert in understanding the context of the question and replying based on the data pertaining to the question provided. 
You will be provided Unless the question asks for a specific number of products, add LIMIT 5. When the question asks for the best, cheapest, most expensive or top products, use ORDER BY on the relevant column (avg_rating, price, discount) before the LIMIT.with Question: and Data:. The data will be in the form of an array or a dataframe or dict. 
Reply based on only the data provided as Data for answering the question asked as Question.
Do not write anything like 'Based on the data' or any other technical words. 
Just a plain simple natural language response.
The Data would always be in context to the question asked.
For example is the question is “What is the average rating?” and data is “4.3”, then answer should be “The average rating for the product is 4.3”.
So make sure the response is curated with the question and data. Make sure to note the column names to have some context, if needed, for your response.
There can also be cases where you are given an entire dataframe in the Data: field. Always remember that the data field contains the answer of the question asked.
All you need to do is to always reply in the following format when asked about a product: 
Produt title, price in indian rupees, discount, and rating, and then product link. Take care that all the products are listed in list format, one line after the other.
Not as a paragraph.
For example:
1. Campus Women Running Shoes: Rs. 1104 (35 percent off), Rating: 4.4 <link>
2. Campus Women Running Shoes: Rs. 1104 (35 percent off), Rating: 4.4 <link>
3. Campus Women Running Shoes: Rs. 1104 (35 percent off), Rating: 4.4 <link>
 
"""
 
 
def generate_sql_query(question):
    # A list of (role, content) tuples is sent as-is. No templating happens,
    # so curly braces in the text are safe.
    response = llm_sql.invoke(
        [
            ("system", sql_prompt),
            ("human", question),
        ]
    )
 
    return response.content
 
 
def run_query(query):
    if query.strip().upper().startswith("SELECT"):
        with sqlite3.connect(db_path) as conn:
            df = pd.read_sql_query(query, conn)
            return df
 
 
def data_comprehension(question, context):
    response = llm_comprehension.invoke(
        [
            ("system", comprehension_prompt),
            ("human", f"QUESTION: {question}. DATA: {context}"),
        ]
    )
 
    return response.content
 
 
def sql_chain(question):
    sql_query = generate_sql_query(question)
    pattern = "<SQL>(.*?)</SQL>"
    matches = re.findall(pattern, sql_query, re.DOTALL)
 
    if len(matches) == 0:
        return "Sorry, LLM is not able to generate a query for your question"
 
    print(matches[0].strip())
 
    response = run_query(matches[0].strip())
    if response is None:
        return "Sorry, there was a problem executing SQL query"
 
    context = response.to_dict(orient="records")
 
    answer = data_comprehension(question, context)
    return answer
 
 
if __name__ == "__main__":
    # question = "All shoes with rating higher than 4.5 and total number of reviews greater than 500"
    # sql_query = generate_sql_query(question)
    # print(sql_query)
    question = "Show me all the nike products with rating higher than 4.5 and price greater than 5000"
    # question = "Show me 3 running shoes for woman"
    # question = "sfsdfsddsfsf"
    answer = sql_chain(question)
    print(answer)