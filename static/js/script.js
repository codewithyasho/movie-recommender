$(document).ready(function() {
    // Initialize Select2 for better dropdown experience
    if ($.fn.select2) {
        $('.movie-select').select2({
            placeholder: 'Search for a movie...',
            allowClear: true,
            width: '100%'
        });
    }

    // Handle form submission
    $('#recommendForm').on('submit', function(e) {
        e.preventDefault();
        
        const movieName = $('#movieSelect').val();
        const enablePosters = $('#enablePosters').is(':checked');
        
        if (!movieName) {
            showAlert('Please select a movie first!', 'warning');
            return;
        }
        
        // Show loading section
        showLoading();
        
        // Hide results section
        $('#resultsSection').addClass('d-none');
        
        // Start progress animation
        animateProgress();
        
        // Make AJAX request
        $.ajax({
            url: '/recommend',
            method: 'POST',
            data: {
                movie: movieName,
                enable_posters: enablePosters ? 'on' : 'off'
            },
            success: function(response) {
                hideLoading();
                if (response.error) {
                    showAlert(response.error, 'danger');
                } else {
                    displayResults(response);
                }
            },
            error: function(xhr, status, error) {
                hideLoading();
                try {
                    const errorResponse = JSON.parse(xhr.responseText);
                    showAlert(errorResponse.error || 'An error occurred while fetching recommendations. Please try again.', 'danger');
                } catch(e) {
                    showAlert('An error occurred while fetching recommendations. Please try again.', 'danger');
                }
                console.error('Error:', error);
            }
        });
    });
    
    function showLoading() {
        $('#loadingSection').removeClass('d-none').addClass('fade-in');
        $('html, body').animate({
            scrollTop: $('#loadingSection').offset().top - 100
        }, 500);
    }
    
    function hideLoading() {
        $('#loadingSection').addClass('d-none');
        $('#progressBar').css('width', '0%');
    }
    
    function animateProgress() {
        let progress = 0;
        const interval = setInterval(function() {
            progress += Math.random() * 15;
            if (progress > 90) {
                progress = 90;
                clearInterval(interval);
            }
            $('#progressBar').css('width', progress + '%');
        }, 300);
        
        // Complete progress when done
        setTimeout(function() {
            clearInterval(interval);
            $('#progressBar').css('width', '100%');
        }, 3000);
    }
    
    function displayResults(response) {
        const { recommendations, selected_movie, enable_posters } = response;
        
        if (!recommendations || recommendations.length === 0) {
            showAlert('No recommendations found for this movie. Please try another one.', 'info');
            return;
        }
        
        // Update selected movie info
        $('#selectedMovie').text(selected_movie);
        
        // Clear previous results
        $('#movieResults').empty();
        
        // Generate results HTML
        let resultsHTML = '';
        
        if (enable_posters) {
            // Grid layout with posters
            recommendations.forEach((movie, index) => {
                resultsHTML += `
                    <div class="col-lg-2 col-md-4 col-sm-6 mb-4">
                        <div class="movie-card slide-up" style="animation-delay: ${index * 0.1}s">
                            <div class="movie-rank">${index + 1}</div>
                            <img src="${movie.poster}" alt="${movie.title}" class="movie-poster" 
                                 onerror="this.src='https://via.placeholder.com/300x450?text=No+Image'">
                            <div class="movie-info">
                                <h5 class="movie-title">${movie.title}</h5>
                                <span class="similarity-score">
                                    <i class="fas fa-star me-1"></i>${(movie.similarity * 100).toFixed(1)}%
                                </span>
                            </div>
                        </div>
                    </div>
                `;
            });
        } else {
            // List layout without posters
            recommendations.forEach((movie, index) => {
                resultsHTML += `
                    <div class="col-12 mb-3">
                        <div class="text-movie-card slide-up" style="animation-delay: ${index * 0.1}s">
                            <div class="text-movie-rank">${index + 1}</div>
                            <div class="row align-items-center">
                                <div class="col-md-8">
                                    <h4 class="movie-title mb-2">${movie.title}</h4>
                                </div>
                                <div class="col-md-4 text-md-end">
                                    <span class="similarity-score">
                                        <i class="fas fa-star me-1"></i>
                                        ${(movie.similarity * 100).toFixed(1)}% Match
                                    </span>
                                </div>
                            </div>
                        </div>
                    </div>
                `;
            });
        }
        
        // Insert results and show section
        $('#movieResults').html(resultsHTML);
        $('#resultsSection').removeClass('d-none').addClass('fade-in');
        
        // Scroll to results
        setTimeout(function() {
            $('html, body').animate({
                scrollTop: $('#resultsSection').offset().top - 100
            }, 500);
        }, 200);
        
        // Add click event to movie cards for potential future features
        $('.movie-card, .text-movie-card').on('click', function() {
            const movieTitle = $(this).find('.movie-title').text();
            // You can add more functionality here, like showing movie details
            console.log('Clicked on movie:', movieTitle);
        });
    }
    
    function showAlert(message, type) {
        const alertHTML = `
            <div class="alert alert-${type} alert-dismissible fade show" role="alert">
                <i class="fas fa-${getAlertIcon(type)} me-2"></i>
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
            </div>
        `;
        
        // Remove existing alerts
        $('.alert').remove();
        
        // Add new alert at the top of main content
        $('.main-content .container').prepend(alertHTML);
        
        // Auto-dismiss after 5 seconds
        setTimeout(function() {
            $('.alert').fadeOut();
        }, 5000);
    }
    
    function getAlertIcon(type) {
        const icons = {
            'success': 'check-circle',
            'danger': 'exclamation-triangle',
            'warning': 'exclamation-circle',
            'info': 'info-circle'
        };
        return icons[type] || 'info-circle';
    }
    
    // Add smooth scrolling for anchor links
    $('a[href^="#"]').on('click', function(event) {
        var target = $(this.getAttribute('href'));
        if (target.length) {
            event.preventDefault();
            $('html, body').stop().animate({
                scrollTop: target.offset().top - 100
            }, 1000);
        }
    });
    
    // Add loading state to button
    $('#recommendForm').on('submit', function() {
        const $btn = $(this).find('button[type="submit"]');
        const originalText = $btn.html();
        
        $btn.html('<i class="fas fa-spinner fa-spin me-2"></i>Loading...').prop('disabled', true);
        
        // Re-enable button after request completes (handled in success/error callbacks)
        setTimeout(function() {
            $btn.html(originalText).prop('disabled', false);
        }, 5000);
    });
    
    // Add hover effects to movie cards
    $(document).on('mouseenter', '.movie-card, .text-movie-card', function() {
        $(this).addClass('shadow-lg');
    }).on('mouseleave', '.movie-card, .text-movie-card', function() {
        $(this).removeClass('shadow-lg');
    });
    
    // Initialize tooltips if Bootstrap is available
    if (typeof bootstrap !== 'undefined') {
        var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }
});

// Add Select2 CSS if not already included
if (!$('link[href*="select2"]').length) {
    $('<link>')
        .appendTo('head')
        .attr({
            type: 'text/css',
            rel: 'stylesheet',
            href: 'https://cdn.jsdelivr.net/npm/select2@4.1.0-rc.0/dist/css/select2.min.css'
        });
}

// Add Select2 JS if not already included
if (typeof $.fn.select2 === 'undefined') {
    $.getScript('https://cdn.jsdelivr.net/npm/select2@4.1.0-rc.0/dist/js/select2.min.js', function() {
        $('.movie-select').select2({
            placeholder: 'Search for a movie...',
            allowClear: true,
            width: '100%'
        });
    });
}
