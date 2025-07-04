# Complex RAG System for Automotive Industry

A sophisticated Retrieval-Augmented Generation (RAG) system built with ColPali for processing and searching complex automotive industry PDFs with tables, diagrams, and technical specifications.

## Features

- **Advanced PDF Processing**: Handles complex PDFs with tables, figures, and technical content
- **ColPali Integration**: Uses state-of-the-art ColPali model for image-text understanding
- **Vector Search**: Qdrant-based vector database for efficient similarity search
- **Automotive-Specific**: Optimized for technical manuals, service guides, and specifications
- **Content Analysis**: Automatically detects tables, diagrams, and technical content
- **Batch Processing**: Efficient processing of large PDFs (500+ pages)
- **Flexible Search**: Support for filtered searches and technical queries

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   PDF Document  │───▶│  Document       │───▶│  ColPali        │
│   (500+ pages)  │    │  Processor      │    │  Processor      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │                       │
                                ▼                       ▼
                       ┌─────────────────┐    ┌─────────────────┐
                       │  Page Analysis  │    │  Embedding      │
                       │  (Tables/Diagrams)│    │  Generation     │
                       └─────────────────┘    └─────────────────┘
                                                        │
                                                        ▼
                       ┌─────────────────┐    ┌─────────────────┐
                       │  Qdrant Vector  │◀───│  RAG Pipeline   │
                       │  Database       │    │  (Orchestration)│
                       └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │  Search &       │
                       │  Retrieval      │
                       └─────────────────┘
```

## Quick Start

### 1. Prerequisites

- Python 3.13+
- Qdrant vector database (local or cloud)
- CUDA-capable GPU (optional, for faster processing)

### 2. Installation

```bash
# Clone the repository
git clone <repository-url>
cd complex-rag

# Install dependencies
pip install -e .

# Or using uv (recommended)
uv sync
```

### 3. Start Qdrant

```bash
# Using Docker (recommended)
docker run -p 6333:6333 qdrant/qdrant

# Or install locally
# Follow instructions at https://qdrant.tech/documentation/guides/installation/
```

### 4. Test the System

```bash
# Run the test script with a generated PDF
python test_rag.py

# Or test with your own PDF
python test_rag.py --pdf your_automotive_manual.pdf
```

## Usage

### Command Line Interface

#### Index a PDF Document

```bash
# Index a complete automotive manual
python main.py index automotive_manual.pdf

# Index with custom settings
python main.py index automotive_manual.pdf \
    --batch-size 8 \
    --dpi 300 \
    --max-pages 100 \
    --device cuda

# Index with specific collection
python main.py index automotive_manual.pdf \
    --collection engine_specs \
    --qdrant-url localhost:6333
```

#### Search Documents

```bash
# Basic search
python main.py search "engine specifications"

# Search with filters
python main.py search "oil pressure" \
    --limit 5 \
    --score-threshold 0.8

# Search for technical content
python main.py search "troubleshooting guide" \
    --limit 10
```

#### System Information

```bash
# Check system status
python main.py info

# Verbose output
python main.py info --verbose
```

### Programmatic Usage

```python
from colpali_rag.models.schemas import IndexingConfig, SearchConfig
from colpali_rag.rag_pipeline import ColPaliRAGPipeline

# Initialize the pipeline
config = IndexingConfig(
    model_name="vidore/colpali",
    batch_size=4,
    dpi=200,
    embedding_dim=128,
    device="auto"
)

rag_pipeline = ColPaliRAGPipeline(
    config=config,
    qdrant_url="localhost:6333",
    collection_name="automotive_docs"
)

# Index a document
summary = rag_pipeline.index_document("automotive_manual.pdf")
print(f"Indexed {summary['processing_stats']['total_pages']} pages")

# Search for content
results = rag_pipeline.search("engine maintenance procedures")
for result in results:
    print(f"Page {result.page_number}: {result.score:.3f}")

# Search with filters
filters = {"has_tables": True, "technical_score": {"gte": 0.5}}
results = rag_pipeline.search_with_filters("specifications", filters)
```

## Configuration

### Environment Variables

Create a `.env` file in the project root:

```env
# ColPali Settings
COLPALI_MODEL_NAME=vidore/colpali
COLPALI_BATCH_SIZE=4
COLPALI_DPI=200
COLPALI_DEVICE=auto

