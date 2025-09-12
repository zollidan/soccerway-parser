"""
Unit tests for H2H data fetching functionality
"""
import pytest
from unittest.mock import patch, mock_open
import json
from main import fetch_h2h_data, H2H_CACHE


class TestH2HFetch:
    """Test class for H2H data fetching"""

    def setup_method(self):
        """Clear cache before each test"""
        H2H_CACHE.clear()

    def test_cache_functionality(self):
        """Test that H2H data is cached properly"""
        mock_data = {"matches": [{"id": 1}]}

        with patch('main.TESTING', True), \
                patch('builtins.open', mock_open(read_data=json.dumps(mock_data))):

            # First call should load from file
            result1 = fetch_h2h_data(123, 456)
            assert result1 == mock_data

            # Second call should use cache (same key order)
            result2 = fetch_h2h_data(123, 456)
            assert result2 == mock_data

            # Different team order should use same cache entry
            result3 = fetch_h2h_data(456, 123)
            assert result3 == mock_data

    def test_cache_key_ordering(self):
        """Test that cache key is consistent regardless of team ID order"""
        mock_data = {"matches": [{"id": 1}]}

        with patch('main.TESTING', True), \
                patch('builtins.open', mock_open(read_data=json.dumps(mock_data))):

            # Fetch with team1=123, team2=456
            fetch_h2h_data(123, 456)

            # Verify cache has entry with sorted key
            cache_keys = list(H2H_CACHE.keys())
            assert len(cache_keys) == 1
            assert cache_keys[0] == ('123', '456')

    def test_testing_mode_file_not_found(self):
        """Test behavior when h2h.json file is not found in testing mode"""
        with patch('main.TESTING', True), \
                patch('builtins.open', side_effect=FileNotFoundError):

            result = fetch_h2h_data(123, 456)
            assert result is None

    def test_testing_mode_json_decode_error(self):
        """Test behavior when h2h.json has invalid JSON in testing mode"""
        with patch('main.TESTING', True), \
                patch('builtins.open', mock_open(read_data="invalid json")):

            result = fetch_h2h_data(123, 456)
            assert result is None

    def test_testing_mode_success(self):
        """Test successful data loading in testing mode"""
        mock_data = {
            "matches": [
                {
                    "teams": [{"id": 123}, {"id": 456}],
                    "winner": 0
                }
            ]
        }

        with patch('main.TESTING', True), \
                patch('builtins.open', mock_open(read_data=json.dumps(mock_data))):

            result = fetch_h2h_data(123, 456)
            assert result == mock_data

    def test_api_mode_success(self):
        """Test successful API call in production mode"""
        mock_data = {"matches": [{"id": 1}]}

        with patch('main.TESTING', False), \
                patch('main._get_with_retries') as mock_get:
            mock_get.return_value = mock_data

            result = fetch_h2h_data(123, 456)
            assert result == mock_data

            # Verify API was called with correct URL
            expected_url = "https://int.soccerway.com/legacy/v1/english/matches/?h2hIds=123%2C456&limit=50&onlydetails=true"
            mock_get.assert_called_once_with(expected_url, headers={'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8', 'Accept-Language': 'ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3', 'Connection': 'keep-alive', 'Host': 'int.soccerway.com', 'Priority': 'u=0, i',
                                             'Sec-Fetch-Dest': 'document', 'Sec-Fetch-Mode': 'navigate', 'Sec-Fetch-Site': 'none', 'Sec-Fetch-User': '?1', 'TE': 'trailers', 'Upgrade-Insecure-Requests': '1', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:142.0) Gecko/20100101 Firefox/142.0'})

    def test_api_mode_exception(self):
        """Test API call exception handling in production mode"""
        with patch('main.TESTING', False), \
                patch('main._get_with_retries', side_effect=Exception("Network error")):

            result = fetch_h2h_data(123, 456)
            assert result is None

    def test_string_team_ids(self):
        """Test fetching with string team IDs"""
        mock_data = {"matches": [{"id": 1}]}

        with patch('main.TESTING', True), \
                patch('builtins.open', mock_open(read_data=json.dumps(mock_data))):

            result = fetch_h2h_data("123", "456")
            assert result == mock_data

            # Verify cache key is string-sorted
            cache_keys = list(H2H_CACHE.keys())
            assert cache_keys[0] == ('123', '456')

    def test_mixed_type_team_ids(self):
        """Test fetching with mixed int/string team IDs"""
        mock_data = {"matches": [{"id": 1}]}

        with patch('main.TESTING', True), \
                patch('builtins.open', mock_open(read_data=json.dumps(mock_data))):

            result = fetch_h2h_data(123, "456")
            assert result == mock_data

            # Verify cache key conversion to strings
            cache_keys = list(H2H_CACHE.keys())
            assert cache_keys[0] == ('123', '456')

    def test_cache_persists_across_calls(self):
        """Test that cache persists across multiple different team pairs"""
        mock_data1 = {"matches": [{"id": 1}]}
        mock_data2 = {"matches": [{"id": 2}]}

        with patch('main.TESTING', True):
            # Mock different files for different team pairs
            def mock_open_side_effect(*args, **kwargs):
                if 'h2h.json' in str(args[0]):
                    # Return different data based on current call context
                    return mock_open(read_data=json.dumps(mock_data1))()
                return mock_open()()

            with patch('builtins.open', side_effect=mock_open_side_effect):
                # First pair
                result1 = fetch_h2h_data(123, 456)
                assert result1 == mock_data1

                # Manually add second entry to simulate different data
                H2H_CACHE[('789', '101')] = mock_data2

                # Verify both entries exist in cache
                assert len(H2H_CACHE) == 2
                assert H2H_CACHE[('123', '456')] == mock_data1
                assert H2H_CACHE[('789', '101')] == mock_data2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
