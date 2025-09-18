# OpenSearch Schema Guide

## What is a Schema?

A **schema** is like a **blueprint** that tells OpenSearch:
- What type of data each field contains
- How to store and search that data
- Rules for handling the data

Think of it like defining columns in a spreadsheet before adding data.

## Field Data Types

### 1. Text Types
Used for searchable text content.

#### `text`
- **Use for**: Full-text search (articles, descriptions, names)
- **Example**: Blog posts, product descriptions
```json
{
  "description": {
    "type": "text"
  }
}
```

#### `keyword`
- **Use for**: Exact matches, filtering, sorting
- **Example**: Status, categories, IDs
```json
{
  "status": {
    "type": "keyword"
  }
}
```

### 2. Number Types

#### `integer`
- **Use for**: Whole numbers
- **Example**: Age, quantity, count
```json
{
  "age": {
    "type": "integer"
  }
}
```

#### `float` / `double`
- **Use for**: Decimal numbers
- **Example**: Prices, ratings, percentages
```json
{
  "price": {
    "type": "float"
  }
}
```

### 3. Date Type
#### `date`
- **Use for**: Timestamps, dates
- **Example**: Created date, last modified
```json
{
  "created_at": {
    "type": "date",
    "format": "yyyy-MM-dd HH:mm:ss"
  }
}
```

### 4. Boolean Type
#### `boolean`
- **Use for**: True/false values
- **Example**: Active status, featured items
```json
{
  "is_active": {
    "type": "boolean"
  }
}
```

## Creating a Schema (Mapping)

### Simple Schema Example
```json
{
  "mappings": {
    "properties": {
      "title": {
        "type": "text"
      },
      "category": {
        "type": "keyword"
      },
      "price": {
        "type": "float"
      },
      "created_at": {
        "type": "date"
      },
      "in_stock": {
        "type": "boolean"
      }
    }
  }
}
```

### Real-World Example: E-commerce Product
```json
{
  "mappings": {
    "properties": {
      "name": {
        "type": "text",
        "analyzer": "standard"
      },
      "description": {
        "type": "text"
      },
      "sku": {
        "type": "keyword"
      },
      "category": {
        "type": "keyword"
      },
      "price": {
        "type": "float"
      },
      "tags": {
        "type": "keyword"
      },
      "created_date": {
        "type": "date"
      },
      "in_stock": {
        "type": "boolean"
      },
      "rating": {
        "type": "float"
      }
    }
  }
}
```

## Dynamic vs Static Mapping

### Dynamic Mapping (Automatic)
- **What it is**: OpenSearch guesses field types automatically
- **Pros**: Easy to start, no setup needed
- **Cons**: Might guess wrong, less control

```python
# Just add data, OpenSearch figures out the schema
document = {
    "name": "iPhone",  # Will be detected as "text"
    "price": 999.99,   # Will be detected as "float"
    "count": 10        # Will be detected as "integer"
}
```

### Static Mapping (Manual)
- **What it is**: You define the schema upfront
- **Pros**: Full control, better performance, consistent
- **Cons**: More setup work

```python
# Define schema first
mapping = {
    "mappings": {
        "properties": {
            "name": {"type": "text"},
            "price": {"type": "float"},
            "count": {"type": "integer"}
        }
    }
}
client.indices.create(index="products", body=mapping)
```

## Best Practices

### 1. Choose the Right Type
```json
{
  "email": {"type": "keyword"},      # Exact match, not searchable text
  "description": {"type": "text"},   # Full-text search
  "user_id": {"type": "keyword"},    # Exact match, filtering
  "age": {"type": "integer"},        # Numbers for range queries
  "active": {"type": "boolean"}      # True/false values
}
```

### 2. Multi-field Mapping
Use both `text` and `keyword` for the same field:
```json
{
  "title": {
    "type": "text",
    "fields": {
      "keyword": {
        "type": "keyword"
      }
    }
  }
}
```

**Usage**:
- `title` for search: "Find products containing 'phone'"
- `title.keyword` for exact match/sorting: "Find exact title 'iPhone 13'"

### 3. Schema Planning Checklist

Before creating an index, ask:
- **What will I search for?** → Use `text`
- **What will I filter by?** → Use `keyword`
- **What will I sort by?** → Use `keyword` or numbers
- **What will I do math on?** → Use numbers
- **Do I need exact matches?** → Use `keyword`

## Common Mistakes to Avoid

### ❌ Wrong Type Choice
```json
{
  "phone_number": {"type": "text"}  // Wrong! Use "keyword"
}
```

### ❌ No Planning
```json
// Don't rely only on dynamic mapping for production
```

### ✅ Better Approach
```json
{
  "phone_number": {"type": "keyword"},  // Exact matches
  "description": {"type": "text"}       // Full-text search
}
```

## Testing Your Schema

### 1. Create Index with Schema
```python
mapping = {
    "mappings": {
        "properties": {
            "title": {"type": "text"},
            "category": {"type": "keyword"},
            "price": {"type": "float"}
        }
    }
}
client.indices.create(index="test_products", body=mapping)
```

### 2. Add Test Document
```python
document = {
    "title": "Test Product",
    "category": "electronics",
    "price": 29.99
}
client.index(index="test_products", body=document)
```

### 3. Test Searches
```python
# Text search
text_search = {"query": {"match": {"title": "test"}}}

# Exact filter
exact_filter = {"query": {"term": {"category": "electronics"}}}

# Range query
range_query = {"query": {"range": {"price": {"gte": 20, "lte": 50}}}}
```