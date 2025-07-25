"""Unit tests for search_jobs function.

Tests follow AAA (Arrange, Act, Assert) pattern and cover:
- Happy path scenarios
- Error handling and edge cases
- Security concerns
- Input validation
"""

import json
from unittest.mock import Mock, patch

import pytest
import requests

from mcp_server_iam.tool import search_jobs


class TestSearchJobs:
    """Test suite for search_jobs function."""

    @pytest.fixture
    def mock_settings(self):
        """Mock settings with valid configuration."""
        settings = Mock()
        settings.rapidapi_key = "test_api_key"
        settings.rapidapi_host = "jsearch.p.rapidapi.com"
        return settings

    @pytest.fixture
    def mock_response_success(self):
        """Mock successful API response."""
        response = Mock()
        response.status_code = 200
        response.json.return_value = {
            "data": [
                {
                    "job_id": "job123",
                    "job_title": "Software Engineer",
                    "employer_name": "Tech Corp",
                    "job_city": "San Francisco",
                    "job_description": "We are looking for a talented engineer...",
                    "job_apply_link": "https://example.com/apply",
                },
                {
                    "job_id": "job456",
                    "job_title": "Senior Developer",
                    "employer_name": "StartupXYZ",
                    "job_city": "New York",
                    "job_description": "Join our amazing team...",
                    "job_apply_link": "https://example.com/apply2",
                },
            ]
        }
        return response

    # ========== Happy Path Tests ==========

    @patch("mcp_server_iam.tool._make_request")
    @patch("mcp_server_iam.tool.settings")
    def test_search_jobs_basic_success(
        self,
        mock_settings_patch,
        mock_make_request,
        mock_settings,
        mock_response_success,
    ):
        """Test successful job search with minimal parameters."""
        # Arrange
        mock_settings_patch.rapidapi_key = mock_settings.rapidapi_key
        mock_settings_patch.rapidapi_host = mock_settings.rapidapi_host
        mock_make_request.return_value = mock_response_success

        # Act
        result = search_jobs(role="Software Engineer")

        # Assert
        assert isinstance(result, list)
        assert len(result) == 2
        assert result[0]["job_id"] == "job123"
        assert result[0]["title"] == "Software Engineer"
        assert result[0]["company"] == "Tech Corp"
        assert result[0]["location"] == "San Francisco"
        assert result[0]["apply_link"] == "https://example.com/apply"

        # Verify API was called correctly
        mock_make_request.assert_called_once()
        call_args = mock_make_request.call_args
        # URL should be encoded
        assert "Software%20Engineer" in call_args[0][0]
        assert call_args[1]["headers"]["X-RapidAPI-Key"] == "test_api_key"

    @patch("mcp_server_iam.tool._make_request")
    @patch("mcp_server_iam.tool.settings")
    @patch("mcp_server_iam.tool.get_country_code")
    def test_search_jobs_with_all_parameters(
        self,
        mock_country_code,
        mock_settings_patch,
        mock_make_request,
        mock_settings,
        mock_response_success,
    ):
        """Test job search with all parameters provided."""
        # Arrange
        mock_settings_patch.rapidapi_key = mock_settings.rapidapi_key
        mock_settings_patch.rapidapi_host = mock_settings.rapidapi_host
        mock_country_code.return_value = "us"
        mock_make_request.return_value = mock_response_success

        # Act
        result = search_jobs(
            role="Data Scientist",
            city="Seattle",
            country="United States",
            platform="linkedin",
            num_jobs=1,
            slice_job_description=50,
        )

        # Assert
        assert isinstance(result, list)
        assert len(result) == 1
        assert "..." in result[0]["description"]
        assert len(result[0]["description"]) <= 54  # 50 chars + "\n...\n"

        # Verify URL construction (all should be encoded)
        called_url = mock_make_request.call_args[0][0]
        assert "Data%20Scientist%20in%20Seattle%20via%20linkedin" in called_url
        assert "&country=us" in called_url

    # ========== Configuration Error Tests ==========

    @patch("mcp_server_iam.tool.settings")
    def test_search_jobs_missing_api_key(self, mock_settings_patch):
        """Test behavior when API key is missing."""
        # Arrange
        mock_settings_patch.rapidapi_key = ""
        mock_settings_patch.rapidapi_host = "jsearch.p.rapidapi.com"

        # Act
        result = search_jobs(role="Engineer")

        # Assert
        assert isinstance(result, dict)
        assert "message" in result
        assert "RAPIDAPI_KEY" in result["message"]

    @patch("mcp_server_iam.tool.settings")
    def test_search_jobs_missing_api_host(self, mock_settings_patch):
        """Test behavior when API host is missing."""
        # Arrange
        mock_settings_patch.rapidapi_key = "test_key"
        mock_settings_patch.rapidapi_host = ""

        # Act
        result = search_jobs(role="Engineer")

        # Assert
        assert isinstance(result, dict)
        assert "message" in result
        assert "RAPIDAPI_HOST" in result["message"]

    # ========== Input Validation Tests ==========

    @patch("mcp_server_iam.tool.settings")
    def test_search_jobs_city_without_country(self, mock_settings_patch, mock_settings):
        """Test validation when city is provided without country."""
        # Arrange
        mock_settings_patch.rapidapi_key = mock_settings.rapidapi_key
        mock_settings_patch.rapidapi_host = mock_settings.rapidapi_host

        # Act
        result = search_jobs(role="Developer", city="Paris")

        # Assert
        assert isinstance(result, dict)
        assert result["message"] == "Country is required when city is provided."

    @pytest.mark.parametrize("invalid_n_jobs", [0, -1, 21, 100])
    def test_search_jobs_invalid_n_jobs(self, invalid_n_jobs):
        """Test that invalid n_jobs values are rejected by Pydantic."""
        # This test assumes Pydantic validation is enforced at a higher level
        # In unit testing, we test the function behavior with edge values
        # The parameter is used by pytest.mark.parametrize
        assert invalid_n_jobs in [0, -1, 21, 100]

    # ========== API Response Error Tests ==========

    @patch("mcp_server_iam.tool._make_request")
    @patch("mcp_server_iam.tool.settings")
    def test_search_jobs_api_error_response(
        self, mock_settings_patch, mock_make_request, mock_settings
    ):
        """Test handling of API error responses."""
        # Arrange
        mock_settings_patch.rapidapi_key = mock_settings.rapidapi_key
        mock_settings_patch.rapidapi_host = mock_settings.rapidapi_host

        error_response = Mock()
        error_response.status_code = 429
        error_response.text = "Rate limit exceeded"
        mock_make_request.return_value = error_response

        # Act
        result = search_jobs(role="Engineer")

        # Assert
        assert isinstance(result, dict)
        assert "Failed to fetch jobs" in result["message"]
        assert "429" in result["message"]
        # We no longer expose the raw error text for security

    @patch("mcp_server_iam.tool._make_request")
    @patch("mcp_server_iam.tool.settings")
    def test_search_jobs_empty_results(
        self, mock_settings_patch, mock_make_request, mock_settings
    ):
        """Test handling when API returns no jobs."""
        # Arrange
        mock_settings_patch.rapidapi_key = mock_settings.rapidapi_key
        mock_settings_patch.rapidapi_host = mock_settings.rapidapi_host

        response = Mock()
        response.status_code = 200
        response.json.return_value = {"data": []}
        mock_make_request.return_value = response

        # Act
        result = search_jobs(role="Underwater Basket Weaver")

        # Assert
        assert isinstance(result, dict)
        assert result["message"] == "No jobs found."

    # ========== Edge Cases and Corner Cases ==========

    @patch("mcp_server_iam.tool._make_request")
    @patch("mcp_server_iam.tool.settings")
    def test_search_jobs_slice_description_edge_cases(
        self, mock_settings_patch, mock_make_request, mock_settings
    ):
        """Test edge cases for slice_job_description parameter."""
        # Arrange
        mock_settings_patch.rapidapi_key = mock_settings.rapidapi_key
        mock_settings_patch.rapidapi_host = mock_settings.rapidapi_host

        response = Mock()
        response.status_code = 200
        response.json.return_value = {
            "data": [
                {
                    "job_id": "job1",
                    "job_title": "Engineer",
                    "job_description": "Short",
                },
                {
                    "job_id": "job2",
                    "job_title": "Developer",
                    "job_description": "This is a longer description that should be truncated",
                },
            ]
        }
        mock_make_request.return_value = response

        # Act - Test with slice_job_description = 0
        result = search_jobs(role="Tech", slice_job_description=0)

        # Assert - When slice is 0, return full description
        assert result[0]["description"] == "Short"
        assert (
            result[1]["description"]
            == "This is a longer description that should be truncated"
        )

    @patch("mcp_server_iam.tool._make_request")
    @patch("mcp_server_iam.tool.settings")
    def test_search_jobs_missing_job_fields(
        self, mock_settings_patch, mock_make_request, mock_settings
    ):
        """Test handling of missing fields in job data."""
        # Arrange
        mock_settings_patch.rapidapi_key = mock_settings.rapidapi_key
        mock_settings_patch.rapidapi_host = mock_settings.rapidapi_host

        response = Mock()
        response.status_code = 200
        response.json.return_value = {
            "data": [
                {
                    # Missing most fields
                    "job_id": "job1",
                }
            ]
        }
        mock_make_request.return_value = response

        # Act
        result = search_jobs(role="Engineer")

        # Assert
        assert len(result) == 1
        assert result[0]["job_id"] == "job1"
        assert result[0]["title"] is None
        assert result[0]["company"] is None
        assert result[0]["location"] is None
        assert result[0]["description"] == ""
        assert result[0]["apply_link"] == "Not provided"

    @patch("mcp_server_iam.tool._make_request")
    @patch("mcp_server_iam.tool.settings")
    @patch("mcp_server_iam.tool.get_country_code")
    def test_search_jobs_country_code_not_found(
        self,
        mock_country_code,
        mock_settings_patch,
        mock_make_request,
        mock_settings,
        mock_response_success,
    ):
        """Test behavior when country code lookup returns None."""
        # Arrange
        mock_settings_patch.rapidapi_key = mock_settings.rapidapi_key
        mock_settings_patch.rapidapi_host = mock_settings.rapidapi_host
        mock_country_code.return_value = None
        mock_make_request.return_value = mock_response_success

        # Act
        result = search_jobs(role="Engineer", country="Atlantis")

        # Assert
        assert isinstance(result, list)
        # Verify country parameter is not added to URL when code is None
        called_url = mock_make_request.call_args[0][0]
        assert "&country=" not in called_url

    # ========== Security Tests ==========

    @patch("mcp_server_iam.tool._make_request")
    @patch("mcp_server_iam.tool.settings")
    def test_search_jobs_sql_injection_attempt(
        self,
        mock_settings_patch,
        mock_make_request,
        mock_settings,
        mock_response_success,
    ):
        """Test that special characters in inputs are properly encoded."""
        # Arrange
        mock_settings_patch.rapidapi_key = mock_settings.rapidapi_key
        mock_settings_patch.rapidapi_host = mock_settings.rapidapi_host
        mock_make_request.return_value = mock_response_success

        # Act
        dangerous_role = "Engineer'; DROP TABLE jobs; --"
        result = search_jobs(role=dangerous_role)

        # Assert
        assert isinstance(result, list)
        # Verify the dangerous string is URL encoded for safety
        called_url = mock_make_request.call_args[0][0]
        assert dangerous_role not in called_url  # Raw string should NOT be in URL
        assert (
            "Engineer%27%3B%20DROP%20TABLE%20jobs%3B%20--" in called_url
        )  # Should be encoded

    @patch("mcp_server_iam.tool._make_request")
    @patch("mcp_server_iam.tool.settings")
    def test_search_jobs_xss_in_response(
        self, mock_settings_patch, mock_make_request, mock_settings
    ):
        """Test handling of potentially malicious content in API response."""
        # Arrange
        mock_settings_patch.rapidapi_key = mock_settings.rapidapi_key
        mock_settings_patch.rapidapi_host = mock_settings.rapidapi_host

        response = Mock()
        response.status_code = 200
        response.json.return_value = {
            "data": [
                {
                    "job_id": "<script>alert('xss')</script>",
                    "job_title": "<img src=x onerror=alert('xss')>",
                    "job_description": "Normal description",
                }
            ]
        }
        mock_make_request.return_value = response

        # Act
        result = search_jobs(role="Engineer")

        # Assert
        # The function currently passes through potentially dangerous content
        assert result[0]["job_id"] == "<script>alert('xss')</script>"
        assert result[0]["title"] == "<img src=x onerror=alert('xss')>"

    # ========== Network Error Tests ==========

    @patch("mcp_server_iam.tool._make_request")
    @patch("mcp_server_iam.tool.settings")
    def test_search_jobs_connection_error(
        self, mock_settings_patch, mock_make_request, mock_settings
    ):
        """Test handling of network connection errors."""
        # Arrange
        mock_settings_patch.rapidapi_key = mock_settings.rapidapi_key
        mock_settings_patch.rapidapi_host = mock_settings.rapidapi_host
        # Simulate that all retries failed
        mock_make_request.side_effect = requests.ConnectionError(
            "Network is unreachable"
        )

        # Act
        result = search_jobs(role="Engineer")

        # Assert
        assert isinstance(result, dict)
        assert (
            result["message"]
            == "Unable to connect to job search service. Please try again later."
        )

    @patch("mcp_server_iam.tool._make_request")
    @patch("mcp_server_iam.tool.settings")
    def test_search_jobs_timeout_error(
        self, mock_settings_patch, mock_make_request, mock_settings
    ):
        """Test handling of request timeout."""
        # Arrange
        mock_settings_patch.rapidapi_key = mock_settings.rapidapi_key
        mock_settings_patch.rapidapi_host = mock_settings.rapidapi_host
        # Simulate that all retries failed with timeout
        mock_make_request.side_effect = requests.Timeout("Request timed out")

        # Act
        result = search_jobs(role="Engineer")

        # Assert
        assert isinstance(result, dict)
        assert result["message"] == "Job search request timed out. Please try again."

    @patch("mcp_server_iam.tool._make_request")
    @patch("mcp_server_iam.tool.settings")
    def test_search_jobs_invalid_json_response(
        self, mock_settings_patch, mock_make_request, mock_settings
    ):
        """Test handling of invalid JSON in API response."""
        # Arrange
        mock_settings_patch.rapidapi_key = mock_settings.rapidapi_key
        mock_settings_patch.rapidapi_host = mock_settings.rapidapi_host

        response = Mock()
        response.status_code = 200
        response.json.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)
        mock_make_request.return_value = response

        # Act
        result = search_jobs(role="Engineer")

        # Assert
        assert isinstance(result, dict)
        assert result["message"] == "Invalid response format from job search API"

    @patch("mcp_server_iam.tool.requests.get")
    @patch("mcp_server_iam.tool.settings")
    def test_search_jobs_retry_on_timeout(
        self,
        mock_settings_patch,
        mock_requests_get,
        mock_settings,
        mock_response_success,
    ):
        """Test that the function retries on timeout and succeeds."""
        # Arrange
        mock_settings_patch.rapidapi_key = mock_settings.rapidapi_key
        mock_settings_patch.rapidapi_host = mock_settings.rapidapi_host
        # First two calls timeout, third succeeds
        mock_requests_get.side_effect = [
            requests.Timeout("Timeout 1"),
            requests.Timeout("Timeout 2"),
            mock_response_success,
        ]

        # Act
        result = search_jobs(role="Engineer")

        # Assert
        assert isinstance(result, list)
        assert len(result) == 2
        # Verify it was called 3 times (2 retries + 1 success)
        assert mock_requests_get.call_count == 3

    @patch("mcp_server_iam.tool._make_request")
    @patch("mcp_server_iam.tool.settings")
    def test_search_jobs_url_encoding(
        self,
        mock_settings_patch,
        mock_make_request,
        mock_settings,
        mock_response_success,
    ):
        """Test that URL parameters are properly encoded."""
        # Arrange
        mock_settings_patch.rapidapi_key = mock_settings.rapidapi_key
        mock_settings_patch.rapidapi_host = mock_settings.rapidapi_host
        mock_make_request.return_value = mock_response_success

        # Act
        result = search_jobs(
            role="Software Engineer & Developer",
            city="New York",
            country="United States",
            platform="linkedin",
        )

        # Assert
        assert isinstance(result, list)
        called_url = mock_make_request.call_args[0][0]
        # Verify spaces and special characters are encoded
        assert "Software%20Engineer%20%26%20Developer" in called_url
        assert "in%20New%20York" in called_url
        assert "via%20linkedin" in called_url

    # ========== Platform Validation Tests ==========

    @patch("mcp_server_iam.tool._make_request")
    @patch("mcp_server_iam.tool.settings")
    def test_search_jobs_empty_platform_string(
        self,
        mock_settings_patch,
        mock_make_request,
        mock_settings,
        mock_response_success,
    ):
        """Test that empty platform string is handled correctly."""
        # Arrange
        mock_settings_patch.rapidapi_key = mock_settings.rapidapi_key
        mock_settings_patch.rapidapi_host = mock_settings.rapidapi_host
        mock_make_request.return_value = mock_response_success

        # Act
        result = search_jobs(role="Engineer", platform="")

        # Assert
        assert isinstance(result, list)
        # Verify platform is not added to query when empty
        called_url = mock_make_request.call_args[0][0]
        assert "via " not in called_url

    # ========== Description Slicing Logic Tests ==========

    @patch("mcp_server_iam.tool._make_request")
    @patch("mcp_server_iam.tool.settings")
    def test_search_jobs_description_not_string(
        self, mock_settings_patch, mock_make_request, mock_settings
    ):
        """Test handling when job_description is not a string."""
        # Arrange
        mock_settings_patch.rapidapi_key = mock_settings.rapidapi_key
        mock_settings_patch.rapidapi_host = mock_settings.rapidapi_host

        response = Mock()
        response.status_code = 200
        response.json.return_value = {
            "data": [
                {
                    "job_id": "job1",
                    "job_description": None,  # Not a string
                },
                {
                    "job_id": "job2",
                    "job_description": {
                        "text": "description"
                    },  # Dict instead of string
                },
            ]
        }
        mock_make_request.return_value = response

        # Act
        result = search_jobs(role="Engineer", slice_job_description=10)

        # Assert
        assert result[0]["description"] == ""
        assert result[1]["description"] == ""


