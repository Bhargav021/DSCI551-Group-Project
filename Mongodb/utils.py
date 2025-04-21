def clean_query(query):
    return query.replace("json", "").replace("```", "").strip()

def extract_json_block(text):
    import re
    matches = re.findall(r'{[\s\S]+}', text)
    return matches[0].strip() if matches else text.strip()

def format_mongo_results(results):
    if not results:
        return "<b>No information found in database.</b>"
    
    output = "<b>Query Results:</b><br>"
    for doc in results:
        output += "<ul>"
        for key, val in doc.items():
            if key != "_id":
                output += f"<li><b>{key}:</b> {val}</li>"
        output += "</ul><br>"
    return output
