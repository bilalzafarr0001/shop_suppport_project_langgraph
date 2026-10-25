"""
rag.py — RAG: answer questions from the store's policy documents.

The 6 steps:
  1. Load the documents
  2. Split them into small pieces
  3. Turn each piece into numbers (embeddings)
  4. Keep the numbers in a vector store
  5. Find the pieces closest to the question (retriever)
  6. Let the AI answer using only those pieces
"""

from pathlib import Path

from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_text_splitters import RecursiveCharacterTextSplitter

from llm import llm

# 1. Load
documents = []
for file in Path("docs").glob("*.md"):
    documents.append(Document(page_content=file.read_text(), metadata={"source": file.name}))

# 2. Split
splitter = RecursiveCharacterTextSplitter(chunk_size=200, chunk_overlap=0)
pieces = splitter.split_documents(documents)


# 3. Embeddings = turn text into a list of numbers.
# Our simple version: one number for each keyword = how many times it appears in the text.
# (Real projects use a model like OpenAIEmbeddings. The idea is the same.)
KEYWORDS = ["ship", "deliver", "track", "free", "fee", "return", "refund", "money", "days",
            "warranty", "defect", "damage", "pay", "cash", "card", "parts"]


class KeywordEmbeddings(Embeddings):

    def embed_query(self, text):
        text = text.lower()
        numbers = []
        for word in KEYWORDS:
            numbers.append(text.count(word))
        numbers.append(1)   # one extra 1, so the list is never all zeros (the math needs that)
        return numbers

    def embed_documents(self, texts):
        all_numbers = []
        for text in texts:
            all_numbers.append(self.embed_query(text))
        return all_numbers


# 4. Vector store
vector_store = InMemoryVectorStore.from_documents(pieces, KeywordEmbeddings())

# 5. Retriever: gives back the 2 closest pieces
retriever = vector_store.as_retriever(search_kwargs={"k": 2})

# 6. Answer
rag_prompt = ChatPromptTemplate.from_template(
    "Answer the question using ONLY this store policy. "
    "If the answer is not there, say our team will check.\n\n"
    "Policy:\n{policy}\n\nQuestion: {question}")
rag_chain = rag_prompt | llm | StrOutputParser()


def answer_from_policies(question):
    best_pieces = retriever.invoke(question)
    policy = ""
    for piece in best_pieces:
        policy = policy + piece.page_content + "\n"
    return rag_chain.invoke({"policy": policy, "question": question})
