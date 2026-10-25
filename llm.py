"""
llm.py — the AI model, the prompts, and the "forms" the AI fills in.
"""

from typing import Literal

from dotenv import load_dotenv
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
from pydantic import BaseModel, Field

load_dotenv()  # reads your GROQ_API_KEY from the .env file

# The AI model. temperature=0 means calm, predictable answers.
llm = ChatGroq(model="openai/gpt-oss-120b", temperature=0)


# ---------- CHAINS:  prompt | llm | parser ----------
# A chain fills in the prompt, sends it to the AI, and gives back plain text.

mood_prompt = ChatPromptTemplate.from_template(
    "Is this customer calm, upset or angry? Answer with ONE word.\n\nMessage: {ticket}")
mood_chain = mood_prompt | llm | StrOutputParser()

reply_prompt = ChatPromptTemplate.from_template("""
You are a friendly support agent for ShopEasy, an online store.
Write a short email reply to {name}.
If the customer is upset or angry, start with a short apology.
Answer every point, using ONLY the team's answers below.
Sign the email as "ShopEasy Support".

Customer's past contact: {history}
Customer's mood: {mood}
Customer's message: {ticket}
Team's answers:
{answers}
""")
reply_chain = reply_prompt | llm | StrOutputParser()

rewrite_prompt = ChatPromptTemplate.from_template(
    "Improve this support email.\n\nEmail:\n{reply}\n\nWhat to fix: {feedback}")
rewrite_chain = rewrite_prompt | llm | StrOutputParser()


# ---------- STRUCTURED OUTPUT: forms the AI fills in ----------
# Use it like this:  llm.with_structured_output(IssueList).invoke("...")

class Issue(BaseModel):
    kind: Literal["order_status", "refund", "policy_question", "product_question"] = Field(
        description="order_status = where is my order. refund = wants money back. "
                    "policy_question = shipping, returns, warranty or payment rules. "
                    "product_question = price or stock of a product.")
    order_id: str = Field(default="", description="The order number if given, digits only")
    detail: str = Field(description="The customer's question in one short sentence")


class IssueList(BaseModel):
    issues: list[Issue]


class Review(BaseModel):
    is_good: bool = Field(description="True if the email is polite and answers every point")
    feedback: str = Field(description="What to fix, or 'ok'")
