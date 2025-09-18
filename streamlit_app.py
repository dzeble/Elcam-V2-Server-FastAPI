import streamlit as st
import PyPDF2
from io import BytesIO
import requests
import json
from opensearchpy import OpenSearch, RequestsHttpConnection, AWSV4SignerAuth
import boto3
import os
from dotenv import load_dotenv
import hashlib
from datetime import datetime

load_dotenv()

# OpenSearch client initialization
@st.cache_resource
def get_opensearch_client():
    host = os.getenv("AWS_HOST").strip("'\"")
    region = os.getenv("AWS_REGION")
    service = os.getenv("AWS_SERVICE")
    
    if not host:
        raise RuntimeError("Missing AWS_HOST environment variable")
    
    session = boto3.Session(
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
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

def extract_text_from_pdf(pdf_file):
    """Extract text content from uploaded PDF file"""
    try:
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        text_content = ""
        
        for page_num in range(len(pdf_reader.pages)):
            page = pdf_reader.pages[page_num]
            text_content += page.extract_text() + "\n"
        
        return text_content.strip()
    except Exception as e:
        st.error(f"Error extracting text from PDF: {str(e)}")
        return None

def chunk_text(text, chunk_size=1000, overlap=200):
    """Split text into overlapping chunks for better search"""
    chunks = []
    start = 0
    
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        
        # Find the last complete sentence or word boundary
        if end < len(text):
            last_period = chunk.rfind('.')
            last_space = chunk.rfind(' ')
            boundary = max(last_period, last_space)
            if boundary > start + chunk_size // 2:
                end = start + boundary + 1
                chunk = text[start:end]
        
        chunks.append({
            "text": chunk.strip(),
            "start_position": start,
            "end_position": end,
            "chunk_id": len(chunks)
        })
        
        start = end - overlap
        if start >= len(text):
            break
    
    return chunks

def index_pdf_document(client, pdf_name, text_content, index_name="pdf_documents"):
    """Index PDF content into OpenSearch"""
    try:
        # Create index if it doesn't exist
        index_mapping = {
            "mappings": {
                "properties": {
                    "filename": {"type": "text"},
                    "content": {"type": "text"},
                    "chunk_id": {"type": "integer"},
                    "start_position": {"type": "integer"},
                    "end_position": {"type": "integer"},
                    "upload_date": {"type": "date"},
                    "file_hash": {"type": "keyword"}
                }
            }
        }
        
        client.indices.create(index=index_name, body=index_mapping, ignore=400)
        
        # Generate file hash for deduplication
        file_hash = hashlib.md5(text_content.encode()).hexdigest()
        
        # Check if document already exists
        existing_docs = client.search(
            index=index_name,
            body={"query": {"term": {"file_hash": file_hash}}},
            size=1
        )
        
        if existing_docs['hits']['total']['value'] > 0:
            return {"status": "exists", "message": "Document already indexed"}
        
        # Chunk the text content
        chunks = chunk_text(text_content)
        
        # Index each chunk
        indexed_chunks = 0
        for chunk in chunks:
            doc = {
                "filename": pdf_name,
                "content": chunk["text"],
                "chunk_id": chunk["chunk_id"],
                "start_position": chunk["start_position"],
                "end_position": chunk["end_position"],
                "upload_date": datetime.now().isoformat(),
                "file_hash": file_hash
            }
            
            response = client.index(index=index_name, body=doc)
            if response.get('result') == 'created':
                indexed_chunks += 1
        
        return {"status": "success", "chunks_indexed": indexed_chunks}
        
    except Exception as e:
        return {"status": "error", "message": str(e)}

def search_documents(client, query, index_name="pdf_documents", size=10):
    """Search through indexed PDF documents"""
    try:
        search_body = {
            "query": {
                "bool": {
                    "should": [
                        {"match": {"content": {"query": query, "boost": 2}}},
                        {"match_phrase": {"content": {"query": query, "boost": 3}}},
                        {"match": {"filename": {"query": query, "boost": 1}}}
                    ]
                }
            },
            "highlight": {
                "fields": {
                    "content": {
                        "fragment_size": 200,
                        "number_of_fragments": 3
                    }
                }
            },
            "sort": [
                {"_score": {"order": "desc"}}
            ],
            "size": size
        }
        
        response = client.search(index=index_name, body=search_body)
        return response['hits']
        
    except Exception as e:
        return {"error": str(e)}

def main():
    st.set_page_config(
        page_title="PDF Search Engine",
        page_icon="📚",
        layout="wide"
    )
    
    st.title("📚 PDF Document Search Engine")
    st.markdown("Upload PDF documents and search through their content using OpenSearch")
    
    # Initialize OpenSearch client
    try:
        client = get_opensearch_client()
        st.success("✅ Connected to OpenSearch successfully!")
    except Exception as e:
        st.error(f"❌ Failed to connect to OpenSearch: {str(e)}")
        st.stop()
    
    # Create tabs
    tab1, tab2, tab3 = st.tabs(["📤 Upload PDF", "🔍 Search Documents", "📊 Document Stats"])
    
    with tab1:
        st.header("Upload PDF Documents")
        
        uploaded_files = st.file_uploader(
            "Choose PDF files",
            type="pdf",
            accept_multiple_files=True,
            help="Upload one or more PDF files to index their content"
        )
        
        if uploaded_files:
            for uploaded_file in uploaded_files:
                with st.expander(f"Processing: {uploaded_file.name}", expanded=True):
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        if st.button(f"Index {uploaded_file.name}", key=uploaded_file.name):
                            with st.spinner(f"Processing {uploaded_file.name}..."):
                                # Extract text
                                text_content = extract_text_from_pdf(uploaded_file)
                                
                                if text_content:
                                    st.success(f"✅ Extracted {len(text_content)} characters from PDF")
                                    
                                    # Preview first 500 characters
                                    st.text_area(
                                        "Content Preview:",
                                        text_content[:500] + "..." if len(text_content) > 500 else text_content,
                                        height=100,
                                        disabled=True
                                    )
                                    
                                    # Index the document
                                    result = index_pdf_document(client, uploaded_file.name, text_content)
                                    
                                    if result["status"] == "success":
                                        st.success(f"✅ Successfully indexed {result['chunks_indexed']} chunks from {uploaded_file.name}")
                                    elif result["status"] == "exists":
                                        st.warning(f"⚠️ {result['message']}")
                                    else:
                                        st.error(f"❌ Error indexing document: {result['message']}")
                                else:
                                    st.error("❌ Failed to extract text from PDF")
                    
                    with col2:
                        st.metric("File Size", f"{uploaded_file.size / 1024:.1f} KB")
    
    with tab2:
        st.header("Search Documents")
        
        col1, col2 = st.columns([3, 1])
        with col1:
            search_query = st.text_input(
                "Enter your search query:",
                placeholder="e.g., machine learning, data analysis, etc."
            )
        with col2:
            num_results = st.selectbox("Results", [5, 10, 20, 50], index=1)
        
        if search_query:
            with st.spinner("Searching..."):
                results = search_documents(client, search_query, size=num_results)
                
                if "error" in results:
                    st.error(f"Search error: {results['error']}")
                elif results['total']['value'] == 0:
                    st.warning("No results found for your query.")
                else:
                    st.success(f"Found {results['total']['value']} results")
                    
                    for idx, hit in enumerate(results['hits']):
                        source = hit['_source']
                        score = hit['_score']
                        
                        with st.expander(f"📄 {source['filename']} (Score: {score:.2f})", expanded=idx < 3):
                            st.markdown(f"**File:** {source['filename']}")
                            st.markdown(f"**Chunk:** {source['chunk_id']} | **Position:** {source['start_position']}-{source['end_position']}")
                            st.markdown(f"**Upload Date:** {source['upload_date']}")
                            
                            # Show highlighted content if available
                            if 'highlight' in hit and 'content' in hit['highlight']:
                                st.markdown("**Highlighted Matches:**")
                                for highlight in hit['highlight']['content']:
                                    st.markdown(f"...{highlight}...", unsafe_allow_html=True)
                            else:
                                st.markdown("**Content:**")
                                content_preview = source['content'][:500]
                                if len(source['content']) > 500:
                                    content_preview += "..."
                                st.text(content_preview)
    
    with tab3:
        st.header("Document Statistics")
        
        try:
            # Get index stats
            index_stats = client.indices.stats(index="pdf_documents")
            doc_count = index_stats['indices']['pdf_documents']['total']['docs']['count']
            index_size = index_stats['indices']['pdf_documents']['total']['store']['size_in_bytes']
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Chunks", doc_count)
            with col2:
                st.metric("Index Size", f"{index_size / 1024 / 1024:.2f} MB")
            with col3:
                # Get unique files count
                unique_files = client.search(
                    index="pdf_documents",
                    body={
                        "size": 0,
                        "aggs": {
                            "unique_files": {
                                "cardinality": {
                                    "field": "file_hash"
                                }
                            }
                        }
                    }
                )
                unique_count = unique_files['aggregations']['unique_files']['value']
                st.metric("Unique Documents", unique_count)
            
            # Show recent documents
            st.subheader("Recent Documents")
            recent_docs = client.search(
                index="pdf_documents",
                body={
                    "size": 10,
                    "query": {"match_all": {}},
                    "sort": [{"upload_date": {"order": "desc"}}],
                    "collapse": {"field": "file_hash"}
                }
            )
            
            if recent_docs['hits']['hits']:
                for hit in recent_docs['hits']['hits']:
                    source = hit['_source']
                    st.write(f"📄 **{source['filename']}** - {source['upload_date']}")
            else:
                st.info("No documents indexed yet.")
                
        except Exception as e:
            st.error(f"Error fetching statistics: {str(e)}")

if __name__ == "__main__":
    main()