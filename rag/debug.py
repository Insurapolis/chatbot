import uvicorn
from fastapi import FastAPI, Body
from fastapi.responses import JSONResponse

from rag.config import Query
from rag.llm import DummyConversation

app = FastAPI()

chain_debug = DummyConversation(model="gpt-3.5-turbo")


@app.post("/chat")
async def chat(
    query: Query = Body(...),
):
    response = chain_debug(query.question)

    return {
        "response": response["response"],
        "total_tokens": response["total_tokens"],
        "mnemory": response["memory"],
    }


@app.post("/clear")
async def clear_conversation():
    chain_debug.clear()
    return JSONResponse({"message": "conversation deleted"})


# if __name__ == "__main__":
#     uvicorn.run("debug:app", host="localhost", port=8000, reload=True)
