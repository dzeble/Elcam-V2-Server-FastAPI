# Streamlit PDF Search Application Guide

## Overview
The Streamlit PDF Search Application is a web-based interface that allows users to upload PDF documents, extract their content, index them in OpenSearch, and perform intelligent searches across all uploaded documents.

## Features

### 📤 PDF Upload & Processing
- **Multi-file Upload**: Upload multiple PDF files simultaneously
- **Text Extraction**: Automatically extracts text content from PDF files using PyPDF2
- **Smart Chunking**: Splits large documents into overlapping chunks for better search performance
- **Deduplication**: Prevents duplicate documents from being indexed using file hash verification
- **Progress Tracking**: Real-time feedback on processing status

### 🔍 Intelligent Search
- **Multi-field Search**: Searches across document content and filenames
- **Relevance Scoring**: Uses OpenSearch's scoring algorithm to rank results
- **Phrase Matching**: Prioritizes exact phrase matches for more accurate results
- **Content Highlighting**: Shows highlighted text snippets where search terms appear
- **Configurable Results**: Choose how many results to display (5-50)

### 📊 Document Statistics
- **Index Metrics**: View total chunks, index size, and unique document count
- **Recent Documents**: See recently uploaded files
- **Storage Analytics**: Monitor space usage and document distribution

## Getting Started

### Prerequisites
1. **Environment Setup**: Ensure your `.env` file contains valid AWS OpenSearch credentials
2. **Dependencies**: Install required packages from `requirements.txt`
3. **OpenSearch Service**: Have access to an AWS OpenSearch domain

### Installation
```bash
# Install dependencies
pip install -r requirements.txt

# Run the Streamlit app
streamlit run streamlit_app.py
```

### Usage Instructions

#### 1. Upload Documents
1. Navigate to the "📤 Upload PDF" tab
2. Click "Choose PDF files" to select one or more PDF documents
3. For each file, click the "Index [filename]" button
4. Monitor the processing progress and view content previews
5. Confirm successful indexing with the success message

#### 2. Search Documents
1. Go to the "🔍 Search Documents" tab
2. Enter your search query in the text input field
3. Select the number of results you want to see
4. Review the search results with highlighted matches
5. Expand result cards to see full content previews

#### 3. Monitor Statistics
1. Visit the "📊 Document Stats" tab
2. View key metrics about your document collection
3. Check recent uploads and index health

## Technical Architecture

### Document Processing Pipeline
```
PDF Upload → Text Extraction → Content Chunking → OpenSearch Indexing
```

### Search Pipeline
```
Search Query → OpenSearch Query → Result Ranking → Highlighting → Display
```

### Key Components

#### Text Chunking Strategy
- **Chunk Size**: 1000 characters per chunk
- **Overlap**: 200 characters between adjacent chunks
- **Boundary Detection**: Respects sentence and word boundaries
- **Metadata**: Tracks chunk position and relationships

#### OpenSearch Index Structure
```json
{
  "filename": "document.pdf",
  "content": "extracted text content",
  "chunk_id": 0,
  "start_position": 0,
  "end_position": 1000,
  "upload_date": "2024-01-01T12:00:00",
  "file_hash": "md5hash"
}
```

#### Search Query Structure
- **Multi-match Query**: Searches content and filename fields
- **Boost Factors**: Phrase matches (3x), content matches (2x), filename matches (1x)
- **Highlighting**: Fragment-based highlighting with configurable size
- **Sorting**: Results ordered by relevance score

## Performance Considerations

### Indexing Performance
- **Batch Processing**: Processes multiple chunks per document efficiently
- **Duplicate Prevention**: Hash-based deduplication reduces redundant processing
- **Error Handling**: Graceful handling of PDF extraction failures

### Search Performance
- **Caching**: OpenSearch client connection is cached across requests
- **Pagination**: Configurable result limits prevent overwhelming responses
- **Highlighting**: Optimized fragment generation for quick previews

### Memory Management
- **Streaming**: PDF processing uses streaming to handle large files
- **Chunk Limits**: Text chunking prevents memory issues with very large documents
- **Connection Pooling**: Efficient OpenSearch connection management

## Troubleshooting

### Common Issues

#### Connection Errors
- **Symptom**: "Failed to connect to OpenSearch"
- **Solution**: Verify AWS credentials and OpenSearch domain accessibility
- **Check**: Environment variables in `.env` file

#### PDF Processing Errors
- **Symptom**: "Error extracting text from PDF"
- **Solution**: Ensure PDF is not password-protected or corrupted
- **Alternative**: Try different PDF processing libraries if needed

#### Search Not Working
- **Symptom**: No results for valid queries
- **Solution**: Confirm documents are properly indexed
- **Debug**: Check document statistics tab for index health

### Performance Tips
1. **Index Management**: Regularly monitor index size and performance
2. **Query Optimization**: Use specific terms rather than very broad queries
3. **Document Preparation**: Ensure PDFs have selectable text (not just images)
4. **Resource Monitoring**: Watch OpenSearch cluster resources during heavy usage

## Security Considerations

### Data Privacy
- **Temporary Storage**: Uploaded files are processed in memory and not permanently stored
- **Access Control**: Uses AWS IAM for OpenSearch access control
- **Encryption**: All data in transit uses SSL/TLS encryption

### Best Practices
1. **Environment Variables**: Keep AWS credentials in environment variables, not code
2. **Access Patterns**: Monitor and audit document access patterns
3. **Data Retention**: Implement document retention policies as needed
4. **User Authentication**: Consider adding user authentication for production use

## Future Enhancements

### Planned Features
- **Advanced Search**: Boolean operators, field-specific queries
- **Document Management**: Delete/update existing documents
- **User Management**: Multi-user support with access controls
- **Export Functionality**: Export search results to various formats
- **Analytics Dashboard**: Advanced usage and content analytics

### Extensibility Options
- **Additional File Types**: Support for Word docs, presentations, etc.
- **OCR Integration**: Handle image-based PDFs
- **Machine Learning**: Semantic search and document classification
- **API Integration**: RESTful API for programmatic access