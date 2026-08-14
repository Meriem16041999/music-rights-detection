from sacem_agent import SacemAgent

agent = SacemAgent(headless=True)

result = agent.search("HELLO LOVE", "Benson Boone")
print(result)