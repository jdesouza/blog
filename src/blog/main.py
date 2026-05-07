import sys

from blog.crew import Blog


def run():
    """Run the crew (CrewAI AMP entry point)."""
    inputs = {"topic": "Kubernetes security best practices"}
    return Blog().crew().kickoff(inputs=inputs)


def train():
    """Train the crew for a given number of iterations."""
    inputs = {"topic": "Kubernetes security best practices"}
    Blog().crew().train(
        n_iterations=int(sys.argv[1]),
        filename=sys.argv[2],
        inputs=inputs,
    )


def replay():
    """Replay the crew execution from a specific task."""
    Blog().crew().replay(task_id=sys.argv[1])


def test():
    """Test the crew execution and return the results."""
    inputs = {"topic": "Kubernetes security best practices"}
    Blog().crew().test(
        n_iterations=int(sys.argv[1]),
        eval_llm=sys.argv[2],
        inputs=inputs,
    )


if __name__ == "__main__":
    run()
