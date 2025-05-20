# Financial Reports Documentation

## Overview
The Financial Reports module provides comprehensive financial reporting capabilities, including Profit & Loss statements, Balance Sheets, and various financial metrics. The reports can be generated for custom date ranges and include comparison functionality.

## Features

### 1. Date Range Selection
- Select custom start and end dates for financial reports
- Compare data between two different periods
- Default view shows last 30 days of data

### 2. Profit & Loss Statement
- Revenue breakdown:
  - Product Sales
  - Shipping Revenue
  - Other Revenue
- Expense breakdown:
  - Cost of Goods
  - Shipping Expenses
  - Marketing Expenses
  - Payroll Expenses
  - Rent Expenses
  - Utilities
  - Website Expenses
  - Payment Processing
- Profit metrics:
  - Gross Profit
  - Net Profit

### 3. Balance Sheet
- Assets:
  - Cash
  - Accounts Receivable
  - Inventory
  - Prepaid Expenses
- Liabilities:
  - Accounts Payable
  - Sales Tax Payable
  - Wages Payable
- Equity:
  - Common Stock
  - Retained Earnings

### 4. Visual Analytics
- Revenue vs Expenses chart
- Expense breakdown pie chart
- Comparison indicators (↑/↓) for period-over-period changes

### 5. Export Capabilities
- Export to Excel (.xlsx)
  - Includes both Profit & Loss and Balance Sheet
  - Properly formatted numbers and dates
  - Filename includes date range
- Export to PDF (coming soon)

## Usage

### Accessing Reports
1. Navigate to the Accounting Dashboard
2. Click on "Financial Reports" card
3. Or directly access via URL: `/accounts/reports/`

### Generating Reports
1. Select date range:
   - Use date pickers to select start and end dates
   - Click "Apply Filter" to update the report
2. For comparison:
   - Click "Compare" button
   - Enter comparison date range
   - View period-over-period changes

### Exporting Data
1. Click "Export to Excel" button
2. File will be downloaded with format: `financial_reports_YYYY-MM-DD_to_YYYY-MM-DD.xlsx`
3. Excel file contains:
   - Profit & Loss sheet
   - Balance Sheet sheet
   - Formatted numbers and dates

## Technical Details

### Template Tags
The following custom template tags are used:
- `subtract`: Subtracts two values, handling various numeric formats
- `get_item`: Safely retrieves items from dictionaries

### Data Processing
- Numbers are formatted with commas and 2 decimal places
- Currency values are prefixed with "BDT"
- Comparison data shows:
  - Up/down arrows (↑/↓)
  - Absolute difference
  - Color-coded badges (green for positive, red for negative)

### Security
- Reports are only accessible to superusers
- All data is properly escaped and sanitized
- Export functionality runs client-side for better performance

## Troubleshooting

### Common Issues
1. **Export not working**
   - Ensure all required JavaScript libraries are loaded
   - Check browser console for errors
   - Try clearing browser cache

2. **Comparison data not showing**
   - Verify both date ranges are selected
   - Check if data exists for the selected periods
   - Ensure proper permissions

3. **Numbers not formatting correctly**
   - Verify the data type in the database
   - Check template filters are properly loaded
   - Ensure proper decimal places in settings

### Support
For additional support:
1. Check the browser console for error messages
2. Verify all required dependencies are installed
3. Contact system administrator for access issues

## Future Enhancements
1. PDF export functionality
2. Additional chart types
3. Custom report builder
4. Scheduled report generation
5. Email report delivery 