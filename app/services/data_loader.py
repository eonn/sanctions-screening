"""
Data loader service for populating sanctions lists.

Author: Eon (Himanshu Shekhar)
Email: eonhimanshu@gmail.com
GitHub: https://github.com/eonn/sanctions-screening
Created: 2024
"""
import logging
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from app.models.database import SanctionsList
from app.models.schemas import EntityType

logger = logging.getLogger(__name__)


def load_sample_sanctions_data(db: Session):
    """
    Load sample sanctions data for testing and demonstration.
    
    Args:
        db: Database session
    """
    sample_data = [
        {
            "list_name": "OFAC SDN List",
            "source": "OFAC",
            "country": "United States",
            "entity_name": "Osama bin Laden",
            "aliases": ["Usama bin Laden", "Osama bin Ladin"],
            "date_of_birth": "1957-03-10",
            "nationality": "Saudi Arabian",
            "passport_number": None,
            "entity_type": EntityType.INDIVIDUAL,
            "designation_date": "1999-01-20",
            "reason": "Terrorism - Leader of al-Qaeda",
            "raw_data": {"ofac_id": "SDGT-001"}
        },
        {
            "list_name": "OFAC SDN List",
            "source": "OFAC",
            "country": "United States",
            "entity_name": "Ayman al-Zawahiri",
            "aliases": ["Ayman al-Zawahri", "Dr. Ayman al-Zawahiri"],
            "date_of_birth": "1951-06-19",
            "nationality": "Egyptian",
            "passport_number": None,
            "entity_type": EntityType.INDIVIDUAL,
            "designation_date": "2001-09-23",
            "reason": "Terrorism - al-Qaeda leadership",
            "raw_data": {"ofac_id": "SDGT-002"}
        },
        {
            "list_name": "UN Security Council",
            "source": "UN",
            "country": "International",
            "entity_name": "Kim Jong-un",
            "aliases": ["Kim Jong Un", "Kim Jong Eun"],
            "date_of_birth": "1984-01-08",
            "nationality": "North Korean",
            "passport_number": None,
            "entity_type": EntityType.INDIVIDUAL,
            "designation_date": "2017-12-22",
            "reason": "Nuclear proliferation - DPRK leadership",
            "raw_data": {"un_id": "UN-001"}
        },
        {
            "list_name": "EU Sanctions",
            "source": "EU",
            "country": "European Union",
            "entity_name": "Vladimir Putin",
            "aliases": ["Vladimir Vladimirovich Putin"],
            "date_of_birth": "1952-10-07",
            "nationality": "Russian",
            "passport_number": None,
            "entity_type": EntityType.INDIVIDUAL,
            "designation_date": "2022-02-25",
            "reason": "Aggression against Ukraine",
            "raw_data": {"eu_id": "EU-001"}
        },
        {
            "list_name": "OFAC SDN List",
            "source": "OFAC",
            "country": "United States",
            "entity_name": "Hezbollah",
            "aliases": ["Hizballah", "Party of God"],
            "date_of_birth": None,
            "nationality": None,
            "passport_number": None,
            "entity_type": EntityType.ORGANIZATION,
            "designation_date": "1997-10-31",
            "reason": "Terrorism - Foreign terrorist organization",
            "raw_data": {"ofac_id": "SDGT-003"}
        },
        {
            "list_name": "OFAC SDN List",
            "source": "OFAC",
            "country": "United States",
            "entity_name": "Hamas",
            "aliases": ["Islamic Resistance Movement"],
            "date_of_birth": None,
            "nationality": None,
            "passport_number": None,
            "entity_type": EntityType.ORGANIZATION,
            "designation_date": "1997-10-31",
            "reason": "Terrorism - Foreign terrorist organization",
            "raw_data": {"ofac_id": "SDGT-004"}
        },
        {
            "list_name": "UN Security Council",
            "source": "UN",
            "country": "International",
            "entity_name": "Taliban",
            "aliases": ["Islamic Emirate of Afghanistan"],
            "date_of_birth": None,
            "nationality": None,
            "passport_number": None,
            "entity_type": EntityType.ORGANIZATION,
            "designation_date": "1999-10-15",
            "reason": "Terrorism - Taliban regime",
            "raw_data": {"un_id": "UN-002"}
        },
        {
            "list_name": "OFAC SDN List",
            "source": "OFAC",
            "country": "United States",
            "entity_name": "John Smith",
            "aliases": ["Johnny Smith", "J. Smith"],
            "date_of_birth": "1980-05-15",
            "nationality": "American",
            "passport_number": "A12345678",
            "entity_type": EntityType.INDIVIDUAL,
            "designation_date": "2023-01-15",
            "reason": "Money laundering - Financial crimes",
            "raw_data": {"ofac_id": "SDNT-001"}
        },
        {
            "list_name": "EU Sanctions",
            "source": "EU",
            "country": "European Union",
            "entity_name": "Maria Garcia",
            "aliases": ["Maria G. Rodriguez"],
            "date_of_birth": "1975-12-03",
            "nationality": "Spanish",
            "passport_number": "ESP78901234",
            "entity_type": EntityType.INDIVIDUAL,
            "designation_date": "2022-06-10",
            "reason": "Corruption - Public office abuse",
            "raw_data": {"eu_id": "EU-002"}
        },
        {
            "list_name": "UK Sanctions",
            "source": "UK",
            "country": "United Kingdom",
            "entity_name": "Robert Johnson",
            "aliases": ["Bob Johnson", "R. Johnson"],
            "date_of_birth": "1965-08-22",
            "nationality": "British",
            "passport_number": "GBP45678901",
            "entity_type": EntityType.INDIVIDUAL,
            "designation_date": "2023-03-20",
            "reason": "Human rights violations",
            "raw_data": {"uk_id": "UK-001"}
        }
    ]
    
    try:
        for data in sample_data:
            sanctions_entry = SanctionsList(**data)
            db.add(sanctions_entry)
        
        db.commit()
        logger.info(f"Loaded {len(sample_data)} sample sanctions entries")
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error loading sample data: {e}")
        raise


