class AgentClientError(Exception):
    """A remote agent could not be reached, or did not answer.

    Lives here rather than in `modules/` because callers must handle it, so it is part of
    the contract: putting it beside the implementation would force `modules/game` to import
    `modules/agent_client` and break the one-way `modules -> interfaces` dependency.
    """
