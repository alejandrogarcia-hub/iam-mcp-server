# DXT Packaging Guide

This guide explains how to package the IAM MCP Server as a Desktop Extension (DXT) using the native DXT CLI tools.

## 📦 DXT Package

The IAM MCP Server can be packaged as a DXT extension:

- **Size**: ~6.8MB
- **Contents**: Complete self-contained extension with all dependencies  
- **Compatibility**: Python ≥3.11, macOS/Windows/Linux

### Installation
Install the generated `.dxt` file in your Claude Desktop or other MCP-compatible application.

## Prerequisites

1. Install the DXT CLI:

   ```bash
   npm install -g @anthropic-ai/dxt
   ```

2. Ensure you have a valid `manifest.json` file in your project root.

3. Create a `.dxtignore` file to exclude unnecessary files from the bundle.

## Using the Native DXT CLI

The DXT CLI provides a `pack` command that creates a `.dxt` file from your project directory:

```bash
# Basic usage - creates extension.dxt in current directory
dxt pack .

# Specify output file
dxt pack . dxt/iam_mcp_server-2.1.0.dxt
```

## Understanding .dxtignore

The `.dxtignore` file works similarly to `.gitignore` and allows you to exclude files and directories from the DXT bundle. The DXT CLI combines your custom exclusions with its default exclusion list.

### Important Notes about .dxtignore

1. **Virtual Environments**: The DXT CLI does NOT exclude Python virtual environments by default. You must explicitly add patterns like `.venv/`, `venv/`, `env/` to your `.dxtignore`.

2. **Pattern Format**:
   - Use `/` at the end for directories (e.g., `.venv/`)
   - Use wildcards for file patterns (e.g., `*.pyc`)
   - Use `**` for recursive patterns (e.g., `src/**/*.test.ts`)
   - Comments start with `#`

3. **Default Exclusions**: The DXT CLI automatically excludes some common files like:
   - `.DS_Store`, `Thumbs.db`
   - `.gitignore`, `.git/`
   - `*.log`
   - `node_modules/.cache/`
   - `package-lock.json`, `yarn.lock`

## Packaging Workflow

1. **Update version** in `manifest.json` if needed

2. **Run the pack command**:

   ```bash
   dxt pack . dxt/iam_mcp_server-VERSION.dxt
   ```

3. **Verify the bundle** contents:

   ```bash
   # The pack command shows archive contents
   # Or use unzip to inspect:
   unzip -l dxt/iam_mcp_server-VERSION.dxt
   ```

## Bundle Structure

A DXT bundle contains:

- `manifest.json` - Extension metadata and configuration
- `icon.png` - Extension icon (756KB)
- `LICENSE` - MIT License file
- `README.md` - Project documentation
- `requirements.txt` - Production dependencies list
- `pyproject.toml` - Project configuration
- `src/mcp_server_iam/` - Python source files
- `dxt/lib/` - Bundled Python dependencies (37 packages)
- `.python-version` - Python version specification

### Dependencies Included

The bundle includes all production dependencies:

- MCP framework and CLI tools
- Pydantic for data validation
- HTTP clients (httpx, requests)
- Logging and utility libraries
- All transitive dependencies

## Troubleshooting

If your bundle is too large or includes unwanted files:

1. Check the "Archive Contents" output from `dxt pack`
2. Update `.dxtignore` to exclude additional patterns
3. Run `dxt pack` again

The CLI will show:

- Total files included
- Number of files ignored by `.dxtignore`
- Package size and unpacked size

## Alternative: Custom Python Script

If you need more control over the packaging process, you can use the custom `create_dxt.py` script, but the native DXT CLI is the recommended approach for standard use cases.