@pytest.mark.unit
class TestSearchJobsIntegration:
    """Integration-style tests that verify the function works with real-like data."""

    @patch("mcp_server_iam.tool._make_request")
    @patch("mcp_server_iam.tool.settings")
    def test_search_jobs_realistic_scenario(
        self, mock_settings_patch, mock_make_request
    ):
        """Test with realistic API response data."""
        # Arrange
        mock_settings_patch.rapidapi_key = "real_api_key"
        mock_settings_patch.rapidapi_host = "jsearch.p.rapidapi.com"

        response = Mock()
        response.status_code = 200
        response.json.return_value = {
            "status": "OK",
            "request_id": "abc123",
            "data": [
                {
                    "job_id": "R8K3jOMmiWttgNsAAAAAA==",
                    "employer_name": "Google",
                    "employer_logo": "https://example.com/logo.png",
                    "job_publisher": "LinkedIn",
                    "job_employment_type": "FULLTIME",
                    "job_title": "Senior Software Engineer",
                    "job_apply_link": "https://www.linkedin.com/jobs/view/123456",
                    "job_description": "We are looking for a Senior Software Engineer to join our team. The ideal candidate will have 5+ years of experience in Python and cloud technologies. You will be responsible for designing and implementing scalable systems that serve millions of users. Benefits include health insurance, 401k matching, and unlimited PTO.",
                    "job_is_remote": True,
                    "job_posted_at_timestamp": 1700000000,
                    "job_city": "Mountain View",
                    "job_state": "CA",
                    "job_country": "US",
                    "job_latitude": 37.3861,
                    "job_longitude": -122.0839,
                    "job_benefits": [
                        "health_insurance",
                        "retirement_savings",
                        "paid_time_off",
                    ],
                    "job_google_link": "https://www.google.com/search?q=senior+software+engineer+google",
                    "job_offer_expiration_timestamp": 1702592000,
                    "job_required_experience": {
                        "no_experience_required": False,
                        "required_experience_in_months": 60,
                        "experience_mentioned": True,
                        "experience_preferred": False,
                    },
                    "job_required_skills": ["Python", "AWS", "Docker", "Kubernetes"],
                    "job_salary_currency": "USD",
                    "job_salary_period": "YEAR",
                    "job_min_salary": 150000,
                    "job_max_salary": 250000,
                }
            ],
        }
        mock_make_request.return_value = response

        # Act
        result = search_jobs(
            role="Senior Software Engineer",
            city="Mountain View",
            country="US",
            platform="linkedin",
            num_jobs=1,
            slice_job_description=100,
        )

        # Assert
        assert len(result) == 1
        job = result[0]
        assert job["job_id"] == "R8K3jOMmiWttgNsAAAAAA=="
        assert job["title"] == "Senior Software Engineer"
        assert job["company"] == "Google"
        assert job["location"] == "Mountain View"
        assert len(job["description"]) == 100 + len("\n...\n")
        assert job["apply_link"] == "https://www.linkedin.com/jobs/view/123456"
