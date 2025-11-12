# 02. Project Context
**Version:** 1.0  
**Author:** Senior Lead Engineer  
**Last Updated:** 2025-11-12

## Purpose
This document provides the business and technical context for QuickCart, a Telegram auto-order bot for digital products. It ensures all stakeholders share a common understanding of the goals, constraints, and environment.

## Project Overview
- **Product:** QuickCart - Telegram bot for automated digital product sales (tutorials, premium accounts, courses)
- **Model:** Inspired by Lynk.id - users receive product content after successful payment
- **Target Users:** Digital product sellers and their customers via Telegram
- **Business Objectives:** 
  - Automate digital product sales through Telegram
  - Provide seamless payment experience with QRIS integration
  - Support multi-tier user system (customer, reseller, admin)
  - Ensure robust audit logging and anti-fraud protection

## Stakeholders
- **Product Owner:** Digital product sellers using Telegram for business
- **Technical Lead:** Senior Lead Engineer
- **Key Users:** 
  - End customers purchasing digital products
  - Resellers with special pricing
  - Bot administrators managing products and users
- **External Partners:** 
  - Pakasir payment gateway
  - Telegram Bot API
  - Digital Ocean (hosting infrastructure)

## Scope & Boundaries

### In-scope features
- Telegram bot with Indonesian UI and English documentation
- QRIS-only payment processing via Pakasir
- Multi-tier user system (customer/reseller/admin)
- Product catalog with categories and stock management
- Account balance system for users
- Flexible navigation (users can switch flows anytime)
- Comprehensive admin commands for management
- Real-time order processing and notifications
- 10-minute payment expiry with automatic handling
- Audit logging for all critical operations
- Anti-fraud detection and prevention

### Out-of-scope items
- Payment methods other than QRIS and account balance
- Physical product fulfillment
- Multi-language support (fixed: Indonesian UI, English docs)
- Web-based admin interface (Telegram-only management)
- Integration with external CRM systems

## Dependencies

### Third-party services
- **Pakasir Payment Gateway:** QRIS payment processing with webhook callbacks
- **Telegram Bot API:** All user interactions and notifications
- **Digital Ocean Droplets:** Application hosting infrastructure

### Internal systems
- **PostgreSQL:** Primary database for operational data
- **Redis:** Session management, caching, and job queuing
- **FastAPI:** Backend application framework
- **Docker:** Containerization and deployment
- **Separate Audit Database:** Permanent logging for compliance

> Note for AI builders: This bot requires zero ambiguity in implementation. All flows must handle unexpected user input gracefully and support flexible navigation patterns.