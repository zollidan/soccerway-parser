"""
Unit tests for H2H (Head-to-Head) statistics calculation
"""
import pytest

from main import parse_h2h_stats


class TestH2HStats:
    """Test class for H2H statistics parsing"""

    def test_empty_h2h_data(self):
        """Test parsing when H2H data is None or empty"""
        result = parse_h2h_stats(None, "123", "456")
        expected = {
            'h2h_игры_дома_ком1': 0,
            'h2h_побед_дома_ком1': 0,
            'h2h_ничьи_ком1': 0,
            'h2h_побед_гостей_ком1': 0,
            'h2h_игры_дома_ком2': 0,
            'h2h_побед_дома_ком2': 0,
            'h2h_ничьи_ком2': 0,
            'h2h_побед_гостей_ком2': 0,
        }
        assert result == expected

    def test_no_matches_key(self):
        """Test parsing when H2H data has no 'matches' key"""
        h2h_data = {"some_other_key": "value"}
        result = parse_h2h_stats(h2h_data, "123", "456")
        expected = {
            'h2h_игры_дома_ком1': 0,
            'h2h_побед_дома_ком1': 0,
            'h2h_ничьи_ком1': 0,
            'h2h_побед_гостей_ком1': 0,
            'h2h_игры_дома_ком2': 0,
            'h2h_побед_дома_ком2': 0,
            'h2h_ничьи_ком2': 0,
            'h2h_побед_гостей_ком2': 0,
        }
        assert result == expected

    def test_team1_home_win(self):
        """Test when team1 plays at home and wins"""
        h2h_data = {
            "matches": [
                {
                    "teams": [
                        {"id": 123},  # team1 home
                        {"id": 456}   # team2 away
                    ],
                    "winner": 0  # home team wins
                }
            ]
        }
        result = parse_h2h_stats(h2h_data, 123, 456)
        assert result['h2h_игры_дома_ком1'] == 1
        assert result['h2h_побед_дома_ком1'] == 1
        assert result['h2h_ничьи_ком1'] == 0
        assert result['h2h_побед_гостей_ком1'] == 0

    def test_team1_home_loss(self):
        """Test when team1 plays at home and loses"""
        h2h_data = {
            "matches": [
                {
                    "teams": [
                        {"id": 123},  # team1 home
                        {"id": 456}   # team2 away
                    ],
                    "winner": 1  # away team wins
                }
            ]
        }
        result = parse_h2h_stats(h2h_data, 123, 456)
        assert result['h2h_игры_дома_ком1'] == 1
        assert result['h2h_побед_дома_ком1'] == 0
        assert result['h2h_ничьи_ком1'] == 0
        assert result['h2h_побед_гостей_ком1'] == 1

    def test_team1_home_draw(self):
        """Test when team1 plays at home and draws"""
        h2h_data = {
            "matches": [
                {
                    "teams": [
                        {"id": 123},  # team1 home
                        {"id": 456}   # team2 away
                    ],
                    "winner": -1  # draw
                }
            ]
        }
        result = parse_h2h_stats(h2h_data, 123, 456)
        assert result['h2h_игры_дома_ком1'] == 1
        assert result['h2h_побед_дома_ком1'] == 0
        assert result['h2h_ничьи_ком1'] == 1
        assert result['h2h_побед_гостей_ком1'] == 0

    def test_team2_home_win(self):
        """Test when team2 plays at home and wins"""
        h2h_data = {
            "matches": [
                {
                    "teams": [
                        {"id": 456},  # team2 home
                        {"id": 123}   # team1 away
                    ],
                    "winner": 0  # home team wins
                }
            ]
        }
        result = parse_h2h_stats(h2h_data, 123, 456)
        assert result['h2h_игры_дома_ком2'] == 1
        assert result['h2h_побед_дома_ком2'] == 1
        assert result['h2h_ничьи_ком2'] == 0
        assert result['h2h_побед_гостей_ком2'] == 0

    def test_team2_home_loss(self):
        """Test when team2 plays at home and loses"""
        h2h_data = {
            "matches": [
                {
                    "teams": [
                        {"id": 456},  # team2 home
                        {"id": 123}   # team1 away
                    ],
                    "winner": 1  # away team wins
                }
            ]
        }
        result = parse_h2h_stats(h2h_data, 123, 456)
        assert result['h2h_игры_дома_ком2'] == 1
        assert result['h2h_побед_дома_ком2'] == 0
        assert result['h2h_ничьи_ком2'] == 0
        assert result['h2h_побед_гостей_ком2'] == 1

    def test_team2_home_draw(self):
        """Test when team2 plays at home and draws"""
        h2h_data = {
            "matches": [
                {
                    "teams": [
                        {"id": 456},  # team2 home
                        {"id": 123}   # team1 away
                    ],
                    "winner": -1  # draw
                }
            ]
        }
        result = parse_h2h_stats(h2h_data, 123, 456)
        assert result['h2h_игры_дома_ком2'] == 1
        assert result['h2h_побед_дома_ком2'] == 0
        assert result['h2h_ничьи_ком2'] == 1
        assert result['h2h_побед_гостей_ком2'] == 0

    def test_multiple_matches(self):
        """Test parsing multiple H2H matches"""
        h2h_data = {
            "matches": [
                {
                    "teams": [
                        {"id": 123},  # team1 home
                        {"id": 456}   # team2 away
                    ],
                    "winner": 0  # team1 wins at home
                },
                {
                    "teams": [
                        {"id": 456},  # team2 home
                        {"id": 123}   # team1 away
                    ],
                    "winner": 1  # team1 wins away
                },
                {
                    "teams": [
                        {"id": 123},  # team1 home
                        {"id": 456}   # team2 away
                    ],
                    "winner": -1  # draw
                }
            ]
        }
        result = parse_h2h_stats(h2h_data, 123, 456)

        # Team1 home stats: 2 games, 1 win, 1 draw, 0 away wins
        assert result['h2h_игры_дома_ком1'] == 2
        assert result['h2h_побед_дома_ком1'] == 1
        assert result['h2h_ничьи_ком1'] == 1
        assert result['h2h_побед_гостей_ком1'] == 0

        # Team2 home stats: 1 game, 0 wins, 0 draws, 1 away win
        assert result['h2h_игры_дома_ком2'] == 1
        assert result['h2h_побед_дома_ком2'] == 0
        assert result['h2h_ничьи_ком2'] == 0
        assert result['h2h_побед_гостей_ком2'] == 1

    def test_string_team_ids(self):
        """Test parsing with string team IDs"""
        h2h_data = {
            "matches": [
                {
                    "teams": [
                        {"id": "123"},  # team1 home as string
                        {"id": "456"}   # team2 away as string
                    ],
                    "winner": 0  # home team wins
                }
            ]
        }
        result = parse_h2h_stats(h2h_data, 123, 456)
        assert result['h2h_игры_дома_ком1'] == 1
        assert result['h2h_побед_дома_ком1'] == 1

    def test_mixed_team_ids(self):
        """Test parsing with mixed int/string team IDs"""
        h2h_data = {
            "matches": [
                {
                    "teams": [
                        {"id": 123},    # team1 home as int
                        {"id": "456"}   # team2 away as string
                    ],
                    "winner": 0  # home team wins
                }
            ]
        }
        result = parse_h2h_stats(h2h_data, "123", 456)
        assert result['h2h_игры_дома_ком1'] == 1
        assert result['h2h_побед_дома_ком1'] == 1

    def test_invalid_teams_data(self):
        """Test parsing when teams data is malformed"""
        h2h_data = {
            "matches": [
                {
                    "teams": [
                        {"id": 123}  # Only one team
                    ],
                    "winner": 0
                },
                {
                    "teams": [],  # No teams
                    "winner": 0
                },
                {
                    # No teams key
                    "winner": 0
                }
            ]
        }
        result = parse_h2h_stats(h2h_data, 123, 456)
        expected = {
            'h2h_игры_дома_ком1': 0,
            'h2h_побед_дома_ком1': 0,
            'h2h_ничьи_ком1': 0,
            'h2h_побед_гостей_ком1': 0,
            'h2h_игры_дома_ком2': 0,
            'h2h_побед_дома_ком2': 0,
            'h2h_ничьи_ком2': 0,
            'h2h_побед_гостей_ком2': 0,
        }
        assert result == expected

    def test_missing_team_ids(self):
        """Test parsing when team IDs are missing"""
        h2h_data = {
            "matches": [
                {
                    "teams": [
                        {},  # No id key
                        {"id": 456}
                    ],
                    "winner": 0
                },
                {
                    "teams": [
                        {"id": 123},
                        {}  # No id key
                    ],
                    "winner": 1
                }
            ]
        }
        result = parse_h2h_stats(h2h_data, 123, 456)
        expected = {
            'h2h_игры_дома_ком1': 0,
            'h2h_побед_дома_ком1': 0,
            'h2h_ничьи_ком1': 0,
            'h2h_побед_гостей_ком1': 0,
            'h2h_игры_дома_ком2': 0,
            'h2h_побед_дома_ком2': 0,
            'h2h_ничьи_ком2': 0,
            'h2h_побед_гостей_ком2': 0,
        }
        assert result == expected

    def test_irrelevant_matches(self):
        """Test that matches not involving the specified teams are ignored"""
        h2h_data = {
            "matches": [
                {
                    "teams": [
                        {"id": 789},  # Different teams
                        {"id": 101}
                    ],
                    "winner": 0
                },
                {
                    "teams": [
                        {"id": 123},  # Only one team matches
                        {"id": 789}
                    ],
                    "winner": 1
                },
                {
                    "teams": [
                        {"id": 123},  # Both teams match
                        {"id": 456}
                    ],
                    "winner": 0  # team1 wins at home
                }
            ]
        }
        result = parse_h2h_stats(h2h_data, 123, 456)
        assert result['h2h_игры_дома_ком1'] == 1
        assert result['h2h_побед_дома_ком1'] == 1
        assert result['h2h_игры_дома_ком2'] == 0

    def test_missing_winner_field(self):
        """Test parsing when winner field is missing"""
        h2h_data = {
            "matches": [
                {
                    "teams": [
                        {"id": 123},
                        {"id": 456}
                    ]
                    # No winner field
                }
            ]
        }
        result = parse_h2h_stats(h2h_data, 123, 456)
        # When winner is missing, it defaults to -1 (draw)
        assert result['h2h_игры_дома_ком1'] == 1
        assert result['h2h_побед_дома_ком1'] == 0
        assert result['h2h_ничьи_ком1'] == 1
        assert result['h2h_побед_гостей_ком1'] == 0

    def test_comprehensive_scenario(self):
        """Test comprehensive scenario with various match outcomes"""
        h2h_data = {
            "matches": [
                # Team1 home wins
                {"teams": [{"id": 123}, {"id": 456}], "winner": 0},
                {"teams": [{"id": 123}, {"id": 456}], "winner": 0},
                # Team1 home losses
                {"teams": [{"id": 123}, {"id": 456}], "winner": 1},
                # Team1 home draws
                {"teams": [{"id": 123}, {"id": 456}], "winner": -1},
                {"teams": [{"id": 123}, {"id": 456}], "winner": -1},
                # Team2 home wins
                {"teams": [{"id": 456}, {"id": 123}], "winner": 0},
                # Team2 home losses
                {"teams": [{"id": 456}, {"id": 123}], "winner": 1},
                {"teams": [{"id": 456}, {"id": 123}], "winner": 1},
                # Team2 home draws
                {"teams": [{"id": 456}, {"id": 123}], "winner": -1},
            ]
        }
        result = parse_h2h_stats(h2h_data, 123, 456)

        # Team1 home: 5 games, 2 wins, 2 draws, 1 away win
        assert result['h2h_игры_дома_ком1'] == 5
        assert result['h2h_побед_дома_ком1'] == 2
        assert result['h2h_ничьи_ком1'] == 2
        assert result['h2h_побед_гостей_ком1'] == 1

        # Team2 home: 4 games, 1 win, 1 draw, 2 away wins
        assert result['h2h_игры_дома_ком2'] == 4
        assert result['h2h_побед_дома_ком2'] == 1
        assert result['h2h_ничьи_ком2'] == 1
        assert result['h2h_побед_гостей_ком2'] == 2


if __name__ == "__main__":
    pytest.main([__file__])
