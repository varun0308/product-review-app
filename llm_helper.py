from typing import List
from langchain_core.messages import HumanMessage, SystemMessage
from langchain.output_parsers import PydanticOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_core.pydantic_v1 import BaseModel, Field, validator
from langchain_openai import ChatOpenAI
import json
from langchain_core.output_parsers import JsonOutputParser
import re

model = ChatOpenAI(temperature=0)

# SHOULD BE IN UTILS OR SOMETHING - NOT IN LLM HELPER
def extract_from_response(response, aspect):
    pattern = r'POSITIVE|NEUTRAL|NEGATIVE|NOT MENTIONED|[nN]ot (specifically|directly )?[mM]ention(ed)?'

    review = {
        f"raw_{aspect}" : response,
    }
    try:
        # 1st and 3rd question will have one of the key words. 2nd answer will have an explanation
        list_response = [x for x in response.split("\n") if x != '' if x != '\n']
        answers = [re.search(pattern, ans).group() if i != 1 else ans[3:] for i, ans in enumerate(list_response)]
        for i, answer in enumerate(answers):
            if (answer not in ["POSITIVE", "NEUTRAL", "NEGATIVE", "NOT MENTIONED"]) and (i in [0, 2]):
                answers[i] = "NOT MENTIONED"
    except AttributeError as e:
        print(e)
        print("ASPECT:", aspect)
        print(response)
        answers = ["NA", "NA", "NA"]
    review[f"overall_{aspect}"] = answers[0]
    review[aspect+"_opinion"] = answers[1]
    review[aspect] = answers[2] if answers[2] not in ["NOT MENTIONED", "not mentioned", "not mention"] else "NOT MENTIONED"
    
    return review

def extract_aspect_ratings(product_review, aspects):
    system = SystemMessage("""For the given product review, extract the information of aspects mentioned and return the review score as needed for each aspect.
Each aspect must be scored as follows: 
- Check if the aspect is mentioned in the review. 
- If yes, value is 1 for positive review, value is 0 for neutral review and -1 for negative review on this aspect of the product as mentioned in the review. 
- If not mentioned, value is string(NA)

INPUT SCHEMA:
    PRODUCT REVIEW: <Review on the product given by the customer>
    ASPECTS: {{{{
        "aspect 1": <Description of aspect 1>,
        "aspect 2": <Description of aspect 2>,
        and so on
    }}}}
OUTPUT SCHEMA:
    {{{{
        "aspect 1": Score for aspect-1 if this aspect has been mentioned in the review else "NA",
        "aspect 2": Score for aspect-2 if this aspect has been mentioned in the review else "NA",
        and so on
    }}}}
Response should be json readable.""")
        
    human = HumanMessage(content=f"""PRODUCT REVIEW:
{product_review}
ASPECTS:
{aspects}
OUTPUT:
```json""")

    messages = [
        system,
        human
    ]

    return json.loads(model.invoke(messages).content)

def extract_aspect_ratings2(product_review, aspects):
    template = """For the given product review, extract the information of aspects mentioned and return the review score as needed for each aspect.
Each aspect must be scored as follows: 
- Check if the aspect is mentioned in the review. 
- If mentioned, Score 1 for positive review, 0 for neutral review and -1 for negative review as mentioned in the review. 
- If not mentioned, score is string(NA)

FORMAT_INSTRUCTIONS: {format_instructions}

INPUT SCHEMA:
    PRODUCT REVIEW: <Review on the product given by the customer>
    ASPECTS: {{{{
        "aspect 1": <Description of aspect 1>,
        and so on
    }}}}
OUTPUT SCHEMA:
    {{{{
        "aspect 1": Score for aspect-1 if this aspect has been mentioned in the review else string(NA),
        and so on
    }}}}
Response should be json readable.
        
PRODUCT REVIEW: {product_review}
ASPECTS: {aspects}
OUTPUT: ```json
"""

    parser = JsonOutputParser()
    prompt = PromptTemplate(
        template=template,
        input_variables=["product_review", "aspects"],
        partial_variables={"format_instructions": parser.get_format_instructions()}
    )
    chain = prompt | model | parser
    response = chain.invoke({"product_review":product_review, "aspects": aspects})

    return response

def extract_imp_aspects(product):
    system = SystemMessage("""For a given product, return a python dictionary of top 5 common aspects that a customer would look for in that product and what each aspect means. 
Return only a python dictionary with 5 items, it should be JSON readable.

Example:
PRODUCT: Redmi 12 5G 4GB RAM 128GB ROM
ASPECTS: {
    "camera_quality": "The clarity, resolution, and overall performance of the mobile phone's camera(s)",
    "appearance": "The design, aesthetics, and build quality of the mobile phone, including its materials and color options.",
    "value_for_money": "The overall worth of the mobile phone in relation to its price, considering its features, performance, and durability.",
    "battery_life": "The duration for which the mobile phone can operate on a single charge",
    "processing_power": "The speed and efficiency of the mobile phone's processor and hardware."}""")
        
    human = HumanMessage(content=f"""PRODUCT: {product}
ASPECTS: """)

    messages = [
        system,
        human
    ]
    return json.loads(model.invoke(messages).content)

def extract_aspect_ratings3(product_review, aspects, rating):
    reviews = {}
    reviews["review_content"] = product_review
    reviews["review_rating"] = rating
    
    for i, (aspect, aspect_definition) in enumerate(aspects.items()):
        prompt = f"""You are an e-commerce review analysis agent. You can accurately analyze the reviews and assign sentiments to the overall review and to the aspects of the product/service.
        
REVIEW: {product_review}
Understand the review and answer the following questions on {aspect}({aspect_definition})
1. What is the sentiment of the overall review? RESPOND WITH: The overall review is POSITIVE/NEUTRAL/NEGATIVE only
2. What does the reviewer talk about the {aspect}?
3. What is the reviewer's opinion on the {aspect}? RESPOND WITH: Sentiment on {aspect} is POSITIVE/NEUTRAL/NEGATIVE/NOT MENTIONED only
""" 
        response = model.invoke(prompt).content
        review = extract_from_response(response, aspect)
        reviews.update(review)
        
    return reviews