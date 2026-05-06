from blog.crew import Blog


def run():
    """Run the crew (CrewAI AMP entry point)."""
    inputs = {"topic": "Kubernetes security best practices"}
    return Blog().crew().kickoff(inputs=inputs)


if __name__ == "__main__":
    run()
