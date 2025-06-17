/**
 * Dashboard JavaScript for Boarding House Management System
 * Handles interactive features, charts, and dynamic content
 */

// Global variables
let revenueChart = null;
let dashboardData = {};

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeDashboard();
});

/**
 * Initialize all dashboard components
 */
function initializeDashboard() {
    // Initialize charts if containers exist
    initializeRevenueChart();
    
    // Initialize real-time updates
    initializeAutoRefresh();
    
    // Initialize interactive elements
    initializeInteractiveElements();
    
    // Initialize tooltips and popovers
    initializeBootstrapComponents();
    
    console.log('Dashboard initialized successfully');
}

/**
 * Initialize the revenue trend chart
 */
function initializeRevenueChart() {
    const chartContainer = document.getElementById('revenueChart');
    if (!chartContainer) {
        console.log('Revenue chart container not found');
        return;
    }

    const ctx = chartContainer.getContext('2d');
    
    // Show loading state
    showChartLoading(chartContainer);
    
    // Fetch revenue data from API
    fetch('/api/dashboard/revenue-data')
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            hideChartLoading(chartContainer);
            createRevenueChart(ctx, data);
        })
        .catch(error => {
            console.error('Error loading revenue data:', error);
            hideChartLoading(chartContainer);
            showChartError(chartContainer, 'Failed to load revenue data');
        });
}

/**
 * Create the revenue chart with Chart.js
 */
function createRevenueChart(ctx, data) {
    // Destroy existing chart if it exists
    if (revenueChart) {
        revenueChart.destroy();
    }
    
    revenueChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: data.map(item => item.month),
            datasets: [{
                label: 'Monthly Revenue',
                data: data.map(item => item.revenue),
                borderColor: 'var(--bs-primary)',
                backgroundColor: 'rgba(13, 110, 253, 0.1)',
                borderWidth: 3,
                tension: 0.4,
                fill: true,
                pointBackgroundColor: 'var(--bs-primary)',
                pointBorderColor: '#fff',
                pointBorderWidth: 2,
                pointRadius: 6,
                pointHoverRadius: 8
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                    titleColor: '#fff',
                    bodyColor: '#fff',
                    borderColor: 'var(--bs-primary)',
                    borderWidth: 1,
                    cornerRadius: 8,
                    displayColors: false,
                    callbacks: {
                        label: function(context) {
                            return 'Revenue: $' + context.parsed.y.toLocaleString('en-US', {
                                minimumFractionDigits: 2,
                                maximumFractionDigits: 2
                            });
                        }
                    }
                }
            },
            scales: {
                x: {
                    grid: {
                        display: false
                    },
                    ticks: {
                        font: {
                            size: 12,
                            weight: '500'
                        }
                    }
                },
                y: {
                    beginAtZero: true,
                    grid: {
                        color: 'rgba(0, 0, 0, 0.1)'
                    },
                    ticks: {
                        font: {
                            size: 12
                        },
                        callback: function(value) {
                            return '$' + value.toLocaleString('en-US');
                        }
                    }
                }
            },
            interaction: {
                intersect: false,
                mode: 'index'
            },
            animation: {
                duration: 1500,
                easing: 'easeInOutQuart'
            }
        }
    });
    
    // Store chart data for potential future use
    dashboardData.revenueData = data;
    
    console.log('Revenue chart created successfully');
}

/**
 * Initialize auto-refresh functionality
 */
function initializeAutoRefresh() {
    // Auto-refresh every 5 minutes (300000 ms)
    const refreshInterval = 300000;
    
    setInterval(() => {
        refreshDashboardData();
    }, refreshInterval);
    
    console.log(`Auto-refresh initialized (${refreshInterval / 1000}s interval)`);
}

/**
 * Refresh dashboard data
 */
function refreshDashboardData() {
    // Only refresh if page is visible (performance optimization)
    if (document.hidden) {
        return;
    }
    
    console.log('Refreshing dashboard data...');
    
    // Refresh revenue chart
    initializeRevenueChart();
    
    // You could add more data refresh logic here
    // For example, updating payment alerts, statistics, etc.
}

/**
 * Initialize interactive elements
 */
function initializeInteractiveElements() {
    // Add click handlers for metric cards
    initializeMetricCards();
    
    // Add hover effects for quick action buttons
    initializeQuickActions();
    
    // Initialize any modals or dropdowns
    initializeModals();
}

/**
 * Initialize metric cards with click interactions
 */
