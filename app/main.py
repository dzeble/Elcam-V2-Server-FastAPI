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
    


import boto3
from typing import List, Optional
from opensearchpy import RequestsHttpConnection
from requests_aws4auth import AWS4Auth

from langchain_community.document_loaders import TextLoader
from langchain_community.vectorstores import OpenSearchVectorSearch
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import CharacterTextSplitter


class OpenSearchIndexer:
    def __init__(
        self,
        opensearch_url: str,
        index_name: str,
        aws_access_key: str,
        aws_secret_key: str,
        region: str = "us-east-2",
        service: str = "es",
        chunk_size: int = 1000,
        chunk_overlap: int = 0,
        openai_api_key: Optional[str] = None,
    ):
        """
        A scalable wrapper for document loading, embedding, and indexing into OpenSearch.
        """

        self.opensearch_url = opensearch_url
        self.index_name = index_name
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

        # AWS auth
        credentials = boto3.Session(
            aws_access_key_id=aws_access_key,
            aws_secret_access_key=aws_secret_key
        ).get_credentials()

        self.awsauth = AWS4Auth(
            aws_access_key, aws_secret_key, region, service, session_token=credentials.token
        )

        # Embeddings
        self.embeddings = OpenAIEmbeddings(openai_api_key=openai_api_key)

        self.vectorstore: Optional[OpenSearchVectorSearch] = None

    def load_and_split(self, file_path: str):
        """Load documents from file and split them into chunks."""
        loader = TextLoader(file_path)
        documents = loader.load()

        splitter = CharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap
        )
        return splitter.split_documents(documents)

    def index_documents(self, docs: List):
        """Embed and index documents into OpenSearch."""
        self.vectorstore = OpenSearchVectorSearch.from_documents(
            docs,
            self.embeddings,
            opensearch_url=self.opensearch_url,
            http_auth=self.awsauth,
            timeout=300,
            use_ssl=True,
            verify_certs=True,
            connection_class=RequestsHttpConnection,
            index_name=self.index_name,
        )

    def search(self, query: str, k: int = 10):
        """Perform similarity search on indexed documents."""
        if not self.vectorstore:
            raise ValueError("Vectorstore not initialized. Call `index_documents` first.")
        return self.vectorstore.similarity_search(query, k=k)


indexer = OpenSearchIndexer(
    opensearch_url="https://your-opensearch-endpoint",
    index_name="test-index",
    aws_access_key="xxxxxx",
    aws_secret_key="xxxxxx",
    region="us-east-2",
    openai_api_key="your-openai-key"
)

# Load + Split
docs = indexer.load_and_split("../../how_to/state_of_the_union.txt")

# Index
indexer.index_documents(docs)

# Search
results = indexer.search("What is feature selection?", k=5)

for r in results:
    print(r.page_content[:200])  # preview
