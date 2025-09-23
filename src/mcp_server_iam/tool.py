import logging
from typing import Annotated, Literal
from urllib.parse import quote

import requests
from pydantic import Field
from requests.exceptions import ConnectionError, RequestException, Timeout
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from mcp_server_iam.config import settings
from mcp_server_iam.utils import get_country_code, sanitize_text

logger = logging.getLogger(__name__)


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((ConnectionError, Timeout)),
    reraise=True,
)
def _make_request(
    url: str, headers: dict, timeout: tuple[int, int] = (5, 30)
) -> requests.Response:
    """Make HTTP request with retry logic.

    Args:
        url: The URL to request
        headers: Request headers
        timeout: Tuple of (connection_timeout, read_timeout) in seconds

    Returns:
        requests.Response object

    Raises:
        ConnectionError: If unable to connect after retries
        Timeout: If request times out after retries
    """
    return requests.get(url, headers=headers, timeout=timeout)


def search_jobs(
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

    Queries multiple job platforms to find positions matching the provided
    role and filters. Results include essential job details formatted for
    easy review and application tracking.

    Args:
        role: Job title or position to search for
        city: Target city for job search (requires country)
        country: Country name or ISO code for location filtering
        platform: Specific job platform to search
        num_jobs: Maximum number of results to return (1-20, default 5)
        slice_job_description: Character limit for job descriptions

    Returns:
        List of dictionaries containing job details (id, title, company,
        location, description, apply_link) or error message dictionary.

    Note:
        Results are temporarily cached for subsequent operations.
        Network errors are automatically retried with exponential backoff.
    """
    if not settings.rapidapi_key or not settings.rapidapi_host:
        return {
            "message": "RapidAPI key or host is not set. Please set RAPIDAPI_KEY and RAPIDAPI_HOST environment variables."
        }

    headers = {
        "X-RapidAPI-Key": settings.rapidapi_key,
        "X-RapidAPI-Host": settings.rapidapi_host,
    }

    # Build query string
    query_parts = [role]
    if city:
        if not country:
            return {"message": "Country is required when city is provided."}
        query_parts.append(f"in {city}")
    if platform and platform != "":
        query_parts.append(f"via {platform}")

    query = " ".join(query_parts)

    # URL encode the query for safety
    encoded_query = quote(query, safe="")

    # Build URL with proper parameters
    url = f"https://{settings.rapidapi_host}/search?query={encoded_query}&num_pages=1&date_posted=week"

    # Add country parameter if provided
    if country:
        country_code = get_country_code(country)
        if country_code:
            url += f"&country={country_code}"

    try:
        response = _make_request(url, headers=headers)

        if response.status_code != 200:
            # Don't expose raw response text for security
            logger.warning(
                "job_search_failed",
                extra={"status_code": response.status_code},
            )
            return {
                "message": f"Failed to fetch jobs. API returned status {response.status_code}"
            }

        try:
            data = response.json()
        except ValueError:
            logger.exception("job_search_invalid_response")
            return {"message": "Invalid response format from job search API"}

        job_list = data.get("data", [])[:num_jobs]

        if not job_list:
            logger.info(
                "job_search_empty_results",
                extra={"role": role, "city": city, "country": country},
            )
            return {"message": "No jobs found."}

        results = []
        for job in job_list:
            description_raw = job.get("job_description")
            if not isinstance(description_raw, str):
                description_raw = ""

            summary = sanitize_text(description_raw, limit=slice_job_description)

            apply_link_raw = job.get("job_apply_link")
            apply_link = (
                sanitize_text(apply_link_raw) if apply_link_raw else "Not provided"
            )

            results.append(
                {
                    "job_id": sanitize_text(job.get("job_id")),
                    "title": sanitize_text(job.get("job_title")),
                    "company": sanitize_text(job.get("employer_name")),
                    "location": sanitize_text(job.get("job_city")),
                    "description": summary,
                    "apply_link": apply_link,
                }
            )

        logger.info(
            "job_search_success",
            extra={
                "role": role,
                "city": city,
                "country": country,
                "count": len(results),
            },
        )
        return results

    except ConnectionError:
        logger.warning("job_search_connection_error")
        return {
            "message": "Unable to connect to job search service. Please try again later."
        }
    except Timeout:
        logger.warning("job_search_timeout")
        return {"message": "Job search request timed out. Please try again."}
    except RequestException:
        # Generic request exception - log the actual error if logging is set up
        logger.exception("job_search_generic_error")
        return {
            "message": "An error occurred while searching for jobs. Please try again later."
        }
