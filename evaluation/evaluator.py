"""Evaluation harness for the Post Explainer agent."""

import asyncio
import json
import logging
import time
from typing import Optional

from app.agents import post_explainer_agent

logger = logging.getLogger(__name__)


class PostExplainerEvaluator:
    """Evaluator for the Post Explainer agent."""

    def __init__(self, test_posts_path: str = "evaluation/test_posts.json"):
        """Initialize evaluator.

        Args:
            test_posts_path: Path to test posts JSON file
        """
        self.test_posts_path = test_posts_path
        self.results = []

    def load_test_posts(self) -> list[dict]:
        """Load test posts from JSON file.

        Returns:
            List of test posts
        """
        try:
            with open(self.test_posts_path, "r") as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error(f"Test posts file not found: {self.test_posts_path}")
            return []

    def compute_keyword_coverage(
        self, explanation: str, expected_keywords: list[str]
    ) -> float:
        """Compute keyword coverage metric.

        Args:
            explanation: Generated explanation
            expected_keywords: List of expected keywords

        Returns:
            Coverage score (0-1)
        """
        if not expected_keywords:
            return 1.0

        explanation_lower = explanation.lower()
        matches = sum(
            1
            for keyword in expected_keywords
            if keyword.lower() in explanation_lower
        )
        return matches / len(expected_keywords)

    def compute_semantic_similarity(
        self, text1: str, text2: str
    ) -> float:
        """Compute simple semantic similarity using token overlap.

        Args:
            text1: First text
            text2: Second text

        Returns:
            Similarity score (0-1)
        """
        tokens1 = set(text1.lower().split())
        tokens2 = set(text2.lower().split())

        if not tokens1 or not tokens2:
            return 0.0

        intersection = tokens1.intersection(tokens2)
        union = tokens1.union(tokens2)

        return len(intersection) / len(union) if union else 0.0

    async def evaluate(self) -> dict:
        """Run evaluation on all test posts.

        Returns:
            Evaluation results and metrics
        """
        test_posts = self.load_test_posts()

        if not test_posts:
            logger.error("No test posts loaded")
            return {"error": "No test posts found"}

        logger.info(f"Starting evaluation with {len(test_posts)} posts")

        results = []
        metrics = {
            "total_posts": len(test_posts),
            "successful_explanations": 0,
            "failed_explanations": 0,
            "avg_keyword_coverage": 0.0,
            "avg_response_time": 0.0,
            "individual_results": [],
        }

        for i, test_post in enumerate(test_posts, 1):
            logger.info(f"Evaluating post {i}/{len(test_posts)}")

            post_text = test_post.get("post", "")
            expected_keywords = test_post.get("expected_keywords", [])
            image_url = test_post.get("image_url")

            start_time = time.time()

            try:
                # Run agent
                state = await post_explainer_agent.run(
                    post=post_text,
                    image_url=image_url,
                )

                response_time = time.time() - start_time

                if state.error or not state.explanation:
                    logger.warning(f"Post {i} failed: {state.error}")
                    metrics["failed_explanations"] += 1
                    continue

                # Compute metrics
                keyword_coverage = self.compute_keyword_coverage(
                    state.explanation, expected_keywords
                )

                result = {
                    "post_id": i,
                    "post": post_text[:50],
                    "keyword_coverage": keyword_coverage,
                    "response_time_ms": response_time * 1000,
                    "num_sources": len(state.sources),
                    "explanation_length": len(state.explanation),
                }

                results.append(result)
                metrics["individual_results"].append(result)
                metrics["successful_explanations"] += 1

                logger.info(f"  Keyword Coverage: {keyword_coverage:.2%}")
                logger.info(f"  Response Time: {response_time:.2f}s")

            except Exception as e:
                logger.error(f"Post {i} error: {str(e)}")
                metrics["failed_explanations"] += 1

        # Calculate aggregate metrics
        if results:
            keyword_coverages = [r["keyword_coverage"] for r in results]
            response_times = [r["response_time_ms"] for r in results]

            metrics["avg_keyword_coverage"] = sum(keyword_coverages) / len(
                keyword_coverages
            )
            metrics["avg_response_time"] = sum(response_times) / len(response_times)

        logger.info("\n" + "=" * 50)
        logger.info("EVALUATION RESULTS")
        logger.info("=" * 50)
        logger.info(f"Total Posts: {metrics['total_posts']}")
        logger.info(f"Successful: {metrics['successful_explanations']}")
        logger.info(f"Failed: {metrics['failed_explanations']}")
        logger.info(f"Avg Keyword Coverage: {metrics['avg_keyword_coverage']:.2%}")
        logger.info(f"Avg Response Time: {metrics['avg_response_time']:.2f}ms")
        logger.info("=" * 50)

        return metrics

    def save_results(self, output_path: str = "evaluation/results.json") -> None:
        """Save evaluation results to JSON.

        Args:
            output_path: Path to save results
        """
        with open(output_path, "w") as f:
            json.dump(self.results, f, indent=2)
        logger.info(f"Results saved to {output_path}")


async def run_evaluation():
    """Run the evaluation harness."""
    evaluator = PostExplainerEvaluator()
    metrics = await evaluator.evaluate()
    print(json.dumps(metrics, indent=2))
    evaluator.save_results()


if __name__ == "__main__":
    asyncio.run(run_evaluation())
