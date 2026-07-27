document.addEventListener('DOMContentLoaded', () => {

  let activeTab = 'home';
  let selectedMovies = [];
  let currentRecommendations = [];
  let catalogMovies = [];
  let watchlist = JSON.parse(localStorage.getItem('cinematic_watchlist') || '[]');
  let searchDebounceTimer = null;

  const navTabs = document.querySelectorAll('.nav-tab');
  const pageViews = document.querySelectorAll('.page-view');

  const searchInput = document.getElementById('searchInput');
  const autocompleteResults = document.getElementById('autocompleteResults');
  const selectedMoviesGrid = document.getElementById('selectedMoviesGrid');
  const emptyTasteState = document.getElementById('emptyTasteState');
  const selectedCountText = document.getElementById('selectedCountText');
  const generateBtn = document.getElementById('generateBtn');
  const moviesGrid = document.getElementById('moviesGrid');
  const resultsTitle = document.getElementById('resultsTitle');

  const genreFilter = document.getElementById('genreFilter');
  const ratingFilter = document.getElementById('ratingFilter');
  const eraFilter = document.getElementById('eraFilter');
  const sortFilter = document.getElementById('sortFilter');

  const catalogSearchInput = document.getElementById('catalogSearchInput');
  const catalogGenreFilter = document.getElementById('catalogGenreFilter');
  const catalogGrid = document.getElementById('catalogGrid');

  const detailModal = document.getElementById('detailModal');
  const closeModalBtn = document.getElementById('closeModalBtn');
  const modalPoster = document.getElementById('modalPoster');
  const modalBackdrop = document.getElementById('modalBackdrop');
  const modalTitle = document.getElementById('modalTitle');
  const modalMeta = document.getElementById('modalMeta');
  const modalTagline = document.getElementById('modalTagline');
  const modalOverview = document.getElementById('modalOverview');
  const modalReason = document.getElementById('modalReason');
  const modalCast = document.getElementById('modalCast');
  const trailerWrapper = document.getElementById('trailerWrapper');
  const trailerFrame = document.getElementById('trailerFrame');
  const watchlistCount = document.getElementById('watchlistCount');

  updateWatchlistBadge();
  fetchHomeDiscoverData();

  window.showTab = function(tabName) {
    activeTab = tabName;
    
    navTabs.forEach(t => {
      if (t.dataset.tab === tabName) {
        t.classList.add('active');
      } else {
        t.classList.remove('active');
      }
    });

    pageViews.forEach(pv => {
      if (pv.id === `page-${tabName}`) {
        pv.classList.add('active');
      } else {
        pv.classList.remove('active');
      }
    });

    window.scrollTo({ top: 0, behavior: 'smooth' });

    if (tabName === 'catalog') {
      fetchCatalogMovies();
    } else if (tabName === 'watchlist') {
      renderWatchlistPage();
    } else if (tabName === 'analytics') {
      renderAnalyticsPage();
    }
  };

  async function fetchHomeDiscoverData() {
    try {
      const [trendRes, topRes] = await Promise.all([
        fetch('/api/trending?limit=6'),
        fetch('/api/top-rated?limit=6')
      ]);

      const trendData = await trendRes.json();
      const topData = await topRes.json();

      renderPosterGrid(trendData.trending || [], 'trendingPosterGrid');
      renderPosterGrid(topData.top_rated || [], 'topRatedPosterGrid');
    } catch (err) {
      console.error("Home discover error:", err);
    }
  }

  function renderPosterGrid(movies, containerId) {
    const container = document.getElementById(containerId);
    if (!container) return;

    if (!movies || movies.length === 0) {
      container.innerHTML = `<div style="color: var(--text-muted);">No movies available right now.</div>`;
      return;
    }

    container.innerHTML = movies.map(m => {
      const posterSrc = m.poster_path || 'https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?w=500&q=80';
      return `
        <div class="poster-card" onclick="openMovieDetails(${m.movieId})">
          <div class="poster-img-wrapper">
            <img class="poster-img" src="${posterSrc}" alt="${escapeHtml(m.title)}" loading="lazy" onerror="this.src='https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?w=500&q=80'">
            <div class="poster-overlay"></div>
            <div class="rating-badge">★ ${m.vote_average ? m.vote_average.toFixed(1) : '8.0'}</div>
            <div class="poster-info">
              <div class="poster-title">${escapeHtml(m.title)}</div>
              <div class="poster-sub">${m.release_year || 'N/A'} • ${escapeHtml(m.genres.split('•')[0] || '')}</div>
            </div>
          </div>
        </div>
      `;
    }).join('');
  }

  searchInput.addEventListener('input', (e) => {
    const query = e.target.value.trim();
    clearTimeout(searchDebounceTimer);

    if (query.length < 2) {
      autocompleteResults.classList.remove('active');
      return;
    }

    searchDebounceTimer = setTimeout(async () => {
      try {
        const res = await fetch(`/api/search?q=${encodeURIComponent(query)}`);
        const data = await res.json();
        renderAutocomplete(data.results || []);
      } catch (err) {
        console.error("Search error:", err);
      }
    }, 220);
  });

  document.addEventListener('click', (e) => {
    if (!searchInput.contains(e.target) && !autocompleteResults.contains(e.target)) {
      autocompleteResults.classList.remove('active');
    }
  });

  function renderAutocomplete(results) {
    if (!results || results.length === 0) {
      autocompleteResults.innerHTML = `<div style="padding: 1rem; text-align: center; color: var(--text-muted);">No movies found for this search. Try another title!</div>`;
      autocompleteResults.classList.add('active');
      return;
    }

    autocompleteResults.innerHTML = results.map(m => {
      const posterSrc = m.poster_path || 'https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?w=200&q=80';
      const year = m.release_year || 'N/A';
      const rating = m.vote_average ? `${m.vote_average.toFixed(1)}/10` : 'N/A';
      const genres = m.genres ? m.genres.replace(/\|/g, ' • ') : 'General';
      const movieJson = escapeHtml(JSON.stringify(m));

      return `
        <div class="search-result-item" onclick='addMovieFromSearch(${movieJson})'>
          <img class="result-poster" src="${posterSrc}" alt="${escapeHtml(m.title)}" onerror="this.src='https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?w=200&q=80'">
          <div class="result-info">
            <div class="result-title">${escapeHtml(m.title)}</div>
            <div class="result-meta">
              <span>📅 ${year}</span>
              <span>•</span>
              <span>${genres}</span>
              <span>•</span>
              <span style="color: var(--accent-amber); font-weight: 700;">★ ${rating}</span>
            </div>
          </div>
          <button class="add-btn-small"><i class="fa-solid fa-plus"></i> Add</button>
        </div>
      `;
    }).join('');

    autocompleteResults.classList.add('active');
  }

  window.addMovieFromSearch = function(movie) {
    autocompleteResults.classList.remove('active');
    searchInput.value = '';

    if (selectedMovies.some(m => m.movieId === movie.movieId)) {
      alert(`"${movie.title}" is already in your taste profile!`);
      return;
    }

    if (selectedMovies.length >= 5) {
      alert("You can select up to 5 movies to guide your recommendations.");
      return;
    }

    selectedMovies.push({
      movieId: movie.movieId,
      id: movie.movieId,
      title: movie.title,
      genres: movie.genres,
      overview: movie.overview,
      poster_path: movie.poster_path,
      rating: 5
    });

    renderSelectedMovies();
  };

  function renderSelectedMovies() {
    if (selectedMovies.length === 0) {
      emptyTasteState.style.display = 'block';
      selectedMoviesGrid.innerHTML = '';
      selectedCountText.innerText = `0 / 5 movies added`;
      generateBtn.disabled = true;
      return;
    }

    emptyTasteState.style.display = 'none';
    selectedCountText.innerText = `${selectedMovies.length} / 5 movies added`;
    generateBtn.disabled = false;

    selectedMoviesGrid.innerHTML = selectedMovies.map((m, idx) => {
      const posterSrc = m.poster_path || 'https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?w=200&q=80';
      const starsHtml = [1, 2, 3, 4, 5].map(star => `
        <span class="star ${star <= m.rating ? 'active' : ''}" onclick="rateSelectedMovie(${idx}, ${star})">★</span>
      `).join('');

      return `
        <div class="selected-movie-card">
          <img class="selected-poster" src="${posterSrc}" alt="${escapeHtml(m.title)}" onerror="this.src='https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?w=200&q=80'">
          <div class="selected-info">
            <div class="selected-name">${escapeHtml(m.title)}</div>
            <div class="rating-stars">${starsHtml}</div>
          </div>
          <button class="remove-selected-btn" onclick="removeSelectedMovie(${idx})" title="Remove">
            <i class="fa-solid fa-xmark"></i>
          </button>
        </div>
      `;
    }).join('');
  }

  window.rateSelectedMovie = function(idx, rating) {
    if (selectedMovies[idx]) {
      selectedMovies[idx].rating = rating;
      renderSelectedMovies();
    }
  };

  window.removeSelectedMovie = function(idx) {
    selectedMovies.splice(idx, 1);
    renderSelectedMovies();
  };

  document.querySelectorAll('.mood-chip').forEach(btn => {
    btn.addEventListener('click', () => {
      const mood = btn.dataset.mood;
      const moodPresets = {
        'Mind-Bending': [
          { movieId: 27205, title: 'Inception', genres: 'Action|Science Fiction|Thriller', overview: 'Espionage through dream infiltration.', poster_path: 'https://image.tmdb.org/t/p/w500/oYuLEW9WAFK1PFi23fcrRf2eAQ9.jpg', rating: 5 },
          { movieId: 157336, title: 'Interstellar', genres: 'Adventure|Drama|Science Fiction', overview: 'Wormhole space travel.', poster_path: 'https://image.tmdb.org/t/p/w500/gEU2QniE6E77NI6lCU6MxlNBvIx.jpg', rating: 5 },
          { movieId: 603, title: 'The Matrix', genres: 'Action|Science Fiction', overview: 'World simulation rebellion.', poster_path: 'https://image.tmdb.org/t/p/w500/f89U3w9nYiBXwA92zWBYVwvbyh5.jpg', rating: 5 }
        ],
        'Sci-Fi Epic': [
          { movieId: 693134, title: 'Dune: Part Two', genres: 'Science Fiction|Adventure', overview: 'Paul Atreides unites with Fremen.', poster_path: 'https://image.tmdb.org/t/p/w500/1pdfLPoWuVzhAcStTWySizKGTTz.jpg', rating: 5 },
          { movieId: 157336, title: 'Interstellar', genres: 'Adventure|Drama|Science Fiction', overview: 'Space travel through wormhole.', poster_path: 'https://image.tmdb.org/t/p/w500/gEU2QniE6E77NI6lCU6MxlNBvIx.jpg', rating: 5 }
        ],
        'Adrenaline Action': [
          { movieId: 155, title: 'The Dark Knight', genres: 'Action|Crime|Drama', overview: 'Batman fights Joker.', poster_path: 'https://image.tmdb.org/t/p/w500/qJ2tW6WMUDux911r6m7haRef0WH.jpg', rating: 5 },
          { movieId: 603, title: 'The Matrix', genres: 'Action|Science Fiction', overview: 'Neo fights machines.', poster_path: 'https://image.tmdb.org/t/p/w500/f89U3w9nYiBXwA92zWBYVwvbyh5.jpg', rating: 5 }
        ],
        'Dark Thriller': [
          { movieId: 550, title: 'Fight Club', genres: 'Drama|Thriller', overview: 'Underground fight club.', poster_path: 'https://image.tmdb.org/t/p/w500/pB8BM7pdSp6B6Ih7QZ4DrQ3PmJK.jpg', rating: 5 },
          { movieId: 680, title: 'Pulp Fiction', genres: 'Thriller|Crime', overview: 'Mob hitmen tales.', poster_path: 'https://image.tmdb.org/t/p/w500/d5iIlFn5s0ImszYzBPb8JPIfbXD.jpg', rating: 5 }
        ],
        'Feel Good': [
          { movieId: 13, title: 'Forrest Gump', genres: 'Comedy|Drama|Romance', overview: 'Historical events unfolding.', poster_path: 'https://image.tmdb.org/t/p/w500/arw2vcBveWOVZr6pxd9LiyvuPhv.jpg', rating: 5 },
          { movieId: 278, title: 'The Shawshank Redemption', genres: 'Drama|Crime', overview: 'Hope and redemption.', poster_path: 'https://image.tmdb.org/t/p/w500/9cqN12YSA8v8wWf3GiYJeEiv2G.jpg', rating: 5 }
        ]
      };

      if (moodPresets[mood]) {
        selectedMovies = [...moodPresets[mood]];
        renderSelectedMovies();
      }
    });
  });

  generateBtn.addEventListener('click', () => {
    fetchRecommendations();
  });

  [genreFilter, ratingFilter, eraFilter, sortFilter].forEach(el => {
    el.addEventListener('change', () => {
      if (selectedMovies.length > 0) {
        fetchRecommendations();
      }
    });
  });

  async function fetchRecommendations() {
    if (selectedMovies.length === 0) return;

    moviesGrid.innerHTML = `
      <div style="grid-column: 1 / -1; text-align: center; padding: 4rem 1rem;">
        <i class="fa-solid fa-spinner fa-spin" style="font-size: 3rem; color: var(--accent-primary); margin-bottom: 1rem;"></i>
        <h3>Running Content Vectors & TMDB Similarity Graph...</h3>
        <p style="color: var(--text-secondary); margin-top: 0.5rem;">Generating high-confidence recommendations with explainable reasons...</p>
      </div>
    `;

    try {
      const payload = {
        user_ratings: selectedMovies,
        filters: {
          genre: genreFilter.value,
          min_rating: parseFloat(ratingFilter.value),
          era: eraFilter.value,
          sort_by: sortFilter.value
        },
        n_recommendations: 12
      };

      const res = await fetch('/api/recommend', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      const data = await res.json();
      currentRecommendations = data.recommendations || [];
      resultsTitle.innerText = `Top ${currentRecommendations.length} Recommendations For You`;
      renderRecommendations(currentRecommendations);
    } catch (err) {
      console.error("Recommendation error:", err);
      moviesGrid.innerHTML = `<div style="grid-column: 1 / -1; text-align: center; color: var(--accent-pink);">Failed to fetch recommendations. Please try again.</div>`;
    }
  }

  function renderRecommendations(movies) {
    if (!movies || movies.length === 0) {
      moviesGrid.innerHTML = `
        <div style="grid-column: 1 / -1; text-align: center; padding: 3rem 1rem; color: var(--text-muted);">
          <i class="fa-solid fa-filter" style="font-size: 2.5rem; margin-bottom: 0.8rem; opacity: 0.4;"></i>
          <h3>No matching recommendations found for these active filters.</h3>
          <p style="margin-top: 0.4rem;">Try resetting your filters or picking different movies!</p>
        </div>
      `;
      return;
    }

    moviesGrid.innerHTML = movies.map(m => {
      const posterSrc = m.poster_path || 'https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?w=500&q=80';
      const isSaved = watchlist.some(w => w.movieId === m.movieId);
      const matchPct = m.match_percentage || 85;

      return `
        <div class="rec-card">
          <div class="rec-poster-wrapper">
            <img class="rec-poster" src="${posterSrc}" alt="${escapeHtml(m.title)}" loading="lazy" onerror="this.src='https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?w=500&q=80'">
            <div class="match-ring-badge">
              <i class="fa-solid fa-bolt" style="color: var(--accent-cyan);"></i> ${matchPct}% Match
            </div>
            <button class="bookmark-btn ${isSaved ? 'saved' : ''}" onclick="toggleWatchlist(${m.movieId})" title="Save to Watchlist">
              <i class="fa-${isSaved ? 'solid' : 'regular'} fa-bookmark"></i>
            </button>
          </div>

          <div class="rec-body">
            <h3 class="rec-title">${escapeHtml(m.title)}</h3>
            
            <div class="rec-meta">
              <span>📅 ${m.release_year}</span>
              <span>•</span>
              <span style="color: var(--accent-amber); font-weight: 700;"><i class="fa-solid fa-star"></i> ${m.vote_average.toFixed(1)}/10</span>
            </div>

            <div class="reason-card">
              <i class="fa-solid fa-brain" style="color: var(--accent-primary); margin-right: 4px;"></i>
              ${formatReasonMarkdown(m.reason)}
            </div>

            <button class="action-btn" onclick="openMovieDetails(${m.movieId})">
              <i class="fa-solid fa-circle-info"></i> View Details & Trailer
            </button>
          </div>
        </div>
      `;
    }).join('');
  }

  async function fetchCatalogMovies() {
    try {
      const res = await fetch('/api/trending?limit=12');
      const data = await res.json();
      catalogMovies = data.trending || [];
      renderPosterGrid(catalogMovies, 'catalogGrid');
    } catch (err) {
      console.error("Catalog error:", err);
    }
  }

  if (catalogSearchInput) {
    catalogSearchInput.addEventListener('input', (e) => {
      const q = e.target.value.toLowerCase().trim();
      const filtered = catalogMovies.filter(m => m.title.toLowerCase().includes(q));
      renderPosterGrid(filtered, 'catalogGrid');
    });
  }

  function renderWatchlistPage() {
    const grid = document.getElementById('watchlistPageGrid');
    if (!grid) return;

    if (watchlist.length === 0) {
      grid.innerHTML = `
        <div style="grid-column: 1 / -1; text-align: center; padding: 4rem 1rem; color: var(--text-muted);">
          <i class="fa-solid fa-bookmark" style="font-size: 3rem; margin-bottom: 1rem; opacity: 0.4;"></i>
          <h3>Your watchlist is empty.</h3>
          <p style="margin-top: 0.4rem;">Bookmark movies while browsing to save them here!</p>
        </div>
      `;
      return;
    }

    renderPosterGrid(watchlist, 'watchlistPageGrid');
  }

  function renderAnalyticsPage() {
    const genreContainer = document.getElementById('analyticsGenreBars');
    const eraContainer = document.getElementById('analyticsEraBars');

    if (!selectedMovies || selectedMovies.length === 0) {
      const emptyMsg = `<div style="color: var(--text-muted); font-size: 0.9rem;">Select movies in the <strong>AI Recommender</strong> tab to see your taste analytics!</div>`;
      if (genreContainer) genreContainer.innerHTML = emptyMsg;
      if (eraContainer) eraContainer.innerHTML = emptyMsg;
      return;
    }

    const genreCounts = {};
    selectedMovies.forEach(m => {
      const gList = (m.genres || '').split(/\||•/);
      gList.forEach(g => {
        const cleanG = g.trim();
        if (cleanG && cleanG !== 'General') {
          genreCounts[cleanG] = (genreCounts[cleanG] || 0) + 1;
        }
      });
    });

    const maxCount = Math.max(...Object.values(genreCounts), 1);
    if (genreContainer) {
      genreContainer.innerHTML = Object.entries(genreCounts).map(([g, cnt]) => `
        <div class="progress-bar-row">
          <div class="progress-label-wrap">
            <span><strong>${escapeHtml(g)}</strong></span>
            <span>${cnt} movies</span>
          </div>
          <div class="progress-track">
            <div class="progress-fill" style="width: ${(cnt / maxCount) * 100}%;"></div>
          </div>
        </div>
      `).join('');
    }

    if (eraContainer) {
      eraContainer.innerHTML = `
        <div class="progress-bar-row">
          <div class="progress-label-wrap">
            <span><strong>Modern Era (2010 - Present)</strong></span>
            <span>High Affinity</span>
          </div>
          <div class="progress-track">
            <div class="progress-fill" style="width: 85%;"></div>
          </div>
        </div>
        <div class="progress-bar-row">
          <div class="progress-label-wrap">
            <span><strong>Average Rating Given</strong></span>
            <span>4.8 / 5 Stars</span>
          </div>
          <div class="progress-track">
            <div class="progress-fill" style="width: 96%; background: var(--accent-amber);"></div>
          </div>
        </div>
      `;
    }
  }

  window.openMovieDetails = async function(movieId) {
    try {
      const res = await fetch(`/api/movie/${movieId}`);
      const d = await res.json();

      modalTitle.innerText = d.title || 'Movie Details';
      modalMeta.innerText = `${d.release_year || 'N/A'} • ${d.genres || ''} • ★ ${d.vote_average ? d.vote_average.toFixed(1) : 'N/A'}/10`;
      modalTagline.innerText = d.tagline ? `"${d.tagline}"` : '';
      modalOverview.innerText = d.overview || 'No overview available.';

      modalPoster.src = d.poster_path || 'https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?w=500&q=80';
      modalBackdrop.src = d.backdrop_path || d.poster_path || 'https://images.unsplash.com/photo-1517604931442-7e0c8ed2963c?w=1280&q=80';

      const recMatch = currentRecommendations.find(r => r.movieId === movieId);
      modalReason.innerHTML = recMatch 
        ? `<i class="fa-solid fa-brain" style="color: var(--accent-primary);"></i> <strong>Why Recommended:</strong> ${formatReasonMarkdown(recMatch.reason)}`
        : `<i class="fa-solid fa-film" style="color: var(--accent-primary);"></i> Directed by <strong>${d.director}</strong>.`;

      if (d.cast && d.cast.length > 0) {
        modalCast.innerHTML = d.cast.map(c => `
          <div class="cast-chip">
            <img class="cast-avatar" src="${c.profile_path || 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=100&q=80'}" alt="${escapeHtml(c.name)}">
            <span style="font-size: 0.82rem;"><strong>${escapeHtml(c.name)}</strong></span>
          </div>
        `).join('');
      } else {
        modalCast.innerHTML = `<span style="color: var(--text-muted); font-size: 0.85rem;">Cast details unavailable.</span>`;
      }

      if (d.trailer_key) {
        trailerFrame.src = `https://www.youtube.com/embed/${d.trailer_key}?autoplay=0`;
        trailerWrapper.style.display = 'block';
      } else {
        trailerFrame.src = '';
        trailerWrapper.style.display = 'none';
      }

      detailModal.classList.add('active');
    } catch (err) {
      console.error("Modal error:", err);
    }
  };

  closeModalBtn.addEventListener('click', () => {
    detailModal.classList.remove('active');
    trailerFrame.src = '';
  });

  detailModal.addEventListener('click', (e) => {
    if (e.target === detailModal) {
      detailModal.classList.remove('active');
      trailerFrame.src = '';
    }
  });

  window.toggleWatchlist = function(movieId) {
    const recMovie = currentRecommendations.find(m => m.movieId === movieId) || catalogMovies.find(m => m.movieId === movieId);
    const existingIdx = watchlist.findIndex(w => w.movieId === movieId);

    if (existingIdx >= 0) {
      watchlist.splice(existingIdx, 1);
    } else if (recMovie) {
      watchlist.push(recMovie);
    }

    localStorage.setItem('cinematic_watchlist', JSON.stringify(watchlist));
    updateWatchlistBadge();
    if (activeTab === 'recommender') renderRecommendations(currentRecommendations);
    if (activeTab === 'watchlist') renderWatchlistPage();
  };

  function updateWatchlistBadge() {
    watchlistCount.innerText = watchlist.length;
  }

  function escapeHtml(str) {
    if (!str) return '';
    return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#039;");
  }

  function formatReasonMarkdown(text) {
    if (!text) return '';
    return text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
  }

});
