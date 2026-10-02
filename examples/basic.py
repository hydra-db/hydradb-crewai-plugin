"""Wire HydraDB as a CrewAI crew's external memory.

Run: set HYDRADB_API_KEY and HYDRADB_TENANT_ID, then `python examples/basic.py`.
"""

import os

from crewai import Agent, Crew, Task
from crewai.memory.external.external_memory import ExternalMemory

from hydradb_crewai import HydraDBClient, HydraDBStorage

client = HydraDBClient(
    api_key=os.environ["HYDRADB_API_KEY"],
    tenant_id=os.environ["HYDRADB_TENANT_ID"],
)

researcher = Agent(
    role="Researcher",
    goal="Answer using durable project memory",
    backstory="Remembers decisions across runs via HydraDB.",
)

task = Task(
    description="Summarise our deployment policy.",
    expected_output="A one-line policy summary.",
    agent=researcher,
)

crew = Crew(
    agents=[researcher],
    tasks=[task],
    external_memory=ExternalMemory(storage=HydraDBStorage(client)),
)

if __name__ == "__main__":
    print(crew.kickoff())
