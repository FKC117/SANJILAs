// Finance App JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Initialize date range picker
    initializeDateRangePicker();
    
    // Initialize export functionality
    initializeExportFunctions();
    
    // Initialize charts if they exist
    initializeCharts();
});

// Date Range Picker
function initializeDateRangePicker() {
    const dateRangeForm = document.getElementById('dateRangeForm');
    if (!dateRangeForm) return;

    const startDateInput = document.getElementById('startDate');
    const endDateInput = document.getElementById('endDate');
    const applyButton = document.getElementById('applyDateRange');

    // Set default dates if not set
    if (!startDateInput.value) {
        const thirtyDaysAgo = new Date();
        thirtyDaysAgo.setDate(thirtyDaysAgo.getDate() - 30);
        startDateInput.value = formatDate(thirtyDaysAgo);
    }

    if (!endDateInput.value) {
        endDateInput.value = formatDate(new Date());
    }

    // Handle date range application
    applyButton.addEventListener('click', function(e) {
        e.preventDefault();
        if (validateDateRange(startDateInput.value, endDateInput.value)) {
            dateRangeForm.submit();
        }
    });
}

// Export Functions
function initializeExportFunctions() {
    const exportCSVButtons = document.querySelectorAll('[data-export="csv"]');
    const exportPDFButtons = document.querySelectorAll('[data-export="pdf"]');

    exportCSVButtons.forEach(button => {
        button.addEventListener('click', function() {
            const tableId = this.dataset.table;
            exportToCSV(tableId);
        });
    });

    exportPDFButtons.forEach(button => {
        button.addEventListener('click', function() {
            const tableId = this.dataset.table;
            exportToPDF(tableId);
        });
    });
}

// Chart Initialization
function initializeCharts() {
    // Initialize any charts that exist on the page
    const chartElements = document.querySelectorAll('canvas[data-chart]');
    chartElements.forEach(canvas => {
        const chartType = canvas.dataset.chart;
        const chartData = JSON.parse(canvas.dataset.chartData || '{}');
        
        switch(chartType) {
            case 'sales':
                initializeSalesChart(canvas, chartData);
                break;
            case 'profit':
                initializeProfitChart(canvas, chartData);
                break;
            case 'products':
                initializeProductChart(canvas, chartData);
                break;
        }
    });
}

// Utility Functions
function formatDate(date) {
    return date.toISOString().split('T')[0];
}

function validateDateRange(startDate, endDate) {
    const start = new Date(startDate);
    const end = new Date(endDate);
    
    if (start > end) {
        showError('Start date cannot be after end date');
        return false;
    }
    
    const diffTime = Math.abs(end - start);
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    
    if (diffDays > 365) {
        showError('Date range cannot exceed 1 year');
        return false;
    }
    
    return true;
}

function showError(message) {
    const errorDiv = document.createElement('div');
    errorDiv.className = 'error-message';
    errorDiv.textContent = message;
    
    const content = document.querySelector('.finance-content');
    content.insertBefore(errorDiv, content.firstChild);
    
    setTimeout(() => {
        errorDiv.remove();
    }, 5000);
}

function showSuccess(message) {
    const successDiv = document.createElement('div');
    successDiv.className = 'success-message';
    successDiv.textContent = message;
    
    const content = document.querySelector('.finance-content');
    content.insertBefore(successDiv, content.firstChild);
    
    setTimeout(() => {
        successDiv.remove();
    }, 5000);
}

// Export Functions
function exportToCSV(tableId) {
    const table = document.getElementById(tableId);
    if (!table) return;

    let csv = [];
    const rows = table.querySelectorAll('tr');
    
    for (const row of rows) {
        const cells = row.querySelectorAll('td, th');
        const rowData = Array.from(cells).map(cell => {
            // Handle special characters and commas
            let text = cell.textContent.trim();
            if (text.includes(',') || text.includes('"') || text.includes('\n')) {
                text = `"${text.replace(/"/g, '""')}"`;
            }
            return text;
        });
        csv.push(rowData.join(','));
    }
    
    const csvContent = csv.join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    
    link.setAttribute('href', url);
    link.setAttribute('download', `${tableId}_export.csv`);
    link.style.visibility = 'hidden';
    
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

function exportToPDF(tableId) {
    // This is a placeholder for PDF export functionality
    // You would typically use a library like jsPDF here
    alert('PDF export functionality will be implemented');
}

// Chart Initialization Functions
function initializeSalesChart(canvas, data) {
    new Chart(canvas, {
        type: 'line',
        data: {
            labels: data.labels || [],
            datasets: [{
                label: 'Sales',
                data: data.values || [],
                borderColor: '#2196F3',
                backgroundColor: 'rgba(33, 150, 243, 0.1)',
                fill: true
            }]
        },
        options: {
            responsive: true,
            plugins: {
                title: {
                    display: true,
                    text: 'Sales Trend'
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        callback: function(value) {
                            return '$' + value.toFixed(2);
                        }
                    }
                }
            }
        }
    });
}

function initializeProfitChart(canvas, data) {
    new Chart(canvas, {
        type: 'doughnut',
        data: {
            labels: data.labels || [],
            datasets: [{
                data: data.values || [],
                backgroundColor: [
                    'rgba(76, 175, 80, 0.5)',
                    'rgba(244, 67, 54, 0.5)',
                    'rgba(33, 150, 243, 0.5)'
                ],
                borderColor: [
                    '#4CAF50',
                    '#F44336',
                    '#2196F3'
                ]
            }]
        },
        options: {
            responsive: true,
            plugins: {
                title: {
                    display: true,
                    text: 'Profit Distribution'
                }
            }
        }
    });
}

function initializeProductChart(canvas, data) {
    new Chart(canvas, {
        type: 'bar',
        data: {
            labels: data.labels || [],
            datasets: [{
                label: 'Sales',
                data: data.sales || [],
                backgroundColor: 'rgba(33, 150, 243, 0.5)',
                borderColor: '#2196F3'
            }, {
                label: 'Profit',
                data: data.profit || [],
                backgroundColor: 'rgba(76, 175, 80, 0.5)',
                borderColor: '#4CAF50'
            }]
        },
        options: {
            responsive: true,
            plugins: {
                title: {
                    display: true,
                    text: 'Product Performance'
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        callback: function(value) {
                            return '$' + value.toFixed(2);
                        }
                    }
                }
            }
        }
    });
} 