from main import app

@app.get("/test")
def test():
    return "test"