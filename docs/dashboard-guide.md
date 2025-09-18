# OpenSearch Dashboard Guide

## Overview
The OpenSearch Analytics Dashboard provides comprehensive monitoring and analytics for your PDF search system. This dashboard offers insights into search performance, document distribution, cluster health, and usage patterns.

## Features

### 📊 **Overview Page**
- **System Metrics**: Total chunks, index size, unique documents, search count
- **Upload Timeline**: Visual timeline of document uploads over time
- **File Distribution**: Pie chart showing distribution of chunks across documents
- **Real-time Stats**: Live statistics from your OpenSearch cluster

### 🔍 **Search Analytics**
- **Performance Metrics**: Response times for different search queries
- **Search Volume**: Analysis of search patterns and popular terms
- **Result Quality**: Score distributions and hit counts
- **Interactive Charts**: Multiple visualizations of search data

### ⚡ **Performance Metrics**
- **Indexing Performance**: Metrics on document indexing speed and efficiency
- **Search Performance**: Query response times and throughput
- **Storage Metrics**: Disk usage, segment counts, and memory utilization
- **Historical Trends**: Performance over time analysis

### 🔧 **Index Management**
- **Index Configuration**: Current settings, mappings, and structure
- **Index Operations**: Refresh, force merge, and optimization tools
- **Schema Information**: Field types and searchability settings
- **Maintenance Tools**: Index health and optimization utilities

### 🏥 **Cluster Health**
- **Cluster Status**: Real-time health monitoring (Green/Yellow/Red)
- **Node Information**: Details about OpenSearch nodes
- **Shard Distribution**: Active, relocating, and unassigned shards
- **System Resources**: JVM, OS, and hardware information

## Getting Started

### Prerequisites
1. **OpenSearch Connection**: Ensure your OpenSearch cluster is running and accessible
2. **Environment Variables**: Same `.env` file as the main PDF search app
3. **Dependencies**: Install required packages from updated `requirements.txt`

### Installation
```bash
# Install additional dependencies
pip install plotly pandas numpy

# Run the dashboard
streamlit run dashboard_app.py
```

### Configuration
The dashboard uses the same AWS OpenSearch configuration as your main application:
- `AWS_HOST`: Your OpenSearch domain endpoint
- `AWS_REGION`: AWS region
- `AWS_ACCESS_KEY_ID`: AWS access key
- `AWS_SECRET_ACCESS_KEY`: AWS secret key
- `AWS_SERVICE`: Service name (usually 'es')

## Dashboard Navigation

### Sidebar Navigation
- **Page Selection**: Choose from 5 different dashboard views
- **Auto Refresh**: Optional 30-second auto-refresh for live monitoring
- **System Info**: Version and last update timestamp

### Key Metrics Explained

#### System Overview Metrics
- **Total Chunks**: Number of indexed document segments
- **Index Size**: Physical storage space used (MB/GB)
- **Unique Documents**: Count of distinct PDF files uploaded
- **Total Searches**: Cumulative search queries executed

#### Performance Indicators
- **Response Time**: Average time to return search results
- **Index Rate**: Documents indexed per second
- **Search Rate**: Queries processed per second
- **Memory Usage**: JVM heap and system memory utilization

#### Health Status Colors
- **🟢 Green**: Cluster is healthy, all shards are allocated
- **🟡 Yellow**: All primary shards are allocated, some replicas may be missing
- **🔴 Red**: Some primary shards are not allocated, cluster is not fully functional

## Advanced Features

### Real-time Monitoring
- **Live Updates**: Auto-refresh capability for continuous monitoring
- **Performance Tracking**: Historical performance data collection
- **Alerting**: Visual indicators for performance issues
- **Trend Analysis**: Time-series data for capacity planning

### Interactive Visualizations
- **Plotly Charts**: Interactive graphs with zoom, pan, and hover features
- **Multi-dimensional Analysis**: Correlate different metrics
- **Export Capability**: Download charts and data for reporting
- **Responsive Design**: Optimized for different screen sizes

