from datetime import datetime
from typing import Annotated, Literal

from mcp.server.fastmcp import FastMCP
from pydantic import Field

from mcp_server_iam.config import settings
from mcp_server_iam.prompt import analyze_job_market as analyze_job_market_prompt
from mcp_server_iam.prompt import generate_cover_letter_prompt, generate_resume_prompt
from mcp_server_iam.prompt import mesh_resumes as mesh_resumes_prompt
from mcp_server_iam.prompt import save_jobs as save_jobs_prompt
from mcp_server_iam.tool import search_jobs as search_jobs_impl

mcp = FastMCP(
    name=settings.app_name,
    instructions="Individual Application Mesh (IAM) MCP Server for job search automation and analysis",
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
    num_jobs: Annotated[
        int,
        Field(description="Number of job results to return", ge=1, le=20, default=5),
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
        num_jobs: Number of results to return (1-20, default 5)
        slice_job_description: Optional character limit for job descriptions

    Returns:
        List of job dictionaries with details, or error message dict if search fails
    """
    return search_jobs_impl(
        role=role,
        city=city,
        country=country,
        platform=platform,
        num_jobs=num_jobs,
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
            default=5,
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
        num_jobs: Number of job listings to analyze for market trends (1-20, default 5)

    Returns:
        str: A structured prompt that guides LLM to analyze job market trends, salary
        ranges, skill requirements, and employment patterns for the specified position.
    """

    return await analyze_job_market_prompt(
        role=role,
        city=city,
        country=country,
        platform=platform,
        num_jobs=num_jobs,
    )


@mcp.prompt(
    name="save_jobs",
    description="Generate instructions for saving job search results to a structured JSON file",
)
async def save_jobs(
    jobs_dir: Annotated[
        str,
        Field(
            description="Directory path where the job file should be saved",
            min_length=1,
        ),
    ],
    role: Annotated[
        str,
        Field(
            description="Job role or title that was searched for",
            min_length=1,
        ),
    ],
    city: Annotated[
        str | None,
        Field(
            description="City or location that was searched in",
        ),
    ] = None,
    country: Annotated[
        str | None,
        Field(
            description="Country or location that was searched in",
        ),
    ] = None,
    num_jobs: Annotated[
        int,
        Field(
            description="Number of job results to save",
            default=5,
            ge=1,
            le=100,
        ),
    ] = 5,
) -> str:
    """
    Generate detailed instructions for saving job search results as JSON.

    This prompt provides comprehensive guidance for LLMs to properly format
    and save job data as a structured JSON file with consistent naming and
    validation requirements.

    Args:
        jobs_dir: Target directory for saving the job file
        role: Job role/title that was searched for
        city: City/location that was searched in (optional)
        country: Country/location that was searched in (optional)
        num_jobs: Number of job results to save (1-100, default 5)

    Returns:
        str: Detailed instructions for saving job data as JSON
    """
    date = datetime.now().strftime("%Y-%m-%d")

    return save_jobs_prompt(
        jobs_dir=jobs_dir,
        date=date,
        role=role,
        city=city,
        country=country,
        num_jobs=num_jobs,
    )


@mcp.prompt(
    name="mesh_resumes",
    description=(
        "A comprehensive prompt for meshing multiple resumes into a single resume. "
        "This prompt guides the LLM through the process of converting, cleaning, extracting, "
        "and merging information from multiple resume files into a single comprehensive document."
    ),
)
def mesh_resumes(
    save_directory: Annotated[
        str,
        Field(
            description="Directory to save the resume mesh",
            min_length=1,
        ),
    ],
) -> str:
    """
    Resume mesh prompt with instructions for the LLM to merge multiple resumes or CVs.

    Creates a structured prompt to process multiple resume files and merge them into
    a single comprehensive resume document. The output should be saved as
    resume_mesh.md in the data/resumes directory using the write_file tool.

    This prompt handles conversion, cleaning, extraction, merging, and alignment
    of information from multiple resume sources with quality requirements and
    formatting guidelines.

    Args:
        save_directory: Directory to save the resume mesh

    Returns:
        str: Complete prompt text for resume mesh process
    """
    date = datetime.now().strftime("%Y-%m-%d")

    return mesh_resumes_prompt(
        save_directory=save_directory,
        resume_mesh_filename=settings.resume_mesh_filename,
        date=date,
    )


@mcp.prompt(
    name="generate_resume",
    description="Resume prompt with instructions for the LLM to generate a resume for a given role, company and job description",
)
def generate_resume(
    save_directory: Annotated[
        str,
        Field(
            description="Directory to save the resume",
            min_length=1,
        ),
    ],
    role: Annotated[str, Field(description="The role to generate a resume for")],
    company: Annotated[
        str, Field(description="The company to generate a resume for", min_length=1)
    ],
    job_description: Annotated[
        str, Field(description="The job description to generate a resume for")
    ],
) -> str:
    """
    Resume prompt with instructions for the LLM to generate a resume for a given role, company and job description

    Args:
        save_directory: The directory to save the resume
        role: The role to generate a resume for
        company: The company to generate a resume for
        job_description: The job description to generate a resume for

    Returns:
        The generated resume in markdown format
    """
    return generate_resume_prompt(
        save_directory=save_directory,
        role=role,
        company=company,
        job_description=job_description,
    )


@mcp.prompt(
    name="generate_cover_letter",
    description="Cover letter prompt with instructions for the LLM to generate a cover letter for a given role, company and job description",
)
def generate_cover_letter(
    save_directory: Annotated[
        str, Field(description="Directory to save the cover letter")
    ],
    role: Annotated[str, Field(description="The role to generate a cover letter for")],
    company: Annotated[
        str, Field(description="The company to generate a cover letter for")
    ],
    job_description: Annotated[
        str, Field(description="The job description to generate a cover letter for")
    ],
) -> str:
    """
    Cover letter prompt with instructions for the LLM to generate a cover letter for a given role, company and job description

    Args:
        save_directory: The directory to save the cover letter
        role: The role to generate a cover letter for
        company: The company to generate a cover letter for
        job_description: The job description to generate a cover letter for

    Returns:
        The generated cover letter in markdown format
    """
    return generate_cover_letter_prompt(
        save_directory=save_directory,
        role=role,
        company=company,
        job_description=job_description,
    )
