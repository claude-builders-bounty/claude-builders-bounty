const settings = $('Build Settings').first().json;
const summary = String($json.summary || '').trim();
if (!summary) throw new Error('Cannot deliver an empty summary');
if (summary.length > 1800) throw new Error('Summary exceeds the delivery limit');
const url = settings.webhookUrl;

if (settings.sendDelivery) {
  if (settings.destinationType === 'discord' &&
      !/^https:\/\/(?:discord\.com|discordapp\.com)\/api\/webhooks\/\d+\/[^/?#]+(?:[?#][^\s]*)?$/.test(url)) {
    throw new Error('Discord delivery must use a Discord webhook URL');
  }
  if (settings.destinationType === 'slack' &&
      !/^https:\/\/hooks\.slack\.com\/services\/[A-Za-z0-9/_-]+(?:[?#][^\s]*)?$/.test(url)) {
    throw new Error('Slack delivery must use a Slack webhook URL');
  }
  if (settings.destinationType === 'local-test' &&
      !/^http:\/\/(?:127\.0\.0\.1|localhost|\[::1\])(?::\d+)?(?:\/[^\s?#]*)?(?:[?#][^\s]*)?$/.test(url)) {
    throw new Error('local-test delivery is restricted to loopback');
  }
  if (!['discord', 'slack', 'local-test'].includes(settings.destinationType)) {
    throw new Error('Unsupported delivery destination');
  }
}

const body = settings.destinationType === 'discord'
  ? { content: summary }
  : { text: summary };

return [{ json: { summary, sendDelivery: settings.sendDelivery, webhookUrl: url, body } }];
