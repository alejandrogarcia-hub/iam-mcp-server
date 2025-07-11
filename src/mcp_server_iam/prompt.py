from typing import Annotated, Literal

from pydantic import Field


async def analyze_job_market(
    role: Annotated[
        str,
        Field(description="Job role/title to analyze market trends for", min_length=1),
    ],
    city: Annotated[
        str | None,
        Field(description="Target city for market analysis (requires country)"),
    ] = None,
    country: Annotated[
        str | None, Field(description="Target country for market analysis")
    ] = None,
    platform: Annotated[
        Literal["linkedin", "indeed", "glassdoor", ""] | None,
        Field(description="Specific platform to focus analysis on"),
    ] = None,
    num_jobs: Annotated[
        int,
        Field(
            description="Number of job listings to analyze for market trends",
            ge=1,
            le=20,
        ),
    ] = 5,
) -> str:
    """
    Generate comprehensive job market analysis prompt for specified role and location.

    Args:
        role: Job role/title to analyze market trends for
        city: Target city for market analysis (requires country)
        country: Target country for market analysis
        platform: Specific platform to focus analysis on
        num_jobs: Number of job listings to analyze for market trends

    Returns:
        str: A structured prompt that guides LLM to analyze job market trends, salary
        ranges, skill requirements, and employment patterns for the specified position.
    """

    return f"""
    # System / Instruction Prompt for LLM
    You are a data-driven AI assistant, your task is to analyze the job market for the top {num_jobs} positions matching a given {role}, optionally filtered by {city} and {country}, and sourced from {platform}.
    Before you run any tools or compose your final output, **outline your high-level approach** in 3–5 bullet points, showing that you’ve thought through every step.

    ## Task Definition
    Analyze the job market for:
    - **Role:** `{role}`
    - **Location:**  
    - City: `{city}` (optional)  
    - Country: `{country}` (required if city is given)  
    - **Platform:** `{platform}` (must be one of `linkedin`, `indeed`, `glassdoor`, or empty)

    ## Pre-Execution Checklist
    1. **Validate inputs**  
    - If `city` is non-empty, ensure `country` is also provided.  
    - If `platform` is non-empty, ensure it is one of `linkedin`, `indeed`, or `glassdoor`.  
    2. **Plan your analysis**  
    - Decide which fields to extract (`title`, `company`, `type`, `description`, `salary`, `work_arrangement`).  
    - Determine how you’ll aggregate and summarize skills/keywords and salary data.  

    ## Execution Steps
    1. **Invoke MCP tool**  
    - run `search_jobs` mcp tool with suitable roles, city, country, platform and num_jobs.
    2. **Extract & Review**  
    - Pull out `title`, `company`, `type` (e.g., Full-time/Contract), `description`, `salary` (if present), `remote/onsite`.  
    3. **Aggregate Insights**  
    - **Top roles:** List and count unique job titles.  
    - **Key skills & keywords:** Identify the most frequent.  
    - **Salary trends:** Compute average, median, range.  
    - **Work arrangement:** Tally remote vs. onsite vs. hybrid.  
    4. **Draft Markdown Report**  
    - Use headings (`## Most Common Roles`, `## Skills & Keywords`, etc.).  
    - Present tables or bullet lists for clarity.  
    - Conclude with a brief summary highlighting any surprises or actionable takeaways.

    ## Output
    Produce a markdown-formatted report under these sections:
    1. **Approach Overview** (your pre-execution bullets)  
    2. **Data Summary**  
    3. **Insights & Trends**  
    4. **Recommendations** (optional: e.g., “Consider upskilling in X…”)

    Thank you for your meticulous analysis.  
    """


def save_jobs(
    jobs_dir: Annotated[str, Field(description="Directory to save jobs")],
    date: Annotated[str, Field(description="Date of the job search")],
    role: Annotated[str, Field(description="Role of the job search")],
    city: Annotated[str, Field(description="City of the job search")],
    n_jobs: Annotated[int, Field(description="Number of jobs to save")],
) -> str:
    """
    Generate instructions for saving job search results to a JSON file.

    Creates detailed LLM instructions for properly formatting and saving
    job data as a structured JSON file with consistent naming conventions.

    Args:
        jobs_dir: Target directory path for saving the job file
        date: Date when the job search was performed (YYYY-MM-DD format)
        role: Job role/title that was searched for
        city: City/location that was searched in
        n_jobs: Number of job results to save

    Returns:
        str: Formatted prompt with detailed instructions for the LLM to save
        job data as a properly structured JSON file.
    """
    # Sanitize inputs for safe filename generation
    safe_role = "".join(c for c in role if c.isalnum() or c in (" ", "-", "_")).strip()
    safe_city = "".join(c for c in city if c.isalnum() or c in (" ", "-", "_")).strip()
    safe_role = safe_role.replace(" ", "_")
    safe_city = safe_city.replace(" ", "_")

    return f"""
# System Instructions for Saving Job Search Results

You are tasked with saving job search results to a structured JSON file. Follow these instructions precisely:

## File Location and Naming
- **Directory**: Save to `{jobs_dir}` directory
- **Filename**: `{date}_{safe_role}_{safe_city}_{n_jobs}.json`
- **Format**: JSON array containing job objects

## Required JSON Structure
Each job must be saved with this exact structure:

```json
[
  {{
    "job_id": "string - unique identifier for the job",
    "title": "string - job title/position name", 
    "company": "string - employer/company name",
    "city": "string - job location city",
    "country": "string - job location country",
    "description": "string - job description or summary",
    "apply_link": "string - application URL or 'Not provided'",
    "saved_date": "{date}",
    "search_criteria": {{
      "role": "{role}",
      "city": "{city}",
      "date_searched": "{date}"
    }}
  }}
]
```

## Critical Instructions

1. **Create the directory** `{jobs_dir}` if it doesn't exist
2. **Use the EXACT filename format**: `{date}_{safe_role}_{safe_city}_{n_jobs}.json`
3. **Ensure valid JSON**: 
   - Proper escaping of quotes and special characters
   - No trailing commas
   - Proper array structure with square brackets
4. **Handle missing data**: Use `null` for missing fields, never leave undefined
5. **Preserve data integrity**: Don't modify or truncate important information
6. **Add metadata**: Include search criteria and save date for tracking

## Data Validation
- Verify all job objects have the required fields
- Ensure `apply_link` is a valid URL or "Not provided"
- Check that `job_id` is unique within the array
- Validate that the JSON is properly formatted before saving

## Success Confirmation
After saving, confirm:
- File was created at the correct path
- JSON is valid and parseable  
- All {n_jobs} jobs were saved successfully
- File size is reasonable (not empty or corrupted)

**IMPORTANT**: Use the `write_file` tool to create the JSON file with the exact filename and structure specified above.
"""


