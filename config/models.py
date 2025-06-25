GROQ_API_KEY="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"

from langchain_groq import ChatGroq
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent

llm = ChatGroq(
    model_name="llama-3.3-70b-versatile",
    api_key=GROQ_API_KEY 
)

agent = create_react_agent(llm, tools=[])

