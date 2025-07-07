"""
Simple Multi-Vector Retrieval - Easy to use with your current setup
"""

from typing import Any, Dict, List

from colpali_rag.qdrant_manager import QdrantManager


def simple_multi_vector_search(
    query_text: str,
    collection_name: str = "automotive_docs",
    limit: int = 10,
    strategy: str = "cascade",
) -> List[Dict[str, Any]]:
    """
    Simple multi-vector search with different strategies

    Strategies:
    - "cascade": Fast first, then refine with slow
    - "parallel": Search all vectors, combine results
    - "best_only": Use only the best vector type (initial)
    """

    qdrant_manager = QdrantManager(collection_name=collection_name)

    if strategy == "best_only":
        # Just use the best vector type
        print("🎯 Using only 'initial' vectors (highest quality)")
        results = qdrant_manager.search_similar_documents_text(
            query_text=query_text, limit=limit, vector_name="initial"
        )
        return results

    elif strategy == "cascade":
        # Step 1: Fast search with max_pooling
        print("🔄 Step 1: Fast search with max_pooling...")
        fast_results = qdrant_manager.search_similar_documents_text(
            query_text=query_text,
            limit=limit * 2,  # Get more candidates
            vector_name="max_pooling",
        )

        # Step 2: Refine with initial vectors
        print("🔄 Step 2: Refining with initial vectors...")
        refined_results = qdrant_manager.search_similar_documents_text(
            query_text=query_text, limit=limit * 2, vector_name="initial"
        )

        # Combine and rerank
        return combine_and_rerank(fast_results, refined_results, limit)

    elif strategy == "parallel":
        # Search with all vector types
        print("⚡ Parallel search with all vector types...")

        all_results = {}
        vector_types = ["initial", "max_pooling", "mean_pooling"]

        for vector_type in vector_types:
            print(f"  Searching with {vector_type}...")
            results = qdrant_manager.search_similar_documents_text(
                query_text=query_text, limit=limit * 2, vector_name=vector_type
            )

            for result in results:
                result_id = result["id"]
                if result_id not in all_results:
                    all_results[result_id] = {
                        "id": result_id,
                        "payload": result["payload"],
                        "scores": {},
                        "vector_count": 0,
                    }

                all_results[result_id]["scores"][vector_type] = result["score"]
                all_results[result_id]["vector_count"] += 1

        # Apply fusion scoring
        return fusion_rerank(list(all_results.values()), limit)


def combine_and_rerank(fast_results: List, refined_results: List, limit: int) -> List:
    """Combine results from cascade search and rerank"""

    # Create a lookup for fast results
    fast_lookup = {r["id"]: r for r in fast_results}

    # Combine results, prioritizing refined ones
    combined = {}

    # Add refined results (higher priority)
    for result in refined_results:
        result_id = result["id"]
        combined[result_id] = result.copy()
        combined[result_id]["source"] = "refined"
        combined[result_id]["boost"] = 1.2  # Boost refined results

    # Add fast results that weren't in refined
    for result in fast_results:
        result_id = result["id"]
        if result_id not in combined:
            combined[result_id] = result.copy()
            combined[result_id]["source"] = "fast"
            combined[result_id]["boost"] = 1.0

    # Apply boost to scores
    for result in combined.values():
        result["score"] *= result["boost"]

    # Sort by boosted score
    final_results = sorted(combined.values(), key=lambda x: x["score"], reverse=True)

    return final_results[:limit]


def fusion_rerank(results: List, limit: int) -> List:
    """Apply score fusion and multi-vector boosting"""

    # Weights for different vector types
    weights = {
        "initial": 1.0,  # Best quality
        "max_pooling": 0.8,  # Good for peaks
        "mean_pooling": 0.7,  # Good for general
    }

    for result in results:
        # Calculate weighted average score
        total_score = 0
        total_weight = 0

        for vector_type, score in result["scores"].items():
            weight = weights.get(vector_type, 1.0)
            total_score += score * weight
            total_weight += weight

        # Average weighted score
        result["fusion_score"] = total_score / total_weight if total_weight > 0 else 0

        # Boost for multiple vector agreement
        vector_boost = 1 + (result["vector_count"] - 1) * 0.1
        result["final_score"] = result["fusion_score"] * vector_boost

    # Sort by final score
    final_results = sorted(results, key=lambda x: x["final_score"], reverse=True)

    # Convert back to original format
    output_results = []
    for result in final_results:
        output_results.append(
            {
                "id": result["id"],
                "score": result["final_score"],
                "payload": result["payload"],
                "vector_sources": list(result["scores"].keys()),
                "vector_count": result["vector_count"],
            }
        )

    return output_results[:limit]


# Easy-to-use function for your current workflow
def enhanced_search(query_text: str, limit: int = 10, strategy: str = "cascade"):
    """
    Drop-in replacement for your current search

    Just replace your current search with this function!
    """

    print(f"🔍 Enhanced search: '{query_text}'")
    print(f"📊 Strategy: {strategy}")
    print("-" * 50)

    results = simple_multi_vector_search(
        query_text=query_text, limit=limit, strategy=strategy
    )

    # Print results in your current format
    for i, result in enumerate(results, 1):
        print(f"{i}. Score: {result['score']:.4f}")
        print(f"   File: {result['payload']['file_name']}")
        print(f"   Page: {result['payload']['page_number']}")

        # Show additional info if available
        if "vector_sources" in result:
            print(f"   Sources: {', '.join(result['vector_sources'])}")
        if "vector_count" in result:
            print(f"   Vector agreement: {result['vector_count']}/3")

        print("---")

    return results


# Test different strategies
if __name__ == "__main__":
    query = "How often should I check the oil level?"

    print("COMPARISON OF STRATEGIES:")
    print("=" * 60)

    strategies = ["best_only", "cascade", "parallel"]

    for strategy in strategies:
        print(f"\n🔍 {strategy.upper()} STRATEGY:")
        enhanced_search(query, limit=5, strategy=strategy)
        print("\n" + "=" * 60)
