from typing import Annotated, Literal

from config import settings
from mcp.server.fastmcp import FastMCP
from prompt import analyze_job_market as analyze_job_market_prompt
from pydantic import Field

mcp = FastMCP(
    name=settings.app_name,
    version=settings.app_version,
    log_level=settings.log_level_name,
)


@mcp.tool(
    name="search_jobs",
    description="Search for job openings based on role, location, and platform preferences",
)
async def search_jobs(
    role: Annotated[
        str,
        Field(
            description="The job role/title to search for (e.g., 'Software Engineer', 'Data Scientist')",
            min_length=1,
        ),
    ],
    city: Annotated[
        str | None,
        Field(
            description="The city to search jobs in (requires country when specified)"
        ),
    ] = None,
    country: Annotated[
        str | None,
        Field(
            description="Country name or ISO_3166-1_alpha-2 code (e.g., 'Switzerland' or 'ch')"
        ),
    ] = None,
    platform: Annotated[
        Literal["linkedin", "indeed", "glassdoor"] | None,
        Field(description="Specific job platform to search on"),
    ] = None,
    n_jobs: Annotated[
        int, Field(description="Number of job results to return", ge=1, le=20)
    ] = 5,
    slice_job_description: Annotated[
        int | None,
        Field(
            description="Maximum characters to include from job description for summary",
            ge=0,
        ),
    ] = None,
) -> list[dict] | dict[str, str]:
    """
    Search for current job openings matching specified criteria.

    This tool searches across major job platforms to find relevant positions
    based on your search parameters. It returns key details about each job
    including title, company, location, description summary, and application link.

    Args:
        role: Job title or role to search for
        city: Optional city to filter results (must provide country if specified)
        country: Optional country for location-based search
        platform: Optional specific platform to search (linkedin, indeed, glassdoor)
        n_jobs: Number of results to return (1-20, default 5)
        slice_job_description: Optional character limit for job descriptions

    Returns:
        List of job dictionaries with details, or error message dict if search fails
    """
    return search_jobs(
        role=role,
        city=city,
        country=country,
        platform=platform,
        n_jobs=n_jobs,
        slice_job_description=slice_job_description,
    )


@mcp.prompt(
    name="analyze_job_market",
    description="Analyze the job market for top jobs for a given role and location",
)
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

    return analyze_job_market_prompt(
        role=role,
        city=city,
        country=country,
        platform=platform,
        num_jobs=num_jobs,
    )
