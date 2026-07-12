
agents_type = {  "knowledge":"knowledge", "research":"research", "sql":"sql", "blocked":'blocked' }
guardrail_type = {"blocked":"blocked" , "orchestrator":"orchestrator"}
dangerous_sql = [ "insert" , "delete" , "update" , "drop", "alter" , " trucate" , "create" , "grant", "revoke" , "exec" , "--"]
forbidden_keywords = [ "not allowed", "not permitted", "unauthorized", "invalid query" ]