// Main JavaScript for Cyber Cafe Management System

// Global variables
let refreshInterval;
const API_BASE_URL = window.location.origin;

// Document ready
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

// Initialize application
function initializeApp() {
    // Initialize tooltips
    initializeTooltips();
    
    // Initialize form validation
    initializeFormValidation();
    
    // Initialize auto-refresh for dashboard
    if (window.location.pathname === '/') {
        startAutoRefresh();
    }
    
    // Initialize keyboard shortcuts
    initializeKeyboardShortcuts();
    
    // Initialize theme detection
    initializeTheme();
    
    console.log('Cyber Cafe Management System initialized');
}

// Tooltip initialization
function initializeTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

// Form validation
function initializeFormValidation() {
    // Generic form validation
    const forms = document.querySelectorAll('.needs-validation');
    
    Array.prototype.slice.call(forms).forEach(function(form) {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
                showNotification('Please fill in all required fields correctly.', 'warning');
            }
            form.classList.add('was-validated');
        }, false);
    });
    
    // Real-time validation for specific inputs
    const numberInputs = document.querySelectorAll('input[type="number"]');
    numberInputs.forEach(input => {
        input.addEventListener('input', function() {
            validateNumberInput(this);
        });
    });
}

// Validate number inputs
function validateNumberInput(input) {
    const value = parseFloat(input.value);
    const min = parseFloat(input.getAttribute('min')) || 0;
    const max = parseFloat(input.getAttribute('max')) || Infinity;
    
    if (isNaN(value) || value < min || value > max) {
        input.classList.add('is-invalid');
        return false;
    } else {
        input.classList.remove('is-invalid');
        input.classList.add('is-valid');
        return true;
    }
}

// Auto-refresh dashboard data
function startAutoRefresh() {
    refreshInterval = setInterval(refreshDashboardData, 30000); // Refresh every 30 seconds
}

function stopAutoRefresh() {
    if (refreshInterval) {
        clearInterval(refreshInterval);
    }
}

