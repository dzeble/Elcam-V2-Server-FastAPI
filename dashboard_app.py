import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
from opensearchpy import OpenSearch, RequestsHttpConnection, AWSV4SignerAuth
import boto3
import os
from dotenv import load_dotenv
from collections import defaultdict
import time

load_dotenv()

# Page configuration
st.set_page_config(
    page_title="OpenSearch Analytics Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin: 0.5rem 0;
    }
    .section-header {
        font-size: 1.5rem;
        color: #2c3e50;
        border-bottom: 2px solid #3498db;
        padding-bottom: 0.5rem;
        margin: 1.5rem 0 1rem 0;
    }
    .success-box {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 5px;
        padding: 1rem;
        margin: 1rem 0;
    }
    .warning-box {
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        border-radius: 5px;
        padding: 1rem;
        margin: 1rem 0;
    }
    .error-box {
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        border-radius: 5px;
        padding: 1rem;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_resource
def get_opensearch_client():
    """Initialize OpenSearch client with AWS authentication"""
    try:
        host = os.getenv("AWS_HOST").strip("'\"")
        region = os.getenv("AWS_REGION")
        service = os.getenv("AWS_SERVICE")
        
        session = boto3.Session(
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        )
        credentials = session.get_credentials()
        
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
    except Exception as e:
        st.error(f"Failed to connect to OpenSearch: {str(e)}")
        return None

def get_cluster_health(client):
    """Get OpenSearch cluster health information"""
    try:
        health = client.cluster.health()
        return health
    except Exception as e:
        st.error(f"Error getting cluster health: {str(e)}")
        return None

def get_index_stats(client, index_name="pdf_documents"):
    """Get detailed index statistics"""
    try:
        stats = client.indices.stats(index=index_name)
        return stats
    except Exception as e:
        st.error(f"Error getting index stats: {str(e)}")
        return None

def get_node_info(client):
    """Get OpenSearch node information"""
    try:
        nodes = client.nodes.info()
        return nodes
    except Exception as e:
        st.error(f"Error getting node info: {str(e)}")
        return None

def search_analytics(client, index_name="pdf_documents"):
    """Get search analytics and popular terms"""
    try:
        # Get document count by upload date
        upload_timeline = client.search(
            index=index_name,
            body={
                "size": 0,
                "aggs": {
                    "uploads_over_time": {
                        "date_histogram": {
                            "field": "upload_date",
                            "calendar_interval": "day",
                            "min_doc_count": 1
                        }
                    }
                }
            }
        )
        
        # Get file type distribution
        file_distribution = client.search(
            index=index_name,
            body={
                "size": 0,
                "aggs": {
                    "unique_files": {
                        "terms": {
                            "field": "filename.keyword",
                            "size": 20
                        },
                        "aggs": {
                            "chunks": {
                                "value_count": {
                                    "field": "chunk_id"
                                }
                            }
                        }
                    }
                }
            }
        )
        
        # Get content size distribution (simplified - remove problematic script)
        content_size_dist = None  # Temporarily disabled due to script issues
        
        return {
            "upload_timeline": upload_timeline,
            "file_distribution": file_distribution,
            "content_size_dist": content_size_dist
        }
    except Exception as e:
        st.error(f"Error getting search analytics: {str(e)}")
        return None

def get_search_performance_metrics(client, index_name="pdf_documents"):
    """Simulate search performance metrics"""
    try:
        # Perform sample searches to get performance data
        search_terms = ["machine learning", "data", "algorithm", "neural network", "artificial intelligence"]
        performance_data = []
        
        for term in search_terms:
            start_time = time.time()
            result = client.search(
                index=index_name,
                body={
                    "query": {"match": {"content": term}},
                    "size": 10
                }
            )
            end_time = time.time()
            
            performance_data.append({
                "search_term": term,
                "response_time_ms": round((end_time - start_time) * 1000, 2),
                "total_hits": result['hits']['total']['value'],
                "max_score": result['hits']['max_score'] if result['hits']['hits'] else 0
            })
        
        return performance_data
    except Exception as e:
        st.error(f"Error getting search performance: {str(e)}")
        return []

def create_upload_timeline_chart(upload_data):
    """Create upload timeline visualization"""
    if not upload_data or 'aggregations' not in upload_data:
        return None
    
    buckets = upload_data['aggregations']['uploads_over_time']['buckets']
    if not buckets:
        return None
    
    dates = [bucket['key_as_string'][:10] for bucket in buckets]
    counts = [bucket['doc_count'] for bucket in buckets]
    
    fig = px.line(
        x=dates, 
        y=counts,
        title="Document Upload Timeline",
        labels={"x": "Date", "y": "Documents Uploaded"},
        markers=True
    )
    fig.update_layout(
        xaxis_title="Date",
        yaxis_title="Number of Chunks Uploaded",
        hovermode='x unified'
    )
    return fig

def create_file_distribution_chart(file_data):
    """Create file distribution pie chart"""
    if not file_data or 'aggregations' not in file_data:
        return None
    
    buckets = file_data['aggregations']['unique_files']['buckets']
    if not buckets:
        return None
    
    files = [bucket['key'] for bucket in buckets[:10]]  # Top 10 files
    chunk_counts = [bucket['chunks']['value'] for bucket in buckets[:10]]
    
    fig = px.pie(
        values=chunk_counts,
        names=files,
        title="Document Distribution by Chunks"
    )
    fig.update_traces(textposition='inside', textinfo='percent+label')
    return fig

def create_performance_chart(performance_data):
    """Create search performance chart"""
    if not performance_data:
        return None
    
    df = pd.DataFrame(performance_data)
    
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=("Response Time", "Total Hits", "Max Score", "Performance Overview"),
        specs=[[{"secondary_y": False}, {"secondary_y": False}],
               [{"secondary_y": False}, {"secondary_y": True}]]
    )
    
    # Response time chart
    fig.add_trace(
        go.Bar(x=df['search_term'], y=df['response_time_ms'], name="Response Time (ms)"),
        row=1, col=1
    )
    
    # Total hits chart
    fig.add_trace(
        go.Bar(x=df['search_term'], y=df['total_hits'], name="Total Hits", marker_color="orange"),
        row=1, col=2
    )
    
    # Max score chart
    fig.add_trace(
        go.Bar(x=df['search_term'], y=df['max_score'], name="Max Score", marker_color="green"),
        row=2, col=1
    )
    
    # Combined overview
    fig.add_trace(
        go.Scatter(x=df['search_term'], y=df['response_time_ms'], name="Response Time", mode="lines+markers"),
        row=2, col=2
    )
    fig.add_trace(
        go.Scatter(x=df['search_term'], y=df['total_hits'], name="Total Hits", yaxis="y2", mode="lines+markers"),
        row=2, col=2, secondary_y=True
    )
    
    fig.update_layout(height=600, showlegend=True, title_text="Search Performance Analysis")
    return fig

