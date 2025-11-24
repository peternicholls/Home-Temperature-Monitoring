#!/usr/bin/env python3
"""
Evaluation framework for Home Temperature Monitoring System.

This module analyzes real-world production data from the database to evaluate:
1. Collection Completeness - Verify sensor discovery and reading collection rates
2. Data Quality & Correctness - Validate format, temperature ranges, metadata
3. System Reliability - Measure database resilience, retry effectiveness, uptime

Usage:
    python source/evaluation.py [--days N] [--output-path PATH]
"""

import os
import json
import sys
import sqlite3
import argparse
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone, timedelta
import yaml

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from source.utils.structured_logger import StructuredLogger


def load_config() -> Dict[str, Any]:
    """Load configuration from config.yaml."""
    config_path = Path(__file__).parent.parent / "config" / "config.yaml"
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    config['component'] = 'evaluation'
    return config


class CollectionCompletenessEvaluator:
    """
    Evaluates sensor discovery and reading collection completeness.
    
    Metrics:
    - Device discovery rate (unique devices found)
    - Reading collection rate (expected vs actual readings)
    - Location mapping accuracy
    - Time coverage (gaps analysis)
    """
    
    def __init__(self, db_path: str, logger: StructuredLogger):
        self.db_path = db_path
        self.logger = logger
    
    def evaluate(self, time_period_days: int = 1) -> Dict[str, Any]:
        """
        Evaluate collection completeness for the specified time period.
        
        Args:
            time_period_days: Number of days to analyze
            
        Returns:
            Dict with completeness metrics
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get time range
            cursor.execute("""
                SELECT MIN(timestamp), MAX(timestamp), COUNT(*)
                FROM readings
                WHERE timestamp >= datetime('now', '-{} days')
            """.format(time_period_days))
            
            min_time, max_time, total_readings = cursor.fetchone()
            
            if not min_time or not max_time:
                self.logger.warning("No readings found in specified time period", days=time_period_days)
                return {
                    "status": "NO_DATA",
                    "completeness_score": 0.0,
                    "reason": f"No readings found in last {time_period_days} days"
                }
            
            # Parse timestamps
            start_dt = datetime.fromisoformat(min_time.replace('+00:00', '')).replace(tzinfo=timezone.utc)
            end_dt = datetime.fromisoformat(max_time.replace('+00:00', '')).replace(tzinfo=timezone.utc)
            duration_hours = (end_dt - start_dt).total_seconds() / 3600
            
            # Count unique devices
            cursor.execute("""
                SELECT device_type, COUNT(DISTINCT device_id) as device_count
                FROM readings
                WHERE timestamp >= datetime('now', '-{} days')
                GROUP BY device_type
            """.format(time_period_days))
            
            devices_by_type = dict(cursor.fetchall())
            total_devices = sum(devices_by_type.values())
            
            # Count readings per device
            cursor.execute("""
                SELECT device_type, device_id, location, COUNT(*) as reading_count
                FROM readings
                WHERE timestamp >= datetime('now', '-{} days')
                GROUP BY device_type, device_id
                ORDER BY device_type, reading_count DESC
            """.format(time_period_days))
            
            device_readings = cursor.fetchall()
            
            # Expected readings (5-minute intervals)
            expected_per_device = (duration_hours * 60) / 5 if duration_hours > 0 else 0
            expected_total = total_devices * expected_per_device
            
            # Calculate collection rate
            collection_rate = (total_readings / expected_total) if expected_total > 0 else 0
            
            # Check location mapping
            cursor.execute("""
                SELECT COUNT(DISTINCT device_id) as devices_with_location
                FROM readings
                WHERE timestamp >= datetime('now', '-{} days')
                AND location IS NOT NULL AND location != ''
            """.format(time_period_days))
            
            devices_with_location = cursor.fetchone()[0]
            location_accuracy = devices_with_location / total_devices if total_devices > 0 else 0
            
            # Calculate gap analysis
            cursor.execute("""
                WITH ordered_readings AS (
                    SELECT 
                        device_id,
                        timestamp,
                        LAG(timestamp) OVER (PARTITION BY device_id ORDER BY timestamp) as prev_timestamp
                    FROM readings
                    WHERE timestamp >= datetime('now', '-{} days')
                )
                SELECT 
                    COUNT(*) as total_gaps
                FROM ordered_readings
                WHERE prev_timestamp IS NOT NULL
                AND (julianday(timestamp) - julianday(prev_timestamp)) * 24 * 60 > 10
            """.format(time_period_days))
            
            total_gaps = cursor.fetchone()[0]
            
            # Overall completeness score
            discovery_score = min(1.0, total_devices / 4)  # Expect 4 devices (2 Hue, 1 Amazon, 1 Nest)
            completeness_score = (
                discovery_score * 0.3 +
                collection_rate * 0.5 +
                location_accuracy * 0.2
            )
            
            status = "EXCELLENT" if completeness_score >= 0.95 else "GOOD" if completeness_score >= 0.75 else "FAIR" if completeness_score >= 0.50 else "POOR"
            
            result = {
                "status": status,
                "completeness_score": round(completeness_score, 4),
                "discovery_score": round(discovery_score, 4),
                "collection_rate": round(collection_rate, 4),
                "location_accuracy": round(location_accuracy, 4),
                "time_period_days": time_period_days,
                "duration_hours": round(duration_hours, 2),
                "total_readings": total_readings,
                "expected_readings": round(expected_total, 1),
                "total_devices": total_devices,
                "devices_by_type": devices_by_type,
                "devices_with_location": devices_with_location,
                "total_gaps_over_10min": total_gaps,
                "device_breakdown": [
                    {
                        "device_type": row[0],
                        "device_id": row[1][:50],  # Truncate long IDs
                        "location": row[2],
                        "reading_count": row[3],
                        "expected_count": round(expected_per_device, 1),
                        "collection_rate": round(row[3] / expected_per_device, 4) if expected_per_device > 0 else 0
                    }
                    for row in device_readings
                ]
            }
            
            conn.close()
            
            self.logger.info(
                "Collection completeness evaluated",
                score=result["completeness_score"],
                status=status,
                devices=total_devices,
                readings=total_readings
            )
            
            return result
            
        except Exception as e:
            self.logger.error("Error evaluating collection completeness", error=str(e))
            return {
                "status": "ERROR",
                "error": str(e),
                "completeness_score": 0.0
            }


class DataQualityCorrectnessEvaluator:
    """
    Evaluates data quality and correctness.
    
    Metrics:
    - ISO 8601 timestamp format validation
    - Temperature value validation (within valid range)
    - Device ID format validation
    - Location metadata presence
    - Data type correctness
    """
    
    def __init__(self, db_path: str, logger: StructuredLogger):
        self.db_path = db_path
        self.logger = logger
        self.min_temp = -10.0
        self.max_temp = 50.0
    
    def evaluate(self, time_period_days: int = 1, sample_size: int = 1000) -> Dict[str, Any]:
        """
        Evaluate data quality for the specified time period.
        
        Args:
            time_period_days: Number of days to analyze
            sample_size: Number of readings to validate
            
        Returns:
            Dict with quality metrics
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Sample readings for validation
            cursor.execute("""
                SELECT 
                    id,
                    timestamp,
                    device_id,
                    temperature_celsius,
                    location,
                    device_type,
                    battery_level
                FROM readings
                WHERE timestamp >= datetime('now', '-{} days')
                ORDER BY RANDOM()
                LIMIT {}
            """.format(time_period_days, sample_size))
            
            readings = cursor.fetchall()
            
            if not readings:
                self.logger.warning("No readings to validate", days=time_period_days)
                return {
                    "status": "NO_DATA",
                    "quality_score": 0.0
                }
            
            # Validation counters
            valid_timestamps = 0
            valid_temperatures = 0
            valid_device_ids = 0
            valid_locations = 0
            valid_battery_levels = 0
            
            issues = []
            
            for reading in readings:
                reading_id, timestamp, device_id, temp, location, device_type, battery = reading
                
                # Validate timestamp (ISO 8601 with timezone)
                try:
                    if timestamp and ("T" in timestamp and ("+" in timestamp or "Z" in timestamp or timestamp.endswith("+00:00"))):
                        # Try parsing
                        datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                        valid_timestamps += 1
                    else:
                        issues.append({"reading_id": reading_id, "issue": "invalid_timestamp_format", "value": timestamp})
                except (ValueError, AttributeError):
                    issues.append({"reading_id": reading_id, "issue": "timestamp_parse_error", "value": timestamp})
                
                # Validate temperature
                if temp is not None and self.min_temp <= temp <= self.max_temp:
                    valid_temperatures += 1
                elif temp is not None:
                    issues.append({"reading_id": reading_id, "issue": "temperature_out_of_range", "value": temp})
                
                # Validate device ID (should have type prefix)
                if device_id and ("hue:" in device_id or "alexa:" in device_id or "nest:" in device_id):
                    valid_device_ids += 1
                else:
                    issues.append({"reading_id": reading_id, "issue": "invalid_device_id_format", "value": device_id})
                
                # Validate location
                if location and location.strip():
                    valid_locations += 1
                else:
                    issues.append({"reading_id": reading_id, "issue": "missing_location", "device_id": device_id})
                
                # Validate battery level (if present, should be 0-100)
                if battery is not None:
                    if 0 <= battery <= 100:
                        valid_battery_levels += 1
                    else:
                        issues.append({"reading_id": reading_id, "issue": "battery_out_of_range", "value": battery})
            
            num_readings = len(readings)
            
            # Calculate scores
            timestamp_score = valid_timestamps / num_readings if num_readings > 0 else 0
            temperature_score = valid_temperatures / num_readings if num_readings > 0 else 0
            device_id_score = valid_device_ids / num_readings if num_readings > 0 else 0
            location_score = valid_locations / num_readings if num_readings > 0 else 0
            
            # Overall quality score (weighted average)
            quality_score = (
                timestamp_score * 0.25 +
                temperature_score * 0.30 +
                device_id_score * 0.25 +
                location_score * 0.20
            )
            
            status = "EXCELLENT" if quality_score >= 0.98 else "GOOD" if quality_score >= 0.90 else "FAIR" if quality_score >= 0.75 else "POOR"
            
            result = {
                "status": status,
                "quality_score": round(quality_score, 4),
                "timestamp_validity": round(timestamp_score, 4),
                "temperature_validity": round(temperature_score, 4),
                "device_id_validity": round(device_id_score, 4),
                "location_validity": round(location_score, 4),
                "total_readings_validated": num_readings,
                "issues_found": len(issues),
                "issues_sample": issues[:10]  # First 10 issues
            }
            
            conn.close()
            
            self.logger.info(
                "Data quality evaluated",
                score=result["quality_score"],
                status=status,
                validated=num_readings,
                issues=len(issues)
            )
            
            return result
            
        except Exception as e:
            self.logger.error("Error evaluating data quality", error=str(e))
            return {
                "status": "ERROR",
                "error": str(e),
                "quality_score": 0.0
            }


