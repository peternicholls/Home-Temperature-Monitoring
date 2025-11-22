#!/usr/bin/env python3
"""
Evaluation framework for Home Temperature Monitoring System.

This module implements comprehensive evaluation of the temperature collection system
using custom evaluators for:
1. Collection Completeness - Verify sensor discovery and reading collection
2. Data Quality & Correctness - Validate format, temperature ranges, metadata
3. System Reliability - Measure error handling and data persistence
"""

import os
import json
import sys
from pathlib import Path
from typing import Dict, Any, Optional
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Try to import Azure AI Evaluation SDK
try:
    from azure.ai.evaluation import evaluate
    AZURE_AI_AVAILABLE = True
except ImportError:
    AZURE_AI_AVAILABLE = False
    logger.warning("azure-ai-evaluation not installed. Install with: pip install azure-ai-evaluation")


class BaseEvaluator:
    """
    Base class for all evaluators to reduce code duplication.
    
    Provides common functionality:
    - Loading evaluation responses from JSON file
    - Extracting scenario response by query_id
    - Error handling patterns
    - Standardized return format
    """
    
    def __init__(self, name: str):
        """
        Initialize base evaluator.
        
        Args:
            name: Name of the evaluator (e.g., 'collection_completeness')
        """
        self.name = name
    
    def _load_responses_file(self) -> Optional[Path]:
        """
        Load the evaluation responses file path.
        
        Returns:
            Path to responses file, or None if not found
        """
        responses_file = Path(__file__).parent.parent / "data" / "evaluation_responses.json"
        return responses_file if responses_file.exists() else None
    
    def _get_scenario_response(self, query_id: str) -> Optional[Dict[str, Any]]:
        """
        Extract scenario response for a given query_id.
        
        Args:
            query_id: Unique query identifier
            
        Returns:
            Dict containing scenario response data, or None if not found
        """
        responses_file = self._load_responses_file()
        
        if not responses_file:
            return None
        
        try:
            with open(responses_file) as f:
                eval_data = json.load(f)
            
            # Extract scenario response
            for response in eval_data.get("evaluation_responses", []):
                if response.get("query_id") == query_id:
                    return response
            
            return None
        except Exception as e:
            logger.error(f"Error loading scenario response for {query_id}: {str(e)}")
            return None
    
    def _create_error_response(
        self,
        query_id: str,
        score_key: str,
        status: str,
        reason: Optional[str] = None,
        error: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create standardized error response.
        
        Args:
            query_id: Unique query identifier
            score_key: Name of the score field (e.g., 'completeness_score')
            status: Status string (e.g., 'FAIL', 'ERROR', 'NO_DATA')
            reason: Optional reason for the error
            error: Optional error message
            
        Returns:
            Dict with error response
        """
        response = {
            "query_id": query_id,
            score_key: 0.0,
            "status": status
        }
        if reason:
            response["reason"] = reason
        if error:
            response["error"] = error
        return response


class CollectionCompletenessEvaluator(BaseEvaluator):
    """
    Evaluates sensor discovery and reading collection completeness.
    
    Metrics:
    - Sensor discovery rate (expected_sensors vs actual)
    - Reading collection rate (expected_readings vs actual)
    - Location mapping accuracy
    """
    
    def __init__(self):
        super().__init__("collection_completeness")
    
    def __call__(
        self,
        *,
        query_id: str,
        scenario: str,
        expected_sensors: int,
        expected_readings: int,
        expected_locations: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Evaluate collection completeness for a given query.
        
        Args:
            query_id: Unique query identifier
            scenario: Description of the test scenario
            expected_sensors: Number of sensors expected to be discovered
            expected_readings: Number of readings expected to be collected
            expected_locations: Comma-separated expected sensor locations
            
        Returns:
            Dict with completeness score (0-1), status, and details
        """
        try:
            # Normalize numeric inputs
            expected_sensors = int(expected_sensors) if expected_sensors else 0
            expected_readings = int(expected_readings) if expected_readings else 0
            
            # Use base class method to check file exists
            responses_file = self._load_responses_file()
            if not responses_file:
                return self._create_error_response(
                    query_id,
                    "completeness_score",
                    "FAIL",
                    reason="No evaluation responses file found",
                    error="evaluation_responses.json missing"
                )
            
            # Use base class method to get scenario response
            scenario_response = self._get_scenario_response(query_id)
            if not scenario_response:
                return self._create_error_response(
                    query_id,
                    "completeness_score",
                    "NO_DATA",
                    reason=f"No response data found for {query_id}"
                )
            
            # Calculate completeness metrics
            sensors_found = scenario_response.get("sensors_found", 0)
            sensors_collected = scenario_response.get("sensors_collected", 0)
            readings_collected = len(scenario_response.get("readings_collected", []))
            
            # Discovery completeness
            discovery_rate = sensors_found / expected_sensors if expected_sensors > 0 else 0
            
            # Collection completeness
            collection_rate = readings_collected / expected_readings if expected_readings > 0 else 0
            
            # Location mapping completeness
            location_accuracy = 1.0
            if expected_locations and isinstance(expected_locations, str):
                expected_locs = set(loc.strip() for loc in expected_locations.split(","))
                actual_locs = set()
                for reading in scenario_response.get("readings_collected", []):
                    actual_locs.add(reading.get("location", ""))
                
                if expected_locs and actual_locs:
                    matched = len(expected_locs & actual_locs)
                    location_accuracy = matched / len(expected_locs) if expected_locs else 0
            
            # Overall completeness score (weighted average)
            completeness_score = (discovery_rate * 0.3 + collection_rate * 0.5 + location_accuracy * 0.2)
            
            status = "PASS" if completeness_score >= 0.95 else "PARTIAL" if completeness_score >= 0.70 else "FAIL"
            
            return {
                "query_id": query_id,
                "scenario": scenario,
                "completeness_score": round(completeness_score, 2),
                "status": status,
                "discovery_rate": round(discovery_rate, 2),
                "collection_rate": round(collection_rate, 2),
                "location_accuracy": round(location_accuracy, 2),
                "sensors_found": sensors_found,
                "expected_sensors": expected_sensors,
                "readings_collected": readings_collected,
                "expected_readings": expected_readings
            }
        
        except Exception as e:
            logger.error(f"Error evaluating collection completeness for {query_id}: {str(e)}")
            return self._create_error_response(
                query_id,
                "completeness_score",
                "ERROR",
                error=str(e)
            )


class DataQualityCorrectnessEvaluator(BaseEvaluator):
    """
    Evaluates data quality and correctness.
    
    Metrics:
    - ISO 8601 timestamp format validation
    - Temperature value validation (within valid range)
    - Device ID format validation (hue: prefix)
    - Battery level validation (0-100)
    - Location metadata presence and validity
    """
    
    def __init__(self):
        super().__init__("data_quality_correctness")
        self.min_temp = -10.0
        self.max_temp = 50.0
    
    def __call__(
        self,
        *,
        query_id: str,
        scenario: str,
        expected_temperature_range: Optional[str] = None,
        expected_locations: Optional[str] = None,
        expected_format: str = "ISO 8601",
        **kwargs
    ) -> Dict[str, Any]:
        """
        Evaluate data quality and correctness for a given query.
        
        Args:
            query_id: Unique query identifier
            scenario: Description of the test scenario
            expected_temperature_range: Expected temperature range (e.g., "15-25")
            expected_locations: Comma-separated expected sensor locations
            expected_format: Expected data format (default: ISO 8601)
            
        Returns:
            Dict with quality score (0-1), status, and validation details
        """
        try:
            # Use base class method to check file exists
            responses_file = self._load_responses_file()
            if not responses_file:
                return self._create_error_response(
                    query_id,
                    "quality_score",
                    "FAIL",
                    reason="No evaluation responses file found"
                )
            
            # Use base class method to get scenario response
            scenario_response = self._get_scenario_response(query_id)
            if not scenario_response:
                return self._create_error_response(
                    query_id,
                    "quality_score",
                    "NO_DATA"
                )
            
            readings = scenario_response.get("readings_collected", [])
            if not readings:
                return self._create_error_response(
                    query_id,
                    "quality_score",
                    "NO_READINGS"
                )
            
            # Validation scores
            valid_timestamps = 0
            valid_temperatures = 0
            valid_device_ids = 0
            valid_battery_levels = 0
            valid_locations = 0
            
            for reading in readings:
                # Validate timestamp (ISO 8601)
                timestamp = reading.get("timestamp", "")
                if "T" in timestamp and ("+" in timestamp or "Z" in timestamp):
                    valid_timestamps += 1
                
                # Validate temperature
                temp = reading.get("temperature_celsius", None)
                if temp is not None and self.min_temp <= temp <= self.max_temp:
                    valid_temperatures += 1
                
                # Validate device ID (hue: prefix)
                device_id = reading.get("device_id", "")
                if device_id.startswith("hue:"):
                    valid_device_ids += 1
                
                # Validate battery level (0-100)
                battery = reading.get("battery_level", None)
                if battery is not None and 0 <= battery <= 100:
                    valid_battery_levels += 1
                
                # Validate location
                location = reading.get("location", "")
                if location and location.strip():
                    valid_locations += 1
            
            num_readings = len(readings)
            
            # Calculate scores
            timestamp_score = valid_timestamps / num_readings if num_readings > 0 else 0
            temperature_score = valid_temperatures / num_readings if num_readings > 0 else 0
            device_id_score = valid_device_ids / num_readings if num_readings > 0 else 0
            battery_score = valid_battery_levels / num_readings if num_readings > 0 else 0
            location_score = valid_locations / num_readings if num_readings > 0 else 0
            
            # Overall quality score (weighted average)
            quality_score = (
                timestamp_score * 0.25 +
                temperature_score * 0.25 +
                device_id_score * 0.20 +
                battery_score * 0.15 +
                location_score * 0.15
            )
            
            status = "PASS" if quality_score >= 0.95 else "PARTIAL" if quality_score >= 0.70 else "FAIL"
            
            return {
                "query_id": query_id,
                "scenario": scenario,
                "quality_score": round(quality_score, 2),
                "status": status,
                "timestamp_validity": round(timestamp_score, 2),
                "temperature_validity": round(temperature_score, 2),
                "device_id_validity": round(device_id_score, 2),
                "battery_validity": round(battery_score, 2),
                "location_validity": round(location_score, 2),
                "total_readings_validated": num_readings
            }
        
        except Exception as e:
            logger.error(f"Error evaluating data quality for {query_id}: {str(e)}")
            return self._create_error_response(
                query_id,
                "quality_score",
                "ERROR",
                error=str(e)
            )


class SystemReliabilityEvaluator(BaseEvaluator):
    """
    Evaluates system reliability and error handling.
    
    Metrics:
    - Collection success rate
    - Duplicate prevention effectiveness
    - Database persistence accuracy
    - Error handling and recovery
    """
    
    def __init__(self):
        super().__init__("system_reliability")
    
    def __call__(
        self,
        *,
        query_id: str,
        scenario: str,
        expected_success: bool = True,
        expected_duplicates: int = 0,
        expected_error: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Evaluate system reliability for a given query.
        
        Args:
            query_id: Unique query identifier
            scenario: Description of the test scenario
            expected_success: Whether successful execution is expected
            expected_duplicates: Expected number of duplicate readings
            expected_error: Expected error type (if failure is expected)
            
        Returns:
            Dict with reliability score (0-1), status, and details
        """
        try:
            # Use base class method to check file exists
            responses_file = self._load_responses_file()
            if not responses_file:
                return self._create_error_response(
                    query_id,
                    "reliability_score",
                    "FAIL",
                    reason="No evaluation responses file found"
                )
            
            # Use base class method to get scenario response
            scenario_response = self._get_scenario_response(query_id)
            if not scenario_response:
                return self._create_error_response(
                    query_id,
                    "reliability_score",
                    "NO_DATA"
                )
            
            # Check execution result
            execution_result = scenario_response.get("execution_result")
            success_as_expected = (execution_result == "success") == expected_success
            
            # Check database persistence
            db_stored = scenario_response.get("database_stored", 0)
            db_errors = scenario_response.get("database_errors", 0)
            db_duplicates = scenario_response.get("database_duplicates", 0)
            
            # Calculate reliability metrics
            execution_score = 1.0 if success_as_expected else 0.0
            
            # Duplicate prevention score
            duplicate_score = 1.0 if db_duplicates == expected_duplicates else 0.5
            
            # Database persistence score
            persistence_score = 1.0 if db_errors == 0 else 0.0
            
            # Error handling score (success rate for multi-cycle operations)
            collection_success_rate = 1.0
            if "readings_collected" in scenario_response:
                readings = scenario_response.get("readings_collected", [])
                if readings:
                    # All readings successfully collected and stored
                    readings_vs_stored = db_stored / len(readings) if readings else 0
                    collection_success_rate = min(1.0, readings_vs_stored)
            
            # Overall reliability score (weighted average)
            reliability_score = (
                execution_score * 0.25 +
                collection_success_rate * 0.35 +
                duplicate_score * 0.25 +
                persistence_score * 0.15
            )
            
            status = "PASS" if reliability_score >= 0.95 else "PARTIAL" if reliability_score >= 0.70 else "FAIL"
            
            return {
                "query_id": query_id,
                "scenario": scenario,
                "reliability_score": round(reliability_score, 2),
                "status": status,
                "execution_score": round(execution_score, 2),
                "collection_success_rate": round(collection_success_rate, 2),
                "duplicate_prevention_score": round(duplicate_score, 2),
                "persistence_score": round(persistence_score, 2),
                "database_stored": db_stored,
                "database_errors": db_errors,
                "database_duplicates": db_duplicates
            }
        
        except Exception as e:
            logger.error(f"Error evaluating system reliability for {query_id}: {str(e)}")
            return self._create_error_response(
                query_id,
                "reliability_score",
                "ERROR",
                error=str(e)
            )


def run_evaluation(
    data_path: str = "data/evaluation_data.jsonl",
    output_path: str = "data/evaluation_results.json"
) -> Dict[str, Any]:
    """
    Run comprehensive evaluation of the temperature monitoring system.
    
    Args:
        data_path: Path to evaluation data file (JSONL format)
        output_path: Path to save evaluation results
        
    Returns:
        Dictionary containing evaluation results
    """
    if not AZURE_AI_AVAILABLE:
        logger.error("azure-ai-evaluation is required to run evaluations")
        return {"status": "ERROR", "message": "azure-ai-evaluation not installed"}
    
    logger.info("=" * 80)
    logger.info("🎯 Starting Temperature Monitoring System Evaluation")
    logger.info("=" * 80)
    
    # Resolve paths relative to workspace root
    workspace_root = Path(__file__).parent.parent
    data_file = workspace_root / data_path
    results_file = workspace_root / output_path
    
    if not data_file.exists():
        logger.error(f"❌ Evaluation data file not found: {data_file}")
        return {"status": "ERROR", "message": f"Data file not found: {data_file}"}
    
    logger.info(f"📂 Using evaluation data: {data_file}")
    logger.info(f"💾 Results will be saved to: {results_file}")
    
    # Initialize evaluators
    logger.info("\n📊 Initializing custom evaluators...")
    evaluators = {
        "collection_completeness": CollectionCompletenessEvaluator(),
        "data_quality_correctness": DataQualityCorrectnessEvaluator(),
        "system_reliability": SystemReliabilityEvaluator()
    }
    logger.info("✅ Evaluators initialized successfully")
    
    # Define evaluator configuration for data mapping
    evaluator_config = {
        "collection_completeness": {
            "column_mapping": {
                "query_id": "${data.query_id}",
                "scenario": "${data.scenario}",
                "expected_sensors": "${data.expected_sensors}",
                "expected_readings": "${data.expected_readings}",
                "expected_locations": "${data.expected_locations}"
            }
        },
        "data_quality_correctness": {
            "column_mapping": {
                "query_id": "${data.query_id}",
                "scenario": "${data.scenario}",
                "expected_temperature_range": "${data.expected_temperature_range}",
                "expected_locations": "${data.expected_locations}",
                "expected_format": "${data.expected_format}"
            }
        },
        "system_reliability": {
            "column_mapping": {
                "query_id": "${data.query_id}",
                "scenario": "${data.scenario}",
                "expected_success": "${data.expected_success}",
                "expected_duplicates": "${data.expected_duplicates}",
                "expected_error": "${data.expected_error}"
            }
        }
    }
    
    try:
        logger.info("\n🚀 Running evaluation framework...")
        logger.info(f"📋 Processing {sum(1 for _ in open(data_file))} evaluation scenarios...\n")
        
        # Run the evaluate API
        result = evaluate(
            data=str(data_file),
            evaluators=evaluators,
            evaluator_config=evaluator_config,
            output_path=str(results_file),
            display_progress_bar=True
        )
        
        logger.info("\n✅ Evaluation completed successfully!")
        logger.info("=" * 80)
        
        # Calculate aggregate metrics
        if hasattr(result, 'to_dict'):
            result_dict = result.to_dict()
        else:
            result_dict = dict(result)
        
        # Log summary
        logger.info("\n📈 EVALUATION SUMMARY")
        logger.info("=" * 80)
        
        metrics = result_dict.get("metrics", {})
        
        for metric_name, metric_value in metrics.items():
            logger.info(f"  {metric_name}: {metric_value}")
        
        logger.info("\n✅ Full results saved to: " + str(results_file))
        logger.info("=" * 80 + "\n")
        
        return result_dict
    
    except Exception as e:
        logger.error(f"\n❌ Evaluation failed with error: {str(e)}")
        logger.error("=" * 80)
        raise


if __name__ == "__main__":
    try:
        results = run_evaluation()
        sys.exit(0)
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        sys.exit(1)
