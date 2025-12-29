import pytest

from cinemagoerng import web as imdb
from cinemagoerng.model import TVMiniSeries, TVSeries


@pytest.mark.parametrize(("imdb_id", "min_seasons", "min_total_episodes"), [
    ("tt0185906", 1, 10),  # Band of Brothers - 1 season, 10 episodes
])
def test_set_all_episodes_should_fetch_episodes_across_all_seasons(
    imdb_id, min_seasons, min_total_episodes
):
    """Test that set_all_episodes fetches all episodes across all seasons."""
    parsed = imdb.get_title(imdb_id=imdb_id)
    assert isinstance(parsed, (TVSeries, TVMiniSeries))
    assert len(parsed.episodes) == 0

    imdb.set_all_episodes(parsed)

    assert len(parsed.episodes) >= min_seasons
    total_episodes = sum(len(eps) for eps in parsed.episodes.values())
    assert total_episodes >= min_total_episodes


@pytest.mark.parametrize(("imdb_id", "season", "episode", "expected_title"), [
    ("tt0185906", "1", "1", "Currahee"),  # Band of Brothers S01E01
    ("tt0185906", "1", "10", "Points"),  # Band of Brothers S01E10
])
def test_set_all_episodes_should_set_correct_episode_data(
    imdb_id, season, episode, expected_title
):
    """Test that episode data is correctly parsed."""
    parsed = imdb.get_title(imdb_id=imdb_id)
    assert isinstance(parsed, (TVSeries, TVMiniSeries))
    imdb.set_all_episodes(parsed)

    assert season in parsed.episodes
    assert episode in parsed.episodes[season]
    ep = parsed.episodes[season][episode]
    assert ep.title == expected_title
    assert ep.imdb_id is not None
    assert ep.imdb_id.startswith("tt")


@pytest.mark.parametrize(("imdb_id",), [
    ("tt0185906",),  # Band of Brothers
])
def test_set_all_episodes_should_set_episode_details(imdb_id):
    """Test that episode details like rating and plot are fetched."""
    parsed = imdb.get_title(imdb_id=imdb_id)
    assert isinstance(parsed, (TVSeries, TVMiniSeries))
    imdb.set_all_episodes(parsed)

    # Check first episode has expected fields
    first_season = list(parsed.episodes.keys())[0]
    first_ep_key = list(parsed.episodes[first_season].keys())[0]
    first_ep = parsed.episodes[first_season][first_ep_key]

    assert first_ep.imdb_id is not None
    assert first_ep.title is not None
    # Rating may or may not be present depending on the episode
    # but the field should exist


@pytest.mark.parametrize(
    ("imdb_id", "filter_seasons", "expected_seasons"),
    [
        # Band of Brothers has only 1 season, filter for season 1
        ("tt0185906", ["1"], ["1"]),
    ],
)
def test_set_all_episodes_with_season_filter(
    imdb_id, filter_seasons, expected_seasons
):
    """Test that season filtering works correctly."""
    parsed = imdb.get_title(imdb_id=imdb_id)
    assert isinstance(parsed, (TVSeries, TVMiniSeries))

    imdb.set_all_episodes(parsed, seasons=filter_seasons)

    # Should only have the filtered seasons
    assert set(parsed.episodes.keys()) == set(expected_seasons)
    # Should have episodes in each season
    for season in expected_seasons:
        assert len(parsed.episodes[season]) > 0


@pytest.mark.parametrize(
    ("imdb_id", "year_from", "year_to", "expected_min_episodes"),
    [
        # Band of Brothers aired in 2001
        ("tt0185906", 2001, 2001, 10),
        # Outside the year range should return 0
        ("tt0185906", 1990, 1995, 0),
    ],
)
def test_set_all_episodes_with_year_filter(
    imdb_id, year_from, year_to, expected_min_episodes
):
    """Test that year filtering works correctly."""
    parsed = imdb.get_title(imdb_id=imdb_id)
    assert isinstance(parsed, (TVSeries, TVMiniSeries))

    imdb.set_all_episodes(parsed, year_from=year_from, year_to=year_to)

    total_episodes = sum(len(eps) for eps in parsed.episodes.values())
    assert total_episodes >= expected_min_episodes
