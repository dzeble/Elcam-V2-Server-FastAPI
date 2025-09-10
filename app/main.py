from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from opensearchpy import OpenSearch, RequestsHttpConnection, AWSV4SignerAuth
import boto3
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

# Pydantic model for indexing
class Doc(BaseModel):
    name: str
    value: int

# OpenSearch client initialization
def get_client():
    host = os.getenv("AWS_HOST")
    region = os.getenv("AWS_REGION")
    service = os.getenv("AWS_SERVICE")

    
    if not host:
        raise RuntimeError("Missing OPENSEARCH_HOST environment variable")
    
    # credentials = boto3.Session().get_credentials()
    session = boto3.Session(
    aws_access_key_id= os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key= os.getenv("AWS_SECRET_ACCESS_KEY"),
)
    credentials = session.get_credentials()

    if not credentials or not credentials.access_key or not credentials.secret_key:
        raise RuntimeError("AWS credentials are missing or not loaded")

    auth = AWSV4SignerAuth(credentials, region, service)
    return OpenSearch(
        hosts=[{"host": host, "port": 443}],
        http_auth=auth,
        use_ssl=True,
        verify_certs=True,
        connection_class=RequestsHttpConnection,
        pool_maxsize=20,
        timeout=30,               
        max_retries=3,            
        retry_on_timeout=True   
    )

@app.post("/index/{index_name}")
async def index_document(index_name: str, doc: Doc):
    client = get_client()
    try:
        client.indices.create(index=index_name, ignore=400)
        resp = client.index(index=index_name, body=doc.dict())
        return resp
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/search/{index_name}")
async def search_docs(index_name: str, query: str):
    client = get_client()
    try:
        body = {"query": {"match": {"name": query}}}
        resp = client.search(index=index_name, body=body)
        return resp
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))