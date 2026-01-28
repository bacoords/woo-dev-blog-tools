---
name: woo-demo-screenshots
description: Take screenshots of the WooCommerce demo store using Playwright MCP. Use when asked to capture screenshots, document UI changes, or create visual references of the demo store at woo-demo-store-mcp.mystagingwebsite.com.
---

# WooCommerce Demo Store Screenshots

Capture screenshots of the WooCommerce demo store using the Playwright MCP browser automation tool.

## Demo Store URL

**Base URL**: `https://woo-demo-store-mcp.mystagingwebsite.com/`

## Demo Store Admin Credentials

Go to my WooCommerce login page and log in using the credentials in the ./.env environment variables WC_USER and WC_PASS.

## Prerequisites

This skill requires the Playwright MCP server to be configured and running. The MCP provides browser automation capabilities for navigation and screenshot capture.

## Common Screenshot Workflows

### Capture Shop Page
Navigate to `/shop/` and take screenshot

### Capture Single Product
Navigate to `/shop/`, click a product, and take screenshot

### Capture Cart
Add item to cart, navigate to `/cart/`, and take screenshot

### Capture Checkout
Navigate to `/checkout/` and take screenshot

### Capture My Account
Navigate to `/my-account/` and take screenshot (login page if not authenticated)

### Capture Single Product Template Editor
Navigate to `/wp-admin/site-editor.php?p=%2Fwp_template%2Fpurple%2F%2Fsingle-product&canvas=edit`

### Capture Product Catalog Template Editor
Navigate to `/wp-admin/site-editor.php?p=%2Fwp_template%2Fpurple%2F%2Farchive-product&canvas=edit`

## Key Store Pages

| Page | URL Path |
|------|----------|
| Home | `/` |
| Shop | `/shop/` |
| Cart | `/cart/` |
| Checkout | `/checkout/` |
| My Account | `/my-account/` |
| Product Category | `/product-category/{category}/` |
| Single Product | `/product/{product-slug}/` |
| Dashboard | `/wp-admin/` |

## Screenshot Best Practices

1. **Wait for page load**: Ensure images and dynamic content have loaded before capturing
2. **Full page vs viewport**: Specify if you need the full scrollable page or just the visible viewport
3. **Responsive views**: Consider capturing at different viewport widths for mobile/tablet/desktop
4. **Session management**: Log in if capturing authenticated pages (e.g., My Account) and keep the session active

## Output

Screenshots are saved to the specified path. Recommended naming convention:
- `woo-demo-{page}-{timestamp}.png`
- Example: `woo-demo-shop-2025-01-27.png`

## Notes

- The demo store may have sample/test data that changes periodically
- If the demo store is unavailable, the demo store site may need to be refreshed