# Qdrant Settings
QDRANT_URL=localhost:6333
QDRANT_API_KEY=your_api_key_here
COLPALI_COLLECTION=automotive_docs

# Processing Settings
COLPALI_CACHE_DIR=./cache
COLPALI_LOG_LEVEL=INFO
```

### Configuration Options

| Parameter | Default | Description |
|-----------|---------|-------------|
| `model_name` | `vidore/colpali` | ColPali model to use |
| `batch_size` | `4` | Number of pages to process simultaneously |
| `dpi` | `200` | Resolution for PDF page rendering |
| `embedding_dim` | `128` | Dimension of generated embeddings |
| `device` | `auto` | Processing device (auto/cpu/cuda/mps) |
| `max_pages` | `None` | Maximum pages to process (None = all) |
| `score_threshold` | `0.7` | Minimum similarity score for search results |

## Automotive Industry Features

### Content Analysis

The system automatically detects and analyzes:

- **Technical Specifications**: Engine parameters, electrical values, mechanical specs
- **Tables**: Data tables, comparison charts, specification matrices
- **Diagrams**: Schematics, flowcharts, wiring diagrams
- **Troubleshooting**: Diagnostic procedures, error codes, solutions

### Technical Terms Recognition

Automatically identifies automotive-specific terminology:

- Engine components (pistons, valves, turbochargers)
- Electrical systems (voltage, current, sensors)
- Mechanical systems (torque, pressure, temperature)
- Diagnostic procedures (troubleshooting, maintenance)

### Search Capabilities

- **Semantic Search**: Find content by meaning, not just keywords
- **Technical Query Support**: Understand automotive terminology
- **Filtered Search**: Search within specific content types (tables, diagrams)
- **Multi-modal**: Search across text and visual content

## Performance Optimization

### For Large PDFs (500+ pages)

```bash
# Use GPU acceleration
python main.py index large_manual.pdf --device cuda

# Increase batch size for faster processing
python main.py index large_manual.pdf --batch-size 8

# Process in chunks
python main.py index large_manual.pdf --max-pages 100
```

### Memory Management

- Adjust `batch_size` based on available GPU memory
- Use `max_pages` to process large documents in chunks
- Monitor memory usage with `--verbose` flag

### Qdrant Optimization

```bash
# Use cloud Qdrant for better performance
python main.py index manual.pdf \
    --qdrant-url https://your-cluster.qdrant.io \
    --qdrant-api-key your_api_key
```

## Troubleshooting

### Common Issues

1. **CUDA Out of Memory**
   ```bash
   # Reduce batch size
   python main.py index manual.pdf --batch-size 2
   ```

2. **Qdrant Connection Failed**
   ```bash
   # Check if Qdrant is running
   curl http://localhost:6333/collections
   ```

3. **Model Download Issues**
   ```bash
   # Clear cache and retry
   rm -rf ./cache/models
   python main.py index manual.pdf
   ```

### Performance Tips

- Use SSD storage for better I/O performance
- Ensure sufficient RAM (16GB+ recommended for large PDFs)
- Use GPU acceleration when available
- Process large documents during off-peak hours

## Development

### Project Structure

```
complex-rag/
├── colpali_rag/
│   ├── __init__.py
│   ├── config.py              # Configuration management
│   ├── colpali_processor.py   # ColPali model integration
│   ├── document_processor.py  # PDF processing and analysis
│   ├── rag_pipeline.py        # Main RAG orchestration
│   ├── core/
│   │   ├── __init__.py
│   │   └── qdrant_manager.py  # Vector database operations
│   └── models/
│       ├── __init__.py
│       └── schemas.py         # Data models and schemas
├── main.py                    # Command-line interface
├── test_rag.py               # Test script
├── pyproject.toml            # Project configuration
└── README.md                 # This file
```

### Running Tests

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests
python test_rag.py

# Run with specific PDF
python test_rag.py --pdf test_document.pdf
```

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For questions and support:

1. Check the troubleshooting section above
2. Review the test script for usage examples
3. Open an issue on GitHub with detailed error information

## Roadmap

- [ ] Web interface for document management
- [ ] Multi-language support
- [ ] Advanced filtering and faceted search
- [ ] Integration with automotive databases
- [ ] Real-time collaboration features
- [ ] Mobile app for field technicians
