# OpenSearch Cluster Configuration Guide

## What is a Cluster?

An OpenSearch **cluster** is like a **team of computers** working together to:
- Store your data
- Handle searches
- Keep your data safe with backups
- Scale when you need more power

Think of it like having multiple librarians instead of just one - they can help more people faster!

## Basic Cluster Concepts

### 1. Node
- **What it is**: A single computer/server in the cluster
- **Think of it as**: One librarian in your team
- **Types**:
  - **Master Node**: The team leader (decides what goes where)
  - **Data Node**: Stores the actual data (holds the books)
  - **Ingest Node**: Processes incoming data (sorts new books)

### 2. Shard
- **What it is**: A piece of an index split across nodes
- **Think of it as**: Dividing a huge book into chapters, each stored by different librarians
- **Why**: Allows parallel processing and better performance

### 3. Replica
- **What it is**: A backup copy of your data
- **Think of it as**: Photocopying important books for safety
- **Why**: If one computer breaks, you don't lose data

## AWS OpenSearch Service Setup

### 1. Basic Configuration

#### Domain Settings
```yaml
Domain Name: my-search-domain
OpenSearch Version: 2.3
Instance Type: t3.small.search (for testing)
Number of Instances: 1 (for development)
```

#### Network Configuration
```yaml
VPC Access: Yes (recommended for production)
Security Groups: Allow HTTPS (port 443)
Subnet: Private subnet (for security)
```

### 2. Instance Types (Simple Guide)

#### Development/Testing
- **t3.small.search**: Good for learning and small projects
- **Cost**: Low
- **Performance**: Basic

#### Production Small
- **m5.large.search**: Good for small businesses
- **Cost**: Medium
- **Performance**: Better

#### Production Large
- **r5.xlarge.search**: Good for big applications
- **Cost**: High
- **Performance**: Best

### 3. Storage Configuration

#### Storage Types
```yaml
EBS Volume Type: gp3 (recommended)
EBS Volume Size: 20 GB (minimum for testing)
```

#### Storage Planning
- **Small project**: 20-100 GB
- **Medium project**: 100-500 GB
- **Large project**: 500+ GB

## Security Configuration

### 1. Access Control

#### Fine-grained Access Control
```yaml
Enable: Yes
Master Username: admin
Master Password: [Strong password]
```

#### IAM Access
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::YOUR-ACCOUNT:user/YOUR-USER"
      },
      "Action": "es:*",
      "Resource": "arn:aws:es:region:account:domain/domain-name/*"
    }
  ]
}
```

### 2. Encryption
```yaml
Encryption at rest: Enabled
Node-to-node encryption: Enabled
```

## Performance Optimization

### 1. Sizing Your Cluster

#### Rule of Thumb for Node Count
```
Small data (< 50 GB): 1 node
Medium data (50-500 GB): 2-3 nodes
Large data (500+ GB): 3+ nodes
```

#### Shard Calculation
```
Target shard size: 10-50 GB
Number of shards = Total data size / Target shard size
```

### 2. Index Templates

#### Create Template for Better Performance
```json
{
  "index_patterns": ["logs-*"],
  "template": {
    "settings": {
      "number_of_shards": 1,
      "number_of_replicas": 1,
      "refresh_interval": "30s"
    },
    "mappings": {
      "properties": {
        "timestamp": {"type": "date"},
        "message": {"type": "text"},
        "level": {"type": "keyword"}
      }
    }
  }
}
```

## Monitoring and Maintenance

### 1. Key Metrics to Watch

#### Cluster Health
- **Green**: Everything is good ✅
- **Yellow**: Some replicas are missing ⚠️
- **Red**: Some primary shards are missing ❌

#### Performance Metrics
```yaml
Search Latency: < 100ms (good)
Index Rate: Depends on your application
CPU Usage: < 80%
Memory Usage: < 85%
Disk Usage: < 85%
```

### 2. CloudWatch Alarms
```yaml
High CPU Usage: > 80%
High Memory Usage: > 85%
Low Disk Space: > 85% used
Cluster Health: Not Green
```

## Configuration Examples

### 1. Development Environment
```yaml
Domain: dev-search
Version: OpenSearch 2.3
Instance: t3.small.search
Instances: 1
Storage: 20 GB GP3
Access: Fine-grained (disabled for simplicity)
VPC: Public access (for testing only)
```

### 2. Production Environment
```yaml
Domain: prod-search
Version: OpenSearch 2.3
Instance: m5.large.search
Instances: 3
Storage: 100 GB GP3 per node
Replicas: 1
Access: Fine-grained enabled
VPC: Private subnets
Encryption: All enabled
```

## Common Configurations

### 1. Log Analytics Setup
```json
{
  "settings": {
    "number_of_shards": 2,
    "number_of_replicas": 1,
    "index.refresh_interval": "1s"
  },
  "mappings": {
    "properties": {
      "@timestamp": {"type": "date"},
      "level": {"type": "keyword"},
      "message": {"type": "text"},
      "service": {"type": "keyword"},
      "host": {"type": "keyword"}
    }
  }
}
```

### 2. E-commerce Search Setup
```json
{
  "settings": {
    "number_of_shards": 1,
    "number_of_replicas": 1,
    "analysis": {
      "analyzer": {
        "product_analyzer": {
          "tokenizer": "standard",
          "filter": ["lowercase", "stop"]
        }
      }
    }
  },
  "mappings": {
    "properties": {
      "name": {
        "type": "text",
        "analyzer": "product_analyzer"
      },
      "category": {"type": "keyword"},
      "price": {"type": "float"},
      "brand": {"type": "keyword"},
      "description": {"type": "text"}
    }
  }
}
```

## Troubleshooting Common Issues

### 1. Cluster Red Status
**Problem**: Some data is unavailable
**Solutions**:
1. Check if nodes are running
2. Increase cluster size
3. Check disk space
4. Review error logs

### 2. Slow Searches
**Problem**: Queries take too long
**Solutions**:
1. Add more nodes
2. Optimize queries
3. Use filters instead of queries when possible
4. Increase refresh interval

### 3. High Memory Usage
**Problem**: Nodes running out of memory
**Solutions**:
1. Use larger instance types
2. Reduce field data usage
3. Optimize mappings
4. Clear old indices

## Best Practices Checklist

### ✅ Security
- [ ] Enable encryption at rest
- [ ] Enable node-to-node encryption
- [ ] Use VPC for network isolation
- [ ] Set up proper IAM policies
- [ ] Use fine-grained access control

### ✅ Performance
- [ ] Right-size your instances
- [ ] Monitor key metrics
- [ ] Set up CloudWatch alarms
- [ ] Use appropriate shard sizes
- [ ] Plan for data growth

### ✅ Reliability
- [ ] Enable replicas for important data
- [ ] Use multiple availability zones
- [ ] Regular backup strategy
- [ ] Monitor cluster health
- [ ] Plan for disaster recovery

## Getting Started Steps

1. **Plan Your Requirements**
   - How much data?
   - How many searches per day?
   - What's your budget?

2. **Start Small**
   - Begin with t3.small for testing
   - Use 1 node initially
   - Enable basic security

3. **Monitor and Scale**
   - Watch performance metrics
   - Add nodes when needed
   - Optimize based on usage patterns

4. **Secure for Production**
   - Enable all encryption
   - Set up proper access controls
   - Use private VPC