const cfg=$('Prepare Summary').first().json;
const response=$input.first().json;
if (response.statusCode !== 200 || !Array.isArray(response.body?.content)) throw new Error('Claude response invalid');
if (response.body.stop_reason === 'max_tokens') throw new Error('Claude response truncated; increase max_tokens');
if (response.body.stop_reason !== 'end_turn') throw new Error('Claude did not complete a normal text response');
const text=response.body.content.filter(x=>x.type==='text').map(x=>x.text).join('\n').trim();
if (!text) throw new Error('Claude returned no text');
// n8n's JavaScript task runner does not expose the browser URL global.
const url=typeof cfg.discordWebhook==='string' ? cfg.discordWebhook.trim() : '';
if (!/^https:\/\/discord\.com\/api\/webhooks\/\d+\/[A-Za-z0-9_-]+$/.test(url)) throw new Error('Set a real Discord webhook in Configuration');
const header=cfg.repo+' | '+cfg.since+' to '+cfg.until+' (end exclusive)\n'+
  'Commits: '+cfg.counts.commits+' | Closed issues: '+cfg.counts.closedIssues+' | Merged PRs: '+cfg.counts.mergedPRs+'\n\n';
const full=header+text;
const parts=[];
// Leave room for part labels and never split a UTF-16 surrogate pair.
for (let cursor=0;cursor<full.length;) {
  let end=Math.min(cursor+1750,full.length);
  if (end<full.length && /[\uD800-\uDBFF]/.test(full[end-1])) end--;
  parts.push(full.slice(cursor,end)); cursor=end;
}
return parts.map((part,i)=>({json:{url,body:{content:`[${i+1}/${parts.length}] ${part}`,allowed_mentions:{parse:[]}},part:i+1,total:parts.length}}));
