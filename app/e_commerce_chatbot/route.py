from semantic_router import Route
from semantic_router.encoders import HuggingFaceEncoder
from semantic_router import SemanticRouter

encoder = HuggingFaceEncoder(
    name="sentence-transformers/all-MiniLM-L6-v2"
)

faq = Route(
    name='faq',
    utterances=[
        "What is your policy on defective products?",
        "What happens if I get a faulty item?",
        "What should I do if I receive a damaged product?",
        "How do I return an item?",
        "What is the return policy?",
        "Can I exchange a product that doesn't fit?",
        "How can I contact customer support?",
        "What is the warranty on your products?",
        "Is there a delivery charge?",
        "When will my order arrive?",
        "Can I change my delivery address?",
        "Can I cancel or modify my order?",
        "What is your privacy policy?",
        "How can I track my order?",
        "What payment methods do you accept?",
        "Do you accept UPI or cash on delivery?",
        "How long does a refund take?",
        "Do you ship internationally?",
        "Do I get a discount with a credit card?",
        "Which card gives a discount?",
        "Is there a discount on HDFC credit card?",
        "Are there any ongoing sales or promotions?",
        "How do I use a promo code?",
        "Received a defective product, what should I do?",
        "It's been 5 days and I haven't received my order, how to track my order?",
    ]
)

sql = Route(
    name='sql',
    utterances=[
        "I want to buy nike shoes that have 50% discount.",
        "Are there any shoes under Rs. 3000?",
        "Do you have formal shoes in size 9?",
        "Are there any Puma shoes on sale?",
        "What is the price of puma running shoes?",
        "Show me black Adidas sneakers under 4000",
        "Pink Puma shoes in price range 1000 to 5000",
        "Cheapest running shoes you have",
        "Which shoes are available in size 8?",
        "List all Nike products with more than 30% discount",
        "Do you have white sneakers for men?",
        "Show me women's sandals below 2000",
        "What is the most expensive shoe in your store?",
        "Any red Reebok shoes available?",
        "Best rated sports shoes under Rs. 5000",
    ]
)

router = SemanticRouter(routes=[faq, sql], encoder=encoder, auto_sync="local")

if __name__ == "__main__":
    # Test cases with safe evaluation using .name
    query_1 = router("What is your policy on defective product?")
    query_2 = router("Pink Puma shoes in price range 5000 to 1000")

    # Safely printing the results
    print(f"Query 1 Route: {query_1.name}")
    print(f"Query 2 Route: {query_2.name}")

    # Example of a query that triggers no route fallback safely
    query_3 = router("Tell me a joke about programming.")
    print(f"Query 3 Route: {query_3.name}")