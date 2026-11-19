from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

app = FastAPI(title="Framework FastAPI Fixture")


class EchoRequest(BaseModel):
    message: str = Field(min_length=1, max_length=50)


@app.post("/echo")
def echo(request: EchoRequest) -> EchoRequest:
    if request.message == "forbidden":
        raise HTTPException(status_code=403, detail="Forbidden message")
    return request
