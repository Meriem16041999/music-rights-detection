from sacem_agent import SacemAgent

agent = SacemAgent(headless=False)

result = agent.search("HELLO LOVE", "Benson Boone")
print(result)