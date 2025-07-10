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
