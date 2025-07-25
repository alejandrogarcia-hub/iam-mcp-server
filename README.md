# IAM MCP SERVER ... kind of 🤔

[![PyPI][pypi-badge]][pypi-url]
[![MIT licensed][mit-badge]][mit-url]
[![Python Version][python-badge]][python-url]

**The Individual Applicant Mesh (IAM) MCP Server is designed to process and manage applicant resumes, as well as facilitate job searches. It offers specialized tools and prompts for job searching, resume aggregation, generating job-specific resumes, and creating tailored cover letters.**

[pypi-badge]: https://img.shields.io/pypi/v/mcp.svg
[pypi-url]: https://pypi.org/project/iam-mcp-server/
[mit-badge]: https://img.shields.io/pypi/l/mcp.svg
[mit-url]: https://github.com/alejandrogarcia-hub/iam-mcp-server/blob/main/LICENSE
[python-badge]: https://img.shields.io/pypi/pyversions/mcp.svg
[python-url]: https://www.python.org/downloads/

**Note: This server does not fully handle system integrations. Instead, it provides focused functionality specifically for an MCP host—hence the "kind of 🤔".**

> 💡 **Community & Support**  
> If you found this project helpful, please consider giving it a star ⭐️. Found a bug or have suggestions? Open an issue—your feedback is welcome!

## 🚀 Quickstart

### 1. Use Claude Desktop as MCP host

