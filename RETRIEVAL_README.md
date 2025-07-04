# PDF Retrieval System with ColPali and Qdrant

This document explains how to use the retrieval system built on top of your ColPali + Qdrant indexing setup.

## Overview

The retrieval system allows you to find similar PDF pages using both image-based and text-based queries. It leverages the ColPali vision-language model to create embeddings and Qdrant for efficient similarity search.

## Prerequisites

1. **Indexed Documents**: Ensure you have run the indexing script first:
   ```bash
   python run_indexing.py
   ```

2. **Qdrant Running**: Make sure Qdrant is accessible (check your `settings.py`)

3. **Dependencies**: All required packages should be installed from your `pyproject.toml`

## Quick Start

### 1. Basic Image Retrieval

Search using a page from your indexed PDF:

```bash
python retrieve.py --pdf "31211033 - JLG 642, 742, 943, 1043, 1055, 1255-1_removed_removed_removed.pdf" --limit 5
```

### 2. Text-Based Retrieval

Search using a text query:

```bash
python retrieve.py --text "safety instructions for aerial work platform" --limit 10
```

### 3. Using an Image Query

Search using a custom image:

```bash
python retrieve.py --image "query_screenshot.png" --limit 10
```

### 4. Advanced Search

```bash
python retrieve.py \
  --text "maintenance procedures for hydraulic system" \
  --collection "automotive_docs" \
  --limit 20 \
  --threshold 0.3 \
  --vector "mean_pooling" \
  --details
```

## Command Line Options

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--image` | `-i` | Path to query image file | - |
| `--pdf` | `-p` | Path to PDF file to extract query page from | - |
| `--text` | `-t` | Text query to search for | - |
| `--collection` | `-c` | Qdrant collection name | `automotive_docs` |
| `--limit` | `-l` | Maximum number of results | `10` |
| `--threshold` | `-th` | Minimum similarity score | `0.5` |
| `--vector` | `-v` | Vector type: `initial`, `max_pooling`, `mean_pooling` | `mean_pooling` |
| `--details` | `-d` | Show detailed metadata | `False` |

## Query Types

### Text Queries

Text queries allow you to search for PDF pages using natural language descriptions. The system uses ColPali's text processing capabilities to convert your query into embeddings that can be compared against the indexed document pages.

**Examples:**
```bash
# Search for safety-related content
python retrieve.py --text "safety warning labels and instructions"

# Search for technical diagrams
python retrieve.py --text "electrical wiring diagram"

# Search for maintenance procedures
python retrieve.py --text "maintenance procedures for hydraulic system"

# Search for operational content
python retrieve.py --text "control panel operation manual"
```

### Image Queries

Image queries use visual similarity to find matching pages. This is useful when you have a screenshot, diagram, or photo that you want to find similar content for.

**Examples:**
```bash
# Use a screenshot as query
python retrieve.py --image "screenshot.png"

# Use a page from a PDF as query
python retrieve.py --pdf "manual.pdf"
```

## Vector Types

The system supports three vector types for search:

1. **`initial`**: Full ColPali embeddings (most accurate, slower)
2. **`max_pooling`**: Max-pooled embeddings (balanced)
3. **`mean_pooling`**: Mean-pooled embeddings (fastest, recommended)

Based on the notebook analysis, `mean_pooling` provides the best balance of speed and accuracy.

## Example Usage Scenarios

### Scenario 1: Find Similar Technical Diagrams

```bash
# Using text query
python retrieve.py --text "technical diagram schematic" --limit 15 --threshold 0.4

# Using image query
python retrieve.py --pdf "manual.pdf" --limit 15 --threshold 0.4
```

### Scenario 2: Search with High Precision

```bash
# Use full embeddings for maximum accuracy
python retrieve.py --text "specific safety procedure" --vector "initial" --threshold 0.7
```

### Scenario 3: Batch Processing

For multiple queries, you can use the Python API:

```python
from retrieve import search_similar_pages, load_query_image

# Text queries
text_queries = [
    "safety instructions",
    "maintenance procedures", 
    "electrical diagrams"
]

for query_text in text_queries:
    results = search_similar_pages(
        query_text=query_text,
        limit=5,
        vector_name="mean_pooling"
    )
    print(f"Query '{query_text}' results:", len(results))

