# Orchestrator

This directory contains the implementation of a multi-agent system for fetching and analyzing labor market data.

## Concept

The system is designed around an orchestrator pattern, where a main "orchestrator" agent manages a team of specialized sub-agents to accomplish a task. This allows for a modular and extensible architecture.

- **Orchestrator:** The main agent, powered by Gemini, that is responsible for planning, delegating, and coordinating the work of the sub-agents.
- **Agents:** Specialized agents that are responsible for specific tasks, such as fetching data from a particular source or performing a specific analysis.
- **Tools:** Functions that the agents can use to interact with the outside world, such as fetching data from an API or a database.

## Implementation Plan

1.  **Develop the Orchestrator:** The `orchestrator.py` file will contain the main orchestrator agent. It will be responsible for:
    -   Taking a high-level task as input.
    -   Breaking down the task into a plan of smaller steps.
    -   Assigning each step to the appropriate agent.
    -   Monitoring the execution of the plan and handling any errors.
    -   Synthesizing the results from the agents into a final response.

2.  **Develop the Agents:** The `agents` directory will contain the specialized agents. Each agent will be responsible for a specific task:
    -   `data_fetcher_agent.py`: This agent will be responsible for fetching data from the StatFin API. It will use the `statfin_tool.py` tool to do this.
    -   `news_fetcher_agent.py`: This agent will be responsible for fetching news from Google News. It will use the `google_news_tool.py` tool to do this.

3.  **Develop the Tools:** The `tools` directory will contain the tools that the agents can use. These tools will be simple Python functions that perform a specific action.

4.  **Integrate with `main.py`:** The `main.py` file will be the entry point for the application. It will be responsible for:
    -   Initializing the orchestrator.
    -   Passing the high-level task to the orchestrator.
    -   Printing the final result from the orchestrator.
