import os
from typing import List

from crewai import Agent, Crew, LLM, Process, Task
from crewai.agents.agent_builder.base_agent import BaseAgent
from crewai.project import CrewBase, agent, crew, task


@CrewBase
class Blog:
    """Minimal crew for AMP deployment validation."""

    agents: List[BaseAgent]
    tasks: List[Task]

    def _llm(self) -> LLM:
        return LLM(
            model=os.getenv("MODEL", "gemini/gemini-2.0-flash"),
            api_key=os.environ.get("GEMINI_API_KEY"),
            temperature=0.7,
        )

    @agent
    def researcher(self) -> Agent:
        return Agent(
            config=self.agents_config["researcher"],  # type: ignore[index]
            llm=self._llm(),
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
