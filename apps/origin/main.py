from fastapi import FastAPI

app = FastAPI(title="IronShield Origin")


@app.get("/")
@app.get("/home")
def home():
    return {"message": "Welcome to the origin service"}


@app.get("/assets")
def assets():
    return {"assets": ["logo.png", "hero.jpg"]}


@app.get("/api/products")
def products():
    return {"products": [{"id": 1, "name": "Edge Shield"}, {"id": 2, "name": "WAF Pro"}]}


@app.post("/login")
def login(payload: dict):
    return {"status": "ok", "received": payload}
