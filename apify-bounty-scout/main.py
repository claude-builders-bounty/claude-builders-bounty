import subprocess
import json
import re
from apify import Actor

async def run():
    # Initialize the Actor and get input
    actor = Actor.start()
    actor_input = await actor.get_input() or {}
    
    # Parameters from user input
    queries = actor_input.get('queries', ['label:bounty state:open', ' "bounty $" state:open'])
    limit = actor_input.get('limit', 50)
    
    results = []
    seen = set()

    print(f"🚀 Apify Bounty Scout starting. Searching for {len(queries)} queries...")

    for q in queries:
        # Use gh CLI for reliable searching
        cmd = f"gh search issues '{q}' --json repository,number,title,labels --limit {limit}"
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, shell=True, check=True)
            output = proc.stdout.strip()
            
            if not output: continue
            
            issues_data = json.loads(output)
            for item in issues_data:
                repo = item.get('repository', 'unknown')
                num = item['number']
                key = f"{repo}#{num}"
                if key in seen: continue
                
                results.append({
                    "repository": repo,
                    "issue_number": num,
                    "title": item['title'],
                    "labels": [l['name'] for l in item['labels']],
                    "url": f"https://github.com/{repo}/issues/{num}"
                })
                seen.add(key)
        except Exception as e:
            print(f"Error processing query {q}: {e}")

    # Save the results to the Apify dataset
    await actor.push_data(results)
    print(f"✅ Successfully found {len(results)} opportunities. Results pushed to dataset.")
    
    await actor.exit()

if __name__ == "__main__":
    import asyncio
    asyncio.run(run())
