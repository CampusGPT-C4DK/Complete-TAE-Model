import sys
import os

# Add the tae_model directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    import uvicorn
    # Use import string for reload to work properly
    uvicorn.run("app.main:app", host="0.0.0.0", port=7000, reload=True)
