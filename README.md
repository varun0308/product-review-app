# Product review App

A detailed product review, directly taken from a product description page, compressed as per requirements
Steps of approach:
- Extract the contents from the page
- Use the title, price, basic description from the page(all these are available under fixed key across products)
- Get N number of reviews
- Prompt to LLM for extraction of overall sentiment and aspect-wise sentiment.
- Display on streamlit App

  
TODO: Automatically extract the HTML content(right now that is the only step that is manual)
