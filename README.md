# ShopEasy Support

An AI customer support desk for an online store.
A customer writes a message. A team of AI agents solves every problem in it and writes one email back.

---

## Commands (Mac)

**One time only**
```bash
cd ~/Downloads
unzip shop_support.zip
cd shop_support
bash setup.sh
```
A text window opens. Paste your Groq key (free at https://console.groq.com/keys), save, close.

**Every time**
```bash
cd ~/Downloads/shop_support
bash start.sh
```

**See the graph as a picture**
```bash
cd ~/Downloads/shop_support
source venv/bin/activate
python draw_graph.py
```
Open `graph.mmd`, copy everything, paste it at https://mermaid.live

**Windows:** double-click `setup_windows.bat` one time, then `start_windows.bat` every time.

---

## Try these messages

| Message | What happens |
|---|---|
| `Where is my order 1002?` | The order agent asks the MCP server |
| `I want a refund for order 1001. Do you accept cash on delivery?` | Two specialists work at the same time |
| `This is the worst! Order 1002 is late and I want my money back for order 1003!` | It stops and asks **you** (the manager) to approve $220 |
| `Is the smart watch in stock?` | The hand-built agent uses its tool |
| `sara`, then `I want my money back for order 1003` | Refused: it's not Sara's order |
| `quit` | Stop |

---

## The files (read them in this order)

| File | What's inside |
|---|---|
| `llm.py` | The AI model, prompts, chains, structured output |
| `tools.py` | The store's data and tools |
| `rag.py` | RAG: search the policy documents |
| `refund_team.py` | A subgraph: refund rules in plain Python |
| `product_team.py` | An agent built by hand: agent ⇄ tools loop |
| `nodes.py` | The state + every step of the main graph |
| `graph.py` | Connects all the steps |
| `mcp_server.py` | The order system, shared with MCP |
| `main.py` | Runs everything (START HERE) |
| `draw_graph.py` | Saves a picture of the graph |
| `docs/` | Policy documents for RAG |
| `data/orders.json` | The orders |

---

## Concepts in this project

**LangChain:** ChatGroq model · prompt templates · chains (`prompt | llm | parser`) · structured output · tools · bind_tools · ready-made agent (`create_agent`) · RAG (load, split, embeddings, vector store, retriever)

**LangGraph:** state · reducers (`operator.add`, `add_messages`) · nodes and edges · conditional edges · nodes running at the same time · `Send` (one worker per problem) · subgraph · `ToolNode` + `tools_condition` · `Command` · loop with a limit · human-in-the-loop (`interrupt`) · checkpointer · store (long-term memory) · retry policy · streaming · async node

**MCP:** server with a tool, a resource and a prompt · `MultiServerMCPClient` · MCP tools inside an agent

---

## Problems?

| Problem | Fix |
|---|---|
| `GROQ_API_KEY` error | Put your key in the `.env` file |
| `No such file: data/orders.json` | Run the app from inside the `shop_support` folder |
| `rate limit` error | Groq free limit. Wait one minute |
| `model not found` | Change the model name in `llm.py` |