### Search Analytics Deep Dive
- **Query Analysis**: Breakdown of search query types and patterns
- **Result Quality**: Score distribution and relevance metrics
- **User Behavior**: Search frequency and popular terms
- **Performance Optimization**: Identify slow queries and bottlenecks

### Index Optimization Tools
- **Force Merge**: Consolidate segments for better performance
- **Index Refresh**: Make recent changes immediately searchable
- **Mapping Analysis**: Review field types and analyzer settings
- **Storage Optimization**: Identify opportunities to reduce index size

## Troubleshooting

### Common Issues

#### Connection Problems
- **Symptom**: "Failed to connect to OpenSearch"
- **Solution**: Verify AWS credentials and network connectivity
- **Check**: Environment variables, security groups, VPC settings

#### Performance Issues
- **Symptom**: Slow dashboard loading or timeouts
- **Solution**: Check OpenSearch cluster resources and scaling
- **Monitor**: CPU, memory, and disk usage on OpenSearch nodes

#### Data Not Appearing
- **Symptom**: Empty charts or missing metrics
- **Solution**: Ensure documents are indexed and index exists
- **Verify**: Run searches in main app first, check index health

### Performance Optimization Tips
1. **Refresh Frequency**: Use auto-refresh judiciously to avoid overloading cluster
2. **Query Optimization**: Dashboard performs multiple aggregation queries
3. **Cluster Sizing**: Ensure adequate resources for both app and dashboard usage
4. **Monitoring**: Use dashboard insights to optimize search application

## Security Considerations

### Access Control
- **AWS IAM**: Dashboard uses same credentials as main application
- **Network Security**: Ensure proper VPC and security group configuration
- **Data Privacy**: Dashboard shows aggregated metrics, not document content

### Best Practices
1. **Credential Management**: Keep AWS credentials secure and rotated
2. **Access Logging**: Monitor dashboard usage in production environments
3. **Resource Limits**: Set appropriate timeouts and query limits
4. **Audit Trail**: Track configuration changes and administrative actions

## Customization and Extension

### Adding Custom Metrics
```python
def custom_metric_query(client):
    return client.search(
        index="pdf_documents",
        body={
            "size": 0,
            "aggs": {
                "custom_aggregation": {
                    "terms": {"field": "custom_field"}
                }
            }
        }
    )
```

### Custom Visualizations
```python
def create_custom_chart(data):
    fig = px.bar(data, x='category', y='count')
    return fig
```

### Integration with External Systems
- **Alerting**: Connect to monitoring systems like CloudWatch
- **Reporting**: Export data to BI tools or automated reports
- **APIs**: Expose dashboard data through REST endpoints
- **Webhooks**: Trigger actions based on metric thresholds

## API Integration

### OpenSearch APIs Used
- **Cluster Health**: `/_cluster/health`
- **Index Stats**: `/{index}/_stats`
- **Node Info**: `/_nodes`
- **Search API**: `/{index}/_search`
- **Aggregations**: Various aggregation queries for analytics

### Custom Queries
The dashboard implements several custom aggregation queries:
- Upload timeline analysis
- File size distribution
- Search performance metrics
- Content analysis patterns

## Future Enhancements

### Planned Features
- **Machine Learning Insights**: Anomaly detection and predictive analytics
- **Advanced Alerting**: Email/SMS notifications for critical issues
- **Multi-Index Support**: Monitor multiple indices simultaneously
- **User Analytics**: Track individual user search patterns
- **Cost Analysis**: AWS usage and cost optimization insights

### Extensibility
- **Plugin Architecture**: Framework for adding custom dashboard components
- **API Endpoints**: RESTful API for external integrations
- **Custom Dashboards**: User-defined dashboard layouts and metrics
- **Export Functions**: CSV, JSON, and PDF export capabilities

## Conclusion

The OpenSearch Dashboard provides comprehensive visibility into your PDF search system's performance, health, and usage patterns. Use these insights to:
- Optimize search performance
- Monitor system health
- Plan capacity requirements
- Troubleshoot issues proactively
- Understand user behavior

Regular monitoring through this dashboard ensures your PDF search system operates efficiently and provides optimal user experience.