The IAM MCP Server is designed to work with Claude Desktop, which provides the necessary MCP host environment. For more details on setting up Claude Desktop with MCP, see the [official MCP quickstart guide](https://modelcontextprotocol.io/quickstart/user).

### 2. Add filesystem MCP server

Add the `filesystem` MCP server to Claude Desktop to enable file system access (see Requirements section below for configuration example).

### 3. Get JSearch API token

Create a free account at [JSearch](https://rapidapi.com/letscrape-6bRBa3QguO5/api/jsearch) to get your API token (200 free requests/month).

⚠️ **Note:** This step is optional. You can let the MCP host or another MCP server handle job searches instead.

### 4. Configure IAM MCP Server

Add the following to your Claude Desktop configuration to run the server directly from PyPI using `uvx`:

```json
{
  "mcpServers": {
    "iam": {
      "command": "uvx",
      "args": [
        "--from", 
        "iam-mcp-server@latest",
        "mcp-server-iam"
      ],
      "env": {
        "LOG_LEVEL": "INFO",
        "RAPIDAPI_KEY": "<YOUR_API_KEY>",
        "RAPIDAPI_HOST": "jsearch.p.rapidapi.com",
        "MCP_TRANSPORT": "stdio"
      }
    }
  }
}
```

------------
> **🚀 Ready to start using IAM MCP Server?**  
> Check out the [Features](#-features) section to learn how to use the available tools and prompts.

## 📝 Requirements

1. 🗂️ The MCP host must have read and write access to the local file system where it is running. For example, you can run the `IAM MCP Server` within `Claude Desktop`, alongside the `filesystem` MCP Server, which provides this capability. This file access requirement applies to version `1.0` and is necessary for proper operation.

   1.1. Add the `filesystem` MCP server

    ```json
        {
            "mcpServers": {
                "filesystem": {
                    "command": "npx",
                    "args": [
                        "-y",
                        "@modelcontextprotocol/server-filesystem",
                        "<add directory for filesystem server>"
                    ]
                }
            }
        }
    ```

2. 🔍 The `search job` MCP tool requires access to [JSearch](https://rapidapi.com/letscrape-6bRBa3QguO5/api/JSearch). You can create an account and get 200 requests per month for free.

## ✨ Features

### Prompts

#### 📊 Analyze Job Market

Directs the LLM step-by-step to perform tasks such as conducting a `job search`, then summarizes and analyzes the resulting job listings. Refer to the full prompt for detailed instructions and context.

#### 📄 Resume Mesh

Easily combine multiple targeted resumes into a single, comprehensive Markdown document.

**What is Resume Mesh?**  
If you’ve applied to similar jobs, you’ve likely created several versions of your resume to match different job descriptions. Resume Mesh brings all those versions together into one unified Markdown file. This gives the MCP host a complete view of your experience and makes it easy to generate new, tailored resumes for future applications.

#### 🎯 Job-Specific Resume Generation

Generate customized resumes for individual job postings.

To use this feature, make sure the MCP host already has access to the `resume mesh`. Each tailored resume is generated using both the resume mesh and the specific job description. You need to attach the `resume mesh` to the MCP host conversation in advance, because the resume generation prompt does not instruct the LLM to load the `resume mesh` from the file system.

#### Cover-Letter Generation

Easily generate a customized cover letter tailored to a specific job description, using the corresponding generated resume.

**How to use:**  
Before generating a cover letter, ensure the MCP host has access to the relevant generated `resume` for the target job. You must manually attach this `resume` to the MCP host conversation, as the cover letter prompt does not automatically retrieve it from the file system.

#### 💾 Save Job

Directs the LLM step-by-step to `save jobs`.

**How to use:**

Start by searching for jobs using the `search jobs` MCP tool. After obtaining the results, you can then instruct the LLM to save those job listings.

### Tools

#### 🚀 Search Jobs

Performs a job search using the following parameters:

- role: The job title or position to search for
- city: (optional) Target city for the job search
- country: (optional) Target country for the job search
- platform: (optional) Specific job platform to use
- number of jobs: (default 5) Number of job listings to retrieve
- slice job description: (optional) Option to include only a portion of the job description

## 🛠️ Installation & Setup

The IAM MCP Server can be installed in multiple ways:

### 📦 Desktop Extension (DXT) - Recommended

**One-click installation for MCP hosts!** DXT (Desktop Extension) format provides the easiest way to install and use the IAM MCP Server.

#### Why DXT?

Desktop Extensions eliminate the complexity of manual MCP server setup by bundling everything into a single installable package:

- **No Python installation required** - All dependencies included
- **One-click installation** - Just like browser extensions
- **Automatic updates** - MCP hosts can manage updates
- **Cross-platform** - Works on macOS, Windows, and Linux
- **Self-contained** - No environment conflicts

#### Download Latest DXT

Get the latest pre-built DXT file from our GitHub releases:

**[📥 Download Latest DXT →](https://github.com/alejandrogarcia-hub/iam-mcp-server/releases/latest)**

Look for `iam_mcp_server-[version].dxt` in the release assets.

#### Installation in Claude Desktop

1. **Download** the latest `.dxt` file from releases
2. **Open Claude Desktop** → Settings → Extensions
3. **Install** the downloaded `.dxt` file
4. **Configure** during installation with these settings:
   - `jsearch_api_key`: Your RapidAPI key from [JSearch](https://rapidapi.com/letscrape-6bRBa3QguO5/api/jsearch) (optional - 200 free requests/month)
   - `path_to_uvx`: Path to your uvx executable (usually `~/.local/bin` on macOS/Linux, `%USERPROFILE%\.local\bin` on Windows)

#### Build DXT Locally

Want to build your own DXT file?

```bash
make dxt
```

The built DXT file will be available in the `dxt/` directory as `iam_mcp_server-[version].dxt`.

### 🐍 Python Package from PyPI

You can also install this project as a Python package from PyPI: [iam-mcp-server](https://pypi.org/project/iam-mcp-server/).

### 🖥️ Alternative: Manual MCP Configuration

For manual installation or other MCP hosts:

1. Locate your `claude_desktop_config.json` file:
   - **macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
   - **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`

#### Option 1: Using `uvx` with PyPI package

```json
{
  "mcpServers": {
    "iam": {
        "command": "uvx",
        "args": [
            "--from", 
            "iam-mcp-server@latest",
            "mcp-server-iam"
        ],
        "env": {
            "LOG_LEVEL": "INFO",
            "RAPIDAPI_KEY": "<API KEY>",
            "RAPIDAPI_HOST": "jsearch.p.rapidapi.com",
            "MCP_TRANSPORT": "stdio"
        }
    }
}
```

#### Option 2: Using source code

```json
{
  "mcpServers": {
    "iam": {
      "command": "<path to>/uv",
      "args": [
        "--directory",
        "<path to>/iam-mcp-server/src/mcp_server_iam",
        "run",
        "__main__.py"
      ],
      "env": {
        "LOG_LEVEL": "INFO",
        "RAPIDAPI_KEY": "<API KEY>",
        "RAPIDAPI_HOST": "jsearch.p.rapidapi.com",
        "MCP_TRANSPORT": "stdio"
      }
    }
  }
}
```

#### Restart your MCP host

- Completely quit and restart your MCP host
- The server will automatically initialize when the host starts

#### Verify the connection

In your MCP host, ask: "What MCP tools are available?" or "List the available MCP servers"

### 🔍 MCP Inspector

In terminal, run `mcp dev src/mcp_server_iam/__main__.py` and accept installing the MCP Inspector.
In the web inspector UI, click `connect` and interact with the MCP server.

⚠️ **Important**, this is for `dev` purposes only.

## ⚙️ Environment Variables

IAM supports configuration through environment variables. Create a `.env` file in the project root or set these variables in your system:

| Variable | Default | Description |
|----------|---------|-------------|
| `APP_NAME` | `iam` | Application name for logging and identification |
| `LOG_LEVEL` | `INFO` | Logging level: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL` |
| `MCP_TRANSPORT` | `stdio` | Application transport version |
| `RESUME_MESH_FILENAME` | `resume_mesh` | Default filename for resume mesh |
| `RAPIDAPI_KEY` | `""` | RapidAPI key for external API access (optional) |
| `RAPIDAPI_HOST` | `jsearch.p.rapidapi.com` | RapidAPI host endpoint |

## 📂 Repository Structure

```text
iam-mcp-server/
├── src/                        # Source code
│   └── mcp_server_iam/         # Main MCP server package
│       ├── __init__.py         # Package initialization
│       ├── __main__.py         # Entry point for running the server
│       ├── config.py           # Configuration management
│       ├── prompt.py           # LLM prompts and instructions
│       ├── server.py           # MCP server implementation
│       ├── tool.py             # MCP tools implementation
│       └── utils.py            # Utility functions
├── tests/                      # Test suite
│   ├── __init__.py
│   └── test_mcp_tools.py       # MCP tools tests
├── .env_example                # Environment variables template
├── LICENSE                     # MIT License
├── makefile                    # Build and development tasks
├── pyproject.toml              # Project configuration and dependencies
├── pytest.ini                 # Pytest configuration
├── README.md                   # This file
├── ruff.toml                   # Ruff linter configuration
└── uv.lock                     # UV dependency lock file
```

### 🔑 Key Components

- **`src/mcp_server_iam/`**: Core MCP server implementation
  - `server.py`: Main MCP server class and protocol handling
  - `tool.py`: Implementation of MCP tools (job search, etc.)
  - `prompt.py`: LLM prompts for resume generation and job analysis
  - `config.py`: Configuration management and environment variables
  - `utils.py`: Helper functions and utilities

- **`tests/`**: Comprehensive test suite for MCP tools and functionality

- **Configuration files**: Project setup, linting, and dependency management

## 📝 License

MIT License - see LICENSE file for details
