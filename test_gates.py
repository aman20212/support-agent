from agent import run_tool          # importing does not start the agent or call the model

print("1. unknown tool     :", run_tool("delete_all_orders", "{}"))
print("2. bad JSON         :", run_tool("issue_refund", "not json"))
print("3. wrong arguments  :", run_tool("issue_refund", '{"order": "1002"}'))
print("4. ineligible order :", run_tool("issue_refund", '{"order_id": "1004", "amount": 1899}'))
print("5. too much money   :", run_tool("issue_refund", '{"order_id": "1002", "amount": 99999}'))
print("6. valid request    :", run_tool("issue_refund", '{"order_id": "1002", "amount": 500}'))