# GitHub Bounty Scout - Apify Actor

This Actor automates the discovery of paid opportunities (Bounties) on GitHub. It uses the GitHub CLI (`gh`) for high-reliability searching and outputs the results into an Apify Dataset.

## 🚀 Features
- **Custom Queries**: Define your own search patterns (e.g., `label:bounty`, `"reward $"`).
- **Automated Filtering**: Scans multiple queries and deduplicates results.
- **Apify Integration**: Results are pushed directly to the Apify Dataset for further processing or export.

## 🛠 Deployment Instructions
1. **Clone the repository** or download the files.
2. **Build the Docker Image**:
   ```bash
   docker build -t github-bounty-scout .
   ```
3. **Run locally**:
   ```bash
   docker run -it github-bounty-scout
   ```
4. **Deploy to Apify**:
   - Upload the `Dockerfile` and `main.py` to the Apify Console.
   - Set the `GH_TOKEN` as an environment variable in the Actor settings to allow the `gh` CLI to authenticate.

## 📦 Technical Stack
- **Python 3.11**
- **Apify SDK**
- **GitHub CLI (gh)**