class SystemReliabilityEvaluator:
    """
    Evaluates system reliability and error handling.
    
    Metrics:
    - Database lock errors (from logs)
    - Retry attempt frequency and success rate
    - System uptime and data gaps
    - Error rate analysis
    """
    
    def __init__(self, db_path: str, log_file_path: str, logger: StructuredLogger):
        self.db_path = db_path
        self.log_file_path = log_file_path
        self.logger = logger
    
    def evaluate(self, time_period_days: int = 1) -> Dict[str, Any]:
        """
        Evaluate system reliability for the specified time period.
        
        Args:
            time_period_days: Number of days to analyze
            
        Returns:
            Dict with reliability metrics
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get database statistics
            cursor.execute("""
                SELECT COUNT(*), MIN(timestamp), MAX(timestamp)
                FROM readings
                WHERE timestamp >= datetime('now', '-{} days')
            """.format(time_period_days))
            
            total_readings, min_time, max_time = cursor.fetchone()
            
            if not min_time or not max_time:
                return {
                    "status": "NO_DATA",
                    "reliability_score": 0.0
                }
            
            # Parse log file for errors
            log_path = Path(self.log_file_path)
            db_lock_errors = 0
            retry_attempts = 0
            total_errors = 0
            error_types = {}
            
            if log_path.exists():
                with open(log_path, 'r') as f:
                    for line in f:
                        try:
                            log_entry = json.loads(line.strip())
                            level = log_entry.get('level', '')
                            message = log_entry.get('message', '')
                            
                            # Count errors
                            if level in ['ERROR', 'CRITICAL']:
                                total_errors += 1
                                error_types[message] = error_types.get(message, 0) + 1
                            
                            # Count database lock errors
                            if 'database' in message.lower() and 'lock' in message.lower():
                                db_lock_errors += 1
                            
                            # Count retry attempts
                            if 'retry' in message.lower() and 'attempt' in message.lower():
                                retry_attempts += 1
                                
                        except json.JSONDecodeError:
                            continue
            
            # Calculate uptime metrics
            start_dt = datetime.fromisoformat(min_time.replace('+00:00', '')).replace(tzinfo=timezone.utc)
            end_dt = datetime.fromisoformat(max_time.replace('+00:00', '')).replace(tzinfo=timezone.utc)
            duration_hours = (end_dt - start_dt).total_seconds() / 3600
            
            # Check WAL mode
            cursor.execute("PRAGMA journal_mode")
            journal_mode = cursor.fetchone()[0]
            wal_enabled = journal_mode.upper() == 'WAL'
            
            # Calculate reliability scores
            db_lock_score = 1.0 if db_lock_errors == 0 else 0.5 if db_lock_errors < 5 else 0.0
            wal_score = 1.0 if wal_enabled else 0.0
            uptime_score = 1.0 if duration_hours >= 24 else duration_hours / 24
            
            # Error rate per hour
            error_rate = total_errors / duration_hours if duration_hours > 0 else 0
            error_score = 1.0 if error_rate < 1 else 0.8 if error_rate < 5 else 0.5 if error_rate < 10 else 0.0
            
            # Overall reliability score
            reliability_score = (
                db_lock_score * 0.35 +
                wal_score * 0.25 +
                uptime_score * 0.20 +
                error_score * 0.20
            )
            
            status = "EXCELLENT" if reliability_score >= 0.95 else "GOOD" if reliability_score >= 0.80 else "FAIR" if reliability_score >= 0.60 else "POOR"
            
            result = {
                "status": status,
                "reliability_score": round(reliability_score, 4),
                "db_lock_score": round(db_lock_score, 4),
                "wal_score": round(wal_score, 4),
                "uptime_score": round(uptime_score, 4),
                "error_score": round(error_score, 4),
                "database_lock_errors": db_lock_errors,
                "retry_attempts": retry_attempts,
                "total_errors": total_errors,
                "error_rate_per_hour": round(error_rate, 2),
                "wal_mode_enabled": wal_enabled,
                "journal_mode": journal_mode,
                "duration_hours": round(duration_hours, 2),
                "total_readings": total_readings,
                "top_errors": sorted(error_types.items(), key=lambda x: x[1], reverse=True)[:5]
            }
            
            conn.close()
            
            self.logger.info(
                "System reliability evaluated",
                score=result["reliability_score"],
                status=status,
                db_locks=db_lock_errors,
                errors=total_errors
            )
            
            return result
            
        except Exception as e:
            self.logger.error("Error evaluating system reliability", error=str(e))
            return {
                "status": "ERROR",
                "error": str(e),
                "reliability_score": 0.0
            }


def run_evaluation(
    time_period_days: int = 1,
    output_path: str = "data/evaluation_results.json"
) -> Dict[str, Any]:
    """
    Run comprehensive evaluation of the temperature monitoring system.
    
    Args:
        time_period_days: Number of days to analyze
        output_path: Path to save evaluation results
        
    Returns:
        Dictionary containing evaluation results
    """
    # Load config and initialize logger
    config = load_config()
    logger = StructuredLogger(config)
    
    logger.info("=" * 80)
    logger.info("Starting Temperature Monitoring System Evaluation", days=time_period_days)
    logger.info("=" * 80)
    
    # Resolve paths
    workspace_root = Path(__file__).parent.parent
    db_path = workspace_root / "data" / "readings.db"
    log_path = workspace_root / config.get('logging', {}).get('log_file_path', 'logs/collection.log')
    results_file = workspace_root / output_path
    
    if not db_path.exists():
        logger.error("Database file not found", path=str(db_path))
        return {"status": "ERROR", "message": f"Database file not found: {db_path}"}
    
    logger.info("Using database", path=str(db_path))
    logger.info("Using log file", path=str(log_path))
    logger.info("Results will be saved to", path=str(results_file))
    
    # Initialize evaluators
    logger.info("Initializing evaluators")
    
    completeness_evaluator = CollectionCompletenessEvaluator(str(db_path), logger)
    quality_evaluator = DataQualityCorrectnessEvaluator(str(db_path), logger)
    reliability_evaluator = SystemReliabilityEvaluator(str(db_path), str(log_path), logger)
    
    logger.info("Running evaluation framework")
    
    # Run evaluations
    results = {
        "evaluation_metadata": {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "time_period_days": time_period_days,
            "database_path": str(db_path),
            "log_file_path": str(log_path)
        },
        "collection_completeness": completeness_evaluator.evaluate(time_period_days),
        "data_quality_correctness": quality_evaluator.evaluate(time_period_days),
        "system_reliability": reliability_evaluator.evaluate(time_period_days)
    }
    
    # Calculate overall score
    overall_score = (
        results["collection_completeness"].get("completeness_score", 0) * 0.35 +
        results["data_quality_correctness"].get("quality_score", 0) * 0.30 +
        results["system_reliability"].get("reliability_score", 0) * 0.35
    )
    
    results["overall_score"] = round(overall_score, 4)
    results["overall_status"] = (
        "EXCELLENT" if overall_score >= 0.95 else
        "GOOD" if overall_score >= 0.80 else
        "FAIR" if overall_score >= 0.60 else
        "POOR"
    )
    
    # Save results
    results_file.parent.mkdir(parents=True, exist_ok=True)
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info("Evaluation completed successfully")
    logger.info("=" * 80)
    logger.info("EVALUATION SUMMARY")
    logger.info("=" * 80)
    logger.info("Overall Score", score=results["overall_score"], status=results["overall_status"])
    logger.info("Collection Completeness", score=results["collection_completeness"].get("completeness_score", 0))
    logger.info("Data Quality", score=results["data_quality_correctness"].get("quality_score", 0))
    logger.info("System Reliability", score=results["system_reliability"].get("reliability_score", 0))
    logger.info("Results saved to", path=str(results_file))
    logger.info("=" * 80)
    
    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate Home Temperature Monitoring System")
    parser.add_argument(
        "--days",
        type=int,
        default=1,
        help="Number of days to analyze (default: 1)"
    )
    parser.add_argument(
        "--output-path",
        type=str,
        default="data/evaluation_results.json",
        help="Output path for results (default: data/evaluation_results.json)"
    )
    
    args = parser.parse_args()
    
    try:
        results = run_evaluation(
            time_period_days=args.days,
            output_path=args.output_path
        )
        sys.exit(0 if results.get("overall_status") in ["EXCELLENT", "GOOD"] else 1)
    except Exception as e:
        print(f"Fatal error: {str(e)}", file=sys.stderr)
        sys.exit(1)