// Refresh dashboard data
async function refreshDashboardData() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/summary`);
        if (response.ok) {
            const data = await response.json();
            updateDashboardCards(data);
        }
    } catch (error) {
        console.error('Error refreshing dashboard data:', error);
    }
}

// Update dashboard cards with new data
function updateDashboardCards(data) {
    // Update summary cards if they exist
    const cards = document.querySelectorAll('.h5');
    cards.forEach(card => {
        const text = card.textContent;
        if (text.includes('PC Sessions')) {
            card.textContent = `💷 ${data.pcs_total} EGP`;
        } else if (text.includes('Services')) {
            card.textContent = `💷 ${data.services_total} EGP`;
        } else if (text.includes('Expenses')) {
            card.textContent = `💷 ${data.expenses_total} EGP`;
        } else if (text.includes('Net Total')) {
            card.textContent = `💷 ${data.total_all} EGP`;
        }
    });
}

// Keyboard shortcuts
function initializeKeyboardShortcuts() {
    document.addEventListener('keydown', function(e) {
        // Ctrl/Cmd + shortcuts
        if (e.ctrlKey || e.metaKey) {
            switch(e.key) {
                case '1':
                    e.preventDefault();
                    window.location.href = '/';
                    break;
                case '2':
                    e.preventDefault();
                    window.location.href = '/pc-logging';
                    break;
                case '3':
                    e.preventDefault();
                    window.location.href = '/service-logging';
                    break;
                case '4':
                    e.preventDefault();
                    window.location.href = '/expenses';
                    break;
                case '5':
                    e.preventDefault();
                    window.location.href = '/services';
                    break;
                case '6':
                    e.preventDefault();
                    window.location.href = '/history';
                    break;
            }
        }
        
        // Escape key to close modals/collapses
        if (e.key === 'Escape') {
            const openModals = document.querySelectorAll('.modal.show');
            openModals.forEach(modal => {
                bootstrap.Modal.getInstance(modal)?.hide();
            });
            
            const openCollapses = document.querySelectorAll('.collapse.show');
            openCollapses.forEach(collapse => {
                bootstrap.Collapse.getInstance(collapse)?.hide();
            });
        }
    });
}

// Theme detection and management
function initializeTheme() {
    // Detect system theme preference
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)');
    
    // Apply theme
    function applyTheme(isDark) {
        if (isDark) {
            document.body.classList.add('dark-theme');
        } else {
            document.body.classList.remove('dark-theme');
        }
    }
    
    // Initial theme application
    applyTheme(prefersDark.matches);
    
    // Listen for theme changes
    prefersDark.addEventListener('change', (e) => applyTheme(e.matches));
}

// Notification system
function showNotification(message, type = 'info', duration = 5000) {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
    alertDiv.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
    
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(alertDiv);
    
    // Auto-remove notification
    setTimeout(() => {
        if (alertDiv.parentNode) {
            alertDiv.remove();
        }
    }, duration);
}

// Loading state management
function setLoadingState(element, isLoading = true) {
    if (isLoading) {
        element.classList.add('loading');
        element.style.pointerEvents = 'none';
        
        // Add spinner if it's a button
        if (element.tagName === 'BUTTON') {
            const originalText = element.textContent;
            element.setAttribute('data-original-text', originalText);
            element.innerHTML = `
                <span class="spinner-border spinner-border-sm" role="status"></span>
                Loading...
            `;
        }
    } else {
        element.classList.remove('loading');
        element.style.pointerEvents = 'auto';
        
        // Restore button text
        if (element.tagName === 'BUTTON' && element.hasAttribute('data-original-text')) {
            element.textContent = element.getAttribute('data-original-text');
            element.removeAttribute('data-original-text');
        }
    }
}

// Form submission with loading state
function submitFormWithLoading(form, onSuccess = null, onError = null) {
    const submitButton = form.querySelector('button[type="submit"]');
    
    if (submitButton) {
        setLoadingState(submitButton, true);
    }
    
    // Add form validation
    if (!form.checkValidity()) {
        form.reportValidity();
        if (submitButton) {
            setLoadingState(submitButton, false);
        }
        return false;
    }
    
    const formData = new FormData(form);
    
    fetch(form.action, {
        method: form.method || 'POST',
        body: formData
    })
    .then(response => {
        if (response.ok) {
            if (onSuccess) {
                onSuccess(response);
            } else {
                // Default success behavior
                showNotification('Operation completed successfully!', 'success');
                if (form.reset) form.reset();
            }
        } else {
            throw new Error('Request failed');
        }
    })
    .catch(error => {
        if (onError) {
            onError(error);
        } else {
            showNotification('An error occurred. Please try again.', 'danger');
        }
    })
    .finally(() => {
        if (submitButton) {
            setLoadingState(submitButton, false);
        }
    });
    
    return false; // Prevent default form submission
}

// Utility functions
function formatCurrency(amount, currency = 'EGP') {
    return `💷 ${amount} ${currency}`;
}

function formatTime(minutes) {
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    return `${hours}h ${mins}m`;
}

function calculatePCTime(cost) {
    return formatTime(cost * 6); // 1 EGP = 6 minutes
}

// Data validation utilities
function validateEmail(email) {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
}

function validatePhone(phone) {
    const re = /^[\+]?[1-9][\d]{0,15}$/;
    return re.test(phone);
}

// Local storage utilities
function saveToLocalStorage(key, data) {
    try {
        localStorage.setItem(key, JSON.stringify(data));
        return true;
    } catch (error) {
        console.error('Error saving to localStorage:', error);
        return false;
    }
}

function loadFromLocalStorage(key, defaultValue = null) {
    try {
        const item = localStorage.getItem(key);
        return item ? JSON.parse(item) : defaultValue;
    } catch (error) {
        console.error('Error loading from localStorage:', error);
        return defaultValue;
    }
}

// Print functionality
function printPage() {
    window.print();
}

function printElement(elementId) {
    const element = document.getElementById(elementId);
    if (!element) return;
    
    const printWindow = window.open('', '_blank');
    printWindow.document.write(`
        <html>
            <head>
                <title>Print</title>
                <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
                <style>
                    body { font-family: Arial, sans-serif; }
                    @media print { body { margin: 0; } }
                </style>
            </head>
            <body>
                ${element.outerHTML}
            </body>
        </html>
    `);
    printWindow.document.close();
    printWindow.print();
}

// Export data functionality
function exportToCSV(data, filename = 'export.csv') {
    const csvContent = convertToCSV(data);
    downloadFile(csvContent, filename, 'text/csv');
}

function convertToCSV(data) {
    if (!data.length) return '';
    
    const headers = Object.keys(data[0]);
    const csvRows = [
        headers.join(','),
        ...data.map(row => 
            headers.map(header => {
                const value = row[header];
                return typeof value === 'string' ? `"${value}"` : value;
            }).join(',')
        )
    ];
    
    return csvRows.join('\n');
}

function downloadFile(content, filename, mimeType) {
    const blob = new Blob([content], { type: mimeType });
    const url = URL.createObjectURL(blob);
    
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    link.click();
    
    URL.revokeObjectURL(url);
}

// Cleanup on page unload
window.addEventListener('beforeunload', function() {
    stopAutoRefresh();
});

// Global error handling
window.addEventListener('error', function(e) {
    console.error('Global error:', e.error);
    showNotification('An unexpected error occurred. Please refresh the page.', 'danger');
});

// Service worker registration (for offline capability)
if ('serviceWorker' in navigator) {
    window.addEventListener('load', function() {
        // Uncomment to enable service worker
        // navigator.serviceWorker.register('/sw.js');
    });
}
