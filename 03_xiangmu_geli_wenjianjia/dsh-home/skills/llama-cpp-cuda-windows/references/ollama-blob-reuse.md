# Reusing Ollama Model Blobs on Windows

## Problem

`ollama cp <model> <output.gguf>` reports success but the file does not appear in the target Windows directory. This is because Ollama on Windows runs in a WSL2 container; `ollama cp` writes to the container's filesystem, not the Windows host filesystem.

## Solution: Direct Blob Copy

### Step 1: Query Model Info via Ollama API

```bash
curl -X POST http://localhost:11434/api/show \
  -H "Content-Type: application/json" \
  -d '{"model":"<model-name>:latest"}'
```

Response contains:
```json
{
  "modelfile": "FROM D:\\Ai\\Ollama\\Models\\blobs\\sha256-<hash>\n..."
}
```

### Step 2: Copy the Blob

```cmd
copy D:\Ai\Ollama\Models\blobs\sha256-<hash> D:\Ai\models\<desired-name>.gguf
```

### Step 3: Verify

```bash
ls -la D:/Ai/models/<desired-name>.gguf
# Should show ~16 GB for 27B Q4_K_M
```

## Why This Works

- Ollama stores models as content-addressed blobs (sha256) in `Ollama/Models/blobs/`
- The blob **is** the GGUF file — no conversion needed
- Copy is instant (same filesystem, no network)
- Preserves exact quantization and metadata

## Default Ollama Paths on Windows

| Component | Path |
|-----------|------|
| Blobs | `D:\Ai\Ollama\Models\blobs\` (if customized) or `C:\Users\<user>\.ollama\models\blobs\` |
| Manifests | `D:\Ai\Ollama\Models\manifests\` or `C:\Users\<user>\.ollama\models\manifests\` |
| Config | `C:\Users\<user>\.ollama\server.json` |

**Note**: User's Ollama was configured with custom path `D:\Ai\Ollama` via `server.json` (`disable_ollama_cloud: true`). Always check `server.json` first.

## Alternative: Ollama REST API Export

If blob path unknown, use `/api/create` to create a new model tag pointing to same layers, then query its blob:

```bash
# Create alias
curl -X POST http://localhost:11434/api/create -H "Content-Type: application/json" -d '{"name":"export-temp","from":"darkidol-rp:latest"}'

# Query alias to get blob path
curl -X POST http://localhost:11434/api/show -H "Content-Type: application/json" -d '{"model":"export-temp"}'
```

Then copy the blob as above.