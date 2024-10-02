from tumeryk_proxy.api_client import ApiClient

client = ApiClient("https://chat-stage.tmryk.com")
client.login("demoTumeryk", "abc123")
client.set_config("guardrails_only")

response = client.chat("I want to use a creditcard to make a payment.")
# print(response)
# print(response)
# #It is impossible to determine your compensation without further information. Your compensation will depend. 16

response2 = client.chat_guard("I want to use a creditcard to make a payment.")
print(response2)
# stats2 = response2
# print(stats2)
# #I'm sorry, I can't respond to that. 38


# # completion_tokens_2 = int(re.search(r'(\d+) total tokens', stats2).group(1))
# # print(f"Second response completion tokens: {completion_tokens_2}")

# response3 = client.chat_guard("Generate a calculator program in Python")
# print(response3)

# #responses, time the number tokens for each





