from fastapi import FastAPI

app = FastAPI(title="Scaffolded FastAPI Service")

@app.get("/")
def read_root():
    return {"message": "Hello from Scaffolded FastAPI Service!"}