function initializeMetricCards() {
    const metricCards = document.querySelectorAll('.card.bg-primary, .card.bg-success, .card.bg-info, .card.bg-warning');
    
    metricCards.forEach(card => {
        card.style.cursor = 'pointer';
        card.style.transition = 'transform 0.2s ease, box-shadow 0.2s ease';
        
        card.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-2px)';
            this.style.boxShadow = '0 0.5rem 1rem rgba(0, 0, 0, 0.15)';
        });
        
        card.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0)';
            this.style.boxShadow = '';
        });
        
        // Add click functionality based on card content
        const cardText = card.textContent.toLowerCase();
        if (cardText.includes('room')) {
            card.addEventListener('click', () => {
                window.location.href = '/rooms';
            });
        } else if (cardText.includes('tenant')) {
            card.addEventListener('click', () => {
                window.location.href = '/tenants';
            });
        } else if (cardText.includes('month')) {
            card.addEventListener('click', () => {
                window.location.href = '/reports/financial';
            });
        }
    });
    
    console.log(`Initialized ${metricCards.length} metric cards`);
}

/**
 * Initialize quick action buttons
 */
function initializeQuickActions() {
    const quickActionButtons = document.querySelectorAll('.btn-lg');
    
    quickActionButtons.forEach(button => {
        button.addEventListener('mouseenter', function() {
            this.style.transform = 'scale(1.05)';
        });
        
        button.addEventListener('mouseleave', function() {
            this.style.transform = 'scale(1)';
        });
    });
    
    console.log(`Initialized ${quickActionButtons.length} quick action buttons`);
}

/**
 * Initialize modals and other Bootstrap components
 */
function initializeModals() {
    // Initialize any modals that might be present
    const modals = document.querySelectorAll('.modal');
    modals.forEach(modal => {
        new bootstrap.Modal(modal);
    });
    
    console.log(`Initialized ${modals.length} modals`);
}

/**
 * Initialize Bootstrap components (tooltips, popovers, etc.)
 */
function initializeBootstrapComponents() {
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Initialize popovers
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function(popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
    
    console.log('Bootstrap components initialized');
}

/**
 * Show loading state for chart
 */
function showChartLoading(container) {
    const loadingDiv = document.createElement('div');
    loadingDiv.className = 'chart-loading text-center p-4';
    loadingDiv.innerHTML = `
        <div class="spinner-border text-primary" role="status">
            <span class="visually-hidden">Loading...</span>
        </div>
        <p class="mt-2 text-muted">Loading chart data...</p>
    `;
    loadingDiv.id = 'chart-loading';
    
    container.parentNode.appendChild(loadingDiv);
    container.style.display = 'none';
}

/**
 * Hide loading state for chart
 */
function hideChartLoading(container) {
    const loadingDiv = document.getElementById('chart-loading');
    if (loadingDiv) {
        loadingDiv.remove();
    }
    container.style.display = 'block';
}

/**
 * Show error state for chart
 */
function showChartError(container, message) {
    const errorDiv = document.createElement('div');
    errorDiv.className = 'chart-error text-center p-4';
    errorDiv.innerHTML = `
        <div class="text-danger mb-2">
            <i class="fas fa-exclamation-triangle fa-2x"></i>
        </div>
        <p class="text-muted">${message}</p>
        <button class="btn btn-outline-primary btn-sm" onclick="initializeRevenueChart()">
            <i class="fas fa-redo"></i> Retry
        </button>
    `;
    
    container.parentNode.appendChild(errorDiv);
    container.style.display = 'none';
}

/**
 * Utility function to format currency
 */
function formatCurrency(amount) {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD',
        minimumFractionDigits: 2
    }).format(amount);
}

/**
 * Utility function to format percentage
 */
function formatPercentage(value) {
    return new Intl.NumberFormat('en-US', {
        style: 'percent',
        minimumFractionDigits: 1,
        maximumFractionDigits: 1
    }).format(value / 100);
}

/**
 * Handle visibility change (for performance optimization)
 */
document.addEventListener('visibilitychange', function() {
    if (!document.hidden) {
        // Page became visible, refresh data if it's been a while
        const lastRefresh = localStorage.getItem('dashboardLastRefresh');
        const now = Date.now();
        const fiveMinutes = 5 * 60 * 1000;
        
        if (!lastRefresh || (now - parseInt(lastRefresh)) > fiveMinutes) {
            refreshDashboardData();
            localStorage.setItem('dashboardLastRefresh', now.toString());
        }
    }
});

/**
 * Global error handler for dashboard
 */
window.addEventListener('error', function(event) {
    console.error('Dashboard error:', event.error);
    
    // Show user-friendly error message for critical failures
    if (event.error && event.error.message) {
        showNotification('An error occurred while loading dashboard data. Please refresh the page.', 'error');
    }
});

/**
 * Show notification to user
 */
function showNotification(message, type = 'info') {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
    alertDiv.style.cssText = 'top: 20px; right: 20px; z-index: 9999; max-width: 300px;';
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(alertDiv);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (alertDiv.parentNode) {
            alertDiv.remove();
        }
    }, 5000);
}

// Export functions for testing or external use
window.DashboardManager = {
    refreshData: refreshDashboardData,
    formatCurrency: formatCurrency,
    formatPercentage: formatPercentage,
    showNotification: showNotification
};

console.log('Dashboard JavaScript loaded successfully');