def mesh_resumes(
    resume_mesh_directory: Annotated[
        str,
        Field(
            description="Directory to save the resume mesh",
            min_length=1,
        ),
    ],
    resume_mesh_filename: Annotated[
        str,
        Field(
            description="Filename for the resume mesh", pattern=r"^[a-zA-Z0-9_\-]+\.md$"
        ),
    ],
    date: Annotated[str, Field(description="Date of the job search")],
) -> str:
    """
    Generate a resume mesh prompt for merging multiple resumes.

    Returns:
        The resume mesh prompt string
    """

    return f"""You are tasked with creating a resume mesh from multiple resumes, or CVs, that are attached to this conversation.

**Process**:

1. **Conversion (MCP host)**:
   - For each attached resume file, convert PDF files to Markdown format. Maintain the original layout and formatting.
   - For files already in text/markdown format, proceed directly to preprocessing

2. **Pre-processing (MCP host)**:
   - CLEAN bad grammar and FIX typos in each resume
   - Do NOT alter the meaning or add new content
   - PRESERVE all original information and context

3. **Extraction (LLM)**:
   - Extract content under each section
   - Identify other clearly labeled sections and extract their content
   - Preserve dates, locations, company names, and specific achievements

4. **Merging and Alignment (LLM)**:
   - Group entries by section (for same sections) OR entity (same job title, employer, and time frame) across all resumes
   - For each group, include Employer, Title, Location, and Dates ONCE
   - Combine all related bullet points and paragraphs from different resumes
   - Maintain chronological order within sections

**Example Merging**:
```
From Resume 1:

Summary

Enterprise data and AI architect, with 10+ years of experience designing and delivering cloud-scale AI, data-analytics and backend platforms in finance, IoT and fintech.

Sygnum Bank, Zurich, Switzerland
Solutions Architect Specialist, August 2022 – December 2024
- Led AI-based portfolio to enhance operational efficiency
- Technical Lead for end-to-end triage system for operational incidents based on RAG, serverless architecture, AI agents and workflows, achieving 20% reduction in operational costs and 30% reduction in critical system incidents  

From Resume 2:

Summary

Computer Scientist with expertise in enterprise data architecture, implementing data platforms, and integrating diverse data sources for AI/ML activities.

Sygnum Bank, Zurich, Switzerland  
Solutions Architect Specialist, August 2022 – December 2024
- Leadership and technical expertise across multiple value streams
- Mentored tech leads in shipping products within regulated environment

Merged Output:

## Summary

Enterprise data and AI architect, with 10+ years of experience designing and delivering cloud-scale AI, data-analytics and backend platforms in finance, IoT and fintech. 

Computer Scientist with expertise in enterprise data architecture, implementing data platforms, and integrating diverse data sources for AI/ML activities.

## Sygnum Bank
**Solutions Architect Specialist** | Zurich, Switzerland | August 2022 – December 2024

- Led AI-based portfolio to enhance operational efficiency and business competitiveness within regulated financial environment
- Technical Lead for end-to-end triage system for operational incidents based on RAG, serverless architecture, AI agents and workflows, achieving 20% reduction in operational costs and 30% reduction in critical system incidents  
- Leadership and technical expertise across multiple value streams, driving innovation in agile environment
- Mentored tech leads in shipping products within regulated technological landscape
```

**Output**: 
- Generate the complete resume mesh as a valid markdown document
- The markdown document shall optimize for LLM reading and understanding

**Quality Requirements**:
- Maintain professional tone and accuracy
- Ensure no information loss from source resumes
- Preserve specific achievements, metrics, skills and technical details
- Use consistent formatting throughout the document

**Save the resume mesh**:
- Use the MCP tool `write_file` to save the generated resume mesh
- The file shall be saved in the directory `{resume_mesh_directory}` with the filename `{resume_mesh_filename}_{date}.md`
- Use the EXACT filename format: `{resume_mesh_filename}_{date}.md`

**IMPORTANT**: Use the `write_file` tool to save the markdown file with the exact directory, filename and structure specified above.
"""