# Image queries
query_images = [
    load_query_image("query1.png"),
    load_query_image("query2.png"),
]

for i, query_image in enumerate(query_images):
    results = search_similar_pages(
        query_image=query_image,
        limit=5,
        vector_name="mean_pooling"
    )
    print(f"Image query {i+1} results:", len(results))
```

### Scenario 4: Text Query Examples

Run the example script to see text queries in action:

```bash
python example_text_retrieval.py
```

This will demonstrate various text queries and their results.

## Best Practices

### 1. Score Thresholds

- **0.7+**: Very similar content (high precision)
- **0.5-0.7**: Moderately similar (balanced)
- **0.3-0.5**: Loosely related (high recall)
- **<0.3**: Very broad matches

**Note**: Text queries often work better with lower thresholds (0.3-0.5) compared to image queries.

### 2. Vector Selection

- **Production**: Use `mean_pooling` for speed
- **Development**: Use `initial` for maximum accuracy
- **Testing**: Compare `max_pooling` vs `mean_pooling`

### 3. Text Query Tips

- Use specific, descriptive terms
- Include technical terminology when relevant
- Try synonyms if initial queries don't work
- Use longer, more detailed queries for better results

### 4. Collection Management

```python
from colpali_rag.qdrant_manager import QdrantManager

# Check collection status
qdrant_manager = QdrantManager(collection_name="automotive_docs")
info = qdrant_manager.get_collection_info()
print(f"Indexed pages: {info['points_count']}")

# Clear collection if needed
# qdrant_manager.clear_collection()
```

### 5. Performance Optimization

- Use `mean_pooling` vectors for faster searches
- Lower score thresholds for broader results
- Use filters when you know specific metadata
- Batch multiple queries when possible

## Troubleshooting

### Common Issues

1. **"No results found"**
   - Lower the score threshold
   - Check if collection has indexed data
   - Verify query image quality

2. **"Collection not found"**
   - Run indexing first: `python run_indexing.py`
   - Check collection name in settings

3. **"Model loading error"**
   - Ensure ColPali model is downloaded
   - Check GPU memory availability

4. **"Qdrant connection error"**
   - Verify Qdrant URL in `settings.py`
   - Check if Qdrant service is running

### Debug Mode

Enable detailed logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Then run your retrieval
from retrieve import search_similar_pages
```

## Integration Examples

### Web API Integration

```python
from flask import Flask, request, jsonify
from retrieve import search_similar_pages, load_query_image

app = Flask(__name__)

@app.route('/search', methods=['POST'])
def search():
    # Get image from request
    image_file = request.files['image']
    query_image = Image.open(image_file.stream)
    
    # Search
    results = search_similar_pages(
        query_image=query_image,
        limit=int(request.args.get('limit', 10))
    )
    
    return jsonify(results)

if __name__ == '__main__':
    app.run(debug=True)
```

### Jupyter Notebook Integration

```python
# In a Jupyter notebook
from retrieve import search_similar_pages, load_query_image
from PIL import Image
import matplotlib.pyplot as plt

# Load and display query image
query_image = load_query_image("query.png")
plt.imshow(query_image)
plt.show()

# Search and display results
results = search_similar_pages(query_image, limit=5)
for result in results:
    print(f"Score: {result['score']:.3f}")
    print(f"Page: {result['payload']['page_number']}")
```

## Performance Benchmarks

Based on the notebook analysis:

- **Mean Pooling**: ~2.46s per batch (8 queries)
- **Max Pooling**: ~2.49s per batch (8 queries)
- **Initial Vectors**: ~10x slower than pooling methods

Quality metrics (NDCG@20):
- **Mean Pooling**: 0.952
- **Max Pooling**: 0.759
- **Binary Quantization**: 0.913 (faster but lower quality)

## Next Steps

1. **Text Queries**: If you need text-based search, consider:
   - Using a text embedding model alongside ColPali
   - Implementing a hybrid search approach

2. **Reranking**: For better results, implement a reranking step:
   - Use cross-encoder models
   - Apply business logic filters

3. **Scaling**: For production use:
   - Implement caching
   - Add monitoring and metrics
   - Consider sharding for large collections

## Support

For issues or questions:
1. Check the troubleshooting section
2. Review the example scripts
3. Examine the notebook for detailed analysis 