def load_sanctions_from_file(db: Session, file_path: str, source: str):
    """
    Load sanctions data from a CSV or JSON file.
    
    Args:
        db: Database session
        file_path: Path to the data file
        source: Source identifier (e.g., "OFAC", "UN", "EU")
    """
    import os
    import csv
    import json
    
    if not os.path.exists(file_path):
        logger.error(f"File not found: {file_path}")
        return
    
    try:
        if file_path.endswith('.csv'):
            _load_csv_sanctions(db, file_path, source)
        elif file_path.endswith('.json'):
            _load_json_sanctions(db, file_path, source)
        else:
            logger.error(f"Unsupported file format: {file_path}")
            
    except Exception as e:
        logger.error(f"Error loading sanctions from file {file_path}: {e}")
        raise


def _load_csv_sanctions(db: Session, file_path: str, source: str):
    """Load sanctions data from CSV file."""
    with open(file_path, 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        
        for row in reader:
            # Map CSV columns to database fields
            sanctions_entry = SanctionsList(
                list_name=row.get('list_name', f'{source} List'),
                source=source,
                country=row.get('country'),
                entity_name=row.get('entity_name', ''),
                aliases=row.get('aliases', '').split(';') if row.get('aliases') else [],
                date_of_birth=row.get('date_of_birth'),
                nationality=row.get('nationality'),
                passport_number=row.get('passport_number'),
                entity_type=row.get('entity_type', EntityType.INDIVIDUAL),
                designation_date=row.get('designation_date'),
                reason=row.get('reason'),
                raw_data=row
            )
            
            db.add(sanctions_entry)
        
        db.commit()
        logger.info(f"Loaded sanctions data from CSV: {file_path}")


def _load_json_sanctions(db: Session, file_path: str, source: str):
    """Load sanctions data from JSON file."""
    with open(file_path, 'r', encoding='utf-8') as file:
        data = json.load(file)
        
        if isinstance(data, list):
            entries = data
        elif isinstance(data, dict) and 'entries' in data:
            entries = data['entries']
        else:
            logger.error(f"Invalid JSON format in {file_path}")
            return
        
        for entry_data in entries:
            sanctions_entry = SanctionsList(
                list_name=entry_data.get('list_name', f'{source} List'),
                source=source,
                country=entry_data.get('country'),
                entity_name=entry_data.get('entity_name', ''),
                aliases=entry_data.get('aliases', []),
                date_of_birth=entry_data.get('date_of_birth'),
                nationality=entry_data.get('nationality'),
                passport_number=entry_data.get('passport_number'),
                entity_type=entry_data.get('entity_type', EntityType.INDIVIDUAL),
                designation_date=entry_data.get('designation_date'),
                reason=entry_data.get('reason'),
                raw_data=entry_data
            )
            
            db.add(sanctions_entry)
        
        db.commit()
        logger.info(f"Loaded sanctions data from JSON: {file_path}")


def clear_sanctions_data(db: Session, source: str = None):
    """
    Clear sanctions data from database.
    
    Args:
        db: Database session
        source: Optional source filter
    """
    try:
        if source:
            db.query(SanctionsList).filter(SanctionsList.source == source).delete()
            logger.info(f"Cleared sanctions data for source: {source}")
        else:
            db.query(SanctionsList).delete()
            logger.info("Cleared all sanctions data")
        
        db.commit()
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error clearing sanctions data: {e}")
        raise 