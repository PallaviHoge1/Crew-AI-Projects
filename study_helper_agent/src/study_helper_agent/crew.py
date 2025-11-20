from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from typing import List
# If you want to run a snippet of code before or after the crew starts,
# you can use the @before_kickoff and @after_kickoff decorators
# https://docs.crewai.com/concepts/crews#example-crew-class-with-decorators

from crewai import LLM

llm = LLM(
    model="gpt-4.1-nano-2025-04-14",
    api_key="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",  # Or set OPENAI_API_KEY
    temperature=0.7,
    max_tokens=4000
)

@CrewBase
class StudyHelperAgent():
    """StudyHelperAgent crew"""

    agents: List[BaseAgent]
    tasks: List[Task]

    # Learn more about YAML configuration files here:
    # Agents: https://docs.crewai.com/concepts/agents#yaml-configuration-recommended
    # Tasks: https://docs.crewai.com/concepts/tasks#yaml-configuration-recommended
    
    # If you would like to add tools to your agents, you can learn more about it here:
    # https://docs.crewai.com/concepts/agents#agent-tools
    @agent
    def content_selector(self) -> Agent:
        return Agent(
            config=self.agents_config['content_selector'], # type: ignore[index]
            verbose=True
        )

    @agent
    def quiz_generator(self) -> Agent:
        return Agent(
            config=self.agents_config['quiz_generator'], # type: ignore[index]
            verbose=True
        )

    @agent
    def project_suggester(self) -> Agent:
        return Agent(
            config=self.agents_config['project_suggester'], # type: ignore[index]
            verbose=True
        )

    # To learn more about structured task outputs,
    # task dependencies, and task callbacks, check out the documentation:
    # https://docs.crewai.com/concepts/tasks#overview-of-a-task
    @task
    def content_selection_task(self) -> Task:
        return Task(
            config=self.tasks_config['content_selection_task'], # type: ignore[index]
            output_file='Output_Data\\content.md'
        )

    @task
    def quiz_generation_task(self) -> Task:
        return Task(
            config=self.tasks_config['quiz_generation_task'], # type: ignore[index]
            output_file='Output_Data\\quiz.md'
        )

    @task
    def project_suggestion_task(self) -> Task:
        return Task(
            config=self.tasks_config['project_suggestion_task'], # type: ignore[index]
            output_file='Output_Data\\projects.md'
        )

    @crew
    def crew(self) -> Crew:
        """Creates the StudyHelperAgent crew"""
        # To learn how to add knowledge sources to your crew, check out the documentation:
        # https://docs.crewai.com/concepts/knowledge#what-is-knowledge

        return Crew(
            agents=self.agents, # Automatically created by the @agent decorator
            tasks=self.tasks, # Automatically created by the @task decorator
            process=Process.sequential,
            verbose=True,
            # process=Process.hierarchical, # In case you wanna use that instead https://docs.crewai.com/how-to/Hierarchical/
        )
