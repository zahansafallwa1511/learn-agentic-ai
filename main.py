from fastapi import FastAPI


app = FastAPI()

@app.get("/")
async def read_root():
    return {"Hello": "World"}

@app.get("/products")
async def read_products():
    return {"products": ["Product 1", "Product 2", "Product 3"]}