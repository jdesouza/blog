import os
from typing import List

from crewai import LLM, Agent, Crew, Process, Task
from crewai.agents.agent_builder.base_agent import BaseAgent
from crewai.project import CrewBase, agent, crew, task


def _gemini_llm() -> LLM:
    """Build the Gemini LLM, reading the API key from a non-standard env var.

    CrewAI's native Gemini provider only auto-reads GOOGLE_API_KEY or
    GEMINI_API_KEY. We bridge GEMI_API_KEY here so deployments that expose
    that name still work without renaming the secret.
    """
    api_key = (
        os.environ.get("GEMI_API_KEY")
        or os.environ.get("GEMINI_API_KEY")
        or os.environ.get("GOOGLE_API_KEY")
    )
    if not api_key:
        raise RuntimeError(
            "No Gemini API key found. Set GEMI_API_KEY, GEMINI_API_KEY, "
            "or GOOGLE_API_KEY in the environment."
        )
    return LLM(model="gemini/gemini-2.0-flash", api_key=api_key)


@CrewBase
class Blog:
    """Minimal crew for AMP deployment validation."""

    agents: List[BaseAgent]
    tasks: List[Task]

    @agent
    def researcher(self) -> Agent:
        return Agent(
            config=self.agents_config["researcher"],  # type: ignore[index]
            llm=_gemini_llm(),
            verbose=True,
        )

    @task
    def research_task(self) -> Task:
        return Task(
            config=self.tasks_config["research_task"],  # type: ignore[index]
        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )
