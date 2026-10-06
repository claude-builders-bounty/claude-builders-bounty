# Claude Builders Bounty - Automated Claim System

An automated system for processing bounty claims on GitHub issues.

## Features

- Automated claim processing via GitHub issues
- On-chain claim execution on Base network
- Comment-based validation and feedback
- Persistent claim state tracking
- Cron job support for batch processing

## Setup

1. Install dependencies:
```bash
npm install
```

2. Create a `.env` file:
```env
RPC_URL=https://mainnet.base.org
WALLET_PRIVATE_KEY=your_wallet_private_key
CLAIM_CONTRACT_ADDRESS=0x96eE7904BdCd8a82c71B4FFc3362C96b1Aae03e0
GITHUB_TOKEN=your_github_token
BOUNTY_REPO_OWNER=claude-builders-bounty
BOUNTY_REPO_NAME=claude-builders-bounty
MIN_CONFIRMATION_BLOCKS=1
CLAIMS_FILE=./claims.json
```

3. Build and run:
```bash
npm run build
npm start
```

## Usage

### Process a specific issue:
```bash
npm run claim 2
```

### Run cron job (process all open issues):
```bash
npm start
```

### Development mode:
```bash
npm run dev
```

## How It Works

1. The system scans GitHub issues for `/claim <wallet_address>` commands
2. Validates the claim request against repository rules
3. Executes the claim transaction on-chain
4. Posts a comment with the transaction details
5. Saves the claim status to prevent duplicate claims

## Bounty Reward Wallet

```
0x96eE7904BdCd8a82c71B4FFc3362C96b1Aae03e0
```

## License

MIT
