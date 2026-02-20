# Domino Vector Database Integration

The `vectordb` module provides integration with Pinecone vector databases through Domino's data source framework.

## Overview

Domino's VectorDB integration allows you to:
- Connect to Pinecone through Domino data sources
- Use Domino's credential management for API keys
- Access vector indexes for similarity search
- Build RAG (Retrieval Augmented Generation) applications

## Prerequisites

1. Pinecone data source configured in Domino
2. Pinecone Python client installed:
   ```bash
   pip install pinecone-client>=3.0.0
   ```

## Pinecone 3.x Integration

### Initialize Pinecone Client

```python
from domino_data.vectordb import domino_pinecone3x_init_params
from pinecone import Pinecone

# Get initialization parameters from Domino data source
init_params = domino_pinecone3x_init_params("my-pinecone-datasource")

# Initialize Pinecone client
pc = Pinecone(**init_params)

# List indexes
indexes = pc.list_indexes()
print(indexes)
```

### Access Index

```python
from domino_data.vectordb import domino_pinecone3x_index_params
from pinecone import Pinecone

# Initialize client
init_params = domino_pinecone3x_init_params("my-pinecone-datasource")
pc = Pinecone(**init_params)

# Get index parameters
index_params = domino_pinecone3x_index_params(
    datasource_name="my-pinecone-datasource",
    index_name="embeddings-index"
)

# Connect to index
index = pc.Index(**index_params)
```

## Vector Operations

### Upsert Vectors

```python
# Prepare vectors with metadata
vectors = [
    {
        "id": "doc1",
        "values": [0.1, 0.2, 0.3, ...],  # 1536 dimensions for OpenAI
        "metadata": {"text": "Document content", "source": "wiki"}
    },
    {
        "id": "doc2",
        "values": [0.4, 0.5, 0.6, ...],
        "metadata": {"text": "Another document", "source": "blog"}
    }
]

# Upsert to index
index.upsert(vectors=vectors, namespace="default")
```

### Query Vectors

```python
# Query by vector
results = index.query(
    vector=[0.1, 0.2, 0.3, ...],
    top_k=10,
    include_metadata=True,
    namespace="default"
)

# Process results
for match in results.matches:
    print(f"ID: {match.id}, Score: {match.score}")
    print(f"Metadata: {match.metadata}")
```

### Query with Filters

```python
# Query with metadata filter
results = index.query(
    vector=query_vector,
    top_k=5,
    filter={"source": {"$eq": "wiki"}},
    include_metadata=True
)
```

### Delete Vectors

```python
# Delete by ID
index.delete(ids=["doc1", "doc2"], namespace="default")

# Delete by filter
index.delete(filter={"source": {"$eq": "old-source"}})

# Delete all in namespace
index.delete(delete_all=True, namespace="test")
```

## Configuration

### Environment Variables

| Variable | Purpose |
|----------|---------|
| `DOMINO_DATA_API_GATEWAY` | Data API gateway URL (default: `http://127.0.0.1:8766`) |

### Headers

The module adds these headers for Domino routing:

| Header | Purpose |
|--------|---------|
| `X-Domino-Datasource` | Data source identifier |
| `X-Domino-Pinecone-Index` | Target Pinecone index |

## RAG Application Example

```python
from domino_data.vectordb import (
    domino_pinecone3x_init_params,
    domino_pinecone3x_index_params
)
from pinecone import Pinecone
from openai import OpenAI

# Initialize clients
pc = Pinecone(**domino_pinecone3x_init_params("pinecone-ds"))
index = pc.Index(**domino_pinecone3x_index_params("pinecone-ds", "docs"))
openai_client = OpenAI()

def get_embedding(text):
    """Get embedding from OpenAI."""
    response = openai_client.embeddings.create(
        model="text-embedding-3-small",
        input=text
    )
    return response.data[0].embedding

def search_documents(query, top_k=5):
    """Search for relevant documents."""
    query_embedding = get_embedding(query)
    results = index.query(
        vector=query_embedding,
        top_k=top_k,
        include_metadata=True
    )
    return [match.metadata["text"] for match in results.matches]

def generate_answer(query, context_docs):
    """Generate answer using context."""
    context = "\n\n".join(context_docs)
    response = openai_client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": f"Answer based on this context:\n{context}"},
            {"role": "user", "content": query}
        ]
    )
    return response.choices[0].message.content

# RAG query
query = "What is Domino Data Lab?"
docs = search_documents(query)
answer = generate_answer(query, docs)
print(answer)
```

## Best Practices

1. **Batch operations**: Upsert vectors in batches of 100
2. **Namespaces**: Use namespaces to organize vectors
3. **Metadata**: Store useful context in metadata fields
4. **Dimensionality**: Match vector dimensions to your embedding model
5. **Index management**: Create indexes appropriate for your use case

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Connection timeout | Check DOMINO_DATA_API_GATEWAY is accessible |
| Authentication error | Verify data source credentials in Domino |
| Index not found | Confirm index name matches Pinecone |
| Dimension mismatch | Ensure vectors match index dimensions |