def main():
    st.markdown('<h1 class="main-header">📊 OpenSearch Analytics Dashboard</h1>', unsafe_allow_html=True)
    
    # Initialize OpenSearch client
    client = get_opensearch_client()
    if not client:
        st.stop()
    
    # Sidebar for navigation
    st.sidebar.title("🔍 Dashboard Navigation")
    page = st.sidebar.selectbox(
        "Select View",
        ["Overview", "Search Analytics", "Performance Metrics", "Index Management", "Cluster Health"]
    )
    
    if page == "Overview":
        st.markdown('<div class="section-header">System Overview</div>', unsafe_allow_html=True)
        
        # Get basic stats
        index_stats = get_index_stats(client)
        
        if index_stats:
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                total_docs = index_stats['indices']['pdf_documents']['total']['docs']['count']
                st.metric("Total Chunks", total_docs, help="Total number of document chunks indexed")
            
            with col2:
                index_size = index_stats['indices']['pdf_documents']['total']['store']['size_in_bytes']
                size_mb = round(index_size / (1024 * 1024), 2)
                st.metric("Index Size", f"{size_mb} MB", help="Total storage used by the index")
            
            with col3:
                # Get unique documents count
                unique_docs = client.search(
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
                unique_count = unique_docs['aggregations']['unique_files']['value']
                st.metric("Unique Documents", unique_count, help="Number of unique PDF files")
            
            with col4:
                search_count = index_stats['indices']['pdf_documents']['total']['search']['query_total']
                st.metric("Total Searches", search_count, help="Total number of search queries executed")
        
        # Get analytics data
        analytics = search_analytics(client)
        
        if analytics:
            col1, col2 = st.columns(2)
            
            with col1:
                # Upload timeline
                timeline_chart = create_upload_timeline_chart(analytics['upload_timeline'])
                if timeline_chart:
                    st.plotly_chart(timeline_chart, use_container_width=True)
                else:
                    st.info("No upload timeline data available")
            
            with col2:
                # File distribution
                distribution_chart = create_file_distribution_chart(analytics['file_distribution'])
                if distribution_chart:
                    st.plotly_chart(distribution_chart, use_container_width=True)
                else:
                    st.info("No file distribution data available")
    
    elif page == "Search Analytics":
        st.markdown('<div class="section-header">Search Analytics</div>', unsafe_allow_html=True)
        
        # Search performance metrics
        performance_data = get_search_performance_metrics(client)
        
        if performance_data:
            st.subheader("Search Performance Metrics")
            
            # Create performance chart
            perf_chart = create_performance_chart(performance_data)
            if perf_chart:
                st.plotly_chart(perf_chart, use_container_width=True)
            
            # Performance data table
            st.subheader("Detailed Performance Data")
            df = pd.DataFrame(performance_data)
            st.dataframe(df, width='stretch')
            
            # Performance insights
            avg_response_time = df['response_time_ms'].mean()
            max_response_time = df['response_time_ms'].max()
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Avg Response Time", f"{avg_response_time:.2f} ms")
            with col2:
                st.metric("Max Response Time", f"{max_response_time:.2f} ms")
            with col3:
                total_results = df['total_hits'].sum()
                st.metric("Total Results Found", total_results)
    
    elif page == "Performance Metrics":
        st.markdown('<div class="section-header">Performance Metrics</div>', unsafe_allow_html=True)
        
        index_stats = get_index_stats(client)
        
        if index_stats:
            # Index performance metrics
            stats = index_stats['indices']['pdf_documents']['total']
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Indexing Performance")
                indexing_stats = stats.get('indexing', {})
                
                metrics_data = {
                    "Metric": ["Total Indexed", "Index Time (ms)", "Index Current", "Delete Total"],
                    "Value": [
                        indexing_stats.get('index_total', 0),
                        indexing_stats.get('index_time_in_millis', 0),
                        indexing_stats.get('index_current', 0),
                        indexing_stats.get('delete_total', 0)
                    ]
                }
                
                st.dataframe(pd.DataFrame(metrics_data), width='stretch')
            
            with col2:
                st.subheader("Search Performance")
                search_stats = stats.get('search', {})
                
                search_metrics = {
                    "Metric": ["Total Queries", "Query Time (ms)", "Fetch Total", "Fetch Time (ms)"],
                    "Value": [
                        search_stats.get('query_total', 0),
                        search_stats.get('query_time_in_millis', 0),
                        search_stats.get('fetch_total', 0),
                        search_stats.get('fetch_time_in_millis', 0)
                    ]
                }
                
                st.dataframe(pd.DataFrame(search_metrics), width='stretch')
            
            # Memory and storage metrics
            st.subheader("Storage Metrics")
            col3, col4, col5 = st.columns(3)
            
            with col3:
                docs_count = stats['docs']['count']
                docs_deleted = stats['docs']['deleted']
                st.metric("Active Documents", docs_count)
                st.metric("Deleted Documents", docs_deleted)
            
            with col4:
                store_size = stats['store']['size_in_bytes']
                size_gb = store_size / (1024**3)
                st.metric("Storage Size", f"{size_gb:.3f} GB")
            
            with col5:
                segments = stats.get('segments', {})
                segment_count = segments.get('count', 0)
                st.metric("Segments", segment_count)
    
    elif page == "Index Management":
        st.markdown('<div class="section-header">Index Management</div>', unsafe_allow_html=True)
        
        # Index information
        try:
            index_info = client.indices.get(index="pdf_documents")
            
            st.subheader("Index Configuration")
            
            # Index settings
            settings = index_info['pdf_documents']['settings']['index']
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**Index Settings:**")
                settings_display = {
                    "Number of Shards": settings.get('number_of_shards', 'N/A'),
                    "Number of Replicas": settings.get('number_of_replicas', 'N/A'),
                    "Creation Date": settings.get('creation_date', 'N/A'),
                    "UUID": settings.get('uuid', 'N/A')[:8] + "..." if settings.get('uuid') else 'N/A'
                }
                
                for key, value in settings_display.items():
                    st.write(f"- **{key}**: {value}")
            
            with col2:
                st.write("**Index Mappings:**")
                mappings = index_info['pdf_documents']['mappings']['properties']
                
                mapping_info = []
                for field, config in mappings.items():
                    mapping_info.append({
                        "Field": field,
                        "Type": config.get('type', 'N/A'),
                        "Searchable": "Yes" if config.get('type') == 'text' else "No"
                    })
                
                st.dataframe(pd.DataFrame(mapping_info), width='stretch')
            
            # Index operations
            st.subheader("Index Operations")
            
            col3, col4, col5 = st.columns(3)
            
            with col3:
                if st.button("Refresh Index"):
                    try:
                        client.indices.refresh(index="pdf_documents")
                        st.success("Index refreshed successfully!")
                    except Exception as e:
                        st.error(f"Error refreshing index: {str(e)}")
            
            with col4:
                if st.button("Get Index Stats"):
                    stats = get_index_stats(client)
                    if stats:
                        st.json(stats)
            
            with col5:
                if st.button("Force Merge Segments"):
                    try:
                        client.indices.forcemerge(index="pdf_documents", max_num_segments=1)
                        st.success("Force merge completed!")
                    except Exception as e:
                        st.error(f"Error during force merge: {str(e)}")
        
        except Exception as e:
            st.error(f"Error getting index information: {str(e)}")
    
    elif page == "Cluster Health":
        st.markdown('<div class="section-header">Cluster Health</div>', unsafe_allow_html=True)
        
        # Cluster health
        health = get_cluster_health(client)
        
        if health:
            col1, col2, col3 = st.columns(3)
            
            with col1:
                status = health['status']
                color = {"green": "🟢", "yellow": "🟡", "red": "🔴"}.get(status, "⚪")
                st.metric("Cluster Status", f"{color} {status.upper()}")
            
            with col2:
                st.metric("Active Nodes", health['number_of_nodes'])
            
            with col3:
                st.metric("Data Nodes", health['number_of_data_nodes'])
            
            # Detailed health information
            st.subheader("Detailed Cluster Information")
            
            health_details = {
                "Cluster Name": health.get('cluster_name', 'N/A'),
                "Active Shards": health.get('active_shards', 'N/A'),
                "Relocating Shards": health.get('relocating_shards', 'N/A'),
                "Initializing Shards": health.get('initializing_shards', 'N/A'),
                "Unassigned Shards": health.get('unassigned_shards', 'N/A'),
                "Pending Tasks": health.get('number_of_pending_tasks', 'N/A'),
                "Active Shards Percent": f"{health.get('active_shards_percent_as_number', 0):.1f}%"
            }
            
            col4, col5 = st.columns(2)
            
            with col4:
                for i, (key, value) in enumerate(health_details.items()):
                    if i < len(health_details) // 2:
                        st.write(f"**{key}**: {value}")
            
            with col5:
                for i, (key, value) in enumerate(health_details.items()):
                    if i >= len(health_details) // 2:
                        st.write(f"**{key}**: {value}")
        
        # Node information
        nodes_info = get_node_info(client)
        
        if nodes_info:
            st.subheader("Node Information")
            
            nodes_data = []
            for node_id, node_data in nodes_info['nodes'].items():
                nodes_data.append({
                    "Node ID": node_id[:8] + "...",
                    "Name": node_data.get('name', 'N/A'),
                    "Version": node_data.get('version', 'N/A'),
                    "JVM Version": node_data.get('jvm', {}).get('version', 'N/A'),
                    "OS": f"{node_data.get('os', {}).get('name', 'N/A')} {node_data.get('os', {}).get('version', '')}"
                })
            
            if nodes_data:
                st.dataframe(pd.DataFrame(nodes_data), width='stretch')
    
    # Auto-refresh option
    st.sidebar.markdown("---")
    auto_refresh = st.sidebar.checkbox("Auto Refresh (30s)")
    
    if auto_refresh:
        time.sleep(30)
        st.rerun()
    
    # Footer
    st.sidebar.markdown("---")
    st.sidebar.markdown("**OpenSearch Dashboard v1.0**")
    st.sidebar.markdown(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()