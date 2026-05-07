from typing import List

from crewai import Agent, Crew, Process, Task
from crewai.agents.agent_builder.base_agent import BaseAgent
from crewai.project import CrewBase, agent, crew, task

from blog.tools import OpenPullRequestTool, ReadRepoFileTool


@CrewBase
class Blog:
    """Remediation crew: turns action items into draft PRs."""

    agents: List[BaseAgent]
    tasks: List[Task]

    @agent
    def remediation_engineer(self) -> Agent:
        return Agent(
            config=self.agents_config["remediation_engineer"],  # type: ignore[index]
            tools=[ReadRepoFileTool(), OpenPullRequestTool()],
            verbose=True,
        )

    @task
    def remediate_and_open_pr_task(self) -> Task:
        return Task(
            config=self.tasks_config["remediate_and_open_pr_task"],  # type: ignore[index]
        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )
