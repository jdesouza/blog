import sys

from blog.crew import Blog


def _sample_inputs() -> dict:
    """Default inputs used for local smoke tests; mirrors the AMP /kickoff payload."""
    return {
        "topic": "Fix privilege escalation in failing.yaml",
        "version": "1",
        "organization_id": "local",
        "repository": {
            "full_name": "jdesouza/blog",
            "default_branch": "main",
        },
        "constraints": {
            "target_branch": "main",
            "draft_pr": True,
            "allowed_path_globs": ["failing.yaml", "*.yaml"],
        },
        "runtime_context": {
            "notes": "Local smoke test from blog sample repo; fix failing.yaml only.",
            "clusters": [{"name": "demo", "provider": "kind"}],
            "workloads": [
                {
                    "kind": "Deployment",
                    "namespace": "default",
                    "name": "nginx-deployment-2",
                    "containers": [{"name": "nginx", "image": "nginx:1.25-alpine"}],
                }
            ],
        },
        "action_items": [
            {
                "id": "ai-nginx-priv-esc",
                "title": "Container may escalate privileges (allowPrivilegeEscalation)",
                "severity": "medium",
                "rule_id": "polaris/privilegeEscalationAllowed",
                "report_type": "polaris",
                "event_type": "privilegeEscalationAllowed",
                "resolution": "None",
                "description": (
                    "Under particular configurations, a container may be able to escalate "
                    "its privileges. Setting allowPrivilegeEscalation to false sets no_new_privs "
                    "behavior expected with runAsNonRoot."
                ),
                "remediation": (
                    "Set securityContext.allowPrivilegeEscalation to false on the container; "
                    "preserve everything else."
                ),
                "iac_files": ["failing.yaml"],
                "resource": {
                    "apiVersion": "apps/v1",
                    "kind": "Deployment",
                    "namespace": "default",
                    "name": "nginx-deployment-2",
                    "fileName": "failing.yaml",
                },
            }
        ],
    }


def run():
    """Run the crew (CrewAI AMP entry point)."""
    return Blog().crew().kickoff(inputs=_sample_inputs())


def train():
    """Train the crew for a given number of iterations."""
    Blog().crew().train(
        n_iterations=int(sys.argv[1]),
        filename=sys.argv[2],
        inputs=_sample_inputs(),
    )


def replay():
    """Replay the crew execution from a specific task."""
    Blog().crew().replay(task_id=sys.argv[1])


def test():
    """Test the crew execution and return the results."""
    Blog().crew().test(
        n_iterations=int(sys.argv[1]),
        eval_llm=sys.argv[2],
        inputs=_sample_inputs(),
    )


if __name__ == "__main__":
    run()
