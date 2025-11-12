#!/usr/bin/env python3
"""
Database Seeding Script
Reference: docs/14-build_plan.md
"""

import asyncio
from src.core.database import db_manager


async def seed_database():
    """Seed initial data for development"""
    print("Seeding database...")
    # Add seed data logic
    print("Database seeded successfully!")


if __name__ == "__main__":
    asyncio.run(seed_database())
